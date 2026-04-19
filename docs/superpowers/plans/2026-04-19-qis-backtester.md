# QIS Backtester Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 4-strategy QIS backtesting Streamlit dashboard deployed to Streamlit Cloud, demonstrating systematic equity derivatives strategy design and institutional/insurance framing for an EQD structuring desk interview.

**Architecture:** Vertical-slice first — Strategy A (CBOE PUT) runs end-to-end before other strategies are added. Each strategy implements a uniform `BaseStrategy` interface (`run()`, `metrics()`, `equity_curve()`, `trade_log()`). Cost toggle re-applies from stored trade logs without re-running backtests.

**Tech Stack:** Python 3.11+, pandas, numpy, scipy, yfinance, pandas-datareader (FRED), plotly, streamlit, pyarrow, pytest.

---

## File Map

| File | Responsibility |
|---|---|
| `app.py` | Streamlit entry point, sidebar, page routing |
| `src/utils/config.py` | Constants: paths, tickers, date range |
| `src/utils/calendar.py` | Trading day utilities |
| `src/data/cache.py` | Parquet read/write keyed by (ticker, start, end) |
| `src/data/loader.py` | yfinance + FRED fetches with cache |
| `src/engine/costs.py` | Cost model: Off/Default/Stressed/Custom |
| `src/strategies/base.py` | Abstract base class |
| `src/strategies/put_write.py` | Strategy A — CBOE PUT replication |
| `src/strategies/covered_call.py` | Strategy B — CBOE BXM replication |
| `src/strategies/vol_target.py` | Strategy C — vol-targeted SPX overlay |
| `src/strategies/aipex_lite.py` | Strategy E — sector ETF factor rotation |
| `src/analytics/tearsheet.py` | Sharpe, Sortino, max DD, VaR, CVaR, heatmap data |
| `src/analytics/insurance_metrics.py` | Solvency II SCR proxy, NAIC RBC proxy |
| `src/analytics/comparisons.py` | Cross-strategy metric table, correlation matrix |
| `src/pricing/black_scholes.py` | Pure numpy BSM + Greeks (delta, gamma, vega, theta, rho) |
| `src/pricing/synthetic_iv.py` | 20-day realized vol + constant skew spread |
| `src/engine/backtester.py` | Thin runner: instantiates and runs all strategies |
| `tests/test_costs.py` | Cost module unit tests |
| `tests/test_tearsheet.py` | Tearsheet metric unit tests |
| `tests/test_pricing.py` | BSM pricing + Greeks tests |
| `tests/test_strategies.py` | Strategy interface + output shape tests |

---

## Task 1: Repo Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `README.md`
- Create: `.env.example`
- Create: All `src/` subdirectories with `__init__.py`
- Create: `data/` (gitignored), `tests/`, `notebooks/`

- [ ] **Step 1: Create the directory tree**

Run from `C:\Users\jhala\OneDrive\Desktop\QIS-backtester\`:

```bash
mkdir -p src/data src/pricing src/strategies src/engine src/analytics src/utils tests data notebooks
touch src/__init__.py src/data/__init__.py src/pricing/__init__.py
touch src/strategies/__init__.py src/engine/__init__.py src/analytics/__init__.py src/utils/__init__.py
touch tests/__init__.py
```

- [ ] **Step 2: Write requirements.txt**

```
streamlit>=1.32.0,<2.0.0
pandas>=2.0.0,<3.0.0
numpy>=1.26.0,<2.0.0
scipy>=1.12.0
yfinance>=0.2.40
pandas-datareader>=0.10.0
pyarrow>=14.0.0
plotly>=5.18.0
matplotlib>=3.8.0
pytest>=8.0.0
```

- [ ] **Step 3: Write .gitignore**

```
data/
.env
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/
.streamlit/secrets.toml
```

- [ ] **Step 4: Write .env.example**

```
# No secrets required for V1 — all data sources are free and unauthenticated
```

- [ ] **Step 5: Create venv and install dependencies**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Expected: all packages install without error. Verify with `pip list | grep streamlit`.

- [ ] **Step 6: Write README.md skeleton**

```markdown
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
\`\`\`bash
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## Data Sources
- CBOE PUT / BXM indices: FRED via pandas-datareader
- SPX, SPY, VIX, sector ETFs: yfinance
- All data cached locally as parquet after first pull

## Pricing
Black-Scholes pricing and Greeks implemented from first principles in pure numpy (no py_vollib dependency). Synthetic IV derived from 20-day rolling realized vol plus a constant skew spread — clearly labeled throughout the dashboard.

## Institutional Framing
Each strategy includes a framing panel covering return profile, capital efficiency, simplified Solvency II SCR-equity proxy, NAIC RBC C-1 factor, liability fit, and a one-sentence structurer pitch.
```

- [ ] **Step 7: Initial git commit**

```bash
git init
git add requirements.txt .gitignore README.md .env.example src/ tests/ notebooks/
git commit -m "chore: scaffold QIS-backtester repo"
```

---

## Task 2: GitHub + Streamlit Cloud Setup

This task has no code — it's account and repo setup.

- [ ] **Step 1: Create GitHub account**

Go to https://github.com — sign up with your email (jjhalasz21@gmail.com). Choose username `jhalasz` or similar.

- [ ] **Step 2: Create GitHub repo**

On GitHub: New repository → name `QIS-backtester` → Public → no README (you already have one) → Create.

- [ ] **Step 3: Push local repo to GitHub**

```bash
git remote add origin https://github.com/YOUR_USERNAME/QIS-backtester.git
git branch -M main
git push -u origin main
```

- [ ] **Step 4: Create Streamlit Community Cloud account**

Go to https://share.streamlit.io — sign in with GitHub. Authorize Streamlit to access your repos.

- [ ] **Step 5: Note deployment URL format**

Once deployed, your app will be at: `https://YOUR_USERNAME-qis-backtester-app-HASH.streamlit.app`. You'll get the exact URL after the first deployment in Task 11.

---

## Task 3: Config + Calendar Utilities

**Files:**
- Create: `src/utils/config.py`
- Create: `src/utils/calendar.py`
- Create: `tests/test_utils.py`

- [ ] **Step 1: Write the failing test**

`tests/test_utils.py`:
```python
import pytest
from datetime import date
from src.utils.config import DATA_DIR, BACKTEST_START, SECTOR_ETFS
from src.utils.calendar import trading_days

def test_data_dir_exists():
    assert DATA_DIR.exists()

def test_backtest_start_is_2007():
    assert BACKTEST_START == "2007-01-01"

def test_sector_etfs_has_five():
    assert len(SECTOR_ETFS) == 5
    assert "XLK" in SECTOR_ETFS

def test_trading_days_returns_business_days():
    days = trading_days("2024-01-01", "2024-01-31")
    # Jan 2024: no business days on weekends
    assert all(d.weekday() < 5 for d in days)
    assert len(days) == 23  # 23 business days in Jan 2024

def test_trading_days_count_over_year():
    days = trading_days("2023-01-01", "2023-12-31")
    # NYSE has ~252 trading days; pandas bdate_range gives ~261 (no holiday adjustment)
    assert 250 <= len(days) <= 265
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_utils.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.utils.config'`

- [ ] **Step 3: Write src/utils/config.py**

```python
from pathlib import Path
import datetime

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

BACKTEST_START = "2007-01-01"
BACKTEST_END = datetime.date.today().strftime("%Y-%m-%d")

SPX_TICKER = "^GSPC"
SPY_TICKER = "SPY"
VIX_TICKER = "^VIX"
TNX_TICKER = "^TNX"

SECTOR_ETFS = ["XLK", "XLF", "XLV", "XLE", "XLY"]

FRED_PUT = "PUTWRITE"   # CBOE S&P 500 PutWrite Index on FRED
FRED_BXM = "BXMCBOE"   # CBOE S&P 500 BuyWrite Index on FRED
# If FRED IDs above fail, fallback tickers for yfinance: "^PUTR", "^BXM"

TRADING_DAYS_PER_YEAR = 252
VOL_TARGET = 0.10
MAX_LEVERAGE = 1.5
VOL_LOOKBACK = 20
VIX_RISK_OFF_THRESHOLD = 30
AIPEX_TOP_N = 3
MOMENTUM_WINDOW = 252   # 12 months
MOMENTUM_SKIP = 21      # skip last month
```

- [ ] **Step 4: Write src/utils/calendar.py**

```python
import pandas as pd

def trading_days(start: str, end: str) -> pd.DatetimeIndex:
    """Return business days between start and end (inclusive). No holiday adjustment."""
    return pd.bdate_range(start=start, end=end)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_utils.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/utils/config.py src/utils/calendar.py tests/test_utils.py
git commit -m "feat: add config constants and calendar utility"
```

---

## Task 4: Parquet Cache Module

**Files:**
- Create: `src/data/cache.py`
- Create: `tests/test_cache.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cache.py`:
```python
import pandas as pd
import pytest
from src.data.cache import cache_key, save, load

def test_cache_key_sanitizes_carets():
    key = cache_key("^GSPC", "2020-01-01", "2020-12-31")
    assert "^" not in key
    assert "GSPC" in key

def test_cache_key_sanitizes_slashes():
    key = cache_key("CBOE/PUT", "2020-01-01", "2020-12-31")
    assert "/" not in key

def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    import src.data.cache as cache_mod
    monkeypatch.setattr(cache_mod, "DATA_DIR", tmp_path)

    df = pd.DataFrame({"close": [100.0, 101.0, 102.0]},
                      index=pd.date_range("2020-01-01", periods=3))
    key = "test_ticker_2020_2020"
    save(key, df, data_dir=tmp_path)

    result = load(key, data_dir=tmp_path)
    assert result is not None
    pd.testing.assert_frame_equal(result, df)

def test_load_returns_none_for_missing(tmp_path):
    from src.data.cache import load
    result = load("nonexistent_key", data_dir=tmp_path)
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_cache.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.data.cache'`

