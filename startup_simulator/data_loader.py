"""Data loading helpers for Startup Simulator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .models import Action, ActionRisk, Event, StartupProfile


def load_events(path: Path) -> List[Event]:
    """Load events from a JSON file."""

    data = _load_json(path)
    events: List[Event] = []
    for item in data:
        events.append(
            Event(
                event_id=item["id"],
                name=item["name"],
                trigger_chance=float(item["trigger_chance"]),
                duration=int(item["duration"]),
                deltas={key: float(value) for key, value in item["deltas"].items()},
                narrative=item["narrative"],
                revert_deltas=
                    {key: float(value) for key, value in item.get("revert_deltas", {}).items()}
                    if item.get("revert_deltas")
                    else None,
            )
        )
    return events


def load_actions(path: Path) -> List[Action]:
    """Load actions from a JSON file."""

    data = _load_json(path)
    actions: List[Action] = []
    for item in data:
        risk_data = item.get("risk")
        risk = None
        if risk_data:
            risk = ActionRisk(
                success_chance=float(risk_data["success_chance"]),
                success_effects={
                    key: float(value) for key, value in risk_data["success_effects"].items()
                },
                failure_effects={
                    key: float(value) for key, value in risk_data["failure_effects"].items()
                },
                success_narrative=risk_data["success_narrative"],
                failure_narrative=risk_data["failure_narrative"],
            )
        actions.append(
            Action(
                action_id=item["id"],
                name=item["name"],
                cost=float(item.get("cost", 0)),
                effects={key: float(value) for key, value in item.get("effects", {}).items()},
                description=item.get("description", ""),
                risk=risk,
            )
        )
    return actions


def load_profiles(path: Path) -> List[StartupProfile]:
    """Load startup profiles from a JSON file."""

    data = _load_json(path)
    profiles: List[StartupProfile] = []
    for item in data:
        profiles.append(
            StartupProfile(
                profile_id=item["id"],
                name=item["name"],
                description=item.get("description", ""),
                stats={key: float(value) for key, value in item["stats"].items()},
            )
        )
    return profiles


def _load_json(path: Path) -> List[Dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
