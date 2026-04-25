from __future__ import annotations
import numpy as np
import pandas as pd
from src.strategies.base import BaseStrategy
from src.data.loader import fetch_prices
from src.analytics import tearsheet
from src.engine.costs import get_cost_bps
from src.utils.config import SPY_TICKER, VOL_TARGET, MAX_LEVERAGE, VOL_LOOKBACK, TRADING_DAYS_PER_YEAR


def _fetch_spy(start: str, end: str) -> pd.Series:
    return fetch_prices(SPY_TICKER, start, end)


class VolTarget(BaseStrategy):
    name = "Vol-Targeted SPX — Capital-Efficient Equity"
    description = (
        "Dynamic SPX exposure scaled inversely to 20-day realized vol, "
        "targeting 10% annualized portfolio vol. Capped at 150% notional."
    )
    instrument_type = "futures"

    def __init__(self) -> None:
        self._equity: pd.Series | None = None
        self._metrics: dict | None = None
        self._trade_log: pd.DataFrame | None = None
        self._weights_series: pd.Series | None = None

    def run(
        self,
        start: str,
        end: str,
        cost_mode: str = "default",
        custom_bps: float = 0.0,
    ) -> None:
        spy = _fetch_spy(start, end)
        spy = spy.sort_index().dropna()
        spy_returns = spy.pct_change().dropna()

        realized = spy_returns.rolling(VOL_LOOKBACK).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        realized = realized.dropna()

        weights = (VOL_TARGET / realized).clip(upper=MAX_LEVERAGE)
        aligned_returns = spy_returns.reindex(weights.index)

        cost_bps = get_cost_bps(self.instrument_type, cost_mode, custom_bps)

        prev_weights = weights.shift(1).fillna(0.0)
        weight_change = (weights - prev_weights).abs()

        gross_returns = weights * aligned_returns
        cost_drag = weight_change * cost_bps / 10_000
        net_returns = gross_returns - cost_drag

        self._equity = (1 + net_returns).cumprod() * 100
        self._equity.name = self.name
        self._weights_series = weights

        trades = []
        for dt in weights.index:
            chg = float(weight_change.loc[dt])
            if chg > 0.001:
                trades.append({
                    "date": dt,
                    "notional": chg,
                    "gross_pnl": float(gross_returns.loc[dt]),
                    "cost_bps": cost_bps,
                    "net_pnl": float(net_returns.loc[dt]),
                })
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

    def weights(self) -> pd.Series:
        if self._weights_series is None:
            raise RuntimeError("Call run() first")
        return self._weights_series

    def institutional_framing(self) -> dict:
        return {
            "return_profile": (
                "Equity-like but smoother. Dynamic leverage scales down in high-vol regimes, "
                "producing lower average vol and shallower drawdowns than static SPX exposure. "
                "Expected to underperform in low-vol bull markets due to leverage cap."
            ),
            "capital_efficiency": (
                "More predictable capital consumption than static equity — vol targeting keeps "
                "realized vol near 10%, reducing the variability of the Solvency II symmetric "
                "adjustment and making regulatory capital planning more stable."
            ),
            "regulatory_treatment": (
                "Treated as equity under Solvency II SCR-equity sub-module. "
                "SCR proxy: 39% × |max 1-year drawdown|. Lower realized drawdown vs. SPX "
                "means a lower estimated SCR charge. NAIC RBC: C-1 factor scaled by vol ratio."
            ),
            "liability_fit": (
                "Return-seeking, not hedging. Suitable for insurance surplus accounts wanting "
                "equity-like long-run returns with more predictable short-run drawdowns — "
                "directly addresses the 'lumpy capital charges' problem under Solvency II."
            ),
            "structurer_pitch": (
                "Pitch to insurance CIOs frustrated by equity SCR volatility — vol targeting "
                "makes equity risk consumption more stable quarter-to-quarter without reducing "
                "long-run return potential."
            ),
        }