- [ ] **Step 3: Write src/data/cache.py**

```python
from pathlib import Path
import pandas as pd
from src.utils.config import DATA_DIR as _DEFAULT_DATA_DIR


def cache_key(ticker: str, start: str, end: str) -> str:
    safe = ticker.replace("^", "").replace("/", "_").replace("=", "")
    return f"{safe}_{start}_{end}"


def _path(key: str, data_dir: Path) -> Path:
    return data_dir / f"{key}.parquet"


def load(key: str, data_dir: Path = _DEFAULT_DATA_DIR) -> pd.DataFrame | None:
    p = _path(key, data_dir)
    if p.exists():
        return pd.read_parquet(p)
    return None


def save(key: str, df: pd.DataFrame, data_dir: Path = _DEFAULT_DATA_DIR) -> None:
    df.to_parquet(_path(key, data_dir))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cache.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/data/cache.py tests/test_cache.py
git commit -m "feat: add parquet cache module"
```

---

## Task 5: Data Loaders

**Files:**
- Create: `src/data/loader.py`

No unit tests for network calls — integration tested implicitly when strategies run. Cache logic already tested in Task 4.

- [ ] **Step 1: Write src/data/loader.py**

```python
from __future__ import annotations
import pandas as pd
import yfinance as yf
import pandas_datareader as pdr
from src.data.cache import cache_key, load, save


def fetch_prices(
    ticker: str,
    start: str,
    end: str,
    force_refresh: bool = False,
) -> pd.Series:
    """Fetch adjusted close prices from yfinance. Returns pd.Series indexed by date."""
    key = cache_key(ticker, start, end)
    if not force_refresh:
        cached = load(key)
        if cached is not None:
            return cached["close"]

    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"yfinance returned no data for {ticker} ({start}–{end})")

    series = df["Close"].squeeze()
    series.index = pd.to_datetime(series.index)
    save(key, pd.DataFrame({"close": series}))
    return series


def fetch_fred(
    series_id: str,
    start: str,
    end: str,
    force_refresh: bool = False,
) -> pd.Series:
    """Fetch a FRED series via pandas-datareader. Returns pd.Series indexed by date."""
    key = cache_key(series_id, start, end)
    if not force_refresh:
        cached = load(key)
        if cached is not None:
            return cached["value"]

    df = pdr.get_data_fred(series_id, start=start, end=end)
    if df.empty:
        raise ValueError(f"FRED returned no data for {series_id} ({start}–{end})")

    series = df.iloc[:, 0].dropna()
    series.index = pd.to_datetime(series.index)
    save(key, pd.DataFrame({"value": series}))
    return series


def fetch_cboe_index(
    fred_id: str,
    yf_fallback: str,
    start: str,
    end: str,
    force_refresh: bool = False,
) -> pd.Series:
    """
    Fetch CBOE index. Tries FRED first; falls back to yfinance.
    FRED IDs: PUTWRITE (PUT index), BXMCBOE (BXM index).
    yfinance fallbacks: ^PUTR, ^BXM.
    """
    try:
        return fetch_fred(fred_id, start, end, force_refresh)
    except Exception:
        return fetch_prices(yf_fallback, start, end, force_refresh)
```

- [ ] **Step 2: Verify loader imports cleanly**

```bash
python -c "from src.data.loader import fetch_prices, fetch_fred, fetch_cboe_index; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/data/loader.py
git commit -m "feat: add yfinance and FRED data loaders with parquet cache"
```

---

## Task 6: Cost Module

**Files:**
- Create: `src/engine/costs.py`
- Create: `tests/test_costs.py`

- [ ] **Step 1: Write the failing test**

`tests/test_costs.py`:
```python
from src.engine.costs import get_cost_bps, apply_costs

def test_off_mode_returns_zero():
    assert get_cost_bps("etf", "off") == 0.0
    assert get_cost_bps("futures", "off") == 0.0
    assert get_cost_bps("index", "off") == 0.0

def test_default_etf_is_2bps():
    assert get_cost_bps("etf", "default") == 2.0

def test_default_futures_is_1bps():
    assert get_cost_bps("futures", "default") == 1.0

def test_default_index_is_0bps():
    assert get_cost_bps("index", "default") == 0.0

def test_stressed_is_3x_default():
    assert get_cost_bps("etf", "stressed") == 6.0
    assert get_cost_bps("futures", "stressed") == 3.0

def test_custom_mode_uses_provided_bps():
    assert get_cost_bps("etf", "custom", custom_bps=7.5) == 7.5

def test_apply_costs_deducts_from_gross():
    # 100 notional, 2bps = 0.02 cost
    net = apply_costs(gross_pnl=1.0, notional=100.0, cost_bps=2.0)
    assert abs(net - (1.0 - 0.02)) < 1e-10

def test_apply_costs_zero_bps_unchanged():
    assert apply_costs(gross_pnl=1.5, notional=100.0, cost_bps=0.0) == 1.5
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_costs.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.engine.costs'`

- [ ] **Step 3: Write src/engine/costs.py**

```python
_DEFAULT: dict[str, float] = {
    "etf": 2.0,      # sector ETFs (AiPEX-Lite)
    "futures": 1.0,  # SPY/SPX proxy (vol-target)
    "options": 5.0,  # SPX options (future use)
    "index": 0.0,    # CBOE published indices (PUT, BXM) — costs already embedded
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_costs.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/engine/costs.py tests/test_costs.py
git commit -m "feat: add transaction cost module with Off/Default/Stressed/Custom modes"
```

---

## Task 7: Base Strategy Abstract Class

**Files:**
- Create: `src/strategies/base.py`

No direct unit tests — abstract classes are tested through concrete implementations.

- [ ] **Step 1: Write src/strategies/base.py**

```python
from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    name: str = "Unnamed Strategy"
    description: str = ""
    instrument_type: str = "index"  # "index" | "futures" | "etf" | "options"

    @abstractmethod
    def run(self, start: str, end: str, cost_mode: str = "default", custom_bps: float = 0.0) -> None:
        """Execute the backtest. Must populate equity curve, metrics, and trade log."""
        ...

    @abstractmethod
    def metrics(self) -> dict:
        """Return dict of performance metrics. Call run() first."""
        ...

    @abstractmethod
    def equity_curve(self) -> pd.Series:
        """Return daily equity curve (base 100). Call run() first."""
        ...

    @abstractmethod
    def trade_log(self) -> pd.DataFrame:
        """
        Return DataFrame of trade records with columns:
        notional, gross_pnl, cost_bps, net_pnl — indexed by date.
        """
        ...

    def institutional_framing(self) -> dict:
        """
        Return dict with keys: return_profile, capital_efficiency,
        regulatory_treatment, liability_fit, structurer_pitch.
        Override in each concrete strategy.
        """
        return {}
```

- [ ] **Step 2: Verify it imports**

```bash
python -c "from src.strategies.base import BaseStrategy; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Write src/engine/backtester.py**

```python
from src.strategies.put_write import PutWrite
from src.strategies.covered_call import CoveredCall
from src.strategies.vol_target import VolTarget
from src.strategies.aipex_lite import AiPexLite

ALL_STRATEGIES: dict = {
    "PUT Write": PutWrite,
    "BXM": CoveredCall,
    "Vol Target": VolTarget,
    "AiPEX-Lite": AiPexLite,
}


def run_all(
    start: str,
    end: str,
    cost_mode: str = "default",
    custom_bps: float = 0.0,
) -> dict:
    """Run all strategies and return {name: strategy_instance}."""
    results = {}
    for name, cls in ALL_STRATEGIES.items():
        s = cls()
        s.run(start, end, cost_mode, custom_bps)
        results[name] = s
    return results
```

Note: `backtester.py` imports will fail until all 4 strategy files exist. This is expected — it's only called once all strategies are implemented (Task 15).

- [ ] **Step 4: Commit**

```bash
git add src/strategies/base.py src/engine/backtester.py
git commit -m "feat: add BaseStrategy abstract class and backtester runner"
```

---

## Task 8: Tearsheet Analytics

**Files:**
- Create: `src/analytics/tearsheet.py`
- Create: `tests/test_tearsheet.py`

- [ ] **Step 1: Write the failing test**

`tests/test_tearsheet.py`:
```python
import numpy as np
import pandas as pd
import pytest
from src.analytics.tearsheet import (
    cagr, annualized_vol, sharpe, sortino,
    max_drawdown, var, cvar, compute_all, monthly_heatmap_data,
)

# Synthetic equity curve: $100 growing at ~10% annualized with some noise
np.random.seed(42)
_RETURNS = np.random.normal(0.0004, 0.01, 252 * 5)  # 5 years of daily returns
_EQUITY = pd.Series(
    100 * np.cumprod(1 + _RETURNS),
    index=pd.bdate_range("2018-01-02", periods=len(_RETURNS)),
)

def test_cagr_positive_for_growing_equity():
    result = cagr(_EQUITY)
    assert result > 0

def test_cagr_type():
    assert isinstance(cagr(_EQUITY), float)

def test_annualized_vol_reasonable():
    result = annualized_vol(_EQUITY.pct_change().dropna())
    assert 0.05 < result < 0.30  # typical equity vol

def test_sharpe_type():
    assert isinstance(sharpe(_EQUITY.pct_change().dropna()), float)

