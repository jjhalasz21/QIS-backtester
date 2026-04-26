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
from src.data.loader import fetch_prices
from src.utils.config import BACKTEST_START, BACKTEST_END

st.set_page_config(
    page_title="QIS Strategies | Jack Halasz",
    layout="wide",
    page_icon="▪",
)

# ── HSBC-style design system ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

/* Page background */
.stApp { background-color: #FFFFFF; }
.main .block-container { padding-top: 28px !important; }

/* ── Sidebar — dark charcoal ── */
[data-testid="stSidebar"] {
    background-color: #1D1D1B !important;
    border-right: 1px solid #2A2A2A;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] .stMarkdown { color: #AAAAAA !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
[data-testid="stSidebar"] hr { border-color: #3A3A3A !important; }
[data-testid="stSidebar"] label {
    color: #888888 !important;
    font-size: 10px !important;
    letter-spacing: 0.10em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] [data-baseweb="radio"] label {
    color: #CCCCCC !important;
    text-transform: none !important;
    font-size: 13px !important;
    letter-spacing: normal !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #2A2A2A !important;
    border-color: #3A3A3A !important;
    border-radius: 0 !important;
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] input {
    background-color: #2A2A2A !important;
    color: #FFFFFF !important;
    border-color: #3A3A3A !important;
    border-radius: 0 !important;
}

/* ── Metric tiles — white card with border ── */
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E8E8E8 !important;
    padding: 18px 20px 14px 20px !important;
    margin-bottom: 4px !important;
    overflow: visible !important;
}
[data-testid="stMetricLabel"] > div {
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #888888 !important;
    white-space: nowrap !important;
    overflow: visible !important;
}
[data-testid="stMetricValue"] {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #1D1D1B !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
    overflow: visible !important;
}
[data-testid="stMetricValue"] > div {
    white-space: nowrap !important;
    overflow: visible !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid #E8E8E8 !important;
    border-radius: 0 !important;
    margin-bottom: 4px !important;
}
[data-testid="stExpander"] summary {
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #1D1D1B !important;
    background-color: #F9F9F9 !important;
    padding: 12px 16px !important;
}

/* ── Info / warning boxes ── */
[data-testid="stInfo"] {
    background-color: #F9F9F9 !important;
    border-left: 3px solid #DB0011 !important;
    border-radius: 0 !important;
    color: #1D1D1B !important;
}
[data-testid="stWarning"] {
    background-color: #FFF8F8 !important;
    border-left: 3px solid #DB0011 !important;
    border-radius: 0 !important;
    color: #1D1D1B !important;
}

/* ── Dividers ── */
hr { border-color: #E8E8E8 !important; margin: 24px 0 !important; }

/* ── Selectbox (main content) ── */
.main [data-baseweb="select"] > div { border-radius: 0 !important; border-color: #E0E0E0 !important; }

/* ── Caption ── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #999999 !important;
    font-size: 11px !important;
    letter-spacing: 0.02em !important;
}

/* ── Dataframe borders ── */
[data-testid="stDataFrame"] { border: 1px solid #E8E8E8 !important; }

/* ── h2 / h3 in main — override to feel clean ── */
.main h2 {
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #1D1D1B !important;
    letter-spacing: -0.01em !important;
}
.main h3 {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #1D1D1B !important;
}
</style>
""", unsafe_allow_html=True)


# ── Design helpers ────────────────────────────────────────────────────────────
def _page_header(title: str, subtitle: str = "") -> None:
    sub_html = f'<div style="font-size:13px;color:#555555;margin-top:4px;font-weight:400;">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div style="border-left:4px solid #DB0011;padding:2px 0 2px 14px;margin-bottom:24px;">
        <div style="font-size:9px;font-weight:700;letter-spacing:0.20em;text-transform:uppercase;color:#DB0011;margin-bottom:4px;">QIS STRATEGIES</div>
        <div style="font-size:26px;font-weight:700;color:#1D1D1B;letter-spacing:-0.02em;line-height:1.1;">{title}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def _section_header(text: str) -> None:
    st.markdown(f"""
    <div style="margin:32px 0 14px 0;">
        <span style="font-size:10px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;
                     color:#1D1D1B;border-bottom:2px solid #DB0011;padding-bottom:4px;">{text}</span>
    </div>
    """, unsafe_allow_html=True)


# Plotly dark theme constants
_BG = "#141414"
_GRID = "#272727"
_AXIS = "#444444"
_FONT = "#CCCCCC"

# Strategy colour palette — Bloomberg-terminal-style, legible on dark canvas
# PUT=HSBC red, BXM=sky blue, VolTarget=amber, AiPEX=emerald
_COLORS = ["#DB0011", "#38BDF8", "#F59E0B", "#10B981"]
_STRAT_NAMES = ["CBOE PUT", "CBOE BXM", "Vol-Targeted SPX", "AiPEX-Lite"]
_SPX_COLOR = "#94A3B8"  # slate gray — benchmark reference line


def _dark(title: str = "", height: int = 400, **kwargs) -> dict:
    base = dict(
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        font=dict(color=_FONT, family="Inter, system-ui, sans-serif", size=11),
        title=dict(
            text=title,
            font=dict(color="#FFFFFF", size=12, family="Inter, system-ui", weight=600),
            x=0, xanchor="left", pad=dict(l=2),
        ),
        xaxis=dict(
            gridcolor=_GRID, linecolor=_AXIS, tickcolor=_AXIS,
            tickfont=dict(color=_FONT, size=10), title_font=dict(color=_FONT),
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor=_GRID, linecolor=_AXIS, tickcolor=_AXIS,
            tickfont=dict(color=_FONT, size=10), title_font=dict(color=_FONT),
            showgrid=True,
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1D1D1B", bordercolor="#DB0011", font=dict(color="white", size=11)),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", font=dict(color=_FONT, size=11),
            orientation="h", y=-0.14, x=0,
        ),
        margin=dict(l=48, r=16, t=44, b=52),
        height=height,
    )
    base.update(kwargs)
    return base


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="padding:12px 0 20px 0;">
    <div style="font-size:9px;font-weight:700;letter-spacing:0.22em;color:#DB0011;margin-bottom:5px;">QIS STRATEGIES</div>
    <div style="font-size:18px;font-weight:700;color:#FFFFFF;letter-spacing:-0.01em;">Backtester</div>
    <div style="font-size:11px;color:#666666;margin-top:3px;">Jack Halasz</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown('<hr style="border-color:#3A3A3A;margin:0 0 16px 0;">', unsafe_allow_html=True)

page = st.sidebar.selectbox(
    "Navigation",
    ["Overview", "Strategy Explorer", "Strategy Comparison", "Client Pitch", "About"],
)

st.sidebar.markdown('<hr style="border-color:#3A3A3A;margin:16px 0;">', unsafe_allow_html=True)

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

st.sidebar.markdown('<hr style="border-color:#3A3A3A;margin:16px 0;">', unsafe_allow_html=True)

start_date = st.sidebar.text_input("Backtest start", value=BACKTEST_START)
end_date   = st.sidebar.text_input("Backtest end",   value=BACKTEST_END)

st.sidebar.markdown('<hr style="border-color:#3A3A3A;margin:16px 0 8px 0;">', unsafe_allow_html=True)
st.sidebar.markdown('<div style="font-size:10px;color:#555555;">Data: FRED · yfinance</div>', unsafe_allow_html=True)


# ── Strategy cache ────────────────────────────────────────────────────────────
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


@st.cache_data(show_spinner="Loading benchmark…")
def _run_spx(start, end):
    px = fetch_prices("SPY", start, end).sort_index().dropna()
    equity = (px / px.iloc[0] * 100).rename("S&P 500")
    return equity, compute_all(equity)


_STRATEGIES = [
    (PutWrite.name,   PutWrite.description,   _run_put_write),
    (CoveredCall.name, CoveredCall.description, _run_covered_call),
    (VolTarget.name,  VolTarget.description,  _run_vol_target),
    (AiPexLite.name,  AiPexLite.description,  _run_aipex),
]
_STRATEGY_MAP = {name: (desc, runner) for name, desc, runner in _STRATEGIES}


# ── Date range guard — warn before running if outside pre-cached window ───────
_CACHE_START = "2007-01-01"
_CACHE_END   = BACKTEST_END  # "2026-04-25"
_date_warning = False
try:
    _ts = pd.Timestamp(start_date)
    _te = pd.Timestamp(end_date)
    if _ts < pd.Timestamp(_CACHE_START) or _te > pd.Timestamp(_CACHE_END) or _ts >= _te:
        _date_warning = True
except Exception:
    _date_warning = True

if _date_warning:
    st.warning(
        f"**Date range outside pre-cached window ({_CACHE_START} – {_CACHE_END}).**  \n"
        "Fetching live data from yfinance / FRED — this may fail on Streamlit Cloud "
        "due to network restrictions. Reset dates in the sidebar to use cached data."
    )

# ── Overview ──────────────────────────────────────────────────────────────────
if page == "Overview":
    _page_header(
        "QIS Strategies",
        "Systematic equity derivatives backtesting — four institutional strategies against Solvency II and NAIC capital constraints.",
    )

    curve,       m,      _log,     _fr   = _run_put_write(start_date, end_date, cost_mode, custom_bps)
    bxm_curve,   bxm_m,  _bxm_log, _bfr  = _run_covered_call(start_date, end_date, cost_mode, custom_bps)
    vt_curve,    vt_m,   _vt_log,  _vfr  = _run_vol_target(start_date, end_date, cost_mode, custom_bps)
    aipex_curve, aipex_m, _ax_log, _afr  = _run_aipex(start_date, end_date, cost_mode, custom_bps)

    _all_curves  = [curve, bxm_curve, vt_curve, aipex_curve]
    _all_metrics = [m, bxm_m, vt_m, aipex_m]
    _ov_names    = [s[0] for s in _STRATEGIES]

    overview_choice = st.selectbox("Highlight strategy", _ov_names, key="overview_select")
    _ov_idx = _ov_names.index(overview_choice)
    _ov_m   = _all_metrics[_ov_idx]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CAGR",     f"{_ov_m['cagr']:.1%}")
    col2.metric("Sharpe",   f"{_ov_m['sharpe']:.2f}")
    col3.metric("Max DD",   f"{_ov_m['max_dd']:.1%}")
    col4.metric("Ann. Vol", f"{_ov_m['vol']:.1%}")

    spx_curve, _ = _run_spx(start_date, end_date)

    _section_header("Cumulative Return — All Strategies vs S&P 500")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=spx_curve.index, y=spx_curve, name="S&P 500",
        line=dict(color=_SPX_COLOR, width=1.5, dash="dash"),
        opacity=0.8,
    ))
    for _n, _c, _col in zip(_ov_names, _all_curves, _COLORS):
        _width = 2.5 if _n == overview_choice else 1.2
        _opacity = 1.0 if _n == overview_choice else 0.45
        fig.add_trace(go.Scatter(
            x=_c.index, y=_c, name=_n,
            line=dict(color=_col, width=_width),
            opacity=_opacity,
        ))
    fig.update_layout(**_dark("", height=420, yaxis_title="Index (base 100)"))
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "AiPEX-Lite is independently implemented, inspired by HSBC's AiPEX concept. "
        "Does not replicate HSBC's proprietary methodology."
    )


# ── Strategy Explorer ─────────────────────────────────────────────────────────
elif page == "Strategy Explorer":
    _page_header("Strategy Explorer")

    strategy_choice = st.selectbox("Select strategy", [s[0] for s in _STRATEGIES])
    _desc, _runner  = _STRATEGY_MAP[strategy_choice]
    curve, m, _log, framing = _runner(start_date, end_date, cost_mode, custom_bps)

    st.caption(_desc)

    _section_header("Performance Summary")
    # fetch spx metrics for delta comparison (loaded later anyway for chart)
    _, spx_m_early = _run_spx(start_date, end_date)
    metrics_display = [
        ("CAGR",     f"{m['cagr']:.1%}",    f"{m['cagr'] - spx_m_early['cagr']:+.1%} vs S&P 500"),
        ("Sharpe",   f"{m['sharpe']:.2f}",  f"{m['sharpe'] - spx_m_early['sharpe']:+.2f} vs S&P 500"),
        ("Sortino",  f"{m['sortino']:.2f}", None),
        ("Max DD",   f"{m['max_dd']:.1%}",  f"{m['max_dd'] - spx_m_early['max_dd']:+.1%} vs S&P 500"),
        ("Ann. Vol", f"{m['vol']:.1%}",     None),
        ("Skew",     f"{m['skew']:.2f}",    None),
    ]
    row1 = st.columns(3)
    row2 = st.columns(3)
    for col, (label, value, delta) in zip(row1, metrics_display[:3]):
        col.metric(label, value, delta)
    for col, (label, value, delta) in zip(row2, metrics_display[3:]):
        col.metric(label, value, delta)

    _section_header("Equity Curve vs S&P 500")
    _ov_names_local = [s[0] for s in _STRATEGIES]
    _strat_color = _COLORS[_ov_names_local.index(strategy_choice)] if strategy_choice in _ov_names_local else "#DB0011"
    spx_curve, spx_m = _run_spx(start_date, end_date)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=spx_curve.index, y=spx_curve, name="S&P 500",
        line=dict(color=_SPX_COLOR, width=1.5, dash="dash"),
        opacity=0.8,
    ))
    fig.add_trace(go.Scatter(
        x=curve.index, y=curve, name=strategy_choice,
        line=dict(color=_strat_color, width=2),
    ))
    fig.update_layout(**_dark("", height=360, yaxis_title="Index (base 100)"))
    st.plotly_chart(fig, use_container_width=True)

    dd = drawdown_series(curve)
    # Parse hex to rgba for fill
    _hex = _strat_color.lstrip("#")
    _r, _g, _b = int(_hex[0:2], 16), int(_hex[2:4], 16), int(_hex[4:6], 16)
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=dd.index, y=dd * 100,
        fill="tozeroy", name="Drawdown",
        line=dict(color=_strat_color, width=1),
        fillcolor=f"rgba({_r},{_g},{_b},0.20)",
    ))
    fig_dd.update_layout(**_dark("", height=220, yaxis_ticksuffix="%", yaxis_title="Drawdown (%)"))
    st.plotly_chart(fig_dd, use_container_width=True)

    _section_header("Monthly Returns")
    hm = monthly_heatmap_data(curve)
    hm.columns = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"][:len(hm.columns)]
    fig_hm = px.imshow(
        hm * 100,
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        text_auto=".1f",
        labels=dict(color="Return (%)"),
        aspect="auto",
    )
    fig_hm.update_layout(
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        font=dict(color=_FONT, size=10),
        margin=dict(l=48, r=16, t=16, b=16),
        height=380,
        coloraxis_colorbar=dict(tickfont=dict(color=_FONT), title_font=dict(color=_FONT)),
        xaxis=dict(tickfont=dict(color=_FONT)),
        yaxis=dict(tickfont=dict(color=_FONT)),
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    _section_header("Tail Risk")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("VaR 95%",  f"{m['var_95']:.2%}")
    c2.metric("CVaR 95%", f"{m['cvar_95']:.2%}")
    c3.metric("VaR 99%",  f"{m['var_99']:.2%}")
    c4.metric("CVaR 99%", f"{m['cvar_99']:.2%}")

    _section_header("Institutional Framing")
    for label, key in [
        ("Return Profile",       "return_profile"),
        ("Capital Efficiency",   "capital_efficiency"),
        ("Regulatory Treatment", "regulatory_treatment"),
        ("Liability Fit",        "liability_fit"),
        ("Structurer Pitch",     "structurer_pitch"),
    ]:
        with st.expander(label, expanded=True):
            st.write(framing.get(key, ""))


# ── Strategy Comparison ───────────────────────────────────────────────────────
elif page == "Strategy Comparison":
    _page_header(
        "Strategy Comparison",
        f"Transaction costs: {cost_mode.upper()}  ·  {start_date} – {end_date}",
    )

    put_curve,   put_m,   put_log,   _ = _run_put_write(start_date, end_date, cost_mode, custom_bps)
    bxm_curve,   bxm_m,   bxm_log,   _ = _run_covered_call(start_date, end_date, cost_mode, custom_bps)
    vt_curve,    vt_m,    vt_log,    _ = _run_vol_target(start_date, end_date, cost_mode, custom_bps)
    aipex_curve, aipex_m, aipex_log, _ = _run_aipex(start_date, end_date, cost_mode, custom_bps)
    spx_curve,   spx_m                 = _run_spx(start_date, end_date)

    curves = [put_curve, bxm_curve, vt_curve, aipex_curve]

    _section_header("Cumulative Return vs S&P 500")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=spx_curve.index, y=spx_curve, name="S&P 500",
        line=dict(color=_SPX_COLOR, width=1.5, dash="dash"),
        opacity=0.8,
    ))
    for name, c, color in zip(_STRAT_NAMES, curves, _COLORS):
        fig.add_trace(go.Scatter(x=c.index, y=c, name=name, line=dict(color=color, width=2)))
    fig.update_layout(**_dark("", height=420, yaxis_title="Index (base 100)"))
    st.plotly_chart(fig, use_container_width=True)

    _section_header("Performance Metrics")
    metric_rows = []
    for name, m in zip(_STRAT_NAMES + ["S&P 500"], [put_m, bxm_m, vt_m, aipex_m, spx_m]):
        metric_rows.append({
            "Strategy":   name,
            "CAGR":       f"{m['cagr']:.1%}",
            "Vol":        f"{m['vol']:.1%}",
            "Sharpe":     f"{m['sharpe']:.2f}",
            "Sortino":    f"{m['sortino']:.2f}",
            "Max DD":     f"{m['max_dd']:.1%}",
            "Skew":       f"{m['skew']:.2f}",
            "Best Mo.":   f"{m['best_month']:.1%}",
            "Worst Mo.":  f"{m['worst_month']:.1%}",
            "VaR 95%":    f"{m['var_95']:.2%}",
            "CVaR 95%":   f"{m['cvar_95']:.2%}",
        })
    st.dataframe(pd.DataFrame(metric_rows).set_index("Strategy"), use_container_width=True)

    _section_header("Return Correlations (incl. S&P 500)")
    ret_df = pd.DataFrame({
        **{n: c.pct_change().dropna() for n, c in zip(_STRAT_NAMES, curves)},
        "S&P 500": spx_curve.pct_change().dropna(),
    })
    corr = ret_df.corr()
    fig_corr = px.imshow(
        corr, text_auto=".2f",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        zmin=-1, zmax=1,
    )
    fig_corr.update_layout(
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        font=dict(color=_FONT, size=11),
        height=340,
        margin=dict(l=16, r=16, t=16, b=16),
        xaxis=dict(tickfont=dict(color=_FONT)),
        yaxis=dict(tickfont=dict(color=_FONT)),
        coloraxis_colorbar=dict(tickfont=dict(color=_FONT), title_font=dict(color=_FONT)),
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    _section_header("Cost Drag (Annualised)")
    drag_rows = []
    for name, log, c in zip(_STRAT_NAMES, [put_log, bxm_log, vt_log, aipex_log], curves):
        if log.empty or "gross_pnl" not in log.columns:
            drag = 0.0
        else:
            total_cost = (log["gross_pnl"] - log["net_pnl"]).sum()
            n_years = (c.index[-1] - c.index[0]).days / 365.25
            drag = total_cost / n_years if n_years > 0 else 0.0
        drag_rows.append({"Strategy": name, "Annual Cost Drag": f"{drag:.3%}"})
    st.dataframe(pd.DataFrame(drag_rows).set_index("Strategy"), use_container_width=True)
    st.caption(
        "Cost drag = gross P&L – net P&L from trade log, annualised. "
        "Zero for CBOE index strategies (costs embedded in published index)."
    )


# ── Client Pitch ──────────────────────────────────────────────────────────────
elif page == "Client Pitch":
    _page_header("Client Pitch")

    pitch_choice = st.selectbox("Select strategy", [s[0] for s in _STRATEGIES])
    _pitch_desc, _pitch_runner = _STRATEGY_MAP[pitch_choice]
    pitch_curve, pitch_m, _, pitch_framing = _pitch_runner(start_date, end_date, cost_mode, custom_bps)

    st.markdown(f"## {pitch_choice}")
    st.caption(_pitch_desc)

    _section_header("Investment Thesis")
    st.info(pitch_framing.get("structurer_pitch", ""))

    _section_header("Historical Performance")
    cols = st.columns(5)
    cols[0].metric("CAGR",     f"{pitch_m['cagr']:.1%}")
    cols[1].metric("Sharpe",   f"{pitch_m['sharpe']:.2f}")
    cols[2].metric("Max DD",   f"{pitch_m['max_dd']:.1%}")
    cols[3].metric("Ann. Vol", f"{pitch_m['vol']:.1%}")
    cols[4].metric("Sortino",  f"{pitch_m['sortino']:.2f}")

    _pitch_color = _COLORS[[s[0] for s in _STRATEGIES].index(pitch_choice)]
    spx_curve_p, _ = _run_spx(start_date, end_date)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=spx_curve_p.index, y=spx_curve_p, name="S&P 500",
        line=dict(color=_SPX_COLOR, width=1.5, dash="dash"),
        opacity=0.8,
    ))
    fig.add_trace(go.Scatter(
        x=pitch_curve.index, y=pitch_curve,
        name=pitch_choice, line=dict(color=_pitch_color, width=2.5),
    ))
    fig.update_layout(**_dark(
        f"Cumulative Return  ·  {start_date[:4]}–{end_date[:4]}  ·  Base 100",
        height=320,
        yaxis_title="Index (base 100)",
    ))
    st.plotly_chart(fig, use_container_width=True)

    _section_header("Institutional Fit")
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

    _section_header("Key Risks & Limitations")
    st.warning(
        "Backtest uses synthetic IV where applicable — not historical options data.  \n"
        "Regulatory metrics are directional proxies, not production-grade calculations.  \n"
        "Past performance does not predict future results.  \n"
        "CBOE index strategies use published index values; individual execution may differ."
    )


# ── About ─────────────────────────────────────────────────────────────────────
elif page == "About":
    _page_header("About & Methodology")

    _section_header("Data Sources")
    st.markdown("""
**CBOE PUT / BXM indices** — Direct FRED CSV download (series: PUTWRITE, BXMCBOE). Falls back to yfinance if unavailable.

**SPX, SPY, VIX, sector ETFs** — yfinance with local parquet cache (shipped with repo for Streamlit Cloud cold-start performance).
    """)

    _section_header("Synthetic IV")
    st.markdown("""
Strategies A (CBOE PUT) and B (CBOE BXM) use published index levels directly — no synthetic IV.
Strategy C (Vol-Targeted SPX) uses 20-day rolling realised vol on SPY as a vol proxy.
Strategy E (AiPEX-Lite) uses sector ETF price data only. All synthetic vol usage is labelled throughout the dashboard.
    """)

    _section_header("Transaction Cost Model")
    st.markdown("""
Costs are applied at trade execution and stored with each trade record.

| Mode     | ETF    | Futures/SPY | CBOE Indices |
|----------|--------|-------------|--------------|
| Default  | 2 bps  | 1 bp        | 0 bps        |
| Stressed | 6 bps  | 3 bps       | 0 bps        |
    """)

    _section_header("Regulatory Metrics")
    st.markdown("""
Solvency II SCR and NAIC RBC figures are simplified directional estimates, not production-grade regulatory calculations.
Do not use for actual capital planning.
    """)

    _section_header("AiPEX Disclaimer")
    st.markdown("""
AiPEX-Lite is an independently implemented strategy inspired by HSBC's AiPEX (AI-driven index) concept.
It does not replicate HSBC's proprietary methodology, signals, or weighting scheme.
    """)
