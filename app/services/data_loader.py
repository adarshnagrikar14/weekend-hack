from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import BASE_DIR


DATA_DIR = BASE_DIR / "app" / "data"


def _load_json(filename: str) -> list[dict[str, Any]]:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def managers() -> list[dict[str, Any]]:
    return _load_json("seed_managers.json")


@lru_cache(maxsize=1)
def resources() -> list[dict[str, Any]]:
    return _load_json("seed_resources.json")


@lru_cache(maxsize=1)
def assets() -> list[dict[str, Any]]:
    return _load_json("seed_assets.json")


@lru_cache(maxsize=1)
def sample_demands() -> list[dict[str, Any]]:
    return _load_json("sample_demands.json")
