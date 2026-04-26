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

from src.pricing.black_scholes import call_price, put_price, delta, gamma, vega, theta, rho

_S, _K, _T, _r, _sig = 100.0, 100.0, 1.0, 0.05, 0.20

def test_call_price_known_value():
    c = call_price(_S, _K, _T, _r, _sig)
    assert abs(c - 10.4506) < 0.01

def test_put_price_known_value():
    p = put_price(_S, _K, _T, _r, _sig)
    assert abs(p - 5.5735) < 0.01

def test_put_call_parity():
    c = call_price(_S, _K, _T, _r, _sig)
    p = put_price(_S, _K, _T, _r, _sig)
    import numpy as np
    parity_rhs = _S - _K * np.exp(-_r * _T)
    assert abs((c - p) - parity_rhs) < 1e-6

def test_call_delta_atm_near_half():
    d = delta(_S, _K, _T, _r, _sig, option_type="call")
    assert 0.5 < d < 0.7

def test_put_delta_negative():
    d = delta(_S, _K, _T, _r, _sig, option_type="put")
    assert -0.6 < d < -0.3

def test_gamma_positive():
    g = gamma(_S, _K, _T, _r, _sig)
    assert g > 0

def test_vega_is_positive():
    assert vega(_S, _K, _T, _r, _sig) > 0

def test_call_theta_negative():
    t = theta(_S, _K, _T, _r, _sig, option_type="call")
    assert t < 0

def test_expired_call_intrinsic():
    assert abs(call_price(110.0, 100.0, 0.0, 0.05, 0.20) - 10.0) < 1e-10
    assert call_price(90.0, 100.0, 0.0, 0.05, 0.20) == 0.0
