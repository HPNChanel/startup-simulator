"""Finance helpers for the Startup Simulator."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FinancialSnapshot:
    """Represents a snapshot of company finances for a single month."""

    revenue: float
    expenses: float

    @property
    def burn(self) -> float:
        """Return the monthly cash burn (expenses minus revenue)."""
        return max(0.0, self.expenses - self.revenue)

    @property
    def net(self) -> float:
        """Return the net cash movement for the month."""
        return self.revenue - self.expenses


def calculate_runway(cash_on_hand: float, monthly_burn: float) -> float:
    """Compute how many months of runway remain given current burn."""
    if monthly_burn <= 0:
        return float("inf")
    return cash_on_hand / monthly_burn


def project_growth(amount: float, weight: float) -> float:
    """Apply a simple growth projection used for revenue or expenses."""
    return amount * weight


__all__ = ["FinancialSnapshot", "calculate_runway", "project_growth"]
