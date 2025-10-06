"""Central configuration for Startup Simulator balancing and persistence.

Designers can safely tweak the values in this module to rebalance the game
without touching the gameplay code. Whenever you adjust a knob here the rest
of the codebase will automatically pick up the change the next time the game
runs. A few guidelines when editing:

* Keep numeric ranges consistent. For example, if you raise the cap for
  ``product_quality`` in :data:`STARTUP_PERCENT_BOUNDS`, consider adjusting
  related UI copy or event logic that references high quality scores.
* Company valuation multipliers in :data:`COMPANY_VALUE_WEIGHTS` directly
  influence how different aspects of the startup contribute to its heuristic
  valuation. Increase a weight to make that component matter more, decrease it
  to reduce its influence. ``bug_rate`` should remain negative so higher bug
  rates continue to penalise the valuation.
* ``ACTION_LIMIT_RANGE`` defines the hard clamp the simulator will apply to any
  per-turn action limit, regardless of whether it comes from designer authored
  content or command line overrides.

All constants exposed here are imported by other modules; renaming them will
require updating the associated imports.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

# ---------------------------------------------------------------------------
# Core file paths and persistence knobs
# ---------------------------------------------------------------------------

GAME_TITLE: str = "Startup Simulator"
DEFAULT_SEED: int = 42

DATA_DIRECTORY: Path = Path(__file__).resolve().parent / "data"
AUTOSAVE_FILENAME: str = "save.json"
SAVE_SCHEMA_VERSION: str = "1.0"
DEFAULT_SAVE_PATH: Path = Path(AUTOSAVE_FILENAME)

# ---------------------------------------------------------------------------
# Economy and gameplay pacing
# ---------------------------------------------------------------------------

DEFAULT_STARTING_FUNDS: float = 500_000.0
MONTHLY_BURN_CAP: float = 120_000.0

DEFAULT_ACTIONS_PER_TURN: int = 2
# Designers can expand the action range, but values below 1 make the game
# unwinnable and values above ~5 tend to trivialise encounters.
ACTION_LIMIT_RANGE: tuple[int, int] = (1, 3)

EVENT_PROBABILITY_WEIGHT: float = 0.35

# ---------------------------------------------------------------------------
# Optional monthly economy variance
# ---------------------------------------------------------------------------

# Set ``ECONOMY_TICK_ENABLED`` to ``True`` to introduce a gentle amount of
# variance to the simulated economy at the start of each month. Designers can
# fine-tune the magnitude of the effect using the percentage ranges below. The
# jitter is applied multiplicatively, so values represent +/- percentage
# adjustments. Keeping the range small (well under 5%) is recommended to avoid
# destabilising the balancing tuned for the deterministic economy.
ECONOMY_TICK_ENABLED: bool = False
ECONOMY_TICK_REVENUE_VARIANCE: tuple[float, float] = (-0.01, 0.015)
ECONOMY_TICK_EXPENSE_VARIANCE: tuple[float, float] = (-0.008, 0.012)

# ---------------------------------------------------------------------------
# Generic numeric ranges used for clamping
# ---------------------------------------------------------------------------

PROBABILITY_RANGE: tuple[float, float] = (0.0, 1.0)
METRIC_VALUE_RANGE: tuple[float, float] = (0.0, 100.0)

STARTUP_INT_BOUNDS: Mapping[str, tuple[int, int | None]] = {
    "balance": (0, None),
    "monthly_revenue": (0, None),
    "monthly_expenses": (0, None),
    "users": (0, None),
    "headcount": (0, None),
    "debt": (0, None),
    "turn": (0, None),
}

STARTUP_PERCENT_BOUNDS: Mapping[str, tuple[float, float]] = {
    "product_quality": (0.0, 100.0),
    "brand_awareness": (0.0, 100.0),
    "team_morale": (0.0, 100.0),
}

STARTUP_RATE_BOUNDS: Mapping[str, tuple[float, float]] = {
    "growth_rate": (0.0, 1.0),
    "churn_rate": (0.0, 1.0),
}

STARTUP_INT_FIELDS: tuple[str, ...] = tuple(STARTUP_INT_BOUNDS.keys())

# ---------------------------------------------------------------------------
# Company valuation tuning
# ---------------------------------------------------------------------------

COMPANY_VALUE_WEIGHTS: Mapping[str, float] = {
    "revenue": 1.1,
    "market_share": 30.0,
    "reputation": 1_000.0,
    "team_size": 2_000.0,
    "bug_rate": -200_000.0,
}
COMPANY_EXPENSE_WEIGHT: float = 1.05

# ---------------------------------------------------------------------------
# Public export surface
# ---------------------------------------------------------------------------

__all__ = [
    "GAME_TITLE",
    "DEFAULT_SEED",
    "DATA_DIRECTORY",
    "AUTOSAVE_FILENAME",
    "SAVE_SCHEMA_VERSION",
    "DEFAULT_SAVE_PATH",
    "DEFAULT_STARTING_FUNDS",
    "MONTHLY_BURN_CAP",
    "DEFAULT_ACTIONS_PER_TURN",
    "ACTION_LIMIT_RANGE",
    "EVENT_PROBABILITY_WEIGHT",
    "ECONOMY_TICK_ENABLED",
    "ECONOMY_TICK_REVENUE_VARIANCE",
    "ECONOMY_TICK_EXPENSE_VARIANCE",
    "PROBABILITY_RANGE",
    "METRIC_VALUE_RANGE",
    "STARTUP_INT_BOUNDS",
    "STARTUP_PERCENT_BOUNDS",
    "STARTUP_RATE_BOUNDS",
    "STARTUP_INT_FIELDS",
    "COMPANY_VALUE_WEIGHTS",
    "COMPANY_EXPENSE_WEIGHT",
]
