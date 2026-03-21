from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def resolve_data_root() -> Path:
    configured = os.getenv("PANCREATIC_SIGNAL_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()

    current_file = Path(__file__).resolve()
    for base in current_file.parents:
        candidate = base / "data"
        if candidate.exists():
            return candidate

    mounted_data = Path("/data")
    if mounted_data.exists():
        return mounted_data

    return current_file.parents[3] / "data"


def resolve_data_path(*parts: str) -> Path:
    return resolve_data_root().joinpath(*parts)
