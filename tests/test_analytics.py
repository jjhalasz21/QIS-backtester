import numpy as np
import pandas as pd
from src.analytics.insurance_metrics import scr_equity_proxy, naic_rbc_proxy

np.random.seed(7)
_RETURNS = np.random.normal(0.0003, 0.012, 252 * 5)
_EQUITY = pd.Series(
    100 * np.cumprod(1 + _RETURNS),
    index=pd.bdate_range("2018-01-02", periods=len(_RETURNS)),
)

def test_scr_proxy_is_positive():
    scr = scr_equity_proxy(_EQUITY)
    assert scr > 0

def test_scr_proxy_between_0_and_50_percent():
    scr = scr_equity_proxy(_EQUITY)
    assert 0 < scr < 0.50

def test_naic_rbc_is_positive():
    rbc = naic_rbc_proxy(_EQUITY)
    assert rbc > 0

def test_naic_rbc_type():
    assert isinstance(naic_rbc_proxy(_EQUITY), float)

def test_high_vol_strategy_has_higher_naic_rbc():
    np.random.seed(42)
    high_vol_rets = np.random.normal(0.0003, 0.025, 252 * 5)
    high_vol_eq = pd.Series(
        100 * np.cumprod(1 + high_vol_rets),
        index=pd.bdate_range("2018-01-02", periods=len(high_vol_rets)),
    )
    assert naic_rbc_proxy(high_vol_eq) > naic_rbc_proxy(_EQUITY)
