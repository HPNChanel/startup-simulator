"""Entry point for the Startup Simulator CLI."""
from __future__ import annotations

import argparse
import json
import random
import textwrap
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

if __package__ in {None, ""}:  # pragma: no cover - convenience for script execution
    import sys

    package_root = Path(__file__).resolve().parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    from startup_simulator import actions, config, events, finance, save_system, startup, ui_text
else:  # pragma: no cover
    from . import actions, config, events, finance, save_system, startup, ui_text


class SaveAndQuit(Exception):
    """Raised when the player requests to save and exit."""


class QuitWithoutSaving(Exception):
    """Raised when the player opts to exit without saving."""


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the CLI."""

    parser = argparse.ArgumentParser(description="Run the Startup Simulator prototype.")
    parser.add_argument(
        "--seed",
        type=int,
        default=config.DEFAULT_SEED,
        help="Random seed to initialise the run.",
    )
    parser.add_argument(
        "--autosave",
        action="store_true",
        help="Enable autosave using the configured save filename.",
    )
    return parser.parse_args()


def _load_startup_profiles() -> List[Dict[str, object]]:
    """Load available startup profiles from disk."""

    profile_path = config.DATA_DIRECTORY / "startup_profiles.json"
    with profile_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list) or not data:
        raise ValueError("startup_profiles.json must contain at least one profile entry.")
    return data


def _render_profile_menu(profiles: List[Dict[str, object]]) -> str:
    lines = ["Choose Your Founding Story:"]
    for index, profile in enumerate(profiles, start=1):
        name = str(profile.get("name", f"Profile {index}"))
        description = str(profile.get("description", ""))
        lines.append(f"{index}. {name}")
        if description:
            lines.append(
                textwrap.fill(
                    description,
                    width=80,
                    initial_indent="    ",
                    subsequent_indent="    ",
                )
            )
        lines.append("")
    lines.append("Press Enter to accept the default (option 1).")
    return "\n".join(lines).rstrip()


def choose_startup_profile() -> Dict[str, object]:
    """Prompt the player to select a startup profile."""

    profiles = _load_startup_profiles()
    print(_render_profile_menu(profiles))
    while True:
        choice = input("Selection: ").strip()
        if not choice:
            return profiles[0]
        if choice.lower() in {"s", "save"}:
            raise SaveAndQuit()
        if choice.lower() in {"q", "quit"}:
            raise QuitWithoutSaving()
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(profiles):
                return profiles[index - 1]
        print("Please enter a valid profile number, or press Enter for the default.")


def initialise_startup(profile: Dict[str, object], seed: int) -> startup.Startup:
    """Create a startup state from a profile definition."""

    instance = startup.Startup()
    metrics = profile.get("metrics")
    if isinstance(metrics, dict):
        for key, value in metrics.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
    instance.rng_seed = seed
    instance.clamp_all()
    return instance


def _render_action_prompt(max_actions: int) -> str:
    base = ui_text.prompt_choose_actions(max_actions)
    extra = (
        "Type 'S' to save & quit or 'Q' to exit without saving at any prompt."
    )
    return f"{base}\n{extra}"


def _parse_action_selection(raw: str, total: int) -> List[int]:
    """Parse a comma-separated list of menu choices."""

    if not raw:
        return []
    tokens = [token.strip() for token in raw.replace(";", ",").split(",") if token.strip()]
    indices: List[int] = []
    for token in tokens:
        if token.lower() in {"s", "save"}:
            raise SaveAndQuit()
        if token.lower() in {"q", "quit"}:
            raise QuitWithoutSaving()
        if token.isdigit():
            index = int(token)
            if 1 <= index <= total:
                indices.append(index)
                continue
        raise ValueError(f"'{token}' is not a valid selection.")
    return indices


def prompt_actions(available: List[actions.Action], max_actions: int) -> List[actions.Action]:
    """Prompt the player to select up to *max_actions* actions."""

    if not available:
        print("No actions are currently available. Press Enter to continue.")
        input("")
        return []

    print(ui_text.render_actions_menu(available))
    print(_render_action_prompt(max_actions))

    while True:
        raw = input("Actions: ").strip()
        try:
            indices = _parse_action_selection(raw, len(available))
        except ValueError as exc:
            print(exc)
            continue
        if len(indices) > max_actions:
            print(f"Please choose at most {max_actions} action(s).")
            continue
        # Preserve selection order but avoid exceeding per-action limits
        chosen: List[actions.Action] = []
        per_turn_counts: Counter[str] = Counter()
        for index in indices:
            action = available[index - 1]
            try:
                actions.validate_action_limit(per_turn_counts, action, max_actions=max_actions)
            except ValueError as exc:
                print(exc)
                break
            chosen.append(action)
            per_turn_counts[action.id] += 1
        else:
            return chosen


def _apply_actions(
    state: startup.Startup,
    selections: Iterable[actions.Action],
    rng: random.Random,
    max_actions: int | None = None,
) -> List[str]:
    """Apply the selected actions to the startup and return narratives."""

    narratives: List[str] = []
    per_turn_counts: Counter[str] = Counter()
    allowed_actions = max_actions if max_actions is not None else config.DEFAULT_ACTIONS_PER_TURN
    for action in selections:
        actions.validate_action_limit(per_turn_counts, action, max_actions=allowed_actions)
        per_turn_counts[action.id] += 1
        state, narrative = actions.apply_action(state, action.id, rng)
        if narrative:
            narratives.append(narrative)
    return narratives


def _check_endings(state: startup.Startup) -> tuple[str, str] | None:
    """Return an ending tuple of (title, description) if conditions are met."""

    if state.balance <= 0:
        return (
            "Bankruptcy",
            "Cash reserves have run dry and operations can no longer continue.",
        )
    if state.team_morale <= 5:
        return (
            "Team Walkout",
            "Morale collapsed and the remaining team resigned en masse.",
        )
    company_value = state.compute_company_value()
    if company_value >= 5_000_000 and state.brand_awareness >= 75:
        return (
            "Triumphant Exit",
            "Investors line up to acquire your thriving company at a stellar valuation.",
        )
    runway = state.recompute_runway()
    if runway <= 1 and state.monthly_expenses > state.monthly_revenue and state.balance < 25_000:
        return (
            "Out of Runway",
            "Runway has dwindled to nothing and additional funding could not be secured.",
        )
    if state.turn > 36:
        return (
            "IPO Ready",
            "Three years of steady execution culminate in a confident march towards an IPO.",
        )
    return None


def _print_turn_intro(state: startup.Startup) -> None:
    header = f"\n=== Month {state.turn} ==="
    print(header)
    print(ui_text.render_dashboard(state))


def _print_messages(title: str, messages: Iterable[str]) -> None:
    collected = [msg for msg in messages if msg]
    if not collected:
        return
    print(f"\n{title}")
    for message in collected:
        wrapped = textwrap.fill(message, width=80, subsequent_indent="    ")
        print(f"  • {wrapped}")


def run() -> None:
    """Run the main CLI loop."""

    args = parse_args()
    rng = random.Random(args.seed)

    print(ui_text.render_title())

    try:
        profile = choose_startup_profile()
    except SaveAndQuit:
        print("No game in progress to save. Exiting.")
        return
    except QuitWithoutSaving:
        print("Exiting without starting a new game.")
        return

    state = initialise_startup(profile, args.seed)
    minimum_limit, maximum_limit = config.ACTION_LIMIT_RANGE
    max_actions = max(minimum_limit, config.DEFAULT_ACTIONS_PER_TURN)
    if maximum_limit is not None:
        max_actions = min(maximum_limit, max_actions)

    print(f"\nYou selected: {profile.get('name', 'Unknown Startup')}")

    try:
        while True:
            _print_turn_intro(state)

            concluded = events.tick_active_events(state)
            _print_messages("Event Updates", concluded)

            state, triggered = events.maybe_trigger_event(state, rng)
            if triggered:
                _print_messages("New Events", triggered)

            available = actions.list_actions(state)
            try:
                selections = prompt_actions(available, max_actions)
            except SaveAndQuit:
                save_system.save_game(state)
                print(f"Game saved to {config.AUTOSAVE_FILENAME}. Goodbye!")
                return
            except QuitWithoutSaving:
                print("Exiting without saving. Goodbye!")
                return

            narratives = _apply_actions(state, selections, rng, max_actions=max_actions)
            _print_messages("Action Outcomes", narratives)

            state.balance = finance.apply_monthly_finances(
                state.balance, state.monthly_revenue, state.monthly_expenses
            )
            state.clamp_all()

            ending = _check_endings(state)
            if ending:
                title, description = ending
                print("\n=== Simulation Complete ===")
                print(f"Ending: {title}")
                print(textwrap.fill(description, width=80))
                print("\nFinal Company Snapshot:\n")
                print(ui_text.render_dashboard(state))
                if args.autosave:
                    save_system.save_game(state)
                    print(f"\nFinal state autosaved to {config.AUTOSAVE_FILENAME}.")
                return

            if args.autosave:
                save_system.save_game(state)
                print(f"Autosaved to {config.AUTOSAVE_FILENAME}.")

            state.turn += 1
    except KeyboardInterrupt:
        print("\nSession interrupted. Goodbye!")


def main() -> None:
    """Module entry point when executed as a script."""

    run()


if __name__ == "__main__":
    main()
