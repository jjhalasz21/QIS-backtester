import pandas as pd
from src.strategies.base import BaseStrategy


def build_metric_table(strategies: dict[str, BaseStrategy]) -> pd.DataFrame:
    """
    Build side-by-side performance table for all strategies.
    strategies: {display_name: strategy_instance} — run() must have been called.
    """
    rows = []
    for name, s in strategies.items():
        m = s.metrics()
        rows.append({
            "Strategy": name,
            "CAGR": f"{m['cagr']:.1%}",
            "Vol": f"{m['vol']:.1%}",
            "Sharpe": f"{m['sharpe']:.2f}",
            "Sortino": f"{m['sortino']:.2f}",
            "Max DD": f"{m['max_dd']:.1%}",
            "Skew": f"{m['skew']:.2f}",
            "Best Mo.": f"{m['best_month']:.1%}",
            "Worst Mo.": f"{m['worst_month']:.1%}",
            "VaR 95%": f"{m['var_95']:.2%}",
            "CVaR 95%": f"{m['cvar_95']:.2%}",
        })
    return pd.DataFrame(rows).set_index("Strategy")


def correlation_matrix(strategies: dict[str, BaseStrategy]) -> pd.DataFrame:
    """Return pairwise correlation of daily returns across all strategies."""
    returns = {
        name: s.equity_curve().pct_change().dropna()
        for name, s in strategies.items()
    }
    return pd.DataFrame(returns).corr()


def cost_drag_table(strategies: dict[str, BaseStrategy]) -> pd.DataFrame:
    """
    Estimate annualized cost drag for each strategy from the trade log.
    Cost drag = sum(gross_pnl - net_pnl) / years.
    """
    rows = []
    for name, s in strategies.items():
        log = s.trade_log()
        if log.empty or "gross_pnl" not in log.columns:
            drag = 0.0
        else:
            total_cost = (log["gross_pnl"] - log["net_pnl"]).sum()
            n_years = len(s.equity_curve()) / 252
            drag = total_cost / n_years if n_years > 0 else 0.0
        rows.append({"Strategy": name, "Annual Cost Drag": f"{drag:.3%}"})
    return pd.DataFrame(rows).set_index("Strategy")
