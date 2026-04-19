# QIS Backtester — Design Spec

**Date:** 2026-04-19
**Author:** Jack Halasz
**Status:** Approved

---

## 1. Purpose & Context

A Quantitative Investment Strategies (QIS) backtesting platform demonstrating fluency with systematic equity derivatives strategy design, Python pricing infrastructure, and institutional/insurance client framing. Target audience: EQD structuring desk interview context, institutional and insurance clients (Solvency II / NAIC-constrained portfolios).

**Deliverable:** Streamlit dashboard backed by a Python package, deployed to Streamlit Community Cloud with a live demo URL.

---

## 2. Scope

### In Scope (4 strategies, cutting Strategy D)
- **Strategy A:** CBOE PUT replication — "Insurance Carry"
- **Strategy B:** CBOE BXM replication — "Yield Enhancement Overlay"
- **Strategy C:** Vol-targeted SPX overlay — "Capital-Efficient Equity"
- **Strategy E:** AiPEX-Lite sector ETF factor rotation — "AI-Driven Factor Rotation"

### Out of Scope (V1)
- Strategy D (1x3 risk reversal) — cut per scope guardrail; most complex options-level strategy
- PDF export of Client Pitch View
- Real historical options data (synthetic IV used instead)
- Margin / rigorous SCR modeling

### Backtest Window
2007–present — captures GFC, 2011 Euro crisis, 2018 VIXplosion, COVID crash, 2022 rate shock.

---

## 3. Architecture

### Directory Structure

```
QIS-backtester/
├── app.py                        # Streamlit entry point
├── requirements.txt
├── README.md
├── .env.example
├── src/
│   ├── data/
│   │   ├── loader.py             # yfinance + FRED pulls
│   │   └── cache.py              # parquet read/write, keyed by (ticker, start, end)
│   ├── pricing/
│   │   ├── black_scholes.py      # pure numpy BSM + Greeks (analytical closed-form)
│   │   └── synthetic_iv.py       # 20-day realized vol + constant skew spread
│   ├── strategies/
│   │   ├── base.py               # abstract: run(), metrics(), equity_curve(), trade_log()
│   │   ├── put_write.py          # Strategy A
│   │   ├── covered_call.py       # Strategy B
│   │   ├── vol_target.py         # Strategy C
│   │   └── aipex_lite.py         # Strategy E
│   ├── engine/
│   │   ├── backtester.py         # simulation loop
│   │   ├── portfolio.py          # position tracking, gross + net P&L per trade
│   │   └── costs.py              # Off / Default / Stressed / Custom cost modes
│   ├── analytics/
│   │   ├── tearsheet.py          # standard + institutional metrics
│   │   ├── insurance_metrics.py  # Solvency II SCR proxy, NAIC RBC proxy
│   │   └── comparisons.py        # cross-strategy metric table
│   └── utils/
│       ├── calendar.py           # trading day utilities
│       └── config.py             # constants, date range, paths
├── data/                         # parquet cache (gitignored)
├── docs/
│   └── superpowers/specs/
├── notebooks/
│   └── research.ipynb
└── tests/
    └── test_strategies.py
```

### Key Architectural Decisions

1. **Uniform strategy interface** — `base.py` abstract class enforces `run()`, `metrics()`, `equity_curve()`, `trade_log()`. The comparison view and cost toggle work automatically for any strategy.
2. **Post-hoc cost application** — trade records store gross and net P&L at execution time. The cost toggle re-applies costs from the stored trade log without re-running the backtest.
3. **Parquet cache** — keyed by `(ticker, start_date, end_date)`. FRED/yfinance called only on cache miss. `force_refresh=True` flag for explicit updates.
4. **Streamlit session state** — backtest results cached per strategy after first run. Page navigation and cost toggle changes do not re-run simulations.

---

## 4. Environment

