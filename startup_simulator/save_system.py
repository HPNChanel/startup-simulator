"""Simple save and load utilities for the simulator."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from . import config
from .startup import Startup


SCHEMA_VERSION: str = config.SAVE_SCHEMA_VERSION
SAVE_PATH: Path = getattr(config, "DEFAULT_SAVE_PATH", Path(config.AUTOSAVE_FILENAME))
_REQUIRED_KEYS: tuple[str, ...] = ("version", "timestamp", "turn", "rng_seed", "startup")


def _current_timestamp() -> str:
    """Return a timezone-aware ISO8601 timestamp."""

    return datetime.now(timezone.utc).isoformat()


def validate_snapshot(data: Mapping[str, Any] | None) -> bool:
    """Validate the structure and schema version of a save snapshot."""

    if not isinstance(data, Mapping):
        return False
    if any(key not in data for key in _REQUIRED_KEYS):
        return False
    if data.get("version") != SCHEMA_VERSION:
        return False
    timestamp = data.get("timestamp")
    if not isinstance(timestamp, str):
        return False
    try:
        datetime.fromisoformat(timestamp)
    except ValueError:
        return False
    try:
        int(data.get("turn"))
        int(data.get("rng_seed"))
    except (TypeError, ValueError):
        return False
    if not isinstance(data.get("startup"), Mapping):
        return False
    return True


def save_game(startup: Startup, path: Path | None = None) -> None:
    """Persist a :class:`Startup` instance to disk."""

    save_path = path or SAVE_PATH
    snapshot = {
        "version": SCHEMA_VERSION,
        "timestamp": _current_timestamp(),
        "turn": int(startup.turn),
        "rng_seed": int(startup.rng_seed),
        "startup": startup.snapshot(),
    }
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with save_path.open("w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, indent=2)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Failed to save game: {exc}")


def load_game(path: Path | None = None) -> Startup | None:
    """Load a saved :class:`Startup` instance from disk."""

    save_path = path or SAVE_PATH
    try:
        if not save_path.exists():
            return None
        with save_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Failed to load game: {exc}")
        return None
    if not validate_snapshot(data):
        print("Save file is invalid or incompatible.")
        return None
    try:
        startup_data = data["startup"]
        startup = Startup.from_snapshot(startup_data)
        startup.turn = int(data["turn"])
        startup.rng_seed = int(data["rng_seed"])
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Failed to restore game state: {exc}")
        return None
    return startup


__all__ = ["SAVE_PATH", "save_game", "load_game", "validate_snapshot"]
