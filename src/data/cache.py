from pathlib import Path
import pandas as pd
from src.utils.config import DATA_DIR


def cache_key(ticker: str, start: str, end: str) -> str:
    safe = ticker.replace("^", "").replace("/", "_").replace("=", "")
    return f"{safe}_{start}_{end}"


def _path(key: str, data_dir: Path) -> Path:
    return data_dir / f"{key}.parquet"


def load(key: str, data_dir: Path = None) -> pd.DataFrame | None:
    if data_dir is None:
        data_dir = DATA_DIR
    p = _path(key, data_dir)
    if p.exists():
        return pd.read_parquet(p)
    return None


def save(key: str, df: pd.DataFrame, data_dir: Path = None) -> None:
    if data_dir is None:
        data_dir = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_path(key, data_dir))
