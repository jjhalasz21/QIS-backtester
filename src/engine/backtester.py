from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.strategies.base import BaseStrategy


def run_all(
    start: str,
    end: str,
    cost_mode: str = "default",
    custom_bps: float = 0.0,
) -> dict[str, "BaseStrategy"]:
    """Run all strategies and return {name: strategy_instance}. Requires all 4 strategies implemented."""
    from src.strategies.put_write import PutWrite
    from src.strategies.covered_call import CoveredCall
    from src.strategies.vol_target import VolTarget
    from src.strategies.aipex_lite import AiPexLite

    ALL_STRATEGIES = {
        "PUT Write": PutWrite,
        "BXM": CoveredCall,
        "Vol Target": VolTarget,
        "AiPEX-Lite": AiPexLite,
    }

    results = {}
    for name, cls in ALL_STRATEGIES.items():
        s = cls()
        s.run(start, end, cost_mode, custom_bps)
        results[name] = s
    return results
