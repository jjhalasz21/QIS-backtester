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
    st.title("Strategy Explorer")
    strategy_choice = st.selectbox("Select strategy", [s[0] for s in _STRATEGIES])
    _desc, _runner = _STRATEGY_MAP[strategy_choice]
    curve, m, _log, framing = _runner(start_date, end_date, cost_mode, custom_bps)

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
    st.caption(f"Transaction costs: {cost_mode.upper()} | {start_date} – {end_date}")

    # Unpack all 4 strategies
    put_curve, put_m, put_log, put_framing = _run_put_write(start_date, end_date, cost_mode, custom_bps)
    bxm_curve, bxm_m, bxm_log, bxm_framing = _run_covered_call(start_date, end_date, cost_mode, custom_bps)
    vt_curve, vt_m, vt_log, vt_framing = _run_vol_target(start_date, end_date, cost_mode, custom_bps)
    aipex_curve, aipex_m, aipex_log, aipex_framing = _run_aipex(start_date, end_date, cost_mode, custom_bps)

    # Cumulative return overlay
    st.subheader("Cumulative Return (base 100)")
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"]
    names = ["CBOE PUT", "CBOE BXM", "Vol-Targeted SPX", "AiPEX-Lite"]
    curves = [put_curve, bxm_curve, vt_curve, aipex_curve]
    fig = go.Figure()
    for name, c, color in zip(names, curves, colors):
        fig.add_trace(go.Scatter(x=c.index, y=c, name=name, line=dict(color=color)))
    fig.update_layout(hovermode="x unified", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Metric table — build inline from tuples (comparisons module expects strategy objects)
    st.subheader("Performance Metrics")
    metric_rows = []
    for name, m in zip(names, [put_m, bxm_m, vt_m, aipex_m]):
        metric_rows.append({
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
    st.dataframe(pd.DataFrame(metric_rows).set_index("Strategy"), use_container_width=True)

    # Correlation matrix
    st.subheader("Return Correlations")
    ret_df = pd.DataFrame({
        n: c.pct_change().dropna()
        for n, c in zip(names, curves)
    })
    corr = ret_df.corr()
    fig_corr = px.imshow(
        corr, text_auto=".2f",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        zmin=-1, zmax=1,
    )
    fig_corr.update_layout(height=350)
    st.plotly_chart(fig_corr, use_container_width=True)

    # Cost drag
    st.subheader("Cost Drag (Annualized)")
    drag_rows = []
    for name, log, curve in zip(names, [put_log, bxm_log, vt_log, aipex_log], curves):
        if log.empty or "gross_pnl" not in log.columns:
            drag = 0.0
        else:
            total_cost = (log["gross_pnl"] - log["net_pnl"]).sum()
            n_years = len(curve) / 252
            drag = total_cost / n_years if n_years > 0 else 0.0
        drag_rows.append({"Strategy": name, "Annual Cost Drag": f"{drag:.3%}"})
    st.dataframe(pd.DataFrame(drag_rows).set_index("Strategy"), use_container_width=True)
    st.caption(
        "Cost drag = gross P&L – net P&L from trade log, annualized. "
        "Zero for CBOE index strategies (costs embedded in published index)."
    )

elif page == "Client Pitch":
    st.title("Client Pitch View")
    pitch_choice = st.selectbox(
        "Select strategy for pitch",
        [s[0] for s in _STRATEGIES],
    )
    _pitch_desc, _pitch_runner = _STRATEGY_MAP[pitch_choice]
    pitch_curve, pitch_m, pitch_log, pitch_framing = _pitch_runner(start_date, end_date, cost_mode, custom_bps)

    st.markdown(f"## {pitch_choice}")
    st.markdown(f"*{_pitch_desc}*")
    st.markdown("---")

    st.markdown("### Investment Thesis")
    st.info(pitch_framing.get("structurer_pitch", ""))

    st.markdown("### Historical Performance")
    cols = st.columns(5)
    cols[0].metric("CAGR", f"{pitch_m['cagr']:.1%}")
    cols[1].metric("Sharpe", f"{pitch_m['sharpe']:.2f}")
    cols[2].metric("Max Drawdown", f"{pitch_m['max_dd']:.1%}")
    cols[3].metric("Annualized Vol", f"{pitch_m['vol']:.1%}")
    cols[4].metric("Sortino", f"{pitch_m['sortino']:.2f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pitch_curve.index, y=pitch_curve,
        name=pitch_choice, line=dict(color="#1f77b4", width=2),
    ))
    fig.update_layout(
        title=f"Cumulative Return ({start_date[:4]}–present, base 100)",
        height=300,
        hovermode="x unified",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Institutional Fit")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Return Profile**")
        st.write(pitch_framing.get("return_profile", ""))
        st.markdown("**Liability Fit**")
        st.write(pitch_framing.get("liability_fit", ""))
    with col2:
        st.markdown("**Capital Efficiency**")
        st.write(pitch_framing.get("capital_efficiency", ""))
        st.markdown("**Regulatory Treatment**")
        st.write(pitch_framing.get("regulatory_treatment", ""))

    st.markdown("### Key Risks & Limitations")
    st.warning(
        "• Backtest uses synthetic IV where applicable — not historical options data.\n"
        "• Regulatory metrics are directional proxies, not production-grade calculations.\n"
        "• Past performance does not predict future results.\n"
        "• CBOE index strategies use published index values; individual execution may differ."
    )

elif page == "About":
    st.title("About & Methodology")
    st.markdown("""
    ### Data Sources
    - **CBOE PUT / BXM indices:** Direct FRED CSV download (series: PUTWRITE, BXMCBOE). Falls back to yfinance if unavailable.
    - **SPX, SPY, VIX, sector ETFs:** yfinance with local parquet cache.

    ### Synthetic IV
    Strategies A (CBOE PUT) and B (CBOE BXM) use published index levels directly — no synthetic IV. Strategy C (Vol-Targeted SPX) uses 20-day rolling realized vol on SPY as a vol proxy. Strategy E (AiPEX-Lite) uses sector ETF price data only. All synthetic vol usage is labeled throughout the dashboard.

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
