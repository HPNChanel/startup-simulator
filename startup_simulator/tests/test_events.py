"""Tests for event loading."""
from __future__ import annotations

import json
from pathlib import Path

from startup_simulator.events import Event, load_events


def test_load_events_returns_event_objects(tmp_path: Path) -> None:
    data = [
        {
            "key": "test_event",
            "name": "Test Event",
            "description": "A simple test event.",
            "probability": 0.5,
            "impact": {"morale": 5},
        }
    ]
    event_file = tmp_path / "events.json"
    event_file.write_text(json.dumps(data), encoding="utf-8")

    events = load_events(event_file)

    assert len(events) == 1
    event = events[0]
    assert isinstance(event, Event)
    assert event.key == "test_event"
