"""Lightweight ANSI helpers for CLI output."""
from __future__ import annotations

import sys
from dataclasses import dataclass
_RESET = "\033[0m"


@dataclass
class TerminalFormatter:
    """Apply minimal ANSI styling when supported."""

    enabled: bool = False

    def configure(self, *, enabled: bool | None = None) -> None:
        """Update the colour output setting."""

        if enabled is None:
            stream = sys.stdout
            enabled = bool(getattr(stream, "isatty", lambda: False)())
        self.enabled = bool(enabled)

    def _wrap(self, text: str, code: str) -> str:
        if not text or not self.enabled:
            return text
        return f"{code}{text}{_RESET}"

    def title(self, text: str) -> str:
        """Style a prominent title block."""

        return self._wrap(text, "\033[95m")

    def header(self, text: str) -> str:
        """Style a section header."""

        return self._wrap(text, "\033[94m")

    def warning(self, text: str) -> str:
        """Style warning or cautionary messages."""

        return self._wrap(text, "\033[93m")


FORMATTER = TerminalFormatter()
FORMATTER.configure()


def configure_color(enabled: bool) -> None:
    """Enable or disable colour output globally."""

    FORMATTER.configure(enabled=enabled)


def title(text: str) -> str:
    return FORMATTER.title(text)


def header(text: str) -> str:
    return FORMATTER.header(text)


def warning(text: str) -> str:
    return FORMATTER.warning(text)


__all__ = ["FORMATTER", "configure_color", "header", "title", "warning"]
