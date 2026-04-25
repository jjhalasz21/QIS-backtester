import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from src.strategies.put_write import PutWrite
from src.strategies.covered_call import CoveredCall
from src.strategies.vol_target import VolTarget
from src.strategies.aipex_lite import AiPexLite
from src.analytics.tearsheet import drawdown_series, monthly_heatmap_data, compute_all
from src.utils.config import BACKTEST_START, BACKTEST_END

st.set_page_config(page_title="QIS Backtester | Jack Halasz", layout="wide")

# ── Sidebar ─────────────────────────────────────────────────────────────────
st.sidebar.title("QIS Backtester")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Page",
    ["Overview", "Strategy Explorer", "Strategy Comparison", "Client Pitch", "About"],
)

cost_mode = st.sidebar.radio(
    "Transaction Costs",
    ["off", "default", "stressed", "custom"],
    index=1,
    format_func=lambda x: {
        "off": "Off (theoretical max)",
        "default": "Default (institutional)",
        "stressed": "Stressed (3× default)",
        "custom": "Custom (bps)",
    }[x],
)
custom_bps = 0.0
if cost_mode == "custom":
    custom_bps = st.sidebar.number_input(
        "Custom cost (bps)", min_value=0.0, max_value=100.0, value=5.0, step=0.5
    )

start_date = st.sidebar.text_input("Backtest start", value=BACKTEST_START)
end_date = st.sidebar.text_input("Backtest end", value=BACKTEST_END)

st.sidebar.markdown("---")
st.sidebar.caption("Data: FRED (CBOE indices), yfinance (SPX, VIX, ETFs)")


# ── Strategy cache ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Running backtest…")
def _run_put_write(start, end, cost_mode, custom_bps):
    s = PutWrite()
    s.run(start, end, cost_mode, custom_bps)
    return s.equity_curve(), s.metrics(), s.trade_log(), s.institutional_framing()


@st.cache_data(show_spinner="Running backtest…")
def _run_covered_call(start, end, cost_mode, custom_bps):
    s = CoveredCall()
    s.run(start, end, cost_mode, custom_bps)
    return s.equity_curve(), s.metrics(), s.trade_log(), s.institutional_framing()


@st.cache_data(show_spinner="Running backtest…")
def _run_vol_target(start, end, cost_mode, custom_bps):
    s = VolTarget()
    s.run(start, end, cost_mode, custom_bps)
    return s.equity_curve(), s.metrics(), s.trade_log(), s.institutional_framing()


@st.cache_data(show_spinner="Running backtest…")
def _run_aipex(start, end, cost_mode, custom_bps):
    s = AiPexLite()
    s.run(start, end, cost_mode, custom_bps)
    return s.equity_curve(), s.metrics(), s.trade_log(), s.institutional_framing()


# Single source of truth for strategy display — add new strategies here only
_STRATEGIES = [
    (PutWrite.name, PutWrite.description, _run_put_write),
    (CoveredCall.name, CoveredCall.description, _run_covered_call),
    (VolTarget.name, VolTarget.description, _run_vol_target),
    (AiPexLite.name, AiPexLite.description, _run_aipex),
]
_STRATEGY_MAP = {name: (desc, runner) for name, desc, runner in _STRATEGIES}


