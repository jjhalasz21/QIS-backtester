import numpy as np
import pandas as pd
import pytest
from src.pricing.synthetic_iv import realized_vol, synthetic_iv

np.random.seed(42)
_PRICES = pd.Series(
    100 * np.cumprod(1 + np.random.normal(0.0004, 0.012, 300)),
    index=pd.bdate_range("2022-01-03", periods=300),
)

def test_realized_vol_annualized_range():
    rv = realized_vol(_PRICES, window=20)
    assert (rv.dropna() > 0.05).all()
    assert (rv.dropna() < 0.60).all()

def test_realized_vol_has_nan_for_first_window_minus_1():
    rv = realized_vol(_PRICES, window=20)
    assert rv.iloc[:19].isna().all()
    assert not pd.isna(rv.iloc[19])

def test_synthetic_iv_is_above_realized_vol():
    rv = realized_vol(_PRICES, window=20)
    siv = synthetic_iv(_PRICES, window=20, skew_spread=0.02)
    valid = rv.dropna().index
    assert (siv.loc[valid] > rv.loc[valid]).all()

def test_synthetic_iv_skew_spread_adds_exactly():
    rv = realized_vol(_PRICES, window=20)
    siv = synthetic_iv(_PRICES, window=20, skew_spread=0.03)
    diff = (siv - rv).dropna()
    assert (abs(diff - 0.03) < 1e-10).all()
