from __future__ import annotations

from datetime import datetime, timezone
import json

from startup_simulator import save_system
from startup_simulator.startup import Startup
from startup_simulator.tests.utils import temporary_save_path


def test_save_and_load_roundtrip() -> None:
    startup = Startup(balance=750_000, turn=5, rng_seed=99)
    startup.active_events.append("launch_party")
    with temporary_save_path(save_system):
        save_system.save_game(startup)
        loaded = save_system.load_game()

    assert loaded is not None
    assert loaded.snapshot() == startup.snapshot()


def test_load_game_missing_file() -> None:
    with temporary_save_path(save_system):
        assert save_system.load_game() is None


def test_load_game_with_corrupted_file() -> None:
    with temporary_save_path(save_system) as path:
        path.write_text("{not valid json}", encoding="utf-8")
        assert save_system.load_game() is None


def test_load_game_with_schema_mismatch() -> None:
    with temporary_save_path(save_system) as path:
        payload = {
            "version": "0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "turn": 1,
            "rng_seed": 42,
            "startup": Startup().snapshot(),
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert save_system.load_game() is None
