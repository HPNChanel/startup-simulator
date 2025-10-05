"""Tests for the finance helpers."""
from __future__ import annotations

from startup_simulator.finance import FinancialSnapshot, calculate_runway, project_growth


def test_financial_snapshot_properties() -> None:
    snapshot = FinancialSnapshot(revenue=30_000, expenses=50_000)
    assert snapshot.burn == 20_000
    assert snapshot.net == -20_000


def test_calculate_runway_handles_zero_burn() -> None:
    assert calculate_runway(100_000, 0) == float("inf")


def test_project_growth() -> None:
    assert project_growth(1000, 1.2) == 1200
