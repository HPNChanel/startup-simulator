"""Definitions and utilities for player actions."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import json
import random

from . import config
from .startup import Startup


@dataclass(frozen=True, slots=True)
class Action:
    """Represents an actionable decision a player can take during a turn."""

    id: str
    name: str
    costs: Mapping[str, float] = field(default_factory=dict)
    effects: Mapping[str, float] = field(default_factory=dict)
    risk: Mapping[str, Any] | None = None
    narrative: str = ""
    max_per_turn: int | None = None


def _coerce_action(data: Mapping[str, Any]) -> Action:
    """Coerce raw dictionary data into an :class:`Action` instance."""

    action_id = data.get("id") or data.get("key")
    if not action_id:
        raise KeyError("Action definition missing required 'id' field.")
    name = data.get("name") or action_id.replace("_", " ").title()

    narrative = data.get("narrative") or data.get("description") or ""

    costs: Mapping[str, float]
    if "costs" in data and isinstance(data["costs"], Mapping):
        costs = dict(data["costs"])
    elif "cost" in data:
        # Legacy single-cost field assumed to target the balance attribute.
        costs = {"balance": float(data["cost"]) }
    else:
        costs = {}

    effects: Mapping[str, float]
    if "effects" in data and isinstance(data["effects"], Mapping):
        effects = dict(data["effects"])
    elif "impact" in data and isinstance(data["impact"], Mapping):
        effects = dict(data["impact"])
    else:
        effects = {}

    risk = data.get("risk") if isinstance(data.get("risk"), Mapping) else None

    max_per_turn = data.get("max_per_turn")
    if max_per_turn is not None:
        max_per_turn = int(max_per_turn)

    return Action(
        id=str(action_id),
        name=str(name),
        costs=costs,
        effects=effects,
        risk=risk,
        narrative=str(narrative),
        max_per_turn=max_per_turn,
    )


def _load_from_json(path: Path) -> Dict[str, Action]:
    """Load actions from the provided JSON path."""

    with path.open("r", encoding="utf-8") as handle:
        raw_actions = json.load(handle)

    if not isinstance(raw_actions, Iterable):
        raise ValueError("Actions JSON must contain a list of action definitions.")

    actions: Dict[str, Action] = {}
    for entry in raw_actions:
        if not isinstance(entry, Mapping):
            raise ValueError("Each action definition must be a JSON object.")
        action = _coerce_action(entry)
        actions[action.id] = action
    return actions


def _fallback_actions() -> Dict[str, Action]:
    """Return an in-code fallback registry of actions."""

    default_actions = [
        Action(
            id="ship_feature",
            name="Ship Major Feature",
            narrative="The team rushes to ship a headline feature.",
            costs={"balance": 25000, "team_morale": 3},
            effects={"product_quality": 8.0, "users": 400},
            risk={
                "success_chance": 0.8,
                "success": {
                    "effects": {"brand_awareness": 6.0},
                    "narrative": "Users love the polish and word of mouth spreads.",
                },
                "failure": {
                    "effects": {"team_morale": -5.0},
                    "narrative": "Unexpected bugs force an emergency rollback.",
                },
            },
            max_per_turn=1,
        ),
        Action(
            id="marketing_blast",
            name="Launch Marketing Campaign",
            narrative="You greenlight a week-long marketing blitz.",
            costs={"balance": 18000},
            effects={"brand_awareness": 12.0, "users": 600},
            risk={
                "success_chance": 0.65,
                "success": {
                    "effects": {"monthly_revenue": 8000},
                    "narrative": "The campaign resonates and signups climb.",
                },
                "failure": {
                    "effects": {"brand_awareness": -4.0},
                    "narrative": "The message misses the mark and social media piles on.",
                },
            },
            max_per_turn=2,
        ),
        Action(
            id="investor_pitch",
            name="Pitch to Investors",
            narrative="You polish the deck and pitch to a room of VCs.",
            costs={"balance": 7000},
            effects={},
            risk={
                "success_chance": 0.45,
                "success": {
                    "effects": {"balance": 220000, "brand_awareness": 8.0},
                    "narrative": "Investors are impressed and wire a new round of funding.",
                },
                "failure": {
                    "effects": {"team_morale": -6.0, "brand_awareness": -3.0},
                    "narrative": "The questions get hostile and word spreads of the shaky pitch.",
                },
            },
            max_per_turn=1,
        ),
    ]

    return {action.id: action for action in default_actions}


def load_actions(data_path: Path | None = None) -> Dict[str, Action]:
    """Load available actions, falling back to defaults if necessary."""

    path = data_path or (config.DATA_DIRECTORY / "actions.json")
    try:
        return _load_from_json(path)
    except FileNotFoundError:
        return _fallback_actions()


ACTION_REGISTRY: Dict[str, Action] = load_actions()


def _affordable(startup: Startup, action: Action) -> bool:
    """Return whether the startup can currently afford the action."""

    balance_cost = action.costs.get("balance")
    if balance_cost is not None and startup.balance < balance_cost:
        return False
    return True


def list_actions(startup: Startup) -> list[Action]:
    """Return the list of actions available to the provided startup state."""

    available = [action for action in ACTION_REGISTRY.values() if _affordable(startup, action)]
    return sorted(available, key=lambda item: item.name)


def _clamp_turn_limit(limit: int | None) -> int:
    if limit is None:
        limit = config.MAX_ACTIONS_PER_TURN
    return max(1, min(3, limit))


def validate_action_limit(
    actions_taken: Mapping[str, int],
    action: Action,
    max_actions: int | None = None,
) -> None:
    """Validate whether another instance of *action* can be taken this turn.

    Raises a :class:`ValueError` if a limit is exceeded.
    """

    limit = _clamp_turn_limit(max_actions)
    total_taken = sum(actions_taken.values())
    if total_taken >= limit:
        raise ValueError(f"A maximum of {limit} actions may be taken per turn.")

    per_action_limit = action.max_per_turn
    if per_action_limit is not None:
        already_taken = actions_taken.get(action.id, 0)
        if already_taken >= per_action_limit:
            raise ValueError(
                f"Action '{action.name}' can only be taken {per_action_limit} time(s) per turn."
            )


def _apply_deltas(startup: Startup, deltas: Mapping[str, float]) -> None:
    numeric_deltas: Dict[str, float] = {}
    for key, delta in deltas.items():
        if not hasattr(startup, key):
            raise ValueError(f"Action references unknown startup attribute '{key}'.")
        numeric_deltas[key] = float(delta)
    if numeric_deltas:
        startup.apply_deltas(numeric_deltas)


def _apply_costs(startup: Startup, action: Action) -> None:
    if not action.costs:
        return
    balance_cost = action.costs.get("balance")
    if balance_cost is not None and startup.balance < balance_cost:
        raise ValueError(
            f"Insufficient balance to perform action '{action.name}'. Required {balance_cost}, have {startup.balance}."
        )
    deltas = {key: -value for key, value in action.costs.items()}
    _apply_deltas(startup, deltas)


def apply_action(startup: Startup, action_id: str, rng: random.Random) -> tuple[Startup, str]:
    """Apply *action_id* to *startup* using the provided RNG for stochastic outcomes."""

    if action_id not in ACTION_REGISTRY:
        raise ValueError(f"Unknown action id: {action_id}")

    action = ACTION_REGISTRY[action_id]
    narrative_parts = [action.narrative.strip()] if action.narrative else []

    _apply_costs(startup, action)
    _apply_deltas(startup, action.effects)

    outcome_text: str | None = None
    if action.risk:
        success_chance = float(action.risk.get("success_chance", 0.0))
        roll = rng.random()
        branch_key = "success" if roll < success_chance else "failure"
        branch = action.risk.get(branch_key)
        if isinstance(branch, Mapping):
            branch_effects = branch.get("effects")
            if isinstance(branch_effects, Mapping):
                _apply_deltas(startup, branch_effects)
            outcome_text = str(branch.get("narrative")) if branch.get("narrative") else None
        else:
            outcome_text = None

    if outcome_text:
        narrative_parts.append(outcome_text.strip())

    startup.clamp_all()

    final_narrative = " ".join(part for part in narrative_parts if part)
    return startup, final_narrative


__all__ = [
    "Action",
    "ACTION_REGISTRY",
    "apply_action",
    "list_actions",
    "load_actions",
    "validate_action_limit",
]
