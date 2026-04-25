from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    name: str = "Unnamed Strategy"
    description: str = ""
    instrument_type: str = "index"  # "index" | "futures" | "etf" | "options"

    @abstractmethod
    def run(self, start: str, end: str, cost_mode: str = "default", custom_bps: float = 0.0) -> None:
        """Execute the backtest. Must populate equity curve, metrics, and trade log."""
        ...

    @abstractmethod
    def metrics(self) -> dict:
        """Return dict of performance metrics. Call run() first."""
        ...

    @abstractmethod
    def equity_curve(self) -> pd.Series:
        """Return daily equity curve (base 100). Call run() first."""
        ...

    @abstractmethod
    def trade_log(self) -> pd.DataFrame:
        """
        Return DataFrame of trade records with columns:
        notional, gross_pnl, cost_bps, net_pnl — indexed by date.
        """
        ...

    def institutional_framing(self) -> dict:
        """
        Return dict with keys: return_profile, capital_efficiency,
        regulatory_treatment, liability_fit, structurer_pitch.
        Override in each concrete strategy.
        """
        return {}
