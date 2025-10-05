"""Simple save and load utilities for the simulator."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from . import config


def save_state(state: Dict[str, Any], path: Path | None = None) -> None:
    """Persist the simulation state to disk."""
    save_path = path or Path(config.AUTOSAVE_FILENAME)
    payload = {
        "schema_version": config.SAVE_SCHEMA_VERSION,
        "state": state,
    }
    with save_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def load_state(path: Path | None = None) -> Dict[str, Any] | None:
    """Load the simulation state from disk if available."""
    save_path = path or Path(config.AUTOSAVE_FILENAME)
    if not save_path.exists():
        return None
    with save_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("schema_version") != config.SAVE_SCHEMA_VERSION:
        raise ValueError("Save file schema version mismatch.")
    return payload.get("state")


__all__ = ["save_state", "load_state"]
