"""Data models for Startup Simulator."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import random


StatDict = Dict[str, float]


@dataclass
class Event:
    """Represents a time-bound event that influences company stats."""

    event_id: str
    name: str
    trigger_chance: float
    duration: int
    deltas: StatDict
    narrative: str
    revert_deltas: Optional[StatDict] = None


@dataclass
class ActionRisk:
    """Represents a risky action outcome."""

    success_chance: float
    success_effects: StatDict
    failure_effects: StatDict
    success_narrative: str
    failure_narrative: str


@dataclass
class Action:
    """Represents an action that the player can take."""

    action_id: str
    name: str
    cost: float
    effects: StatDict
    description: str
    risk: Optional[ActionRisk] = None


@dataclass
class StartupProfile:
    """Configuration for a starting company profile."""

    profile_id: str
    name: str
    description: str
    stats: StatDict


@dataclass
class ActiveEvent:
    """Tracks an event currently affecting the company."""

    event: Event
    remaining_turns: int


@dataclass
class GameStats:
    """Holds the numeric metrics for the company."""

    balance: float
    revenue: float
    expenses: float
    product_level: int
    bug_rate: float
    team_size: int
    morale: float
    productivity: float
    reputation: float
    users: float
    market_share: float

    def to_dict(self) -> StatDict:
        """Serialize stats into a dictionary."""

        return asdict(self)

    @classmethod
    def from_dict(cls, data: StatDict) -> "GameStats":
        """Create stats from a dictionary."""

        return cls(
            balance=float(data["balance"]),
            revenue=float(data["revenue"]),
            expenses=float(data["expenses"]),
            product_level=int(data["product_level"]),
            bug_rate=float(data["bug_rate"]),
            team_size=int(data["team_size"]),
            morale=float(data["morale"]),
            productivity=float(data["productivity"]),
            reputation=float(data["reputation"]),
            users=float(data["users"]),
            market_share=float(data["market_share"]),
        )


@dataclass
class GameState:
    """Represents the full game state."""

    stats: GameStats
    turn: int
    active_events: List[ActiveEvent] = field(default_factory=list)
    last_report: List[str] = field(default_factory=list)
    rng_state: Optional[Tuple[int, Tuple[int, ...], Optional[int]]] = None

    def to_dict(self) -> Dict[str, object]:
        """Serialize the game state to a JSON-compatible dictionary."""

        return {
            "stats": self.stats.to_dict(),
            "turn": self.turn,
            "active_events": [
                {
                    "event_id": active.event.event_id,
                    "remaining_turns": active.remaining_turns,
                }
                for active in self.active_events
            ],
            "last_report": self.last_report,
            "rng_state": self._serialize_rng_state(),
        }

    def _serialize_rng_state(self) -> Optional[Dict[str, object]]:
        if self.rng_state is None:
            return None
        version, state, gauss = self.rng_state
        return {
            "version": version,
            "state": list(state),
            "gauss": gauss,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, object],
        events_by_id: Dict[str, Event],
    ) -> "GameState":
        """Deserialize a game state from a dictionary."""

        stats = GameStats.from_dict(data["stats"])  # type: ignore[index]
        active_events: List[ActiveEvent] = []
        for entry in data.get("active_events", []):  # type: ignore[arg-type]
            event_id = entry["event_id"]
            remaining = int(entry["remaining_turns"])
            event = events_by_id.get(event_id)
            if event:
                active_events.append(ActiveEvent(event=event, remaining_turns=remaining))
        rng_state = cls._deserialize_rng_state(data.get("rng_state"))
        return cls(
            stats=stats,
            turn=int(data["turn"]),
            active_events=active_events,
            last_report=list(data.get("last_report", [])),
            rng_state=rng_state,
        )

    @staticmethod
    def _deserialize_rng_state(data: Optional[Dict[str, object]]) -> Optional[Tuple[int, Tuple[int, ...], Optional[int]]]:
        if not data:
            return None
        version = int(data["version"])
        state = tuple(int(value) for value in data["state"])  # type: ignore[index]
        gauss_value = data.get("gauss")
        gauss = int(gauss_value) if gauss_value is not None else None
        return (version, state, gauss)


SCHEMA_VERSION = "1.0"


def default_rng(seed: Optional[int] = None) -> random.Random:
    """Create a deterministic random generator."""

    rng = random.Random()
    if seed is not None:
        rng.seed(seed)
    return rng
