"""Utility functions for Startup Simulator."""

from __future__ import annotations

from typing import Iterable, Optional
from textwrap import fill


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value between minimum and maximum."""

    return max(minimum, min(value, maximum))


def format_currency(value: float) -> str:
    """Format currency values for display."""

    return f"${value:,.0f}"


def format_percentage(value: float) -> str:
    """Format percentage values for display."""

    return f"{value:.1f}%"


def wrap_text(text: str, width: int = 70) -> str:
    """Wrap narrative text for terminal display."""

    return fill(text, width=width)


def join_and(items: Iterable[str]) -> str:
    """Join items with commas and an 'and'."""

    items_list = list(items)
    if not items_list:
        return ""
    if len(items_list) == 1:
        return items_list[0]
    return ", ".join(items_list[:-1]) + f" and {items_list[-1]}"


def parse_int(value: str) -> Optional[int]:
    """Parse an integer from a string if possible."""

    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None
