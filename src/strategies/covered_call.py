from __future__ import annotations
import pandas as pd
from src.strategies.base import BaseStrategy
from src.data.loader import fetch_cboe_index
from src.analytics import tearsheet
from src.utils.config import FRED_BXM


def _fetch_index(start: str, end: str) -> pd.Series:
    return fetch_cboe_index(
        fred_id=FRED_BXM,
        yf_fallback="^BXM",
        start=start,
        end=end,
    )


class CoveredCall(BaseStrategy):
    name = "CBOE BXM — Yield Enhancement Overlay"
    description = (
        "Long SPX + short 1-month ATM call, tracking the CBOE BXM Index. "
        "Published index values used directly — no per-option simulation required."
    )
    instrument_type = "index"

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
        # cost_mode / custom_bps intentionally unused: CBOE BXM Index
        # settlement prices already embed transaction costs.
        index = _fetch_index(start, end)
        index = index.sort_index().dropna()
        returns = index.pct_change().dropna()

        self._equity = ((1 + returns).cumprod() * 100).copy()
        self._equity.iloc[0] = 100.0
        self._equity.name = self.name

        monthly_ret = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        trades = [
            {
                "date": dt,
                "notional": 1.0,
                "gross_pnl": float(ret),
                "cost_bps": 0.0,
                "net_pnl": float(ret),
            }
            for dt, ret in monthly_ret.items()
        ]
        self._trade_log = pd.DataFrame(trades).set_index("date")
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
                "Equity-like with capped upside. Call premium collected monthly creates income; "
                "upside above the strike is forfeited. Underperforms in strong bull markets, "
                "outperforms in flat or mildly declining markets."
            ),
            "capital_efficiency": (
                "Lower realized vol than direct SPX because call premium cushions drawdowns. "
                "Reduced vol contribution lowers portfolio SCR charge relative to unhedged equity."
            ),
            "regulatory_treatment": (
                "Long equity + short call treated as a covered call position under Solvency II. "
                "SCR proxy: 39% × |max 1-year drawdown| (symmetric adjustment, directional only). "
                "NAIC RBC: C-1 factor ~30% of market value, adjusted for realized vol vs. SPX."
            ),
            "liability_fit": (
                "Yield-enhancing overlay on existing equity allocation. Suitable for insurance "
                "portfolios already holding equity that want to generate additional income without "
                "increasing duration or credit exposure."
            ),
            "structurer_pitch": (
                "Pitch to insurance CIOs who hold equity and want to monetize implied vol premium "
                "while reducing mark-to-market volatility on their equity sleeve."
            ),
        }
