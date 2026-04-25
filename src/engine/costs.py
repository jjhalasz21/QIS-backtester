_DEFAULT: dict[str, float] = {
    "etf": 2.0,      # sector ETFs (AiPEX-Lite)
    "futures": 1.0,  # SPY/SPX proxy (vol-target)
    "options": 5.0,  # SPX options (future use)
    "index": 0.0,    # CBOE published indices — costs already embedded
}

_STRESSED_MULTIPLIER = 3.0


def get_cost_bps(
    instrument_type: str,
    cost_mode: str,
    custom_bps: float = 0.0,
) -> float:
    """Return cost in basis points for a given instrument and cost mode."""
    if cost_mode == "off":
        return 0.0
    if cost_mode == "custom":
        return float(custom_bps)
    base = _DEFAULT.get(instrument_type, 2.0)
    if cost_mode == "stressed":
        return base * _STRESSED_MULTIPLIER
    return base  # "default"


def apply_costs(gross_pnl: float, notional: float, cost_bps: float) -> float:
    """Deduct cost from gross P&L. Cost = |notional| * cost_bps / 10_000."""
    return gross_pnl - abs(notional) * cost_bps / 10_000
