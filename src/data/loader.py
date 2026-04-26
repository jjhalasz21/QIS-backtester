from __future__ import annotations
import datetime
import io
import pandas as pd
import requests
import yfinance as yf
from src.data.cache import cache_key, load, load_covering, save


def fetch_prices(
    ticker: str,
    start: str,
    end: str,
    force_refresh: bool = False,
) -> pd.Series:
    """Fetch adjusted close prices from yfinance. Returns pd.Series indexed by date."""
    key = cache_key(ticker, start, end)
    if not force_refresh:
        # 1. exact cache hit
        cached = load(key)
        if cached is not None:
            return cached["close"]
        # 2. slice from any wider cached file — handles custom date ranges without network
        covering = load_covering(ticker, start, end)
        if covering is not None:
            return covering["close"]

    # Clamp end to yesterday — yfinance has no data for today or future dates
    end_clamped = str(min(
        pd.Timestamp(end).date(),
        datetime.date.today() - datetime.timedelta(days=1),
    ))
    df = yf.download(ticker, start=start, end=end_clamped, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"yfinance returned no data for {ticker} ({start}–{end_clamped})")

    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    series = close.squeeze()
    series.index = pd.to_datetime(series.index)
    save(key, pd.DataFrame({"close": series}))
    return series


def fetch_fred(
    series_id: str,
    start: str,
    end: str,
    force_refresh: bool = False,
) -> pd.Series:
    """Fetch a FRED series via pandas-datareader. Returns pd.Series indexed by date."""
    key = cache_key(series_id, start, end)
    if not force_refresh:
        cached = load(key)
        if cached is not None:
            return cached["value"]

    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text), parse_dates=["DATE"], index_col="DATE")
    df = df[(df.index >= pd.Timestamp(start)) & (df.index <= pd.Timestamp(end))]
    if df.empty:
        raise ValueError(f"FRED returned no data for {series_id} ({start}–{end})")

    series = df.iloc[:, 0].replace(".", float("nan")).astype(float).dropna()
    series.index = pd.to_datetime(series.index)
    save(key, pd.DataFrame({"value": series}))
    return series


def fetch_cboe_index(
    fred_id: str,
    yf_fallback: str,
    start: str,
    end: str,
    force_refresh: bool = False,
) -> pd.Series:
    """
    Fetch CBOE index. Tries FRED first; falls back to yfinance.
    FRED IDs: PUTWRITE (PUT index), BXMCBOE (BXM index).
    yfinance fallbacks: ^PUTR, ^BXM.
    """
    try:
        return fetch_fred(fred_id, start, end, force_refresh)
    except Exception:
        return fetch_prices(yf_fallback, start, end, force_refresh)
