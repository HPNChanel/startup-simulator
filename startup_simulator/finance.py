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


def compute_runway(balance: int, expenses: int) -> int:
    """Return the number of whole months the balance can cover expenses.

    Assumptions:
        * ``expenses`` represents the monthly cash outflow only (no revenue).
        * Non-positive expenses are treated as zero, yielding infinite runway,
          which is represented as ``0`` months to signal "no burn".
        * The runway is reported in whole months using integer arithmetic.

    Args:
        balance: Current cash on hand.
        expenses: Expected monthly expenses.

    Returns:
        The number of full months the current balance can sustain the expenses.
    """

    normalized_expenses = max(0, expenses)
    if normalized_expenses == 0:
        return 0
    normalized_balance = max(0, balance)
    return normalized_balance // normalized_expenses


def apply_monthly_finances(balance: int, revenue: int, expenses: int) -> int:
    """Return the new balance after applying a month's revenue and expenses.

    Assumptions:
        * Expenses that are zero or negative are treated as zero.
        * Revenue can be negative to represent refunds or losses.

    Args:
        balance: Current cash on hand.
        revenue: Money earned during the month.
        expenses: Money spent during the month.

    Returns:
        The resulting balance after the financial movements.
    """

    normalized_expenses = max(0, expenses)
    return balance + revenue - normalized_expenses


def projected_burn(balance: int, expenses: int, months: int) -> int:
    """Estimate the cash consumed over a number of months.

    Assumptions:
        * Expenses are constant for each month and non-positive values are
          treated as zero.
        * The burn cannot exceed the available balance; excess expenses are
          capped at the current balance.
        * Months less than or equal to zero result in zero burn.

    Args:
        balance: Current cash on hand.
        expenses: Expected monthly expenses.
        months: Number of months to project.

    Returns:
        The projected amount of cash consumed over the specified period.
    """

    normalized_months = max(0, months)
    if normalized_months == 0:
        return 0

    normalized_balance = max(0, balance)
    normalized_expenses = max(0, expenses)
    total_burn = normalized_expenses * normalized_months
    return min(normalized_balance, total_burn)


def adjust_expenses_for_regulation(expenses: int, severity: int) -> int:
    """Adjust expenses based on regulation severity expressed as a percentage.

    Assumptions:
        * ``severity`` represents a percentage change where positive values
          increase expenses and negative values decrease them.
        * Expenses are clamped at zero after adjustment to avoid negative
          operating costs.
        * Integer arithmetic is used, so percentage effects are floored.

    Args:
        expenses: Baseline monthly expenses before regulation.
        severity: Regulatory impact as a percentage (e.g., ``10`` for +10%).

    Returns:
        The adjusted expense value after applying the regulatory impact.
    """

    normalized_expenses = max(0, expenses)
    adjustment = (normalized_expenses * severity) // 100
    adjusted = normalized_expenses + adjustment
    return max(0, adjusted)


__all__ = [
    "FinancialSnapshot",
    "calculate_runway",
    "project_growth",
    "compute_runway",
    "apply_monthly_finances",
    "projected_burn",
    "adjust_expenses_for_regulation",
]