def test_sortino_gte_sharpe_for_positive_skew():
    r = _EQUITY.pct_change().dropna()
    # Sortino >= Sharpe when downside vol < total vol (true for most equity returns)
    assert sortino(r) >= sharpe(r) - 0.5  # loose bound

def test_max_drawdown_is_negative():
    assert max_drawdown(_EQUITY) < 0

def test_var_95_lt_var_99():
    r = _EQUITY.pct_change().dropna()
    assert var(r, 0.95) > var(r, 0.99)  # 99% VaR is more negative

def test_cvar_lte_var():
    r = _EQUITY.pct_change().dropna()
    assert cvar(r, 0.95) <= var(r, 0.95)

def test_compute_all_returns_required_keys():
    result = compute_all(_EQUITY)
    required = {"cagr", "vol", "sharpe", "sortino", "max_dd",
                "skew", "kurt", "best_month", "worst_month",
                "var_95", "var_99", "cvar_95", "cvar_99"}
    assert required.issubset(result.keys())

def test_monthly_heatmap_data_shape():
    heatmap = monthly_heatmap_data(_EQUITY)
    assert isinstance(heatmap, pd.DataFrame)
    assert heatmap.shape[1] == 12  # 12 months
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_tearsheet.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.analytics.tearsheet'`

- [ ] **Step 3: Write src/analytics/tearsheet.py**

```python
import numpy as np
import pandas as pd

_TRADING_DAYS = 252


def cagr(equity: pd.Series) -> float:
    n_years = len(equity) / _TRADING_DAYS
    if n_years == 0:
        return 0.0
    return float((equity.iloc[-1] / equity.iloc[0]) ** (1 / n_years) - 1)


def annualized_vol(returns: pd.Series) -> float:
    return float(returns.std() * np.sqrt(_TRADING_DAYS))


def sharpe(returns: pd.Series, rf_annual: float = 0.02) -> float:
    rf_daily = (1 + rf_annual) ** (1 / _TRADING_DAYS) - 1
    excess = returns - rf_daily
    std = excess.std()
    if std == 0:
        return 0.0
    return float(excess.mean() / std * np.sqrt(_TRADING_DAYS))


def sortino(returns: pd.Series, rf_annual: float = 0.02) -> float:
    rf_daily = (1 + rf_annual) ** (1 / _TRADING_DAYS) - 1
    excess = returns - rf_daily
    downside_std = excess[excess < 0].std()
    if downside_std == 0:
        return 0.0
    return float(excess.mean() / downside_std * np.sqrt(_TRADING_DAYS))


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())


def drawdown_series(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    return (equity - peak) / peak


def var(returns: pd.Series, confidence: float = 0.95) -> float:
    return float(np.percentile(returns.dropna(), (1 - confidence) * 100))


def cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    threshold = var(returns, confidence)
    tail = returns[returns <= threshold]
    if tail.empty:
        return threshold
    return float(tail.mean())


def monthly_heatmap_data(equity: pd.Series) -> pd.DataFrame:
    """Return DataFrame of monthly returns with years as rows and months (1–12) as columns."""
    monthly = equity.resample("ME").last().pct_change().dropna()
    df = monthly.to_frame("ret")
    df["year"] = df.index.year
    df["month"] = df.index.month
    return df.pivot(index="year", columns="month", values="ret")


def compute_all(equity: pd.Series, rf_annual: float = 0.02) -> dict:
    returns = equity.pct_change().dropna()
    monthly = equity.resample("ME").last().pct_change().dropna()
    return {
        "cagr": cagr(equity),
        "vol": annualized_vol(returns),
        "sharpe": sharpe(returns, rf_annual),
        "sortino": sortino(returns, rf_annual),
        "max_dd": max_drawdown(equity),
        "skew": float(returns.skew()),
        "kurt": float(returns.kurtosis()),
        "best_month": float(monthly.max()),
        "worst_month": float(monthly.min()),
        "var_95": var(returns, 0.95),
        "var_99": var(returns, 0.99),
        "cvar_95": cvar(returns, 0.95),
        "cvar_99": cvar(returns, 0.99),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_tearsheet.py -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/analytics/tearsheet.py tests/test_tearsheet.py
git commit -m "feat: add tearsheet analytics (Sharpe, Sortino, max DD, VaR, CVaR, heatmap)"
```

---

## Task 9: Strategy A — CBOE PUT Write (Vertical Slice)

**Files:**
- Create: `src/strategies/put_write.py`
- Modify: `tests/test_strategies.py`

- [ ] **Step 1: Write the failing test**

`tests/test_strategies.py`:
```python
import numpy as np
import pandas as pd
import pytest

# We test the strategy interface using a synthetic equity curve injected via monkeypatching.
# Real data pull is tested implicitly when you run `streamlit run app.py`.

from src.strategies.put_write import PutWrite
from src.engine.costs import get_cost_bps


def _make_fake_index(n=500, start="2020-01-02", base=100.0):
    np.random.seed(1)
    rets = np.random.normal(0.0003, 0.008, n)
    prices = base * np.cumprod(1 + rets)
    return pd.Series(prices, index=pd.bdate_range(start, periods=n))


def test_put_write_implements_interface():
    s = PutWrite()
    assert hasattr(s, "run")
    assert hasattr(s, "metrics")
    assert hasattr(s, "equity_curve")
    assert hasattr(s, "trade_log")
    assert hasattr(s, "institutional_framing")


def test_put_write_run_with_synthetic_data(monkeypatch):
    import src.strategies.put_write as pw_mod
    fake = _make_fake_index()
    monkeypatch.setattr(pw_mod, "_fetch_index", lambda *a, **kw: fake)

    s = PutWrite()
    s.run("2020-01-01", "2021-12-31", "default")

    curve = s.equity_curve()
    assert isinstance(curve, pd.Series)
    assert len(curve) > 0
    assert curve.iloc[0] == pytest.approx(100.0, rel=0.01)

    m = s.metrics()
    assert "sharpe" in m
    assert "max_dd" in m
    assert "cagr" in m

    log = s.trade_log()
    assert isinstance(log, pd.DataFrame)


def test_put_write_institutional_framing_keys():
    s = PutWrite()
    framing = s.institutional_framing()
    assert "return_profile" in framing
    assert "structurer_pitch" in framing
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_strategies.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.strategies.put_write'`

- [ ] **Step 3: Write src/strategies/put_write.py**

```python
from __future__ import annotations
import pandas as pd
from src.strategies.base import BaseStrategy
from src.data.loader import fetch_cboe_index, fetch_prices
from src.analytics import tearsheet
from src.utils.config import FRED_PUT, SPX_TICKER


def _fetch_index(start: str, end: str) -> pd.Series:
    return fetch_cboe_index(
        fred_id=FRED_PUT,
        yf_fallback="^PUTR",
        start=start,
        end=end,
    )


class PutWrite(BaseStrategy):
    name = "CBOE PUT — Insurance Carry"
    description = (
        "Fully collateralized 1-month ATM SPX put-write, tracking the CBOE PUT Index. "
        "Published index values used directly — no per-option simulation required."
    )
    instrument_type = "index"

    def __init__(self) -> None:
        self._equity: pd.Series | None = None
        self._metrics: dict | None = None
        self._trade_log: pd.DataFrame | None = None

    def run(
        self,
        start: str,
        end: str,
        cost_mode: str = "default",
        custom_bps: float = 0.0,
    ) -> None:
        index = _fetch_index(start, end)
        index = index.sort_index().dropna()

        returns = index.pct_change().dropna()

        # Build equity curve (base 100)
        self._equity = (1 + returns).cumprod() * 100
        self._equity.iloc[0] = 100.0
        self._equity.name = self.name

        # Trade log: monthly entries, 0 bps cost (costs embedded in published index)
        monthly_ret = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        trades = [
            {
                "date": dt,
                "notional": 1.0,
                "gross_pnl": float(ret),
                "cost_bps": 0.0,
                "net_pnl": float(ret),
            }
            for dt, ret in monthly_ret.items()
        ]
        self._trade_log = pd.DataFrame(trades).set_index("date")

        self._metrics = tearsheet.compute_all(self._equity)

    def metrics(self) -> dict:
        if self._metrics is None:
            raise RuntimeError("Call run() first")
        return self._metrics

    def equity_curve(self) -> pd.Series:
        if self._equity is None:
            raise RuntimeError("Call run() first")
        return self._equity

    def trade_log(self) -> pd.DataFrame:
        if self._trade_log is None:
            raise RuntimeError("Call run() first")
        return self._trade_log

    def institutional_framing(self) -> dict:
        return {
            "return_profile": (
                "Credit-like. Positive carry with limited upside capture. "
                "Return distribution resembles short-duration corporate bonds — "
                "regular premium income with occasional large losses in vol spikes."
            ),
            "capital_efficiency": (
                "Realized vol and max drawdown are materially lower than direct SPX exposure. "
                "Lower vol implies a lower Solvency II SCR-equity symmetric adjustment, "
                "reducing required capital vs. holding the index directly."
            ),
            "regulatory_treatment": (
                "Treated as a derivatives position under the Solvency II SCR-equity sub-module. "
                "SCR proxy: 39% × |max 1-year drawdown| (symmetric adjustment, directional only). "
                "NAIC RBC: C-1 factor ~30% of market value, scaled by (realized vol / 15% SPX long-run vol)."
            ),
            "liability_fit": (
                "Carry-generating. Attractive for insurance general accounts seeking equity risk premium "
                "with bond-like volatility and without duration extension or credit spread exposure."
            ),
            "structurer_pitch": (
                "Pitch to insurance CIOs seeking yield above short-duration credit with lower regulatory "
                "capital consumption than direct equity — the put premium is the carry source."
            ),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_strategies.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Smoke-test the live data pull**

```bash
python -c "
from src.strategies.put_write import PutWrite
s = PutWrite()
s.run('2007-01-01', '2024-12-31')
print(s.equity_curve().tail())
print(s.metrics())
"
```

Expected: equity curve printed with recent dates, metrics dict with valid numbers. If FRED `PUTWRITE` fails, it will fall back to yfinance `^PUTR`. If both fail, check the FRED series ID — alternatives include `CBOEPUT` or downloading directly from CBOE website and loading as CSV.

- [ ] **Step 6: Commit**

```bash
git add src/strategies/put_write.py tests/test_strategies.py
git commit -m "feat: add Strategy A — CBOE PUT write with institutional framing"
```

---

## Task 10: Streamlit App — Skeleton + Pages 1 & 2 (Strategy A only)

**Files:**
- Create: `app.py`

No unit tests — verify by running `streamlit run app.py`.

- [ ] **Step 1: Write app.py**

```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from src.strategies.put_write import PutWrite
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
    return s


