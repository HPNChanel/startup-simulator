from __future__ import annotations

import random

from startup_simulator import actions
from startup_simulator.startup import Startup
from startup_simulator.tests.utils import PatchManager, expect_raises


def test_list_actions_filters_unaffordable() -> None:
    affordable = actions.Action(
        id="affordable",
        name="Affordable",
        narrative="",
        costs={"balance": 1_000},
        effects={},
    )
    pricey = actions.Action(
        id="pricey",
        name="Pricey",
        narrative="",
        costs={"balance": 10_000},
        effects={},
    )
    registry = {action.id: action for action in (affordable, pricey)}

    with PatchManager() as patches:
        patches.setattr(actions, "ACTION_REGISTRY", registry)
        available = actions.list_actions(Startup(balance=5_000))

    assert [action.name for action in available] == ["Affordable"]


def test_apply_action_deducts_cost_and_clamps() -> None:
    action = actions.Action(
        id="clamp_test",
        name="Clamp Test",
        narrative="Testing narrative.",
        costs={"balance": 500},
        effects={"product_quality": 150.0},
    )
    with PatchManager() as patches:
        patches.setattr(actions, "ACTION_REGISTRY", {action.id: action})
        state = Startup(balance=1_000, product_quality=80.0)
        updated, narrative = actions.apply_action(state, "clamp_test", random.Random(1))

    assert updated.balance == 500
    assert updated.product_quality == 100.0
    assert narrative == "Testing narrative."


def test_apply_action_handles_risk_success() -> None:
    risky = actions.Action(
        id="risky",
        name="Risky",
        narrative="Taking a risk.",
        costs={},
        effects={"brand_awareness": 1.0},
        risk={
            "success_chance": 0.99,
            "success": {
                "effects": {"balance": 5_000},
                "narrative": "It works!",
            },
            "failure": {
                "effects": {"team_morale": -10.0},
                "narrative": "It fails.",
            },
        },
    )
    with PatchManager() as patches:
        patches.setattr(actions, "ACTION_REGISTRY", {risky.id: risky})
        state = Startup(balance=100)
        rng = random.Random(1234)
        updated, narrative = actions.apply_action(state, "risky", rng)

    assert updated.balance == 5_100
    assert updated.brand_awareness > 1.0
    assert "It works!" in narrative


def test_apply_action_handles_risk_failure() -> None:
    risky = actions.Action(
        id="risky_fail",
        name="Risky Fail",
        narrative="Attempting something bold.",
        costs={},
        effects={},
        risk={
            "success_chance": 0.5,
            "success": {
                "effects": {"balance": 5_000},
            },
            "failure": {
                "effects": {"team_morale": -5.0},
                "narrative": "It fails badly.",
            },
        },
    )
    with PatchManager() as patches:
        patches.setattr(actions, "ACTION_REGISTRY", {risky.id: risky})
        state = Startup(team_morale=50.0)
        updated, narrative = actions.apply_action(state, "risky_fail", random.Random(1234))

    assert updated.team_morale == 45.0
    assert narrative.endswith("It fails badly.")


def test_unknown_action_raises() -> None:
    with expect_raises(ValueError, "Unknown action id: does_not_exist"):
        actions.apply_action(Startup(), "does_not_exist", random.Random(0))


def test_validate_action_limit() -> None:
    limited = actions.Action(
        id="limited",
        name="Limited",
        narrative="",
        costs={},
        effects={},
        max_per_turn=1,
    )

    actions.validate_action_limit({"limited": 0}, limited)

    with expect_raises(ValueError):
        actions.validate_action_limit({"limited": 1}, limited)

    with expect_raises(ValueError):
        actions.validate_action_limit({"limited": 0, "other": 3}, limited, max_actions=1)
