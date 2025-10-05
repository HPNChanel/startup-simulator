"""Configuration constants for the Startup Simulator package."""
from __future__ import annotations

from pathlib import Path

# General simulation configuration
GAME_TITLE: str = "Startup Simulator"
DEFAULT_SEED: int = 42
AUTOSAVE_FILENAME: str = "save.json"
DATA_DIRECTORY: Path = Path(__file__).resolve().parent / "data"
SAVE_SCHEMA_VERSION: str = "1.0"

# Financial tuning parameters
DEFAULT_STARTING_FUNDS: float = 500_000.0
MONTHLY_BURN_CAP: float = 120_000.0
REVENUE_GROWTH_WEIGHT: float = 1.1
EXPENSE_GROWTH_WEIGHT: float = 1.05

# Gameplay
MAX_ACTIONS_PER_TURN: int = 2
EVENT_PROBABILITY_WEIGHT: float = 0.35

__all__ = [
    "GAME_TITLE",
    "DEFAULT_SEED",
    "AUTOSAVE_FILENAME",
    "DATA_DIRECTORY",
    "SAVE_SCHEMA_VERSION",
    "DEFAULT_STARTING_FUNDS",
    "MONTHLY_BURN_CAP",
    "REVENUE_GROWTH_WEIGHT",
    "EXPENSE_GROWTH_WEIGHT",
    "MAX_ACTIONS_PER_TURN",
    "EVENT_PROBABILITY_WEIGHT",
]
