"""Command line interface entry point for Startup Simulator."""

from __future__ import annotations

import argparse
from pathlib import Path

from startup_simulator.game import StartupSimulator


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="Play Startup Simulator (FinTech Edition).")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for deterministic runs.",
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).parent / "data",
        help="Path to game data files.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the Startup Simulator application."""

    args = parse_args()
    simulator = StartupSimulator(args.data_path, seed=args.seed)
    try:
        simulator.run()
    except KeyboardInterrupt:
        print("\nSession ended by user.")


if __name__ == "__main__":
    main()
