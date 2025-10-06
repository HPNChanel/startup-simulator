"""Random events and their effects."""
from __future__ import annotations

from collections.abc import Callable, Mapping
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from . import config
from .startup import Startup


# ---------------------------------------------------------------------------
# Event data structures


@dataclass(frozen=True, slots=True)
class GameEvent:
    """Describes a random event that can occur during the simulation."""

    id: str
    name: str
    trigger_chance: float
    duration_turns: int
    apply: Callable[[Startup], None]
    revert: Callable[[Startup], None] | None = None
    narrative: str = ""


# ---------------------------------------------------------------------------
# Event loading helpers


def _build_effect_callable(effects: Mapping[str, float] | None) -> Callable[[Startup], None]:
    """Create a callable that applies *effects* to a :class:`Startup` instance."""

    effects = dict(effects or {})

    def _apply(startup: Startup) -> None:
        if effects:
            startup.apply_deltas(effects)

    return _apply


def _coerce_event(data: Mapping[str, Any]) -> GameEvent:
    """Coerce raw event data into a :class:`GameEvent` instance."""

    event_id = data.get("id") or data.get("key")
    if not event_id:
        raise KeyError("Event definition missing required 'id' field.")
    name = data.get("name") or str(event_id).replace("_", " ").title()
    narrative = data.get("narrative") or data.get("description") or ""

    trigger_chance = float(data.get("trigger_chance") or data.get("probability") or 0.0)
    trigger_chance = max(0.0, min(1.0, trigger_chance))

    duration = data.get("duration_turns") or data.get("duration") or data.get("turns") or 1
    duration_turns = max(1, int(duration))

    effects = data.get("effects") or data.get("impact") or {}
    revert_effects = data.get("revert_effects") or data.get("revert")

    apply_callable = _build_effect_callable(effects)
    revert_callable = None
    if revert_effects:
        revert_callable = _build_effect_callable(revert_effects)
    elif duration_turns > 1 and effects:
        inverted = {key: -value for key, value in dict(effects).items()}
        revert_callable = _build_effect_callable(inverted)

    return GameEvent(
        id=str(event_id),
        name=str(name),
        trigger_chance=trigger_chance,
        duration_turns=duration_turns,
        apply=apply_callable,
        revert=revert_callable,
        narrative=str(narrative),
    )


def _load_from_json(path: Path) -> Dict[str, GameEvent]:
    """Load game events from the provided JSON file."""

    with path.open("r", encoding="utf-8") as handle:
        raw_events = json.load(handle)

    if not isinstance(raw_events, Iterable):
        raise ValueError("Events JSON must contain a list of event definitions.")

    events: Dict[str, GameEvent] = {}
    for entry in raw_events:
        if not isinstance(entry, Mapping):
            raise ValueError("Each event definition must be a JSON object.")
        event = _coerce_event(entry)
        events[event.id] = event
    return events


def _fallback_events() -> Dict[str, GameEvent]:
    """Return a default in-code registry of events."""

    return {
        event.id: event
        for event in (
            GameEvent(
                id="server_crash",
                name="Major Server Crash",
                trigger_chance=0.18,
                duration_turns=2,
                apply=_build_effect_callable(
                    {
                        "monthly_revenue": -12000,
                        "brand_awareness": -6.0,
                        "team_morale": -4.0,
                    }
                ),
                revert=_build_effect_callable({"monthly_revenue": 12000, "team_morale": 2.0}),
                narrative="A severe outage shakes user trust and the team scrambles to recover.",
            ),
            GameEvent(
                id="pr_boost",
                name="Glowingly Positive Press",
                trigger_chance=0.22,
                duration_turns=1,
                apply=_build_effect_callable(
                    {
                        "brand_awareness": 10.0,
                        "monthly_revenue": 6000,
                        "users": 450,
                    }
                ),
                narrative="Tech media hails your momentum and signups spike overnight.",
            ),
            GameEvent(
                id="talent_poached",
                name="Key Talent Poached",
                trigger_chance=0.12,
                duration_turns=3,
                apply=_build_effect_callable({"headcount": -2, "team_morale": -8.0}),
                revert=_build_effect_callable({"team_morale": 4.0}),
                narrative="A competitor lures away senior engineers, rattling the remaining team.",
            ),
            GameEvent(
                id="customer_uprising",
                name="Customer Advocacy Uprising",
                trigger_chance=0.1,
                duration_turns=2,
                apply=_build_effect_callable({"churn_rate": -0.01, "brand_awareness": 8.0}),
                revert=_build_effect_callable({"churn_rate": 0.01}),
                narrative="Power users rally behind you, convincing friends to stick around.",
            ),
        )
    }


