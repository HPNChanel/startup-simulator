"""Core startup state model and helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, Iterable, List, Mapping

from . import config


DEFAULT_BASELINE_STATE: Dict[str, Any] = {
    "balance": 500_000,
    "monthly_revenue": 45_000,
    "monthly_expenses": 110_000,
    "users": 1_500,
    "growth_rate": 0.08,
    "churn_rate": 0.04,
    "product_quality": 60.0,
    "brand_awareness": 40.0,
    "team_morale": 70.0,
    "headcount": 18,
    "debt": 0,
}


@dataclass(slots=True)
class Startup:
    """Represents the mutable startup simulation state.

    Monetary values are tracked as whole dollars (not floats) to avoid precision
    drift when repeatedly applying changes.
    """

    balance: int = DEFAULT_BASELINE_STATE["balance"]
    monthly_revenue: int = DEFAULT_BASELINE_STATE["monthly_revenue"]
    monthly_expenses: int = DEFAULT_BASELINE_STATE["monthly_expenses"]
    users: int = DEFAULT_BASELINE_STATE["users"]
    growth_rate: float = DEFAULT_BASELINE_STATE["growth_rate"]
    churn_rate: float = DEFAULT_BASELINE_STATE["churn_rate"]
    product_quality: float = DEFAULT_BASELINE_STATE["product_quality"]
    brand_awareness: float = DEFAULT_BASELINE_STATE["brand_awareness"]
    team_morale: float = DEFAULT_BASELINE_STATE["team_morale"]
    headcount: int = DEFAULT_BASELINE_STATE["headcount"]
    debt: int = DEFAULT_BASELINE_STATE["debt"]
    turn: int = 1
    rng_seed: int = config.DEFAULT_SEED
    active_events: List[str] = field(default_factory=list)

    _INT_FIELDS: ClassVar[Iterable[str]] = (
        "balance",
        "monthly_revenue",
        "monthly_expenses",
        "users",
        "headcount",
        "debt",
    )
    _PERCENT_FIELDS: ClassVar[Mapping[str, float]] = {
        "product_quality": 100.0,
        "brand_awareness": 100.0,
        "team_morale": 100.0,
    }
    _RATE_FIELDS: ClassVar[Iterable[str]] = ("growth_rate", "churn_rate")

    def __post_init__(self) -> None:
        for field_name in self._INT_FIELDS:
            setattr(self, field_name, int(getattr(self, field_name)))
        if not isinstance(self.active_events, list):
            self.active_events = list(self.active_events)
        self.clamp_all()

    def clamp_all(self) -> None:
        """Clamp values to sensible bounds for the simulation."""

        for field_name in self._INT_FIELDS:
            value = getattr(self, field_name)
            if value < 0:
                setattr(self, field_name, 0)
        for field_name, maximum in self._PERCENT_FIELDS.items():
            value = getattr(self, field_name)
            if value < 0:
                value = 0.0
            if value > maximum:
                value = maximum
            setattr(self, field_name, value)
        for field_name in self._RATE_FIELDS:
            value = getattr(self, field_name)
            value = max(0.0, min(1.0, value))
            setattr(self, field_name, value)
        if self.turn < 0:
            self.turn = 0

    def compute_company_value(self) -> int:
        """Estimate the company value using a heuristic formula."""

        annual_revenue = self.monthly_revenue * 12
        annual_expenses = self.monthly_expenses * 12
        base_value = int(self.balance + annual_revenue * config.REVENUE_GROWTH_WEIGHT)
        expense_penalty = int(annual_expenses * config.EXPENSE_GROWTH_WEIGHT)
        qualitative_score = (self.product_quality + self.brand_awareness + self.team_morale) / 3
        qualitative_bonus = int(qualitative_score * 1_000)
        debt_penalty = max(0, self.debt)
        value = base_value - expense_penalty + qualitative_bonus - debt_penalty
        return max(0, value)

    def recompute_runway(self) -> int:
        """Recalculate and return the months of runway based on current burn."""

        if self.monthly_expenses <= 0:
            return 0
        return max(0, self.balance // self.monthly_expenses)

    def apply_deltas(self, deltas: Mapping[str, int | float]) -> None:
        """Apply a batch of changes to the startup state."""

        for key, delta in deltas.items():
            if not hasattr(self, key):
                raise KeyError(f"Unknown startup attribute: {key}")
            if key == "active_events":
                raise ValueError("Cannot apply numeric delta to active_events list.")
            current = getattr(self, key)
            if isinstance(current, list):  # pragma: no cover - safeguard
                raise ValueError(f"Cannot apply numeric delta to list field '{key}'.")
            new_value = current + delta  # type: ignore[operator]
            if key in self._INT_FIELDS:
                new_value = int(round(new_value))
            setattr(self, key, new_value)
        self.clamp_all()

    def snapshot(self) -> Dict[str, Any]:
        """Return a serialisable snapshot of the startup state."""

        return {
            "balance": self.balance,
            "monthly_revenue": self.monthly_revenue,
            "monthly_expenses": self.monthly_expenses,
            "users": self.users,
            "growth_rate": self.growth_rate,
            "churn_rate": self.churn_rate,
            "product_quality": self.product_quality,
            "brand_awareness": self.brand_awareness,
            "team_morale": self.team_morale,
            "headcount": self.headcount,
            "debt": self.debt,
            "turn": self.turn,
            "rng_seed": self.rng_seed,
            "active_events": list(self.active_events),
        }

    @classmethod
    def from_snapshot(cls, data: Mapping[str, Any]) -> "Startup":
        """Recreate a :class:`Startup` instance from saved data."""

        defaults = cls()
        keys = (
            "balance",
            "monthly_revenue",
            "monthly_expenses",
            "users",
            "growth_rate",
            "churn_rate",
            "product_quality",
            "brand_awareness",
            "team_morale",
            "headcount",
            "debt",
            "turn",
            "rng_seed",
        )
        kwargs = {key: data.get(key, getattr(defaults, key)) for key in keys}
        for field_name in defaults._INT_FIELDS:
            if field_name in kwargs:
                kwargs[field_name] = int(kwargs[field_name])
        instance = cls(**kwargs)
        events = data.get("active_events") or []
        instance.active_events = list(events)
        instance.clamp_all()
        return instance


__all__ = ["Startup", "DEFAULT_BASELINE_STATE"]

