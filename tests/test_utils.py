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
    assert all(d.weekday() < 5 for d in days)
    assert len(days) == 23  # 23 business days in Jan 2024

def test_trading_days_count_over_year():
    days = trading_days("2023-01-01", "2023-12-31")
    assert 250 <= len(days) <= 265
