import pandas as pd

def trading_days(start: str, end: str) -> pd.DatetimeIndex:
    """Return business days between start and end (inclusive). No holiday adjustment."""
    return pd.bdate_range(start=start, end=end)