- **Location:** `C:\Users\jhala\OneDrive\Desktop\QIS-backtester\`
- **Python environment:** `venv` + `requirements.txt`
- **Deployment:** GitHub repo → Streamlit Community Cloud (both accounts to be created during build)
- **No secrets required for V1** — all data sources are free and unauthenticated

---

## 5. Data Layer

### Sources

| Source | Tickers / Series | Used For |
|---|---|---|
| FRED via `pandas-datareader` | `CBOE/PUT`, `CBOE/BXM` | Strategies A & B index levels |
| yfinance | `^GSPC`, `SPY`, `^VIX` | SPX proxy, vol signal |
| yfinance | `XLK`, `XLF`, `XLV`, `XLE`, `XLY` | AiPEX-Lite sector ETFs |
| yfinance | `^TNX` | Risk-free rate for BSM |

### Synthetic IV (Strategy C)
- 20-day rolling realized vol on SPX, annualized
- Constant skew spread (~2 vol points) added to proxy implied vol
- Labeled as synthetic throughout the dashboard — not historical IV
- Adequate for vol-targeting which uses realized vol directly

---

## 6. Pricing

### Pure Numpy BSM
Written from first principles — no `py_vollib` dependency:
- `call_price()`, `put_price()` — standard Black-Scholes for European options
- Greeks: delta, gamma, vega, theta, rho — all analytical closed-form
- IV solver via `scipy.optimize.brentq` if needed
- Fully explainable in an interview context

---

## 7. Strategies

### Strategy A — CBOE PUT ("Insurance Carry")
- Load `CBOE/PUT` index from FRED; compute daily returns from index levels
- No options simulation — published index is already net of strategy
- Cost: 0 bps (index values are net)
- Benchmark: SPX total return
- Institutional angle: positive carry with bond-like return profile; lower equity SCR than direct equity

### Strategy B — CBOE BXM ("Yield Enhancement Overlay")
- Load `CBOE/BXM` from FRED; same approach as Strategy A
- Cost: 0 bps
- Institutional angle: yield enhancement on existing equity; caps upside, reduces vol contribution to SCR

### Strategy C — Vol-Targeted SPX Overlay ("Capital-Efficient Equity")
- Daily SPY returns as SPX proxy
- Target weight = 10% / 20-day realized vol, capped at 150% notional
- Rebalance daily; transaction costs applied on notional delta each day (1 bp/leg)
- Tracks: realized vol vs. 10% target, leverage ratio over time
- Institutional angle: lower drawdowns → lower SCR volatility → lower capital charge volatility

### Strategy E — AiPEX-Lite ("AI-Driven Factor Rotation")
- Universe: XLK, XLF, XLV, XLE, XLY
- Monthly signals: 12-1 month momentum + VIX level as risk-on/off gate
- Rank sectors → equal-weight top 3 each month
- Cost: 2 bps/leg on rotation notional
- Institutional angle: systematic factor exposure with transparent methodology; addresses insurance need for explainable allocation models
- Dashboard explicitly references HSBC AiPEX as inspiration; labels AiPEX-Lite as independent implementation

---

## 8. Transaction Cost Model

| Instrument | Default Cost | Rationale |
|---|---|---|
| Sector ETFs (AiPEX-Lite) | 2 bps/leg | Tight spreads, high liquidity |
| SPY / SPX futures proxy (vol-target) | 1 bp/leg | Extremely liquid |
| CBOE index replications (PUT, BXM) | 0 bps | Published index values are already net |

**Toggle modes:** Off / Default / Stressed (3x default) / Custom (bps input)

Costs re-applied post-hoc from trade log — no backtest re-run on toggle change. Cost drag metric shows annualized return impact.

---

## 9. Analytics & Tearsheet

### Standard Metrics
CAGR, annualized vol, Sharpe, Sortino, max drawdown, drawdown duration, recovery time, skewness, kurtosis, best/worst month, rolling 12-month return and vol, monthly return heatmap, 95%/99% VaR and CVaR, correlation to SPX / AGG proxy / VIX.

### Institutional Framing Panel (every strategy page)
| Field | Content |
|---|---|
| Return profile | Equity-like / credit-like / uncorrelated |
| Capital efficiency | Vol and DD vs. direct SPX; implies lower SCR charge |
| Regulatory treatment | Simplified Solvency II SCR-equity proxy + NAIC RBC C-1 factor |
| Liability fit | Carry-generating vs. hedging; maps to insurance GA use case |
| Structurer pitch | One sentence: when to pitch this to an insurance CIO |

### Comparison View
Side-by-side metric table (all 4 strategies), cumulative return overlay, correlation matrix, cost drag comparison. All figures respect active cost setting.

---

## 10. Streamlit UI

### Sidebar (global)
- Transaction cost toggle: Off / Default / Stressed / Custom (bps)
- Date range slider (default: 2007–present)
- Strategy selector

### Pages
1. **Overview** — project summary, 4-strategy vs. SPX cumulative chart, headline metrics
2. **Strategy Explorer** — single strategy: rules, institutional framing, equity curve, drawdown, rolling metrics, heatmap, gross vs. net P&L
3. **Strategy Comparison** — metric table, cumulative overlay, correlation matrix, cost drag chart
4. **Client Pitch View** — single strategy as pitchbook one-pager: thesis → rules → performance → risks → institutional fit
5. **About / Methodology** — synthetic IV disclosure, cost model assumptions, regulatory proxy limitations, AiPEX disclaimer

---

## 11. Build Sequence (Vertical Slice First)

1. Scaffold repo, venv, requirements.txt, README skeleton
2. GitHub account + repo setup; Streamlit Cloud account
3. Data loaders + parquet cache (FRED + yfinance)
4. Config, calendar utilities
5. Base strategy abstract class + portfolio tracker + cost module
6. **Strategy A (PUT write) end-to-end** — data → backtest → metrics → equity curve
7. Tearsheet analytics module
8. Streamlit app skeleton + Page 1 (Overview) + Page 2 (Strategy Explorer) for Strategy A
9. Sidebar cost toggle wired to analytics
10. Deploy to Streamlit Cloud (working 1-strategy demo)
11. Strategy B (BXM) — same pattern, add to comparison
12. Strategy C (vol-target) — add synthetic IV, daily rebalance logic
13. Strategy E (AiPEX-Lite) — momentum + VIX signal, monthly rotation
14. Pure numpy BSM module (for any future options work; demonstrates pricing knowledge)
15. Insurance metrics module (SCR proxy, NAIC RBC)
16. Institutional framing panels for all 4 strategies
17. Pages 3 (Comparison), 4 (Pitch View), 5 (About)
18. Cost drag metric + gross vs. net P&L charts
19. Unit tests for strategy logic
20. README polish — screenshots, setup instructions, AiPEX disclaimer, live demo URL

---

## 12. Success Criteria

- [ ] All 4 strategies backtest over 2007–present
- [ ] Streamlit app runs locally and is deployed to Streamlit Cloud with live URL
- [ ] Each strategy has institutional framing panel
- [ ] Cost toggle (Off / Default / Stressed / Custom) updates all metrics without re-running backtests
- [ ] Tearsheet metrics match industry standards
- [ ] Client Pitch View renders cleanly for at least one strategy
- [ ] Pure numpy BSM implemented and explainable
- [ ] README labels AiPEX-Lite as independent implementation inspired by HSBC AiPEX
- [ ] Public GitHub repo with clean commit history and screenshots

---

## 13. Resume Bullet (Target)

> Built a QIS backtesting platform in Python simulating four systematic equity strategies (put-writing, covered calls, vol-targeting, and an AiPEX-inspired factor rotation) with pure numpy Black-Scholes pricing and institutional/insurance framing including Solvency II capital efficiency proxies. [GitHub link] [Live demo link]
