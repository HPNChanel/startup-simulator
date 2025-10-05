"""Definitions and utilities for player actions."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import json

from . import config


@dataclass(slots=True)
class Action:
    """Represents an actionable decision a player can take during a turn."""

    key: str
    name: str
    description: str
    cost: float
    impact: Dict[str, float]


def load_actions(data_path: Path | None = None) -> List[Action]:
    """Load available actions from the JSON definition file."""
    path = data_path or (config.DATA_DIRECTORY / "actions.json")
    with path.open("r", encoding="utf-8") as handle:
        raw_actions = json.load(handle)
    return [Action(**item) for item in raw_actions]


def action_keys(actions: Iterable[Action]) -> List[str]:
    """Return a list of action keys for quick membership tests."""
    return [action.key for action in actions]


__all__ = ["Action", "load_actions", "action_keys"]
