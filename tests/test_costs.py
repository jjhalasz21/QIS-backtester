from src.engine.costs import get_cost_bps, apply_costs

def test_off_mode_returns_zero():
    assert get_cost_bps("etf", "off") == 0.0
    assert get_cost_bps("futures", "off") == 0.0
    assert get_cost_bps("index", "off") == 0.0

def test_default_etf_is_2bps():
    assert get_cost_bps("etf", "default") == 2.0

def test_default_futures_is_1bps():
    assert get_cost_bps("futures", "default") == 1.0

def test_default_index_is_0bps():
    assert get_cost_bps("index", "default") == 0.0

def test_stressed_is_3x_default():
    assert get_cost_bps("etf", "stressed") == 6.0
    assert get_cost_bps("futures", "stressed") == 3.0

def test_custom_mode_uses_provided_bps():
    assert get_cost_bps("etf", "custom", custom_bps=7.5) == 7.5

def test_apply_costs_deducts_from_gross():
    # 100 notional, 2bps = 0.02 cost
    net = apply_costs(gross_pnl=1.0, notional=100.0, cost_bps=2.0)
    assert abs(net - (1.0 - 0.02)) < 1e-10

def test_apply_costs_zero_bps_unchanged():
    assert apply_costs(gross_pnl=1.5, notional=100.0, cost_bps=0.0) == 1.5
