"""Text formatting helpers for the command line interface.

The functions in this module only ever return strings. They do not mutate
state or perform any input/output which keeps them safe to use when composing
larger CLI flows. Formatting aims to stay within a typical terminal width and
leans on :mod:`textwrap` for wrapping narrative paragraphs.
"""
from __future__ import annotations

import textwrap
from typing import Iterable, Mapping

from . import config
from .actions import Action
from .startup import Startup


_CURRENCY_FIELDS = {
    "balance",
    "monthly_revenue",
    "monthly_expenses",
    "company_value",
    "debt",
}
_PERCENT_FIELDS = {"growth_rate", "churn_rate"}
_SCORE_FIELDS = {"product_quality", "brand_awareness", "team_morale"}
_INT_FIELDS = {"users", "headcount", "turn"}


def _label_for(field: str) -> str:
    """Return a human-friendly label for a field name."""

    overrides = {
        "monthly_revenue": "Monthly Revenue",
        "monthly_expenses": "Monthly Expenses",
        "product_quality": "Product Quality",
        "brand_awareness": "Brand Awareness",
        "team_morale": "Team Morale",
        "company_value": "Company Value",
    }
    if field in overrides:
        return overrides[field]
    return field.replace("_", " ").title()


def _format_currency(value: float | int) -> str:
    sign = "-" if value < 0 else ""
    amount = abs(int(round(value)))
    return f"{sign}${amount:,}"


def _format_percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def _format_score(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value))}"
    return f"{value:.1f}"


def _format_value(field: str, value: float | int) -> str:
    """Format *value* appropriately for the given *field* name."""

    if field in _CURRENCY_FIELDS:
        return _format_currency(value)
    if field in _PERCENT_FIELDS:
        return _format_percentage(float(value))
    if field in _SCORE_FIELDS:
        return _format_score(float(value))
    if field in _INT_FIELDS:
        return f"{int(round(value)):,}"
    if isinstance(value, float) and abs(value - round(value)) < 1e-9:
        return f"{int(round(value))}"
    return f"{value}"


def _format_delta(field: str, amount: float | int, *, invert: bool = False) -> str:
    """Return a signed delta string for a metric change."""

    numeric = float(amount)
    if invert:
        numeric = -numeric
    sign = "+" if numeric > 0 else ""  # negative numbers already contain '-'
    value = _format_value(field, numeric)
    return f"{sign}{value} {_label_for(field)}"


def render_title() -> str:
    """Return the main title banner for the CLI."""

    title = config.GAME_TITLE
    bar = "=" * len(title)
    tagline = textwrap.fill(
        "Guide your fledgling company through funding, growth, and tough "
        "decisions one turn at a time.",
        width=80,
    )
    return f"{bar}\n{title}\n{bar}\n{tagline}"


def render_dashboard(startup: Startup) -> str:
    """Create a tabular overview of the startup state."""

    metrics = {
        "turn": startup.turn,
        "balance": startup.balance,
        "monthly_revenue": startup.monthly_revenue,
        "monthly_expenses": startup.monthly_expenses,
        "users": startup.users,
        "growth_rate": startup.growth_rate,
        "churn_rate": startup.churn_rate,
        "product_quality": startup.product_quality,
        "brand_awareness": startup.brand_awareness,
        "team_morale": startup.team_morale,
        "headcount": startup.headcount,
        "debt": startup.debt,
        "company_value": startup.compute_company_value(),
    }

    formatted_items = [
        ("Turn", _format_value("turn", metrics["turn"])),
        ("Balance", _format_value("balance", metrics["balance"])),
        ("Monthly Revenue", _format_value("monthly_revenue", metrics["monthly_revenue"])),
        ("Monthly Expenses", _format_value("monthly_expenses", metrics["monthly_expenses"])),
        ("Company Value", _format_value("company_value", metrics["company_value"])),
        ("Runway", f"{startup.recompute_runway()} months"),
        ("Users", _format_value("users", metrics["users"])),
        ("Growth Rate", _format_value("growth_rate", metrics["growth_rate"])),
        ("Churn Rate", _format_value("churn_rate", metrics["churn_rate"])),
        ("Product Quality", _format_value("product_quality", metrics["product_quality"])),
        ("Brand Awareness", _format_value("brand_awareness", metrics["brand_awareness"])),
        ("Team Morale", _format_value("team_morale", metrics["team_morale"])),
        ("Headcount", _format_value("headcount", metrics["headcount"])),
        ("Debt", _format_value("debt", metrics["debt"])),
    ]

    label_width = max(len(label) for label, _ in formatted_items)
    value_width = max(len(value) for _, value in formatted_items)
    header = "Company Dashboard"
    bar = "-" * max(len(header), label_width + value_width + 3)

    lines = [header, bar]
    for label, value in formatted_items:
        lines.append(f"{label:<{label_width}} : {value:>{value_width}}")
    return "\n".join(lines)


def render_events(narratives: list[str]) -> str:
    """Return a formatted list of recent event narratives."""

    if not narratives:
        return "No new events this turn."

    wrapped = []
    for narrative in narratives:
        paragraph = textwrap.fill(
            narrative,
            width=80,
            initial_indent="  • ",
            subsequent_indent="    ",
        )
        wrapped.append(paragraph)
    return "\n".join(["Recent Events:"] + wrapped)


def _format_changes(changes: Mapping[str, float | int], *, invert: bool = False) -> str:
    """Format a mapping of metric deltas for menu display."""

    if not changes:
        return "None"
    parts = [_format_delta(field, amount, invert=invert) for field, amount in changes.items()]
    return "; ".join(parts)


def render_actions_menu(actions: list[Action]) -> str:
    """Format an action selection menu for the CLI."""

    if not actions:
        return "No actions are currently available."

    lines = ["Available Actions:"]
    for index, action in enumerate(actions, start=1):
        lines.append(f"{index}. {action.name}")
        if action.narrative:
            lines.append(
                textwrap.fill(
                    action.narrative,
                    width=80,
                    initial_indent="    ",
                    subsequent_indent="    ",
                )
            )
        if action.costs:
            lines.append(f"    Cost: {_format_changes(action.costs, invert=True)}")
        else:
            lines.append("    Cost: None")
        if action.effects:
            lines.append(f"    Effects: {_format_changes(action.effects)}")
        else:
            lines.append("    Effects: None")
        if action.max_per_turn is not None:
            lines.append(f"    Limit: {action.max_per_turn} per turn")
        if action.risk and "success_chance" in action.risk:
            chance = action.risk["success_chance"]
            chance_line = f"    Risk: {chance * 100:.0f}% success chance"
            lines.append(chance_line)
        lines.append("")
    return "\n".join(lines).rstrip()


def prompt_choose_actions(max_actions: int) -> str:
    """Return the instruction prompt for choosing actions."""

    if max_actions <= 0:
        max_actions = 1
    plural = "s" if max_actions != 1 else ""
    instruction = (
        f"Choose up to {max_actions} action{plural} by typing their numbers separated by commas. "
        "Press Enter to continue without taking further actions."
    )
    return textwrap.fill(instruction, width=80)


def format_menu(options: Iterable[str]) -> str:
    """Return a formatted menu string from the provided options."""

    lines = [f" - {option}" for option in options]
    return "\n".join(lines)


def banner(title: str) -> str:
    """Create a simple banner for the CLI display."""

    bar = "=" * len(title)
    return f"{bar}\n{title}\n{bar}"


__all__ = [
    "render_title",
    "render_dashboard",
    "render_events",
    "render_actions_menu",
    "prompt_choose_actions",
    "format_menu",
    "banner",
]

