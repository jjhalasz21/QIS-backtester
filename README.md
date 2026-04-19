# QIS Backtester

A Quantitative Investment Strategies (QIS) backtesting platform simulating four systematic equity strategies against institutional and insurance portfolio constraints.

**Live demo:** _coming soon_
**Author:** Jack Halasz

## Strategies
- **CBOE PUT — Insurance Carry:** Fully collateralized put-write, tracking CBOE PUT Index
- **CBOE BXM — Yield Enhancement Overlay:** Long SPX + short ATM call, tracking CBOE BXM Index
- **Vol-Targeted SPX — Capital-Efficient Equity:** Dynamic SPX exposure targeting 10% portfolio vol
- **AiPEX-Lite — AI-Driven Factor Rotation:** Monthly sector ETF rotation using momentum + VIX signal

> **AiPEX-Lite disclaimer:** This strategy is independently implemented and is inspired by HSBC's AiPEX index concept. It does not replicate HSBC's proprietary methodology.

## Setup
```bash
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Data Sources
- CBOE PUT / BXM indices: FRED via pandas-datareader
- SPX, SPY, VIX, sector ETFs: yfinance
- All data cached locally as parquet after first pull

## Pricing
Black-Scholes pricing and Greeks implemented from first principles in pure numpy (no py_vollib dependency). Synthetic IV derived from 20-day rolling realized vol plus a constant skew spread — clearly labeled throughout the dashboard.

## Institutional Framing
Each strategy includes a framing panel covering return profile, capital efficiency, simplified Solvency II SCR-equity proxy, NAIC RBC C-1 factor, liability fit, and a one-sentence structurer pitch.