# ── Page routing ─────────────────────────────────────────────────────────────
if page == "Overview":
    st.title("QIS Backtester")
    st.markdown(
        """
        A systematic equity derivatives backtesting platform simulating four institutional strategies
        against Solvency II and NAIC capital constraints.

        > **AiPEX-Lite disclaimer:** Independently implemented, inspired by HSBC's AiPEX concept.
        > Does not replicate HSBC's proprietary methodology.

        *Now featuring Strategy E: AiPEX-Lite sector ETF momentum rotation.*
        """
    )

    curve, m, _log, _framing = _run_put_write(start_date, end_date, cost_mode, custom_bps)
    bxm_curve, bxm_m, _bxm_log, _bxm_framing = _run_covered_call(start_date, end_date, cost_mode, custom_bps)
    vt_curve, vt_m, _vt_log, _vt_framing = _run_vol_target(start_date, end_date, cost_mode, custom_bps)
    aipex_curve, aipex_m, _aipex_log, _aipex_framing = _run_aipex(start_date, end_date, cost_mode, custom_bps)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CAGR", f"{m['cagr']:.1%}")
    col2.metric("Sharpe", f"{m['sharpe']:.2f}")
    col3.metric("Max Drawdown", f"{m['max_dd']:.1%}")
    col4.metric("Annualized Vol", f"{m['vol']:.1%}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve.index, y=curve, name="CBOE PUT", line=dict(color="#1f77b4")))
    fig.add_trace(go.Scatter(x=bxm_curve.index, y=bxm_curve, name="CBOE BXM", line=dict(color="#ff7f0e")))
    fig.add_trace(go.Scatter(x=vt_curve.index, y=vt_curve, name="Vol-Targeted SPX", line=dict(color="#2ca02c")))
    fig.add_trace(go.Scatter(x=aipex_curve.index, y=aipex_curve, name="AiPEX-Lite", line=dict(color="#9467bd")))
    fig.update_layout(
        title="Cumulative Return (base 100)",
        xaxis_title="Date",
        yaxis_title="Index Level",
        hovermode="x unified",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

elif page == "Strategy Explorer":
    strategy_choice = st.sidebar.selectbox("Strategy", [s[0] for s in _STRATEGIES])
    _desc, _runner = _STRATEGY_MAP[strategy_choice]
    curve, m, _log, framing = _runner(start_date, end_date, cost_mode, custom_bps)

    st.title(strategy_choice)
    st.caption(_desc)

    # ── Headline metrics ─────────────────────────────────────────────────────
    cols = st.columns(6)
    metrics_display = [
        ("CAGR", f"{m['cagr']:.1%}"),
        ("Sharpe", f"{m['sharpe']:.2f}"),
        ("Sortino", f"{m['sortino']:.2f}"),
        ("Max DD", f"{m['max_dd']:.1%}"),
        ("Vol", f"{m['vol']:.1%}"),
        ("Skew", f"{m['skew']:.2f}"),
    ]
    for col, (label, value) in zip(cols, metrics_display):
        col.metric(label, value)

    st.markdown("---")

    # ── Equity curve + drawdown ───────────────────────────────────────────────
    dd = drawdown_series(curve)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve.index, y=curve, name="Equity Curve", line=dict(color="#1f77b4")))
    fig.update_layout(title="Equity Curve (base 100)", height=350, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=dd.index, y=dd * 100,
        fill="tozeroy", name="Drawdown %",
        line=dict(color="#d62728"),
    ))
    fig_dd.update_layout(
        title="Drawdown (%)",
        yaxis_ticksuffix="%",
        height=250,
        hovermode="x unified",
    )
    st.plotly_chart(fig_dd, use_container_width=True)

    # ── Monthly heatmap ───────────────────────────────────────────────────────
    st.subheader("Monthly Returns")
    hm = monthly_heatmap_data(curve)
    hm.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][:len(hm.columns)]
    fig_hm = px.imshow(
        hm * 100,
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        text_auto=".1f",
        labels=dict(color="Return (%)"),
        aspect="auto",
    )
    fig_hm.update_layout(height=400)
    st.plotly_chart(fig_hm, use_container_width=True)

    # ── Tail risk ─────────────────────────────────────────────────────────────
    st.subheader("Tail Risk")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("VaR 95%", f"{m['var_95']:.2%}")
    col2.metric("CVaR 95%", f"{m['cvar_95']:.2%}")
    col3.metric("VaR 99%", f"{m['var_99']:.2%}")
    col4.metric("CVaR 99%", f"{m['cvar_99']:.2%}")

    st.markdown("---")

    # ── Institutional framing panel ───────────────────────────────────────────
    st.subheader("Institutional Framing")
    for label, key in [
        ("Return Profile", "return_profile"),
        ("Capital Efficiency", "capital_efficiency"),
        ("Regulatory Treatment", "regulatory_treatment"),
        ("Liability Fit", "liability_fit"),
        ("Structurer Pitch", "structurer_pitch"),
    ]:
        with st.expander(label, expanded=True):
            st.write(framing.get(key, ""))

elif page == "Strategy Comparison":
    st.title("Strategy Comparison")
    st.info("Additional strategies coming soon. Currently showing: CBOE PUT.")

elif page == "Client Pitch":
    st.title("Client Pitch View")
    st.info("Select a strategy to generate the pitch view. Coming soon.")

elif page == "About":
    st.title("About & Methodology")
    st.markdown("""
    ### Data Sources
    - **CBOE PUT / BXM indices:** FRED via pandas-datareader (series: PUTWRITE, BXMCBOE). Falls back to yfinance if unavailable.
    - **SPX, SPY, VIX, sector ETFs:** yfinance with local parquet cache.

    ### Synthetic IV
    Not used in V1 strategies A and B (published index levels used directly). Strategy C uses 20-day rolling realized vol on SPX as a vol proxy — labeled as synthetic throughout.

    ### Transaction Cost Model
    Costs are applied at trade execution and stored with each trade record. The sidebar toggle re-applies costs post-hoc without re-running the backtest.
    | Mode | ETF | Futures/SPY | CBOE Indices |
    |---|---|---|---|
    | Default | 2 bps | 1 bp | 0 bps |
    | Stressed | 6 bps | 3 bps | 0 bps |

    ### Regulatory Metrics (Directional Proxies Only)
    Solvency II SCR and NAIC RBC figures are simplified directional estimates, not production-grade regulatory calculations. Do not use for actual capital planning.

    ### AiPEX Disclaimer
    AiPEX-Lite is an independently implemented strategy inspired by HSBC's AiPEX (AI-driven index) concept. It does not replicate HSBC's proprietary methodology, signals, or weighting scheme.
    """)
