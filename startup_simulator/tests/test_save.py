"""Tests for the save system."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from startup_simulator import save_system
from startup_simulator.startup import Startup


@pytest.fixture(autouse=True)
def override_save_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "save.json"
    monkeypatch.setattr(save_system, "SAVE_PATH", path)
    return path


def test_save_and_load_roundtrip() -> None:
    startup = Startup(balance=750_000, turn=5, rng_seed=99)
    startup.active_events.append("launch_party")
    save_system.save_game(startup)
    loaded = save_system.load_game()
    assert loaded is not None
    assert loaded.snapshot() == startup.snapshot()


def test_load_game_missing_file() -> None:
    assert save_system.load_game() is None


def test_load_game_with_corrupted_file(override_save_path: Path) -> None:
    override_save_path.write_text("{not valid json}", encoding="utf-8")
    assert save_system.load_game() is None


def test_load_game_with_schema_mismatch(override_save_path: Path) -> None:
    payload = {
        "version": "0.0",  # incorrect schema version
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "turn": 1,
        "rng_seed": 42,
        "startup": Startup().snapshot(),
    }
    override_save_path.write_text(json.dumps(payload), encoding="utf-8")
    assert save_system.load_game() is None
