from __future__ import annotations

import json
import random
from pathlib import Path
from tempfile import TemporaryDirectory

from startup_simulator import events
from startup_simulator.events import GameEvent, apply_event_effects, load_events, maybe_trigger_event, tick_active_events
from startup_simulator.startup import Startup
from startup_simulator.tests.utils import PatchManager


def test_load_events_returns_game_events() -> None:
    data = [
        {
            "id": "flash_sale",
            "name": "Flash Sale Frenzy",
            "trigger_chance": 0.5,
            "duration_turns": 1,
            "effects": {"balance": 1500},
            "narrative": "A surprise sale boosts the cash position.",
        }
    ]

    with TemporaryDirectory() as tmp_dir:
        event_file = Path(tmp_dir) / "events.json"
        event_file.write_text(json.dumps(data), encoding="utf-8")
        loaded = load_events(event_file)

    assert len(loaded) == 1
    event = loaded[0]
    assert isinstance(event, GameEvent)

    startup = Startup()
    initial_balance = startup.balance
    apply_event_effects(startup, event)

    assert startup.balance == initial_balance + 1500


def test_event_lifecycle_triggers_and_reverts() -> None:
    def apply_fn(startup: Startup) -> None:
        startup.apply_deltas({"team_morale": -10.0})

    def revert_fn(startup: Startup) -> None:
        startup.apply_deltas({"team_morale": 10.0})

    custom_event = GameEvent(
        id="stress_wave",
        name="Stress Wave",
        trigger_chance=1.0,
        duration_turns=2,
        apply=apply_fn,
        revert=revert_fn,
        narrative="Pivotal deadlines leave the team frazzled.",
    )

    with PatchManager() as patches:
        patches.setattr(events, "EVENT_REGISTRY", {custom_event.id: custom_event})
        patches.setattr(events.config, "EVENT_PROBABILITY_WEIGHT", 1.0)
        startup = Startup()
        rng = random.Random(0)
        updated, narratives = maybe_trigger_event(startup, rng)

        assert updated is startup
        assert narratives == [custom_event.narrative]
        assert startup.team_morale == 60.0
        assert startup.active_events == ["stress_wave:2"]

        messages = tick_active_events(startup)
        assert messages == []
        assert startup.active_events == ["stress_wave:1"]
        assert startup.team_morale == 60.0

        messages = tick_active_events(startup)
        assert messages == ["Stress Wave has concluded."]
        assert startup.active_events == []
        assert startup.team_morale == 70.0


def test_event_trigger_is_deterministic_with_seed() -> None:
    def apply_fn(startup: Startup) -> None:
        startup.apply_deltas({"brand_awareness": 5.0})

    custom_event = GameEvent(
        id="consistent_buzz",
        name="Consistent Buzz",
        trigger_chance=0.4,
        duration_turns=1,
        apply=apply_fn,
        narrative="Organic buzz gently lifts awareness.",
    )

    with PatchManager() as patches:
        patches.setattr(events, "EVENT_REGISTRY", {custom_event.id: custom_event})
        startup_one = Startup()
        startup_two = Startup()
        rng_one = random.Random(1234)
        rng_two = random.Random(1234)
        for _ in range(3):
            maybe_trigger_event(startup_one, rng_one)
            maybe_trigger_event(startup_two, rng_two)

    assert startup_one.brand_awareness == startup_two.brand_awareness
    assert startup_one.active_events == startup_two.active_events
