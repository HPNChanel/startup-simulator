"""Player and company state models used by the simulator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from . import config


@dataclass(slots=True)
class Metric:
    """Quantifies a single company metric such as morale or product quality."""

    name: str
    value: float

    def apply_delta(self, delta: float) -> None:
        """Apply a change to the metric value while keeping it within sensible bounds."""
        minimum, maximum = config.METRIC_VALUE_RANGE
        updated = self.value + delta
        if minimum is not None:
            updated = max(minimum, updated)
        if maximum is not None:
            updated = min(maximum, updated)
        self.value = updated


@dataclass(slots=True)
class PlayerState:
    """Represents the overall simulation state for a single player."""

    name: str
    cash: float = config.DEFAULT_STARTING_FUNDS
    month: int = 1
    metrics: Dict[str, Metric] = field(default_factory=dict)
    actions_taken: List[str] = field(default_factory=list)

    def record_action(self, action_key: str) -> None:
        """Record that the player has taken the specified action this turn."""
        if len(self.actions_taken) >= config.DEFAULT_ACTIONS_PER_TURN:
            raise ValueError("Action limit reached for this turn.")
        self.actions_taken.append(action_key)

    def reset_actions(self) -> None:
        """Reset the action counter for a new turn."""
        self.actions_taken.clear()


__all__ = ["Metric", "PlayerState"]
