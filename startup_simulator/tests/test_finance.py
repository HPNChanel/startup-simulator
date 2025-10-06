"""Tests for the finance helpers."""
from __future__ import annotations

from startup_simulator.finance import (
    FinancialSnapshot,
    apply_monthly_finances,
    calculate_runway,
    compute_runway,
    project_growth,
)


def test_financial_snapshot_properties() -> None:
    snapshot = FinancialSnapshot(revenue=30_000, expenses=50_000)
    assert snapshot.burn == 20_000
    assert snapshot.net == -20_000


def test_calculate_runway_handles_zero_burn() -> None:
    assert calculate_runway(100_000, 0) == float("inf")


def test_project_growth() -> None:
    assert project_growth(1000, 1.2) == 1200


def test_compute_runway_edge_cases() -> None:
    assert compute_runway(25_000, 5_000) == 5
    assert compute_runway(9_999, 3_000) == 3
    assert compute_runway(10_000, 0) == 0
    assert compute_runway(10_000, -1_000) == 0
    assert compute_runway(-5_000, 2_000) == 0


def test_apply_monthly_finances_normalises_inputs() -> None:
    assert apply_monthly_finances(50_000, 10_000, 5_000) == 55_000
    assert apply_monthly_finances(50_000, -2_500, -10_000) == 47_500
    assert apply_monthly_finances(0, 0, 100_000) == -100_000
