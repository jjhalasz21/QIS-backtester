from pathlib import Path
import re
import pandas as pd
from src.utils.config import DATA_DIR

_DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})$')


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


def load_covering(ticker: str, start: str, end: str, data_dir: Path = None) -> pd.DataFrame | None:
    """Return cached data sliced to [start, end] from any wider cached file for this ticker."""
    if data_dir is None:
        data_dir = DATA_DIR
    safe = ticker.replace("^", "").replace("/", "_").replace("=", "")
    for p in sorted(data_dir.glob(f"{safe}_*.parquet")):
        m = _DATE_RE.search(p.stem)
        if not m:
            continue
        c_start, c_end = m.group(1), m.group(2)
        if c_start <= start and c_end >= end:
            df = pd.read_parquet(p)
            sliced = df[(df.index >= pd.Timestamp(start)) & (df.index <= pd.Timestamp(end))]
            return sliced if not sliced.empty else None
    return None


def save(key: str, df: pd.DataFrame, data_dir: Path = None) -> None:
    if data_dir is None:
        data_dir = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_path(key, data_dir))
