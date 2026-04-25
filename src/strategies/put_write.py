from __future__ import annotations
import pandas as pd
from src.strategies.base import BaseStrategy
from src.data.loader import fetch_cboe_index, fetch_prices
from src.analytics import tearsheet
from src.utils.config import FRED_PUT, SPX_TICKER


def _fetch_index(start: str, end: str) -> pd.Series:
    return fetch_cboe_index(
        fred_id=FRED_PUT,
        yf_fallback="^PUTR",
        start=start,
        end=end,
    )


class PutWrite(BaseStrategy):
    name = "CBOE PUT — Insurance Carry"
    description = (
        "Fully collateralized 1-month ATM SPX put-write, tracking the CBOE PUT Index. "
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
        index = _fetch_index(start, end)
        index = index.sort_index().dropna()

        returns = index.pct_change().dropna()

        # Build equity curve (base 100)
        self._equity = (1 + returns).cumprod() * 100
        self._equity.iloc[0] = 100.0
        self._equity.name = self.name

        # Trade log: monthly entries, 0 bps cost (costs embedded in published index)
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
                "Credit-like. Positive carry with limited upside capture. "
                "Return distribution resembles short-duration corporate bonds — "
                "regular premium income with occasional large losses in vol spikes."
            ),
            "capital_efficiency": (
                "Realized vol and max drawdown are materially lower than direct SPX exposure. "
                "Lower vol implies a lower Solvency II SCR-equity symmetric adjustment, "
                "reducing required capital vs. holding the index directly."
            ),
            "regulatory_treatment": (
                "Treated as a derivatives position under the Solvency II SCR-equity sub-module. "
                "SCR proxy: 39% × |max 1-year drawdown| (symmetric adjustment, directional only). "
                "NAIC RBC: C-1 factor ~30% of market value, scaled by (realized vol / 15% SPX long-run vol)."
            ),
            "liability_fit": (
                "Carry-generating. Attractive for insurance general accounts seeking equity risk premium "
                "with bond-like volatility and without duration extension or credit spread exposure."
            ),
            "structurer_pitch": (
                "Pitch to insurance CIOs seeking yield above short-duration credit with lower regulatory "
                "capital consumption than direct equity — the put premium is the carry source."
            ),
        }
