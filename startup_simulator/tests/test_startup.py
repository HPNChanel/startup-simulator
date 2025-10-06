from __future__ import annotations

from startup_simulator import config
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

    weights = config.COMPANY_VALUE_WEIGHTS
    annual_revenue = startup.monthly_revenue * 12
    revenue_component = annual_revenue * weights["revenue"]
    market_share_component = startup.users * weights["market_share"]
    reputation_score = (startup.product_quality + startup.brand_awareness + startup.team_morale) / 3
    reputation_component = reputation_score * weights["reputation"]
    team_component = startup.headcount * weights["team_size"]
    bug_penalty = startup.bug_rate * weights["bug_rate"]
    expense_penalty = startup.monthly_expenses * 12 * config.COMPANY_EXPENSE_WEIGHT
    expected_value = (
        startup.balance
        + revenue_component
        + market_share_component
        + reputation_component
        + team_component
        + bug_penalty
        - expense_penalty
        - max(0, startup.debt)
    )

    assert startup.compute_company_value() == max(0, int(round(expected_value)))


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
