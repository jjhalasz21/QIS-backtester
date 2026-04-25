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
    pd.testing.assert_frame_equal(result, df, check_freq=False)

def test_load_returns_none_for_missing(tmp_path):
    from src.data.cache import load
    result = load("nonexistent_key", data_dir=tmp_path)
    assert result is None
