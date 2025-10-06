from __future__ import annotations

from startup_simulator.config import EXPENSE_GROWTH_WEIGHT, REVENUE_GROWTH_WEIGHT
from startup_simulator.startup import Startup


def test_compute_company_value_matches_formula() -> None:
    startup = Startup(
        balance=200_000,
        monthly_revenue=50_000,
        monthly_expenses=20_000,
        product_quality=80.0,
        brand_awareness=60.0,
        team_morale=90.0,
        debt=100_000,
    )

    annual_revenue = startup.monthly_revenue * 12
    annual_expenses = startup.monthly_expenses * 12
    expected_base = int(startup.balance + annual_revenue * REVENUE_GROWTH_WEIGHT)
    expected_penalty = int(annual_expenses * EXPENSE_GROWTH_WEIGHT)
    qualitative_score = (startup.product_quality + startup.brand_awareness + startup.team_morale) / 3
    qualitative_bonus = int(qualitative_score * 1_000)
    expected_value = expected_base - expected_penalty + qualitative_bonus - max(0, startup.debt)

    assert startup.compute_company_value() == max(0, expected_value)


def test_compute_company_value_clamps_to_zero() -> None:
    startup = Startup(
        balance=0,
        monthly_revenue=0,
        monthly_expenses=100_000,
        product_quality=0.0,
        brand_awareness=0.0,
        team_morale=0.0,
        debt=2_000_000,
    )

    assert startup.compute_company_value() == 0
