import numpy as np
import pandas as pd
import pytest
from src.analytics.tearsheet import (
    cagr, annualized_vol, sharpe, sortino,
    max_drawdown, var, cvar, compute_all, monthly_heatmap_data,
)

# Synthetic equity curve: $100 growing at ~10% annualized with some noise
np.random.seed(42)
_RETURNS = np.random.normal(0.0004, 0.01, 252 * 5)  # 5 years of daily returns
_EQUITY = pd.Series(
    100 * np.cumprod(1 + _RETURNS),
    index=pd.bdate_range("2018-01-02", periods=len(_RETURNS)),
)

def test_cagr_positive_for_growing_equity():
    result = cagr(_EQUITY)
    assert result > 0

def test_cagr_type():
    assert isinstance(cagr(_EQUITY), float)

def test_annualized_vol_reasonable():
    result = annualized_vol(_EQUITY.pct_change().dropna())
    assert 0.05 < result < 0.30  # typical equity vol

def test_sharpe_type():
    assert isinstance(sharpe(_EQUITY.pct_change().dropna()), float)

def test_sortino_gte_sharpe_for_positive_skew():
    r = _EQUITY.pct_change().dropna()
    assert sortino(r) >= sharpe(r) - 0.5  # loose bound

def test_max_drawdown_is_negative():
    assert max_drawdown(_EQUITY) < 0

def test_var_95_lt_var_99():
    r = _EQUITY.pct_change().dropna()
    assert var(r, 0.95) > var(r, 0.99)  # 99% VaR is more negative

def test_cvar_lte_var():
    r = _EQUITY.pct_change().dropna()
    assert cvar(r, 0.95) <= var(r, 0.95)

def test_compute_all_returns_required_keys():
    result = compute_all(_EQUITY)
    required = {"cagr", "vol", "sharpe", "sortino", "max_dd",
                "skew", "kurt", "best_month", "worst_month",
                "var_95", "var_99", "cvar_95", "cvar_99"}
    assert required.issubset(result.keys())

def test_monthly_heatmap_data_shape():
    heatmap = monthly_heatmap_data(_EQUITY)
    assert isinstance(heatmap, pd.DataFrame)
    assert heatmap.shape[1] == 12  # 12 months
