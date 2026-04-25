import numpy as np
import pandas as pd

_TRADING_DAYS = 252


def cagr(equity: pd.Series) -> float:
    n_years = len(equity) / _TRADING_DAYS
    if n_years == 0:
        return 0.0
    return float((equity.iloc[-1] / equity.iloc[0]) ** (1 / n_years) - 1)


def annualized_vol(returns: pd.Series) -> float:
    return float(returns.std() * np.sqrt(_TRADING_DAYS))


def sharpe(returns: pd.Series, rf_annual: float = 0.02) -> float:
    rf_daily = (1 + rf_annual) ** (1 / _TRADING_DAYS) - 1
    excess = returns - rf_daily
    std = excess.std()
    if std == 0:
        return 0.0
    return float(excess.mean() / std * np.sqrt(_TRADING_DAYS))


def sortino(returns: pd.Series, rf_annual: float = 0.02) -> float:
    rf_daily = (1 + rf_annual) ** (1 / _TRADING_DAYS) - 1
    excess = returns - rf_daily
    downside_std = excess[excess < 0].std()
    if downside_std == 0:
        return 0.0
    return float(excess.mean() / downside_std * np.sqrt(_TRADING_DAYS))


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())


def drawdown_series(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    return (equity - peak) / peak


def var(returns: pd.Series, confidence: float = 0.95) -> float:
    return float(np.percentile(returns.dropna(), (1 - confidence) * 100))


def cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    threshold = var(returns, confidence)
    tail = returns[returns <= threshold]
    if tail.empty:
        return threshold
    return float(tail.mean())


def monthly_heatmap_data(equity: pd.Series) -> pd.DataFrame:
    """Return DataFrame of monthly returns with years as rows and months (1–12) as columns."""
    monthly = equity.resample("ME").last().pct_change().dropna()
    df = monthly.to_frame("ret")
    df["year"] = df.index.year
    df["month"] = df.index.month
    return df.pivot(index="year", columns="month", values="ret")


def compute_all(equity: pd.Series, rf_annual: float = 0.02) -> dict:
    returns = equity.pct_change().dropna()
    monthly = equity.resample("ME").last().pct_change().dropna()
    return {
        "cagr": cagr(equity),
        "vol": annualized_vol(returns),
        "sharpe": sharpe(returns, rf_annual),
        "sortino": sortino(returns, rf_annual),
        "max_dd": max_drawdown(equity),
        "skew": float(returns.skew()),
        "kurt": float(returns.kurtosis()),
        "best_month": float(monthly.max()),
        "worst_month": float(monthly.min()),
        "var_95": var(returns, 0.95),
        "var_99": var(returns, 0.99),
        "cvar_95": cvar(returns, 0.95),
        "cvar_99": cvar(returns, 0.99),
    }
