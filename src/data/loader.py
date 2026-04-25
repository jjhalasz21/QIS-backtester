from __future__ import annotations
import pandas as pd
import yfinance as yf
import pandas_datareader as pdr
from src.data.cache import cache_key, load, save


def fetch_prices(
    ticker: str,
    start: str,
    end: str,
    force_refresh: bool = False,
) -> pd.Series:
    """Fetch adjusted close prices from yfinance. Returns pd.Series indexed by date."""
    key = cache_key(ticker, start, end)
    if not force_refresh:
        cached = load(key)
        if cached is not None:
            return cached["close"]

    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"yfinance returned no data for {ticker} ({start}–{end})")

    series = df["Close"].squeeze()
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

    df = pdr.get_data_fred(series_id, start=start, end=end)
    if df.empty:
        raise ValueError(f"FRED returned no data for {series_id} ({start}–{end})")

    series = df.iloc[:, 0].dropna()
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
