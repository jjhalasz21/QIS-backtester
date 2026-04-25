import numpy as np
import pandas as pd

_TRADING_DAYS = 252


def realized_vol(prices: pd.Series, window: int = 20) -> pd.Series:
    """
    Annualized realized vol from log returns over a rolling window.
    Returns NaN for the first (window-1) observations.
    """
    log_returns = np.log(prices / prices.shift(1))
    return log_returns.rolling(window, min_periods=window - 1).std() * np.sqrt(_TRADING_DAYS)


def synthetic_iv(
    prices: pd.Series,
    window: int = 20,
    skew_spread: float = 0.02,
) -> pd.Series:
    """
    Proxy for implied vol: realized vol + constant skew spread.
    The skew_spread (~2 vol points) approximates the implied-realized vol premium.
    Labeled as synthetic throughout the dashboard — not historical IV.
    """
    return realized_vol(prices, window) + skew_spread
