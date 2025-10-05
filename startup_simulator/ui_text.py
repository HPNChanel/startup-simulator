"""Text helpers for presenting information in the CLI."""
from __future__ import annotations

from typing import Iterable


def format_menu(options: Iterable[str]) -> str:
    """Return a formatted menu string from the provided options."""
    lines = [f" - {option}" for option in options]
    return "\n".join(lines)


def banner(title: str) -> str:
    """Create a simple banner for the CLI display."""
    bar = "=" * len(title)
    return f"{bar}\n{title}\n{bar}"


__all__ = ["format_menu", "banner"]
