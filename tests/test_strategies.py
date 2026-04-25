import numpy as np
import pandas as pd
import pytest

from src.strategies.put_write import PutWrite
from src.engine.costs import get_cost_bps


def _make_fake_index(n=500, start="2020-01-02", base=100.0):
    np.random.seed(1)
    rets = np.random.normal(0.0003, 0.008, n)
    prices = base * np.cumprod(1 + rets)
    return pd.Series(prices, index=pd.bdate_range(start, periods=n))


def test_put_write_implements_interface():
    s = PutWrite()
    assert hasattr(s, "run")
    assert hasattr(s, "metrics")
    assert hasattr(s, "equity_curve")
    assert hasattr(s, "trade_log")
    assert hasattr(s, "institutional_framing")


def test_put_write_run_with_synthetic_data(monkeypatch):
    import src.strategies.put_write as pw_mod
    fake = _make_fake_index()
    monkeypatch.setattr(pw_mod, "_fetch_index", lambda *a, **kw: fake)

    s = PutWrite()
    s.run("2020-01-01", "2021-12-31", "default")

    curve = s.equity_curve()
    assert isinstance(curve, pd.Series)
    assert len(curve) > 0
    assert curve.iloc[0] == pytest.approx(100.0, rel=0.01)

    m = s.metrics()
    assert "sharpe" in m
    assert "max_dd" in m
    assert "cagr" in m

    log = s.trade_log()
    assert isinstance(log, pd.DataFrame)


def test_put_write_institutional_framing_keys():
    s = PutWrite()
    framing = s.institutional_framing()
    assert "return_profile" in framing
    assert "structurer_pitch" in framing
