"""Core gameplay loop for Startup Simulator."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .data_loader import load_actions, load_events, load_profiles
from .models import (
    Action,
    ActiveEvent,
    Event,
    GameState,
    GameStats,
    SCHEMA_VERSION,
    StartupProfile,
    default_rng,
)
from .utils import clamp, format_currency, format_percentage, join_and, parse_int, wrap_text


STATS_RANGES = {
    "balance": (0.0, float("inf")),
    "revenue": (0.0, float("inf")),
    "expenses": (0.0, float("inf")),
    "product_level": (0.0, 10.0),
    "bug_rate": (0.0, 100.0),
    "team_size": (0.0, 500.0),
    "morale": (0.0, 100.0),
    "productivity": (0.0, 100.0),
    "reputation": (0.0, 100.0),
    "users": (0.0, float("inf")),
    "market_share": (0.0, 100.0),
}


class StartupSimulator:
    """Main application controller for the Startup Simulator."""

    def __init__(self, data_path: Path, seed: Optional[int] = None) -> None:
        self.data_path = data_path
        self.events = load_events(data_path / "events.json")
        self.actions = load_actions(data_path / "actions.json")
        self.profiles = load_profiles(data_path / "startup_profiles.json")
        self.events_by_id = {event.event_id: event for event in self.events}
        self.rng = default_rng(seed)
        self.state: Optional[GameState] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def new_game(self, profile: StartupProfile) -> None:
        """Start a new game with a chosen profile."""

        stats = self._create_stats_from_profile(profile)
        self.state = GameState(stats=stats, turn=1)
        self.state.rng_state = self.rng.getstate()
        self.state.last_report = [
            f"You begin your journey as {profile.name}.",
            profile.description,
        ]

    def load_game(self, path: Path) -> None:
        """Load a saved game."""

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported save file version.")
        state_data = payload["state"]
        state = GameState.from_dict(state_data, self.events_by_id)
        self.state = state
        rng_state = state.rng_state
        if rng_state:
            self.rng.setstate(rng_state)
        self._info("Game loaded successfully.")

    def save_game(self, path: Path) -> None:
        """Persist the current game state to disk."""

        if not self.state:
            raise ValueError("No active game to save.")
        self.state.rng_state = self.rng.getstate()
        payload = {
            "schema_version": SCHEMA_VERSION,
            "saved_at": dt.datetime.utcnow().isoformat(),
            "state": self.state.to_dict(),
        }
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        self._info(f"Game saved to {path}.")

    def run(self) -> None:
        """Run the CLI application."""

        while True:
            self._print_main_menu()
            choice = input("> ").strip().lower()
            if choice == "1":
                profile = self._choose_profile()
                if profile:
                    self.new_game(profile)
                    self._game_loop()
            elif choice == "2":
                path = self._prompt_path("Enter save file path to load: ")
                try:
                    self.load_game(path)
                    self._game_loop()
                except (FileNotFoundError, ValueError) as error:
                    self._info(str(error))
            elif choice == "q":
                self._info("Goodbye!")
                break
            else:
                self._info("Please choose a valid option.")

    # ------------------------------------------------------------------
    # Game loop
    # ------------------------------------------------------------------
    def _game_loop(self) -> None:
        assert self.state is not None
        while True:
            self._print_turn_header()
            self._print_last_report()
            self._process_active_events()
            self._trigger_random_event()
            if not self._choose_actions():
                break
            self._update_turn()
            ending = self._check_end_conditions()
            if ending:
                self._info(ending)
                break
            if not self._prompt_continue():
                break

    def _print_turn_header(self) -> None:
        assert self.state is not None
        print("\n" + "=" * 72)
        print(f"Month {self.state.turn}")
        print("=" * 72)

    def _print_last_report(self) -> None:
        assert self.state is not None
        if not self.state.last_report:
            return
        print("\nLast month's highlights:")
        for entry in self.state.last_report:
            print(f"- {wrap_text(entry)}")
        self.state.last_report.clear()

    def _process_active_events(self) -> None:
        assert self.state is not None
        ongoing_reports: List[str] = []
        still_active: List[ActiveEvent] = []
        for active in self.state.active_events:
            self._apply_deltas(active.event.deltas)
            ongoing_reports.append(
                f"Event: {active.event.name} persists ({active.remaining_turns} turns left)."
            )
            active.remaining_turns -= 1
            if active.remaining_turns > 0:
                still_active.append(active)
            else:
                if active.event.revert_deltas:
                    self._apply_deltas(active.event.revert_deltas)
                ongoing_reports.append(f"Event: {active.event.name} has ended.")
        self.state.active_events = still_active
        if ongoing_reports:
            self._print_event_block("Ongoing events", ongoing_reports)
            self.state.last_report.extend(ongoing_reports)

    def _trigger_random_event(self) -> None:
        assert self.state is not None
        shuffled_events = list(self.events)
        self.rng.shuffle(shuffled_events)
        for event in shuffled_events:
            if self._is_event_active(event.event_id):
                continue
            if self.rng.random() <= event.trigger_chance:
                self._apply_event(event)
                break

    def _is_event_active(self, event_id: str) -> bool:
        assert self.state is not None
        return any(active.event.event_id == event_id for active in self.state.active_events)

    def _apply_event(self, event: Event) -> None:
        assert self.state is not None
        self._apply_deltas(event.deltas)
        report_lines = [f"Event triggered: {event.name}", event.narrative]
        self.state.last_report.extend(report_lines)
        self._print_event_block("New event", report_lines)
        if event.duration > 1:
            self.state.active_events.append(
                ActiveEvent(event=event, remaining_turns=event.duration - 1)
            )

    def _choose_actions(self) -> bool:
        assert self.state is not None
        max_actions = 3
        min_actions = 1
        action_count = self._prompt_int(
            f"How many actions will you take this month? ({min_actions}-{max_actions}, 0 to save & exit): ",
            minimum=0,
            maximum=max_actions,
        )
        if action_count == 0:
            if self._prompt_save():
                self._info("Game saved. Returning to main menu.")
                return False
            self._info("Save unsuccessful. Continuing the current month.")
            return True
        for _ in range(action_count):
            action = self._prompt_action_choice()
            if not action:
                break
            self._execute_action(action)
        return True

    def _prompt_action_choice(self) -> Optional[Action]:
        assert self.state is not None
        print("\nChoose an action:")
        for index, action in enumerate(self.actions, start=1):
            print(f"  {index}. {action.name} - {action.description}")
            print(f"     Cost: {format_currency(action.cost)}")
        print("  0. Finish actions early")
        choice = self._prompt_int("Selection: ", minimum=0, maximum=len(self.actions))
        if choice == 0:
            return None
        return self.actions[choice - 1]

    def _execute_action(self, action: Action) -> None:
        assert self.state is not None
        if self.state.stats.balance < action.cost:
            self.state.last_report.append(
                f"Insufficient balance for {action.name}. Action skipped."
            )
            return
        self.state.stats.balance -= action.cost
        self._apply_deltas(action.effects)
        report_entries = [f"Action taken: {action.name}"]
        if action.effects:
            effect_list = self._describe_effects(action.effects)
            if effect_list:
                report_entries.append(f"Effects: {effect_list}.")
        if action.risk:
            outcome = self.rng.random()
            if outcome <= action.risk.success_chance:
                self._apply_deltas(action.risk.success_effects)
                report_entries.append(action.risk.success_narrative)
            else:
                self._apply_deltas(action.risk.failure_effects)
                report_entries.append(action.risk.failure_narrative)
        self.state.last_report.extend(report_entries)

    def _describe_effects(self, effects: Dict[str, float]) -> str:
        parts: List[str] = []
        for key, value in effects.items():
            if key in {"balance", "revenue", "expenses"}:
                prefix = "+" if value >= 0 else "-"
                formatted = f"{prefix}{format_currency(abs(value))}"
            elif key in {"market_share", "bug_rate", "morale", "productivity", "reputation"}:
                prefix = "+" if value >= 0 else "-"
                formatted = f"{prefix}{format_percentage(abs(value))}"
            elif key == "users":
                prefix = "+" if value >= 0 else "-"
                formatted = f"{prefix}{abs(int(value)):,} users"
            elif key == "team_size":
                formatted = f"team size {'+' if value >= 0 else ''}{int(value)}"
            elif key == "product_level":
                formatted = f"product level {'+' if value >= 0 else ''}{int(value)}"
            else:
                formatted = f"{key} {'+' if value >= 0 else ''}{value}"
            parts.append(f"{key} {formatted}")
        return join_and(parts)

    def _update_turn(self) -> None:
        assert self.state is not None
        self._clamp_stats()
        self.state.turn += 1
        summary = self._build_summary()
        self.state.last_report.append(summary)

    def _build_summary(self) -> str:
        assert self.state is not None
        stats = self.state.stats
        runway = self._calculate_runway(stats)
        company_value = self._calculate_company_value(stats)
        summary = (
            f"Balance {format_currency(stats.balance)}, "
            f"Revenue {format_currency(stats.revenue)}, "
            f"Expenses {format_currency(stats.expenses)}, "
            f"Runway {runway:.1f} months, Company Value {format_currency(company_value)}"
        )
        return summary

    def _clamp_stats(self) -> None:
        assert self.state is not None
        stats = self.state.stats
        for key, (minimum, maximum) in STATS_RANGES.items():
            value = getattr(stats, key)
            clamped = clamp(float(value), minimum, maximum)
            if key in {"product_level", "team_size"}:
                setattr(stats, key, int(round(clamped)))
            else:
                setattr(stats, key, clamped)

    def _calculate_runway(self, stats: GameStats) -> float:
        burn = stats.expenses - stats.revenue
        if burn <= 0:
            return 24.0
        if stats.expenses == 0:
            return 24.0
        months = stats.balance / burn if burn > 0 else 24.0
        return max(0.0, min(months, 60.0))

    def _calculate_company_value(self, stats: GameStats) -> float:
        return (
            (stats.revenue * 4)
            + (stats.market_share * 2000)
            + (stats.reputation * 100)
            + (stats.team_size * 500)
            - (stats.bug_rate * 50)
        )

    def _check_end_conditions(self) -> Optional[str]:
        assert self.state is not None
        stats = self.state.stats
        runway = self._calculate_runway(stats)
        company_value = self._calculate_company_value(stats)
        if stats.balance <= 0 or runway <= 0:
            return "Bankruptcy! Your startup ran out of cash."
        if company_value >= 5_000_000:
            return "Congratulations! You achieved an IPO-level valuation."
        if stats.reputation >= 70 and stats.market_share >= 30:
            return "Acquisition offer accepted! A strategic buyer acquires your company."
        if company_value >= 1_000_000 and stats.morale >= 80:
            return "Neutral exit: You sold the company with the team in high spirits."
        return None

    def _prompt_continue(self) -> bool:
        while True:
            choice = input("Continue to next month? (y/n/save): ").strip().lower()
            if choice in {"y", "yes"}:
                return True
            if choice in {"n", "no"}:
                return False
            if choice == "save":
                if self._prompt_save():
                    return False
            else:
                self._info("Please respond with y, n, or save.")

    def _prompt_save(self) -> bool:
        path = self._prompt_path("Enter save file path: ")
        try:
            self.save_game(path)
            return True
        except (FileNotFoundError, ValueError) as error:
            self._info(str(error))
            return False

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _apply_deltas(self, deltas: Dict[str, float]) -> None:
        assert self.state is not None
        for key, value in deltas.items():
            if hasattr(self.state.stats, key):
                current = getattr(self.state.stats, key)
                setattr(self.state.stats, key, current + value)

    def _create_stats_from_profile(self, profile: StartupProfile) -> GameStats:
        stats = {
            "balance": 200_000.0,
            "revenue": 10_000.0,
            "expenses": 30_000.0,
            "product_level": 1,
            "bug_rate": 10.0,
            "team_size": 5,
            "morale": 70.0,
            "productivity": 80.0,
            "reputation": 50.0,
            "users": 5_000.0,
            "market_share": 2.0,
        }
        stats.update(profile.stats)
        return GameStats(
            balance=float(stats["balance"]),
            revenue=float(stats["revenue"]),
            expenses=float(stats["expenses"]),
            product_level=int(stats["product_level"]),
            bug_rate=float(stats["bug_rate"]),
            team_size=int(stats["team_size"]),
            morale=float(stats["morale"]),
            productivity=float(stats["productivity"]),
            reputation=float(stats["reputation"]),
            users=float(stats["users"]),
            market_share=float(stats["market_share"]),
        )

    def _print_main_menu(self) -> None:
        print("\nStartup Simulator - FinTech Edition")
        print("1. New Game")
        print("2. Load Game")
        print("q. Quit")

    def _choose_profile(self) -> Optional[StartupProfile]:
        if not self.profiles:
            self._info("No profiles available.")
            return None
        print("\nChoose your founding profile:")
        for index, profile in enumerate(self.profiles, start=1):
            print(f"  {index}. {profile.name} - {profile.description}")
        print("  0. Cancel")
        choice = self._prompt_int("Selection: ", minimum=0, maximum=len(self.profiles))
        if choice == 0:
            return None
        return self.profiles[choice - 1]

    def _prompt_int(self, prompt: str, minimum: int, maximum: int) -> int:
        while True:
            raw = input(prompt)
            parsed = parse_int(raw)
            if parsed is None:
                self._info("Enter a valid number.")
                continue
            if parsed < minimum or parsed > maximum:
                self._info(f"Choose a number between {minimum} and {maximum}.")
                continue
            return parsed

    def _prompt_path(self, prompt: str) -> Path:
        while True:
            raw = input(prompt).strip()
            if not raw:
                self._info("Path cannot be empty.")
                continue
            return Path(raw)

    def _info(self, message: str) -> None:
        print(wrap_text(message))

    def _print_event_block(self, title: str, lines: Iterable[str]) -> None:
        entries = list(lines)
        if not entries:
            return
        print(f"\n{title}:")
        for entry in entries:
            wrapped = wrap_text(entry)
            lines = wrapped.splitlines()
            if not lines:
                continue
            print(f"  - {lines[0]}")
            for line in lines[1:]:
                print(f"    {line}")


def list_available_actions(actions: Iterable[Action]) -> List[str]:
    """Return a formatted list of action names."""

    return [action.name for action in actions]
