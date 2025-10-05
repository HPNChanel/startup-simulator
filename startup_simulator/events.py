"""Random events and their effects."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from . import config


@dataclass(slots=True)
class Event:
    """Describes a random event that can occur during the simulation."""

    key: str
    name: str
    description: str
    probability: float
    impact: Dict[str, float]


def load_events(data_path: Path | None = None) -> List[Event]:
    """Load random events from disk."""
    path = data_path or (config.DATA_DIRECTORY / "events.json")
    with path.open("r", encoding="utf-8") as handle:
        raw_events = json.load(handle)
    return [Event(**item) for item in raw_events]


__all__ = ["Event", "load_events"]
