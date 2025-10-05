"""Tests for the save system."""
from __future__ import annotations

from pathlib import Path

from startup_simulator import save_system


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    save_file = tmp_path / "save.json"
    state = {"player": "Alex", "month": 3}
    save_system.save_state(state, save_file)
    loaded = save_system.load_state(save_file)
    assert loaded == state


def test_load_state_missing_file(tmp_path: Path) -> None:
    save_file = tmp_path / "missing.json"
    assert save_system.load_state(save_file) is None
