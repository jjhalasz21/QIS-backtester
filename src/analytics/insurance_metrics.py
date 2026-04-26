"""
Simplified regulatory capital proxies. Directional estimates only —
not production-grade regulatory calculations. Do not use for actual capital planning.
"""
import numpy as np
import pandas as pd

_TRADING_DAYS = 252
_SCR_EQUITY_BASE = 0.39
_NAIC_C1_BASE = 0.30
_SPX_LONG_RUN_VOL = 0.15


def scr_equity_proxy(equity: pd.Series) -> float:
    """
    Simplified Solvency II SCR-equity proxy.
    Approximation: 39% × |worst 1-year drawdown|.
    Directional proxy only — not EIOPA-compliant.
    """
    annual_returns = equity.pct_change(_TRADING_DAYS).dropna()
    worst_annual = float(annual_returns.min())
    return _SCR_EQUITY_BASE * abs(worst_annual)


def naic_rbc_proxy(equity: pd.Series) -> float:
    """
    Simplified NAIC RBC C-1 proxy for equity.
    Base: 30% of market value, scaled by realized vol / 15% long-run vol baseline.
    Directional proxy only.
    """
    returns = equity.pct_change().dropna()
    realized = float(returns.std() * np.sqrt(_TRADING_DAYS))
    vol_ratio = realized / _SPX_LONG_RUN_VOL
    return _NAIC_C1_BASE * vol_ratio