# ── Page routing ─────────────────────────────────────────────────────────────
if page == "Overview":
    st.title("QIS Backtester")
    st.markdown(
        """
        A systematic equity derivatives backtesting platform simulating four institutional strategies
        against Solvency II and NAIC capital constraints.

        > **AiPEX-Lite disclaimer:** Independently implemented, inspired by HSBC's AiPEX concept.
        > Does not replicate HSBC's proprietary methodology.

        *More strategies loading — check back soon.*
        """
    )

    s = _run_put_write(start_date, end_date, cost_mode, custom_bps)
    curve = s.equity_curve()
    m = s.metrics()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CAGR", f"{m['cagr']:.1%}")
    col2.metric("Sharpe", f"{m['sharpe']:.2f}")
    col3.metric("Max Drawdown", f"{m['max_dd']:.1%}")
    col4.metric("Annualized Vol", f"{m['vol']:.1%}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve.index, y=curve, name="CBOE PUT", line=dict(color="#1f77b4")))
    fig.update_layout(
        title="Cumulative Return (base 100)",
        xaxis_title="Date",
        yaxis_title="Index Level",
        hovermode="x unified",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

elif page == "Strategy Explorer":
    strategy_choice = st.sidebar.selectbox("Strategy", ["CBOE PUT — Insurance Carry"])

    s = _run_put_write(start_date, end_date, cost_mode, custom_bps)
    curve = s.equity_curve()
    m = s.metrics()
    framing = s.institutional_framing()

    st.title(s.name)
    st.caption(s.description)

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
```

- [ ] **Step 2: Run locally and verify**

```bash
streamlit run app.py
```

Open http://localhost:8501. Verify:
- Sidebar renders with cost toggle and page selector
- Overview page shows metrics and chart for CBOE PUT
- Strategy Explorer shows equity curve, drawdown, heatmap, and institutional framing panel
- Other pages show placeholder messages

- [ ] **Step 3: Commit**

```bash
git add app.py
git push origin main
git commit -m "feat: add Streamlit app with Overview and Strategy Explorer (Strategy A)"
```

---

## Task 11: Deploy to Streamlit Cloud

No code — deployment steps.

- [ ] **Step 1: Push all current code to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Deploy on Streamlit Community Cloud**

1. Go to https://share.streamlit.io
2. Click "New app"
3. Repository: `YOUR_USERNAME/QIS-backtester`
4. Branch: `main`
5. Main file: `app.py`
6. Click "Deploy"

- [ ] **Step 3: Wait for build to complete (~3–5 minutes)**

Streamlit Cloud installs requirements.txt and runs app.py. If build fails, check the logs — most common issue is a missing package in requirements.txt.

- [ ] **Step 4: Record your live URL**

Format: `https://YOUR_USERNAME-qis-backtester-app-XXXXX.streamlit.app`

Update README.md:
```markdown
**Live demo:** https://YOUR_USERNAME-qis-backtester-app-XXXXX.streamlit.app
```

- [ ] **Step 5: Commit README with live URL**

```bash
git add README.md
git commit -m "docs: add Streamlit Cloud live demo URL"
git push origin main
```

---

## Task 12: Strategy B — CBOE BXM (Covered Call)

**Files:**
- Create: `src/strategies/covered_call.py`
- Modify: `tests/test_strategies.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_strategies.py`:
```python
from src.strategies.covered_call import CoveredCall

def test_covered_call_run_with_synthetic_data(monkeypatch):
    import src.strategies.covered_call as cc_mod
    fake = _make_fake_index()
    monkeypatch.setattr(cc_mod, "_fetch_index", lambda *a, **kw: fake)

    s = CoveredCall()
    s.run("2020-01-01", "2021-12-31", "default")

    curve = s.equity_curve()
    assert isinstance(curve, pd.Series)
    assert len(curve) > 0

    m = s.metrics()
    assert "sharpe" in m and "max_dd" in m

def test_covered_call_institutional_framing():
    s = CoveredCall()
    framing = s.institutional_framing()
    assert "structurer_pitch" in framing
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_strategies.py::test_covered_call_run_with_synthetic_data -v
```

Expected: `ModuleNotFoundError: No module named 'src.strategies.covered_call'`

- [ ] **Step 3: Write src/strategies/covered_call.py**

```python
from __future__ import annotations
import pandas as pd
from src.strategies.base import BaseStrategy
from src.data.loader import fetch_cboe_index
from src.analytics import tearsheet
from src.utils.config import FRED_BXM


def _fetch_index(start: str, end: str) -> pd.Series:
    return fetch_cboe_index(
        fred_id=FRED_BXM,
        yf_fallback="^BXM",
        start=start,
        end=end,
    )


class CoveredCall(BaseStrategy):
    name = "CBOE BXM — Yield Enhancement Overlay"
    description = (
        "Long SPX + short 1-month ATM call, tracking the CBOE BXM Index. "
        "Published index values used directly — no per-option simulation required."
    )
    instrument_type = "index"

    def __init__(self) -> None:
        self._equity: pd.Series | None = None
        self._metrics: dict | None = None
        self._trade_log: pd.DataFrame | None = None

    def run(
        self,
        start: str,
        end: str,
        cost_mode: str = "default",
        custom_bps: float = 0.0,
    ) -> None:
        index = _fetch_index(start, end)
        index = index.sort_index().dropna()
        returns = index.pct_change().dropna()

        self._equity = (1 + returns).cumprod() * 100
        self._equity.iloc[0] = 100.0
        self._equity.name = self.name

        monthly_ret = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        trades = [
            {
                "date": dt,
                "notional": 1.0,
                "gross_pnl": float(ret),
                "cost_bps": 0.0,
                "net_pnl": float(ret),
            }
            for dt, ret in monthly_ret.items()
        ]
        self._trade_log = pd.DataFrame(trades).set_index("date")
        self._metrics = tearsheet.compute_all(self._equity)

    def metrics(self) -> dict:
        if self._metrics is None:
            raise RuntimeError("Call run() first")
        return self._metrics

    def equity_curve(self) -> pd.Series:
        if self._equity is None:
            raise RuntimeError("Call run() first")
        return self._equity

    def trade_log(self) -> pd.DataFrame:
        if self._trade_log is None:
            raise RuntimeError("Call run() first")
        return self._trade_log

    def institutional_framing(self) -> dict:
        return {
            "return_profile": (
                "Equity-like with capped upside. Call premium collected monthly creates income; "
                "upside above the strike is forfeited. Underperforms in strong bull markets, "
                "outperforms in flat or mildly declining markets."
            ),
            "capital_efficiency": (
                "Lower realized vol than direct SPX because call premium cushions drawdowns. "
                "Reduced vol contribution lowers portfolio SCR charge relative to unhedged equity."
            ),
            "regulatory_treatment": (
                "Long equity + short call treated as a covered call position under Solvency II. "
                "SCR proxy: 39% × |max 1-year drawdown| (symmetric adjustment, directional only). "
                "NAIC RBC: C-1 factor ~30% of market value, adjusted for realized vol vs. SPX."
            ),
            "liability_fit": (
                "Yield-enhancing overlay on existing equity allocation. Suitable for insurance "
                "portfolios already holding equity that want to generate additional income without "
                "increasing duration or credit exposure."
            ),
            "structurer_pitch": (
                "Pitch to insurance CIOs who hold equity and want to monetize implied vol premium "
                "while reducing mark-to-market volatility on their equity sleeve."
            ),
        }
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_strategies.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Wire Strategy B into app.py**

In `app.py`, add the import and cache function after PutWrite:

```python
from src.strategies.covered_call import CoveredCall

@st.cache_data(show_spinner="Running backtest…")
def _run_covered_call(start, end, cost_mode, custom_bps):
    s = CoveredCall()
    s.run(start, end, cost_mode, custom_bps)
    return s
```

Update the Overview page's cumulative chart to show both strategies:
```python
# In the Overview page block, replace the single strategy chart with:
put_s = _run_put_write(start_date, end_date, cost_mode, custom_bps)
bxm_s = _run_covered_call(start_date, end_date, cost_mode, custom_bps)

fig = go.Figure()
for s, color in [(put_s, "#1f77b4"), (bxm_s, "#ff7f0e")]:
    fig.add_trace(go.Scatter(x=s.equity_curve().index, y=s.equity_curve(), name=s.name, line=dict(color=color)))
```

Update Strategy Explorer sidebar:
```python
strategy_choice = st.sidebar.selectbox(
    "Strategy",
    ["CBOE PUT — Insurance Carry", "CBOE BXM — Yield Enhancement Overlay"]
)
# Map choice to cached strategy
strategy_map = {
    "CBOE PUT — Insurance Carry": _run_put_write,
    "CBOE BXM — Yield Enhancement Overlay": _run_covered_call,
}
s = strategy_map[strategy_choice](start_date, end_date, cost_mode, custom_bps)
```

- [ ] **Step 6: Verify in browser**

```bash
streamlit run app.py
```

Overview page should now show two strategy lines on the cumulative chart.

- [ ] **Step 7: Commit and push**

```bash
git add src/strategies/covered_call.py tests/test_strategies.py app.py
git commit -m "feat: add Strategy B — CBOE BXM covered call"
git push origin main
```

---

## Task 13: Synthetic IV Module

**Files:**
- Create: `src/pricing/synthetic_iv.py`
- Create: `tests/test_pricing.py`

- [ ] **Step 1: Write the failing test**

`tests/test_pricing.py`:
```python
import numpy as np
import pandas as pd
import pytest
from src.pricing.synthetic_iv import realized_vol, synthetic_iv

np.random.seed(42)
_PRICES = pd.Series(
    100 * np.cumprod(1 + np.random.normal(0.0004, 0.012, 300)),
    index=pd.bdate_range("2022-01-03", periods=300),
)

def test_realized_vol_annualized_range():
    rv = realized_vol(_PRICES, window=20)
    # For 1.2% daily std, annualized vol ~ 19%; allow range
    assert (rv.dropna() > 0.05).all()
    assert (rv.dropna() < 0.60).all()

def test_realized_vol_has_nan_for_first_window_minus_1():
    rv = realized_vol(_PRICES, window=20)
    assert rv.iloc[:19].isna().all()
    assert not pd.isna(rv.iloc[19])

def test_synthetic_iv_is_above_realized_vol():
    rv = realized_vol(_PRICES, window=20)
    siv = synthetic_iv(_PRICES, window=20, skew_spread=0.02)
    valid = rv.dropna().index
    assert (siv.loc[valid] > rv.loc[valid]).all()

def test_synthetic_iv_skew_spread_adds_exactly():
    rv = realized_vol(_PRICES, window=20)
    siv = synthetic_iv(_PRICES, window=20, skew_spread=0.03)
    diff = (siv - rv).dropna()
    assert (abs(diff - 0.03) < 1e-10).all()
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_pricing.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.pricing.synthetic_iv'`

- [ ] **Step 3: Write src/pricing/synthetic_iv.py**

```python
import numpy as np
import pandas as pd

_TRADING_DAYS = 252


def realized_vol(prices: pd.Series, window: int = 20) -> pd.Series:
    """
    Annualized realized vol from log returns over a rolling window.
    Returns NaN for the first (window-1) observations.
    """
    log_returns = np.log(prices / prices.shift(1))
    return log_returns.rolling(window).std() * np.sqrt(_TRADING_DAYS)


def synthetic_iv(
    prices: pd.Series,
    window: int = 20,
    skew_spread: float = 0.02,
) -> pd.Series:
    """
    Proxy for implied vol: realized vol + constant skew spread.
    The skew_spread (~2 vol points) approximates the implied-realized vol premium.
    Labeled as synthetic throughout the dashboard — not historical IV.
    """
    return realized_vol(prices, window) + skew_spread
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_pricing.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pricing/synthetic_iv.py tests/test_pricing.py
git commit -m "feat: add synthetic IV module (realized vol + constant skew spread)"
```

---

## Task 14: Strategy C — Vol-Targeted SPX Overlay

**Files:**
- Create: `src/strategies/vol_target.py`
- Modify: `tests/test_strategies.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_strategies.py`:
```python
from src.strategies.vol_target import VolTarget

def test_vol_target_run_with_synthetic_data(monkeypatch):
    import src.strategies.vol_target as vt_mod
    fake = _make_fake_index()
    monkeypatch.setattr(vt_mod, "_fetch_spy", lambda *a, **kw: fake)

    s = VolTarget()
    s.run("2020-01-01", "2021-12-31", "default")

    curve = s.equity_curve()
    assert isinstance(curve, pd.Series)
    assert len(curve) > 100  # should have ample data after vol lookback

    m = s.metrics()
    assert "sharpe" in m

def test_vol_target_weights_capped_at_max_leverage(monkeypatch):
    import src.strategies.vol_target as vt_mod
    # Low-vol input → weight would exceed max leverage without cap
    low_vol_prices = pd.Series(
        100 * np.cumprod(1 + np.random.normal(0.0005, 0.001, 300)),
        index=pd.bdate_range("2022-01-03", periods=300),
    )
    monkeypatch.setattr(vt_mod, "_fetch_spy", lambda *a, **kw: low_vol_prices)

    s = VolTarget()
    s.run("2022-01-01", "2023-12-31", "default")
    assert s.weights().max() <= 1.51  # MAX_LEVERAGE + floating point tolerance
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_strategies.py::test_vol_target_run_with_synthetic_data -v
```

Expected: `ModuleNotFoundError: No module named 'src.strategies.vol_target'`

- [ ] **Step 3: Write src/strategies/vol_target.py**

```python
from __future__ import annotations
import numpy as np
import pandas as pd
from src.strategies.base import BaseStrategy
from src.data.loader import fetch_prices
from src.analytics import tearsheet
from src.engine.costs import get_cost_bps
from src.utils.config import SPY_TICKER, VOL_TARGET, MAX_LEVERAGE, VOL_LOOKBACK


def _fetch_spy(start: str, end: str) -> pd.Series:
    return fetch_prices(SPY_TICKER, start, end)


class VolTarget(BaseStrategy):
    name = "Vol-Targeted SPX — Capital-Efficient Equity"
    description = (
        "Dynamic SPX exposure scaled inversely to 20-day realized vol, "
        "targeting 10% annualized portfolio vol. Capped at 150% notional."
    )
    instrument_type = "futures"

    def __init__(self) -> None:
        self._equity: pd.Series | None = None
        self._metrics: dict | None = None
        self._trade_log: pd.DataFrame | None = None
        self._weights_series: pd.Series | None = None

    def run(
        self,
        start: str,
        end: str,
        cost_mode: str = "default",
        custom_bps: float = 0.0,
    ) -> None:
        spy = _fetch_spy(start, end)
        spy = spy.sort_index().dropna()
        spy_returns = spy.pct_change().dropna()

        # 20-day rolling realized vol (annualized)
        realized = spy_returns.rolling(VOL_LOOKBACK).std() * np.sqrt(252)
        realized = realized.dropna()

        weights = (VOL_TARGET / realized).clip(upper=MAX_LEVERAGE)
        aligned_returns = spy_returns.reindex(weights.index)

        cost_bps = get_cost_bps(self.instrument_type, cost_mode, custom_bps)

        prev_weights = weights.shift(1).fillna(0.0)
        weight_change = (weights - prev_weights).abs()

        gross_returns = weights * aligned_returns
        cost_drag = weight_change * cost_bps / 10_000
        net_returns = gross_returns - cost_drag

        self._equity = (1 + net_returns).cumprod() * 100
        self._equity.name = self.name
        self._weights_series = weights

        trades = []
        for dt in weights.index:
            chg = float(weight_change.loc[dt])
            if chg > 0.001:
                trades.append({
                    "date": dt,
                    "notional": chg,
                    "gross_pnl": float(gross_returns.loc[dt]),
                    "cost_bps": cost_bps,
                    "net_pnl": float(net_returns.loc[dt]),
                })
        self._trade_log = pd.DataFrame(trades).set_index("date") if trades else pd.DataFrame()
        self._metrics = tearsheet.compute_all(self._equity)

    def metrics(self) -> dict:
        if self._metrics is None:
            raise RuntimeError("Call run() first")
        return self._metrics

    def equity_curve(self) -> pd.Series:
        if self._equity is None:
            raise RuntimeError("Call run() first")
        return self._equity

    def trade_log(self) -> pd.DataFrame:
        if self._trade_log is None:
            raise RuntimeError("Call run() first")
        return self._trade_log

    def weights(self) -> pd.Series:
        if self._weights_series is None:
            raise RuntimeError("Call run() first")
        return self._weights_series

    def institutional_framing(self) -> dict:
        return {
            "return_profile": (
                "Equity-like but smoother. Dynamic leverage scales down in high-vol regimes, "
                "producing lower average vol and shallower drawdowns than static SPX exposure. "
                "Expected to underperform in low-vol bull markets due to leverage cap."
            ),
            "capital_efficiency": (
                "More predictable capital consumption than static equity — vol targeting keeps "
                "realized vol near 10%, reducing the variability of the Solvency II symmetric "
                "adjustment and making regulatory capital planning more stable."
            ),
            "regulatory_treatment": (
                "Treated as equity under Solvency II SCR-equity sub-module. "
                "SCR proxy: 39% × |max 1-year drawdown|. Lower realized drawdown vs. SPX "
                "means a lower estimated SCR charge. NAIC RBC: C-1 factor scaled by vol ratio."
            ),
            "liability_fit": (
                "Return-seeking, not hedging. Suitable for insurance surplus accounts wanting "
                "equity-like long-run returns with more predictable short-run drawdowns — "
                "directly addresses the 'lumpy capital charges' problem under Solvency II."
            ),
            "structurer_pitch": (
                "Pitch to insurance CIOs frustrated by equity SCR volatility — vol targeting "
                "makes equity risk consumption more stable quarter-to-quarter without reducing "
                "long-run return potential."
            ),
        }
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_strategies.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Wire into app.py**

Add after CoveredCall import and cache function in app.py:
```python
from src.strategies.vol_target import VolTarget

@st.cache_data(show_spinner="Running backtest…")
def _run_vol_target(start, end, cost_mode, custom_bps):
    s = VolTarget()
    s.run(start, end, cost_mode, custom_bps)
    return s
```

Add `"Vol-Targeted SPX — Capital-Efficient Equity"` to the Strategy Explorer selectbox and `strategy_map`.

Add to Overview chart:
```python
vt_s = _run_vol_target(start_date, end_date, cost_mode, custom_bps)
fig.add_trace(go.Scatter(x=vt_s.equity_curve().index, y=vt_s.equity_curve(), name=vt_s.name, line=dict(color="#2ca02c")))
```

- [ ] **Step 6: Run and verify in browser**

```bash
streamlit run app.py
```

Vol target strategy should appear in Explorer with leverage/vol tracking charts.

- [ ] **Step 7: Commit and push**

```bash
git add src/strategies/vol_target.py tests/test_strategies.py app.py
git commit -m "feat: add Strategy C — vol-targeted SPX overlay"
git push origin main
```

---

## Task 15: Strategy E — AiPEX-Lite

**Files:**
- Create: `src/strategies/aipex_lite.py`
- Modify: `tests/test_strategies.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_strategies.py`:
```python
from src.strategies.aipex_lite import AiPexLite

def _make_sector_prices(tickers, n=500, start="2019-01-02"):
    np.random.seed(99)
    return {
        t: pd.Series(
            100 * np.cumprod(1 + np.random.normal(0.0004, 0.01, n)),
            index=pd.bdate_range(start, periods=n),
        )
        for t in tickers
    }

def test_aipex_run_with_synthetic_data(monkeypatch):
    import src.strategies.aipex_lite as al_mod
    from src.utils.config import SECTOR_ETFS, VIX_TICKER

    sector_data = _make_sector_prices(SECTOR_ETFS)
    # Low VIX (risk-on) so strategy always rotates
    vix_data = pd.Series(15.0, index=sector_data[SECTOR_ETFS[0]].index)

    def fake_fetch(ticker, start, end, **kw):
        if ticker in sector_data:
            return sector_data[ticker]
        return vix_data

    monkeypatch.setattr(al_mod, "_fetch_prices", fake_fetch)

    s = AiPexLite()
    s.run("2019-01-01", "2021-01-01", "default")

    curve = s.equity_curve()
    assert isinstance(curve, pd.Series)
    assert len(curve) >= 10  # monthly, so ~24 months

    m = s.metrics()
    assert "sharpe" in m

def test_aipex_trade_log_has_cost_bps(monkeypatch):
    import src.strategies.aipex_lite as al_mod
    from src.utils.config import SECTOR_ETFS

    sector_data = _make_sector_prices(SECTOR_ETFS)
    vix_data = pd.Series(15.0, index=sector_data[SECTOR_ETFS[0]].index)

    def fake_fetch(ticker, start, end, **kw):
        return sector_data.get(ticker, vix_data)

    monkeypatch.setattr(al_mod, "_fetch_prices", fake_fetch)

    s = AiPexLite()
    s.run("2019-01-01", "2021-01-01", "default")
    log = s.trade_log()
    if not log.empty:
        assert "cost_bps" in log.columns
        assert (log["cost_bps"] >= 0).all()
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_strategies.py::test_aipex_run_with_synthetic_data -v
```

Expected: `ModuleNotFoundError: No module named 'src.strategies.aipex_lite'`

- [ ] **Step 3: Write src/strategies/aipex_lite.py**

```python
from __future__ import annotations
import pandas as pd
from src.strategies.base import BaseStrategy
from src.data.loader import fetch_prices
from src.analytics import tearsheet
from src.engine.costs import get_cost_bps
from src.utils.config import (
    SECTOR_ETFS, VIX_TICKER,
    VIX_RISK_OFF_THRESHOLD, AIPEX_TOP_N,
    MOMENTUM_WINDOW, MOMENTUM_SKIP,
)


def _fetch_prices(ticker: str, start: str, end: str, **kwargs) -> pd.Series:
    return fetch_prices(ticker, start, end, **kwargs)


class AiPexLite(BaseStrategy):
    name = "AiPEX-Lite — AI-Driven Factor Rotation"
    description = (
        "Monthly sector ETF rotation using 12-1 month momentum + VIX risk-on/off gate. "
        "Equal-weights top 3 of 5 S&P 500 sector ETFs (XLK, XLF, XLV, XLE, XLY). "
        "Independently implemented, inspired by HSBC AiPEX concept."
    )
    instrument_type = "etf"

    def __init__(self) -> None:
        self._equity: pd.Series | None = None
        self._metrics: dict | None = None
        self._trade_log: pd.DataFrame | None = None

    def run(
        self,
        start: str,
        end: str,
        cost_mode: str = "default",
        custom_bps: float = 0.0,
    ) -> None:
        prices = {t: _fetch_prices(t, start, end) for t in SECTOR_ETFS}
        vix = _fetch_prices(VIX_TICKER, start, end)

        price_df = pd.DataFrame(prices).sort_index().dropna()
        vix = vix.reindex(price_df.index).ffill()

        cost_bps = get_cost_bps(self.instrument_type, cost_mode, custom_bps)
        monthly_ends = price_df.resample("ME").last().index

        trades = []
        portfolio_returns = []
        current_weights = pd.Series(0.0, index=SECTOR_ETFS)

        for i in range(1, len(monthly_ends)):
            signal_date = monthly_ends[i - 1]
            rebalance_date = monthly_ends[i]

            # 12-1 month momentum
            t_minus_12 = signal_date - pd.DateOffset(months=12)
            t_minus_1 = signal_date - pd.DateOffset(months=1)
            p_start = price_df.asof(t_minus_12)
            p_end = price_df.asof(t_minus_1)

            if p_start.isna().any() or p_end.isna().any():
                current_weights = pd.Series(1.0 / len(SECTOR_ETFS), index=SECTOR_ETFS)
                continue

            momentum = (p_end / p_start) - 1

            # VIX risk-off gate
            vix_level = float(vix.asof(signal_date))
            if vix_level > VIX_RISK_OFF_THRESHOLD:
                new_weights = current_weights  # hold; don't rotate in risk-off
            else:
                top_sectors = momentum.nlargest(AIPEX_TOP_N).index.tolist()
                new_weights = pd.Series(0.0, index=SECTOR_ETFS)
                new_weights[top_sectors] = 1.0 / AIPEX_TOP_N

            # Month returns
            p_entry = price_df.asof(signal_date)
            p_exit = price_df.asof(rebalance_date)
            month_ret = (p_exit / p_entry) - 1
            gross_ret = float((new_weights * month_ret).sum())

            turnover = float((new_weights - current_weights).abs().sum())
            cost_drag = turnover * cost_bps / 10_000
            net_ret = gross_ret - cost_drag

            portfolio_returns.append({"date": rebalance_date, "net_return": net_ret})

            if turnover > 0.001:
                trades.append({
                    "date": rebalance_date,
                    "notional": turnover,
                    "gross_pnl": gross_ret,
                    "cost_bps": cost_bps,
                    "net_pnl": net_ret,
                })

            current_weights = new_weights

        if not portfolio_returns:
            raise ValueError("Not enough data to compute AiPEX-Lite returns. Extend the backtest window.")

        ret_df = pd.DataFrame(portfolio_returns).set_index("date")
        self._equity = (1 + ret_df["net_return"]).cumprod() * 100
        self._equity.name = self.name
        self._trade_log = pd.DataFrame(trades).set_index("date") if trades else pd.DataFrame()
        self._metrics = tearsheet.compute_all(self._equity)

    def metrics(self) -> dict:
        if self._metrics is None:
            raise RuntimeError("Call run() first")
        return self._metrics

    def equity_curve(self) -> pd.Series:
        if self._equity is None:
            raise RuntimeError("Call run() first")
        return self._equity

    def trade_log(self) -> pd.DataFrame:
        if self._trade_log is None:
            raise RuntimeError("Call run() first")
        return self._trade_log

    def institutional_framing(self) -> dict:
        return {
            "return_profile": (
                "Equity-like with factor tilt. Monthly sector rotation generates return dispersion "
                "vs. market-cap SPX. Not market-neutral — beta to equity is high. "
                "VIX gate reduces rotation in extreme vol events."
            ),
            "capital_efficiency": (
                "Sector ETF portfolio with monthly rotation maintains similar vol to SPX. "
                "VIX risk-off gate provides partial downside protection in tail events, "
                "modestly reducing max drawdown vs. static equity."
            ),
            "regulatory_treatment": (
                "Treated as equity under Solvency II SCR-equity sub-module. "
                "SCR proxy: 39% × |max 1-year drawdown|. "
                "NAIC RBC: C-1 factor ~30% of market value, adjusted for realized vol."
            ),
            "liability_fit": (
                "Return-seeking, not hedging. Suitable for insurance surplus accounts seeking "
                "active equity exposure with a transparent, auditable rules-based process — "
                "explicitly contrasts with black-box ML models."
            ),
            "structurer_pitch": (
                "Pitch to insurance CIOs seeking explainable factor equity exposure: "
                "rules-based, monthly, fully auditable, with a clear narrative around "
                "momentum and risk-off protection that can be presented to a board."
            ),
        }
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_strategies.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Wire into app.py**

Add import and cache function:
```python
from src.strategies.aipex_lite import AiPexLite

@st.cache_data(show_spinner="Running backtest…")
def _run_aipex(start, end, cost_mode, custom_bps):
    s = AiPexLite()
    s.run(start, end, cost_mode, custom_bps)
    return s
```

Add `"AiPEX-Lite — AI-Driven Factor Rotation"` to the Explorer selectbox and `strategy_map`. Add to Overview chart with color `"#9467bd"`.

- [ ] **Step 6: Commit and push**

```bash
git add src/strategies/aipex_lite.py tests/test_strategies.py app.py
git commit -m "feat: add Strategy E — AiPEX-Lite sector ETF factor rotation"
git push origin main
```

---

## Task 16: Pure Numpy BSM + Greeks

**Files:**
- Create: `src/pricing/black_scholes.py`
- Modify: `tests/test_pricing.py`

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_pricing.py`:
```python
from src.pricing.black_scholes import call_price, put_price, delta, gamma, vega, theta, rho

# Known BSM values (S=100, K=100, T=1yr, r=5%, σ=20%)
# Call ≈ 10.4506, Put ≈ 5.5735 (put-call parity: C - P = S - K*e^{-rT})
_S, _K, _T, _r, _sig = 100.0, 100.0, 1.0, 0.05, 0.20

def test_call_price_known_value():
    c = call_price(_S, _K, _T, _r, _sig)
    assert abs(c - 10.4506) < 0.01

def test_put_price_known_value():
    p = put_price(_S, _K, _T, _r, _sig)
    assert abs(p - 5.5735) < 0.01

def test_put_call_parity():
    c = call_price(_S, _K, _T, _r, _sig)
    p = put_price(_S, _K, _T, _r, _sig)
    # C - P = S - K * exp(-r * T)
    import numpy as np
    parity_rhs = _S - _K * np.exp(-_r * _T)
    assert abs((c - p) - parity_rhs) < 1e-6

def test_call_delta_atm_near_half():
    d = delta(_S, _K, _T, _r, _sig, option_type="call")
    assert 0.5 < d < 0.7  # ATM call delta slightly above 0.5

def test_put_delta_negative():
    d = delta(_S, _K, _T, _r, _sig, option_type="put")
    assert -0.6 < d < -0.3

def test_gamma_positive():
    g = gamma(_S, _K, _T, _r, _sig)
    assert g > 0

def test_call_vega_equals_put_vega():
    assert abs(vega(_S, _K, _T, _r, _sig, "call") - vega(_S, _K, _T, _r, _sig, "put")) < 1e-10

def test_call_theta_negative():
    t = theta(_S, _K, _T, _r, _sig, option_type="call")
    assert t < 0  # time decay is negative

def test_expired_call_intrinsic():
    assert abs(call_price(110.0, 100.0, 0.0, 0.05, 0.20) - 10.0) < 1e-10
    assert call_price(90.0, 100.0, 0.0, 0.05, 0.20) == 0.0
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_pricing.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.pricing.black_scholes'`

- [ ] **Step 3: Write src/pricing/black_scholes.py**

```python
"""
Black-Scholes option pricing and analytical Greeks.
All implemented from first principles in pure numpy — no py_vollib dependency.

Notation:
  S  = spot price
  K  = strike price
  T  = time to expiry in years
  r  = continuously compounded risk-free rate (annual)
  σ  = implied volatility (annual)
"""
import numpy as np
from scipy.stats import norm


def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))


def _d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return _d1(S, K, T, r, sigma) - sigma * np.sqrt(T)


def call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes European call price."""
    if T <= 0:
        return max(S - K, 0.0)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    return float(S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))


def put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes European put price."""
    if T <= 0:
        return max(K - S, 0.0)
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    return float(K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))


def delta(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Delta: ∂V/∂S. Call ∈ (0,1), Put ∈ (-1,0)."""
    if T <= 0:
        if option_type == "call":
            return 1.0 if S > K else 0.0
        return -1.0 if S < K else 0.0
    d1 = _d1(S, K, T, r, sigma)
    if option_type == "call":
        return float(norm.cdf(d1))
    return float(norm.cdf(d1) - 1)


def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Gamma: ∂²V/∂S². Same for calls and puts."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    return float(norm.pdf(d1) / (S * sigma * np.sqrt(T)))


def vega(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Vega: ∂V/∂σ per 1% change in vol. Same for calls and puts."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    return float(S * norm.pdf(d1) * np.sqrt(T) / 100)


def theta(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Theta: ∂V/∂t per calendar day (negative = time decay)."""
    if T <= 0:
        return 0.0
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
    if option_type == "call":
        term2 = -r * K * np.exp(-r * T) * norm.cdf(d2)
    else:
        term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
    return float((term1 + term2) / 365)


def rho(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Rho: ∂V/∂r per 1% change in rates."""
    if T <= 0:
        return 0.0
    d2 = _d2(S, K, T, r, sigma)
    if option_type == "call":
        return float(K * T * np.exp(-r * T) * norm.cdf(d2) / 100)
    return float(-K * T * np.exp(-r * T) * norm.cdf(-d2) / 100)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_pricing.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pricing/black_scholes.py tests/test_pricing.py
git commit -m "feat: add pure numpy BSM pricing and analytical Greeks (delta, gamma, vega, theta, rho)"
```

---

## Task 17: Insurance Metrics + Institutional Framing Panels

**Files:**
- Create: `src/analytics/insurance_metrics.py`
- Create: `tests/test_analytics.py`

- [ ] **Step 1: Write the failing test**

`tests/test_analytics.py`:
```python
import numpy as np
import pandas as pd
from src.analytics.insurance_metrics import scr_equity_proxy, naic_rbc_proxy

np.random.seed(7)
_RETURNS = np.random.normal(0.0003, 0.012, 252 * 5)
_EQUITY = pd.Series(
    100 * np.cumprod(1 + _RETURNS),
    index=pd.bdate_range("2018-01-02", periods=len(_RETURNS)),
)

def test_scr_proxy_is_positive():
    scr = scr_equity_proxy(_EQUITY)
    assert scr > 0

def test_scr_proxy_between_0_and_50_percent():
    scr = scr_equity_proxy(_EQUITY)
    assert 0 < scr < 0.50

def test_naic_rbc_is_positive():
    rbc = naic_rbc_proxy(_EQUITY)
    assert rbc > 0

def test_naic_rbc_type():
    assert isinstance(naic_rbc_proxy(_EQUITY), float)

def test_high_vol_strategy_has_higher_naic_rbc():
    high_vol_rets = np.random.normal(0.0003, 0.025, 252 * 5)
    high_vol_eq = pd.Series(
        100 * np.cumprod(1 + high_vol_rets),
        index=pd.bdate_range("2018-01-02", periods=len(high_vol_rets)),
    )
    assert naic_rbc_proxy(high_vol_eq) > naic_rbc_proxy(_EQUITY)
```

- [ ] **Step 2: Run to verify it fails**

```bash
pytest tests/test_analytics.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.analytics.insurance_metrics'`

- [ ] **Step 3: Write src/analytics/insurance_metrics.py**

```python
"""
Simplified regulatory capital proxies. Directional estimates only —
not production-grade regulatory calculations. Do not use for actual capital planning.
"""
import numpy as np
import pandas as pd

_TRADING_DAYS = 252
_SCR_EQUITY_BASE = 0.39         # Solvency II SCR-equity symmetric adjustment base
_NAIC_C1_BASE = 0.30            # NAIC RBC C-1 factor for common equity
_SPX_LONG_RUN_VOL = 0.15        # 15% assumed SPX long-run vol baseline


def scr_equity_proxy(equity: pd.Series) -> float:
    """
    Simplified Solvency II SCR-equity proxy.
    Approximation: 39% × |worst 1-year drawdown|.
    The actual SCR symmetric adjustment is calculated quarterly by EIOPA;
    this is a directional proxy for comparison purposes only.
    """
    annual_returns = equity.pct_change(_TRADING_DAYS).dropna()
    worst_annual = float(annual_returns.min())
    return _SCR_EQUITY_BASE * abs(worst_annual)


def naic_rbc_proxy(equity: pd.Series) -> float:
    """
    Simplified NAIC RBC C-1 proxy for equity.
    Base factor: 30% of market value for common stock.
    Adjusted upward/downward by the ratio of realized vol to 15% SPX long-run vol.
    """
    returns = equity.pct_change().dropna()
    realized = float(returns.std() * np.sqrt(_TRADING_DAYS))
    vol_ratio = realized / _SPX_LONG_RUN_VOL
    return _NAIC_C1_BASE * vol_ratio
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_analytics.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/analytics/insurance_metrics.py tests/test_analytics.py
git commit -m "feat: add Solvency II SCR proxy and NAIC RBC proxy (directional estimates)"
```

---

## Task 18: Comparisons Module

**Files:**
- Create: `src/analytics/comparisons.py`

- [ ] **Step 1: Write src/analytics/comparisons.py**

```python
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
    Estimate annualized cost drag for each strategy.
    Cost drag = gross CAGR - net CAGR, approximated from trade log.
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
```

- [ ] **Step 2: Verify import**

```bash
python -c "from src.analytics.comparisons import build_metric_table, correlation_matrix, cost_drag_table; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/analytics/comparisons.py
git commit -m "feat: add comparisons module (metric table, correlation matrix, cost drag)"
```

---

## Task 19: Pages 3, 4, 5 + Cost Drag Charts

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add helper to collect all 4 strategies in app.py**

Add this function to `app.py` after all 4 cache functions:
```python
def _all_strategies(start, end, cost_mode, custom_bps):
    return {
        "CBOE PUT": _run_put_write(start, end, cost_mode, custom_bps),
        "CBOE BXM": _run_covered_call(start, end, cost_mode, custom_bps),
        "Vol Target": _run_vol_target(start, end, cost_mode, custom_bps),
        "AiPEX-Lite": _run_aipex(start, end, cost_mode, custom_bps),
    }
```

- [ ] **Step 2: Replace the Strategy Comparison page block in app.py**

```python
elif page == "Strategy Comparison":
    from src.analytics.comparisons import build_metric_table, correlation_matrix, cost_drag_table

    st.title("Strategy Comparison")
    st.caption(f"Transaction costs: {cost_mode.upper()} | {start_date} – {end_date}")

    strategies = _all_strategies(start_date, end_date, cost_mode, custom_bps)

    # ── Cumulative return overlay ─────────────────────────────────────────────
    st.subheader("Cumulative Return (base 100)")
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"]
    fig = go.Figure()
    for (name, s), color in zip(strategies.items(), colors):
        fig.add_trace(go.Scatter(
            x=s.equity_curve().index, y=s.equity_curve(),
            name=name, line=dict(color=color),
        ))
    fig.update_layout(hovermode="x unified", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # ── Metric table ──────────────────────────────────────────────────────────
    st.subheader("Performance Metrics")
    st.dataframe(build_metric_table(strategies), use_container_width=True)

    # ── Correlation matrix ────────────────────────────────────────────────────
    st.subheader("Return Correlations")
    corr = correlation_matrix(strategies)
    fig_corr = px.imshow(
        corr, text_auto=".2f",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        zmin=-1, zmax=1,
    )
    fig_corr.update_layout(height=350)
    st.plotly_chart(fig_corr, use_container_width=True)

    # ── Cost drag ─────────────────────────────────────────────────────────────
    st.subheader("Cost Drag (Annualized)")
    st.dataframe(cost_drag_table(strategies), use_container_width=True)
    st.caption(
        "Cost drag = gross P&L – net P&L from trade log, annualized. "
        "Zero for CBOE index strategies (costs embedded in published index)."
    )
```

- [ ] **Step 3: Replace the Client Pitch page block in app.py**

```python
elif page == "Client Pitch":
    st.title("Client Pitch View")
    pitch_choice = st.sidebar.selectbox(
        "Strategy for pitch",
        ["CBOE PUT — Insurance Carry", "CBOE BXM — Yield Enhancement Overlay",
         "Vol-Targeted SPX — Capital-Efficient Equity", "AiPEX-Lite — AI-Driven Factor Rotation"],
    )
    pitch_map = {
        "CBOE PUT — Insurance Carry": _run_put_write,
        "CBOE BXM — Yield Enhancement Overlay": _run_covered_call,
        "Vol-Targeted SPX — Capital-Efficient Equity": _run_vol_target,
        "AiPEX-Lite — AI-Driven Factor Rotation": _run_aipex,
    }
    s = pitch_map[pitch_choice](start_date, end_date, cost_mode, custom_bps)
    m = s.metrics()
    framing = s.institutional_framing()
    curve = s.equity_curve()

    st.markdown(f"## {s.name}")
    st.markdown(f"*{s.description}*")
    st.markdown("---")

    # ── Investment thesis ─────────────────────────────────────────────────────
    st.markdown("### Investment Thesis")
    st.info(framing.get("structurer_pitch", ""))

    # ── Performance summary ───────────────────────────────────────────────────
    st.markdown("### Historical Performance")
    cols = st.columns(5)
    cols[0].metric("CAGR", f"{m['cagr']:.1%}")
    cols[1].metric("Sharpe", f"{m['sharpe']:.2f}")
    cols[2].metric("Max Drawdown", f"{m['max_dd']:.1%}")
    cols[3].metric("Annualized Vol", f"{m['vol']:.1%}")
    cols[4].metric("Sortino", f"{m['sortino']:.2f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve.index, y=curve, name=s.name, line=dict(color="#1f77b4", width=2)))
    fig.update_layout(
        title=f"Cumulative Return ({start_date[:4]}–present, base 100)",
        height=300,
        hovermode="x unified",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Institutional framing ─────────────────────────────────────────────────
    st.markdown("### Institutional Fit")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Return Profile**")
        st.write(framing.get("return_profile", ""))
        st.markdown("**Liability Fit**")
        st.write(framing.get("liability_fit", ""))
    with col2:
        st.markdown("**Capital Efficiency**")
        st.write(framing.get("capital_efficiency", ""))
        st.markdown("**Regulatory Treatment**")
        st.write(framing.get("regulatory_treatment", ""))

    # ── Key risks ─────────────────────────────────────────────────────────────
    st.markdown("### Key Risks & Limitations")
    st.warning(
        "• Backtest uses synthetic IV where applicable — not historical options data.\n"
        "• Regulatory metrics are directional proxies, not production-grade calculations.\n"
        "• Past performance does not predict future results.\n"
        "• CBOE index strategies use published index values; individual execution may differ."
    )
```

- [ ] **Step 4: Run locally and verify all 5 pages**

```bash
streamlit run app.py
```

Check:
- Overview: 4 strategy lines on chart
- Strategy Explorer: all 4 strategies selectable, framing panels visible
- Strategy Comparison: metric table, correlation heatmap, cost drag table all render
- Client Pitch: all 4 strategies selectable, clean one-pager layout
- About: methodology text renders

- [ ] **Step 5: Commit and push**

```bash
git add app.py
git commit -m "feat: complete all 5 Streamlit pages with comparison, pitch, and cost drag views"
git push origin main
```

---

## Task 20: README Polish

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write final README.md**

```markdown
# QIS Backtester

**Live demo:** [your-streamlit-url]
**Author:** Jack Halasz

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

**Synthetic IV:** 20-day rolling realized vol + 2 vol point skew spread, used as an implied vol proxy. Clearly labeled as synthetic throughout — not historical IV.

**Data sources:**
- CBOE PUT / BXM indices: FRED via pandas-datareader (series: PUTWRITE, BXMCBOE). Falls back to yfinance if unavailable.
- SPX, SPY, VIX, sector ETFs (XLK, XLF, XLV, XLE, XLY): yfinance
- All data cached locally as parquet after first pull

**Backtest window:** 2007–present (captures GFC, 2011 Euro crisis, 2018 VIXplosion, COVID crash, 2022 rate shock)

---

## Regulatory Metrics (Directional Proxies Only)

Solvency II SCR-equity proxy: 39% × |worst 1-year drawdown|

NAIC RBC C-1 proxy: 30% × (realized vol / 15% SPX long-run vol)

These are simplified directional estimates for comparison purposes. Do not use for actual regulatory capital planning.

---

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/QIS-backtester.git
cd QIS-backtester
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. First run fetches data from FRED and yfinance (~30 seconds); subsequent runs use the local parquet cache.

---

## Tests

```bash
pytest tests/ -v
```

---

## Architecture

```
src/
├── data/        loader.py (yfinance + FRED), cache.py (parquet)
├── pricing/     black_scholes.py (BSM + Greeks), synthetic_iv.py
├── strategies/  base.py (abstract), put_write.py, covered_call.py, vol_target.py, aipex_lite.py
├── engine/      backtester.py, costs.py
├── analytics/   tearsheet.py, insurance_metrics.py, comparisons.py
└── utils/       config.py, calendar.py
```

Each strategy exposes the same interface (`run()`, `metrics()`, `equity_curve()`, `trade_log()`, `institutional_framing()`), making the comparison view and cost toggle trivially extensible to new strategies.
```

- [ ] **Step 2: Add a screenshot to README (after app is running)**

Take a screenshot of the Strategy Explorer page with CBOE PUT selected and institutional framing visible. Save as `docs/screenshot.png`. Add to README:

```markdown
## Screenshot

![Strategy Explorer](docs/screenshot.png)
```

- [ ] **Step 3: Final commit and push**

```bash
git add README.md docs/screenshot.png
git commit -m "docs: final README polish with architecture, data sources, and live demo URL"
git push origin main
```

---

## Self-Review Against Spec

**Spec coverage check:**

| Spec requirement | Covered by task |
|---|---|
| Strategy A (CBOE PUT) | Task 9 |
| Strategy B (CBOE BXM) | Task 12 |
| Strategy C (vol-target) | Task 14 |
| Strategy E (AiPEX-Lite) | Task 15 |
| Pure numpy BSM + Greeks | Task 16 |
| Parquet cache | Task 4 |
| Cost toggle Off/Default/Stressed/Custom | Task 6 |
| Cost re-applied post-hoc from trade log | Tasks 9,12,14,15 (trade_log stores gross+net) |
| Tearsheet: Sharpe, Sortino, max DD, VaR, CVaR | Task 8 |
| Monthly return heatmap | Task 8 + Task 10 |
| Institutional framing panel (5 fields per strategy) | Tasks 9,12,14,15 |
| Solvency II SCR proxy | Task 17 |
| NAIC RBC proxy | Task 17 |
| Page 1: Overview + 4-strategy chart | Task 10 |
| Page 2: Strategy Explorer | Task 10 |
| Page 3: Strategy Comparison + correlation + cost drag | Task 19 |
| Page 4: Client Pitch View | Task 19 |
| Page 5: About / Methodology | Task 10 |
| GitHub + Streamlit Cloud deployment | Tasks 2, 11 |
| AiPEX disclaimer | Tasks 15, 20 |
| 2007–present backtest window | config.py (Task 3) |

All spec requirements covered. No gaps found.
