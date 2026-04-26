# QIS Backtester

**Live demo:** [qis-backtester-4vpappvczjyctft9mkye7wj.streamlit.app](https://qis-backtester-4vpappvczjyctft9mkye7wj.streamlit.app)  
**GitHub:** https://github.com/jjhalasz21/QIS-backtester  
**Author:** J H

A Quantitative Investment Strategies (QIS) backtesting platform simulating four systematic equity strategies against institutional and insurance portfolio constraints (Solvency II / NAIC).

Built to demonstrate fluency with QIS product design, derivatives pricing infrastructure, and institutional client framing — the language of equity derivatives structuring desks.

---

## Strategies

| Strategy | Type | Institutional Angle |
|---|---|---|
| **CBOE PUT — Insurance Carry** | Index replication | Positive carry, bond-like vol, lower equity SCR |
| **CBOE BXM — Yield Enhancement** | Index replication | Yield on existing equity, lower vol vs. direct SPX |
| **Vol-Targeted SPX** | Dynamic overlay | Predictable capital consumption, stable SCR charge |
| **AiPEX-Lite** | Factor rotation | Explainable systematic equity, rules-based for insurance boards |

> **AiPEX-Lite disclaimer:** Independently implemented, inspired by HSBC's AiPEX (AI-driven index) concept. Does not replicate HSBC's proprietary methodology, signals, or weighting scheme.

---

## Features

- **Transaction cost toggle:** Off / Default (institutional) / Stressed (3×) / Custom (bps) — costs re-applied post-hoc from trade logs without re-running backtests
- **Institutional framing panel** per strategy: return profile, capital efficiency, Solvency II SCR proxy, NAIC RBC proxy, liability fit, structurer pitch
- **Client Pitch View:** clean one-pager layout suitable for a structuring conversation
- **Strategy Comparison:** side-by-side metrics, correlation matrix, cost drag analysis
- **Pure numpy BSM:** Black-Scholes pricing and Greeks (Δ, Γ, ν, θ, ρ) from first principles — no py_vollib

---

## Pricing & Data

**BSM:** Implemented from first principles in `src/pricing/black_scholes.py`. Full closed-form Greeks. No external pricing library.

**Synthetic IV:** 20-day rolling realized vol + 2 vol point skew spread, used as an implied vol proxy for Strategy C. Clearly labeled as synthetic throughout — not historical IV.

**Data sources:**
- CBOE PUT / BXM indices: Direct FRED CSV download (series: PUTWRITE, BXMCBOE). Falls back to yfinance if unavailable.
- SPX, SPY, VIX, sector ETFs (XLK, XLF, XLV, XLE, XLY): yfinance
- All data cached locally as parquet after first pull

**Backtest window:** 2007–present (captures GFC, 2011 Euro crisis, 2018 VIXplosion, COVID crash, 2022 rate shock)

---

## Regulatory Metrics (Directional Proxies Only)

Solvency II SCR-equity proxy: 39% × |worst 1-year rolling return|

NAIC RBC C-1 proxy: 30% × (realized vol / 15% SPX long-run vol)

These are simplified directional estimates for comparison purposes. Do not use for actual regulatory capital planning.

---

## Setup

```bash
git clone https://github.com/jjhalasz21/QIS-backtester.git
cd QIS-backtester
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. First run fetches data from FRED and yfinance (~30 seconds); subsequent runs use the local parquet cache.

---

## Tests

```bash
pytest tests/ -v
```

62 tests covering strategy logic, BSM pricing, tearsheet analytics, and insurance metrics.

---

## Architecture

```
src/
├── data/        loader.py (yfinance + direct FRED CSV), cache.py (parquet)
├── pricing/     black_scholes.py (BSM + Greeks), synthetic_iv.py
├── strategies/  base.py (abstract), put_write.py, covered_call.py, vol_target.py, aipex_lite.py
├── engine/      costs.py (Off/Default/Stressed/Custom cost model)
├── analytics/   tearsheet.py, insurance_metrics.py, comparisons.py
└── utils/       config.py, calendar.py
```

Each strategy exposes the same interface (`run()`, `metrics()`, `equity_curve()`, `trade_log()`, `institutional_framing()`), making the comparison view and cost toggle trivially extensible to new strategies.

---

## Resume Bullet

> Built a QIS backtesting platform in Python simulating four systematic equity strategies (put-writing, covered calls, vol-targeting, and an AiPEX-inspired factor rotation) with pure numpy Black-Scholes pricing and institutional/insurance framing including Solvency II capital efficiency proxies. [[GitHub](https://github.com/jjhalasz21/QIS-backtester)] [[Live demo](https://qis-backtester-4vpappvczjyctft9mkye7wj.streamlit.app)]