def load_events(data_path: Path | None = None) -> List[GameEvent]:
    """Load available events, falling back to defaults if necessary."""

    path = data_path or (config.DATA_DIRECTORY / "events.json")
    try:
        registry = _load_from_json(path)
    except FileNotFoundError:
        registry = _fallback_events()

    return [registry[key] for key in sorted(registry)]


EVENT_REGISTRY: Dict[str, GameEvent] = {event.id: event for event in load_events()}


# ---------------------------------------------------------------------------
# Active event helpers


_ACTIVE_DELIMITER = ":"


def _decode_active_events(values: Iterable[str]) -> Dict[str, int]:
    """Decode the active event payload stored on the :class:`Startup`."""

    decoded: Dict[str, int] = {}
    for entry in values:
        if not isinstance(entry, str):  # pragma: no cover - safeguard
            continue
        if _ACTIVE_DELIMITER in entry:
            event_id, remaining = entry.split(_ACTIVE_DELIMITER, 1)
        else:
            event_id, remaining = entry, "0"
        try:
            turns_remaining = max(0, int(remaining))
        except ValueError:
            turns_remaining = 0
        if event_id:
            decoded[event_id] = turns_remaining
    return decoded


def _encode_active_events(values: Mapping[str, int]) -> List[str]:
    return [f"{event_id}{_ACTIVE_DELIMITER}{max(0, int(turns))}" for event_id, turns in values.items()]


def apply_event_effects(startup: Startup, event: GameEvent) -> None:
    """Apply the effects of *event* to *startup*."""

    event.apply(startup)
    startup.clamp_all()


def _state_adjusted_chance(startup: Startup, event: GameEvent) -> float:
    """Return the trigger chance for *event* adjusted for current state."""

    base_chance = event.trigger_chance * config.EVENT_PROBABILITY_WEIGHT

    if event.id == "server_crash":
        bug_pressure = max(0.0, 1.0 - startup.product_quality / 100)
        base_chance += bug_pressure * 0.25
    elif event.id == "pr_boost":
        reputation = startup.brand_awareness / 100
        base_chance += reputation * 0.2
    elif event.id == "talent_poached":
        morale_gap = max(0.0, (75.0 - startup.team_morale) / 100)
        base_chance += morale_gap * 0.15
    elif event.id == "customer_uprising":
        happy_customers = max(0.0, startup.product_quality / 100)
        base_chance += happy_customers * 0.12

    return max(0.0, min(1.0, base_chance))


def maybe_trigger_event(startup: Startup, rng: random.Random) -> Tuple[Startup, List[str]]:
    """Potentially trigger an event for *startup*, returning narratives."""

    narratives: List[str] = []
    active = _decode_active_events(startup.active_events)

    for event_id in sorted(EVENT_REGISTRY):
        if event_id in active and active[event_id] > 0:
            continue
        event = EVENT_REGISTRY[event_id]
        chance = _state_adjusted_chance(startup, event)
        roll = rng.random()
        if roll <= chance:
            apply_event_effects(startup, event)
            if event.duration_turns > 0:
                active[event.id] = event.duration_turns
            narrative = event.narrative or f"{event.name} occurs."
            narratives.append(narrative)
            break

    startup.active_events = _encode_active_events(active)
    startup.clamp_all()
    return startup, narratives


def tick_active_events(startup: Startup) -> List[str]:
    """Advance durations and resolve events that have completed."""

    messages: List[str] = []
    active = _decode_active_events(startup.active_events)
    updated: Dict[str, int] = {}

    for event_id, turns in active.items():
        event = EVENT_REGISTRY.get(event_id)
        if not event:
            continue
        remaining = max(0, turns - 1)
        if remaining > 0:
            updated[event_id] = remaining
        else:
            if event.revert:
                event.revert(startup)
                startup.clamp_all()
            messages.append(f"{event.name} has concluded.")

    startup.active_events = _encode_active_events(updated)
    return messages


__all__ = [
    "GameEvent",
    "EVENT_REGISTRY",
    "apply_event_effects",
    "load_events",
    "maybe_trigger_event",
    "tick_active_events",
]

