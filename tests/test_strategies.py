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
    assert set(["notional", "gross_pnl", "cost_bps", "net_pnl"]).issubset(log.columns)


def test_put_write_institutional_framing_keys():
    s = PutWrite()
    framing = s.institutional_framing()
    assert "return_profile" in framing
    assert "structurer_pitch" in framing


def test_put_write_guard_clauses():
    s = PutWrite()
    with pytest.raises(RuntimeError):
        s.metrics()
    with pytest.raises(RuntimeError):
        s.equity_curve()
    with pytest.raises(RuntimeError):
        s.trade_log()


from src.strategies.covered_call import CoveredCall


def test_covered_call_run_with_synthetic_data(monkeypatch):
    import src.strategies.covered_call as cc_mod
    fake = _make_fake_index()
    monkeypatch.setattr(cc_mod, "_fetch_index", lambda *a, **kw: fake)

    s = CoveredCall()
    s.run("2020-01-01", "2021-12-31", "default")

    curve = s.equity_curve()
    assert isinstance(curve, pd.Series)
    assert len(curve) > 0

    m = s.metrics()
    assert "sharpe" in m and "max_dd" in m

def test_covered_call_institutional_framing():
    s = CoveredCall()
    framing = s.institutional_framing()
    assert "structurer_pitch" in framing


def test_covered_call_equity_starts_at_100(monkeypatch):
    import src.strategies.covered_call as cc_mod
    fake = _make_fake_index()
    monkeypatch.setattr(cc_mod, "_fetch_index", lambda *a, **kw: fake)

    s = CoveredCall()
    s.run("2020-01-01", "2021-12-31", "default")
    assert s.equity_curve().iloc[0] == pytest.approx(100.0, rel=0.01)


def test_covered_call_trade_log_schema(monkeypatch):
    import src.strategies.covered_call as cc_mod
    fake = _make_fake_index()
    monkeypatch.setattr(cc_mod, "_fetch_index", lambda *a, **kw: fake)

    s = CoveredCall()
    s.run("2020-01-01", "2021-12-31", "default")
    log = s.trade_log()
    assert isinstance(log, pd.DataFrame)
    assert {"notional", "gross_pnl", "cost_bps", "net_pnl"}.issubset(log.columns)


def test_covered_call_guard_clauses():
    s = CoveredCall()
    with pytest.raises(RuntimeError):
        s.metrics()
    with pytest.raises(RuntimeError):
        s.equity_curve()
    with pytest.raises(RuntimeError):
        s.trade_log()


from src.strategies.vol_target import VolTarget


def test_vol_target_run_with_synthetic_data(monkeypatch):
    import src.strategies.vol_target as vt_mod
    fake = _make_fake_index()
    monkeypatch.setattr(vt_mod, "_fetch_spy", lambda *a, **kw: fake)

    s = VolTarget()
    s.run("2020-01-01", "2021-12-31", "default")

    curve = s.equity_curve()
    assert isinstance(curve, pd.Series)
    assert len(curve) > 100

    m = s.metrics()
    assert "sharpe" in m

def test_vol_target_weights_capped_at_max_leverage(monkeypatch):
    import src.strategies.vol_target as vt_mod
    low_vol_prices = pd.Series(
        100 * np.cumprod(1 + np.random.normal(0.0005, 0.001, 300)),
        index=pd.bdate_range("2022-01-03", periods=300),
    )
    monkeypatch.setattr(vt_mod, "_fetch_spy", lambda *a, **kw: low_vol_prices)

    s = VolTarget()
    s.run("2022-01-01", "2023-12-31", "default")
    from src.utils.config import MAX_LEVERAGE
    assert s.weights().max() <= MAX_LEVERAGE

def test_vol_target_institutional_framing(monkeypatch):
    import src.strategies.vol_target as vt_mod
    fake = _make_fake_index()
    monkeypatch.setattr(vt_mod, "_fetch_spy", lambda *a, **kw: fake)
    s = VolTarget()
    s.run("2020-01-01", "2021-12-31", "default")
    framing = s.institutional_framing()
    for key in ("return_profile", "capital_efficiency", "regulatory_treatment", "liability_fit", "structurer_pitch"):
        assert key in framing
        assert isinstance(framing[key], str) and len(framing[key]) > 20

def test_vol_target_guard_clauses():
    s = VolTarget()
    import pytest as pt
    with pt.raises(RuntimeError):
        s.equity_curve()
    with pt.raises(RuntimeError):
        s.metrics()
    with pt.raises(RuntimeError):
        s.trade_log()
    with pt.raises(RuntimeError):
        s.weights()
