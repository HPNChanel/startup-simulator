"""Entry point for the Startup Simulator CLI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

if __package__ in {None, ""}:  # pragma: no cover - convenience for script execution
    import sys

    package_root = Path(__file__).resolve().parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    from startup_simulator import actions, config, events, player, save_system, startup, ui_text
else:  # pragma: no cover
    from . import actions, config, events, player, save_system, startup, ui_text


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the CLI."""
    parser = argparse.ArgumentParser(description="Run the Startup Simulator prototype.")
    parser.add_argument("--seed", type=int, default=config.DEFAULT_SEED, help="Random seed to initialise the run.")
    parser.add_argument(
        "--autosave",
        action="store_true",
        help="Enable autosave using the configured save filename.",
    )
    return parser.parse_args()


def load_startup_profile() -> Dict[str, Any]:
    """Load the default startup profile from disk."""
    profile_path = config.DATA_DIRECTORY / "startup_profiles.json"
    with profile_path.open("r", encoding="utf-8") as handle:
        profiles = json.load(handle)
    return profiles[0]


def initialise_player(profile: Dict[str, Any]) -> player.PlayerState:
    """Create a player state using the provided startup profile."""
    state = player.PlayerState(name=profile["name"])
    for metric_name, value in profile.get("metrics", {}).items():
        state.metrics[metric_name] = player.Metric(metric_name, float(value))
    return state


def run() -> None:
    """Run the minimal CLI loop."""
    args = parse_args()
    title_banner = ui_text.banner(config.GAME_TITLE)
    print(title_banner)
    profile = load_startup_profile()
    state = initialise_player(profile)

    dummy_startup = startup.Startup()
    available_actions = actions.list_actions(dummy_startup)
    available_events = events.load_events()

    print(f"Loaded profile: {state.name}")
    print("Available actions:")
    print(ui_text.format_menu(action.name for action in available_actions))
    print("\nPotential events:")
    print(ui_text.format_menu(event.name for event in available_events))

    if args.autosave:
        save_system.save_state({"player": state.name, "seed": args.seed})
        print(f"Game state autosaved to {config.AUTOSAVE_FILENAME}.")

    print("\nThank you for trying the Startup Simulator prototype!")


def main() -> None:
    """Module entry point when executed as a script."""
    run()


if __name__ == "__main__":
    main()
