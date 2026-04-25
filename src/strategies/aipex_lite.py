from __future__ import annotations
import pandas as pd
from src.strategies.base import BaseStrategy
from src.data.loader import fetch_prices
from src.analytics import tearsheet
from src.engine.costs import get_cost_bps
from src.utils.config import (
    SECTOR_ETFS, VIX_TICKER,
    VIX_RISK_OFF_THRESHOLD, AIPEX_TOP_N,
)


def _fetch_prices(ticker: str, start: str, end: str, **kwargs) -> pd.Series:
    return fetch_prices(ticker, start, end, **kwargs)


class AiPexLite(BaseStrategy):
    name = "AiPEX-Lite — AI-Driven Factor Rotation"
    description = (
        "Monthly sector ETF rotation using 12-1 month momentum + VIX risk-on/off gate. "
        "Equal-weights top 3 of 5 S&P 500 sector ETFs (XLK, XLF, XLV, XLE, XLY). "
        "Independently implemented, inspired by HSBC AiPEX concept."
    )
    instrument_type = "etf"

    def __init__(self) -> None:
        self._equity: pd.Series | None = None
        self._metrics: dict | None = None
        self._trade_log: pd.DataFrame | None = None

    def run(
        self,
        start: str,
        end: str,
        cost_mode: str = "default",
        custom_bps: float = 0.0,
    ) -> None:
        prices = {t: _fetch_prices(t, start, end) for t in SECTOR_ETFS}
        vix = _fetch_prices(VIX_TICKER, start, end)

        price_df = pd.DataFrame(prices).sort_index().dropna()
        vix = vix.reindex(price_df.index).ffill()

        cost_bps = get_cost_bps(self.instrument_type, cost_mode, custom_bps)
        monthly_ends = price_df.resample("ME").last().index

        trades = []
        portfolio_returns = []
        current_weights = pd.Series(0.0, index=SECTOR_ETFS)

        for i in range(1, len(monthly_ends)):
            signal_date = monthly_ends[i - 1]
            rebalance_date = monthly_ends[i]

            t_minus_12 = signal_date - pd.DateOffset(months=12)
            t_minus_1 = signal_date - pd.DateOffset(months=1)
            p_start = price_df.asof(t_minus_12)
            p_end = price_df.asof(t_minus_1)

            if p_start.isna().any() or p_end.isna().any():
                current_weights = pd.Series(1.0 / len(SECTOR_ETFS), index=SECTOR_ETFS)
                continue

            momentum = (p_end / p_start) - 1

            vix_level = float(vix.asof(signal_date))
            if vix_level > VIX_RISK_OFF_THRESHOLD:
                new_weights = current_weights
            else:
                top_sectors = momentum.nlargest(AIPEX_TOP_N).index.tolist()
                new_weights = pd.Series(0.0, index=SECTOR_ETFS)
                new_weights[top_sectors] = 1.0 / AIPEX_TOP_N

            p_entry = price_df.asof(signal_date)
            p_exit = price_df.asof(rebalance_date)
            month_ret = (p_exit / p_entry) - 1
            gross_ret = float((new_weights * month_ret).sum())

            turnover = float((new_weights - current_weights).abs().sum())
            cost_drag = turnover * cost_bps / 10_000
            net_ret = gross_ret - cost_drag

            portfolio_returns.append({"date": rebalance_date, "net_return": net_ret})

            if turnover > 0.001:
                trades.append({
                    "date": rebalance_date,
                    "notional": turnover,
                    "gross_pnl": gross_ret,
                    "cost_bps": cost_bps,
                    "net_pnl": net_ret,
                })

            current_weights = new_weights

        if not portfolio_returns:
            raise ValueError("Not enough data to compute AiPEX-Lite returns. Extend the backtest window.")

        ret_df = pd.DataFrame(portfolio_returns).set_index("date")
        equity = (1 + ret_df["net_return"]).cumprod() * 100
        self._equity = (equity / equity.iloc[0] * 100).rename(self.name)
        self._trade_log = pd.DataFrame(trades).set_index("date") if trades else pd.DataFrame()
        self._metrics = tearsheet.compute_all(self._equity)

    def metrics(self) -> dict:
        if self._metrics is None:
            raise RuntimeError("Call run() first")
        return self._metrics

    def equity_curve(self) -> pd.Series:
        if self._equity is None:
            raise RuntimeError("Call run() first")
        return self._equity

    def trade_log(self) -> pd.DataFrame:
        if self._trade_log is None:
            raise RuntimeError("Call run() first")
        return self._trade_log

    def institutional_framing(self) -> dict:
        return {
            "return_profile": (
                "Equity-like with factor tilt. Monthly sector rotation generates return dispersion "
                "vs. market-cap SPX. Not market-neutral — beta to equity is high. "
                "VIX gate reduces rotation in extreme vol events."
            ),
            "capital_efficiency": (
                "Sector ETF portfolio with monthly rotation maintains similar vol to SPX. "
                "VIX risk-off gate provides partial downside protection in tail events, "
                "modestly reducing max drawdown vs. static equity."
            ),
            "regulatory_treatment": (
                "Treated as equity under Solvency II SCR-equity sub-module. "
                "SCR proxy: 39% × |max 1-year drawdown|. "
                "NAIC RBC: C-1 factor ~30% of market value, adjusted for realized vol."
            ),
            "liability_fit": (
                "Return-seeking, not hedging. Suitable for insurance surplus accounts seeking "
                "active equity exposure with a transparent, auditable rules-based process — "
                "explicitly contrasts with black-box ML models."
            ),
            "structurer_pitch": (
                "Pitch to insurance CIOs seeking explainable factor equity exposure: "
                "rules-based, monthly, fully auditable, with a clear narrative around "
                "momentum and risk-off protection that can be presented to a board."
            ),
        }
