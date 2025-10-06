# Startup Simulator

Startup Simulator is a lightweight command-line prototype that simulates the early days of running a startup. The project scaffolding provides data-driven actions and events, a minimal CLI, and supporting modules that can be expanded into a richer experience.

## Quickstart

1. Install Python 3.10 or later.
2. Clone the repository and install optional development dependencies if you plan to run the tests (`pip install -r requirements-dev.txt` when available).
3. From the repository root, run the simulator:

   ```bash
   python startup_simulator/main.py
   ```

4. Pick a founding profile when prompted and choose up to the allowed number of actions each turn. The dashboard updates after every turn and the game ends when you reach a success or failure condition.

The CLI supports several quality-of-life flags:

- `--seed SEED` — set the random seed used for the session (defaults to 42).
- `--profile "Profile Name"` — skip the interactive profile prompt.
- `--max-actions N` — override how many actions you can take per turn (clamped to the configured limits).
- `--autosave` — persist the state to `save.json` after every turn and on endings.
- `--no-color` — disable ANSI colours if your terminal does not support them.

Run `python startup_simulator/main.py --help` to see the full usage text.

## Design overview

The simulator is intentionally modular so designers and developers can work in parallel:

- `startup_simulator/main.py` wires the CLI loop together, handles command-line options, and coordinates the other modules.
- `startup_simulator/config.py` centralises balancing constants, save file paths, and shared tunables.
- `startup_simulator/actions.py` defines action schemas and helper functions for applying costs/effects.
- `startup_simulator/events.py` drives the random event lifecycle and monthly ticking logic.
- `startup_simulator/startup.py` stores the company state and exposes helpers for clamping metrics and computing valuation.
- `startup_simulator/ui_text.py` formats textual dashboards, action menus, and event summaries.
- `startup_simulator/data/` houses the JSON definitions that power actions, events, and starting profiles.

All modules aim to be side-effect free aside from `main.py`, which keeps the codebase approachable for experimentation.

## How to tweak balancing

- Use `startup_simulator/config.py` to update key knobs such as `DEFAULT_ACTIONS_PER_TURN`, `ACTION_LIMIT_RANGE`, runway caps, or valuation weights. These values are imported throughout the simulator, so adjusting them in one place changes the behaviour everywhere.
- Update numeric fields directly on the JSON files in `startup_simulator/data/` when you want to tune costs, effects, or event probabilities.
- Re-run the CLI after any change; there is no additional build step.

## How to add new actions or events

1. Open `startup_simulator/data/actions.json` or `startup_simulator/data/events.json` depending on what you want to extend.
2. Copy an existing entry and adjust the `id`, `name`, `narrative`, and `costs`/`effects` fields. Costs subtract from the listed metrics, while effects add to them.
3. For events, provide `duration` and `cooldown` values to control how long the modifier sticks around and how frequently it can reoccur.
4. Keep numeric deltas within the ranges defined in `config.py` to avoid unbalanced gameplay.
5. Run the simulator to immediately test the new content; the loader reads from disk on every run.

If you need a new starting scenario, add an object to `startup_simulator/data/startup_profiles.json` with the profile `name`, optional `description`, and a `metrics` mapping for any fields that should override the defaults.

## Save file format

The simulator writes saves to `save.json` (or the path configured in `config.py`). The file is JSON with a schema enforced by `startup_simulator/save_system.py`:

```json
{
  "version": "1.0",
  "timestamp": "2024-01-01T12:34:56+00:00",
  "turn": 3,
  "rng_seed": 42,
  "startup": { "balance": 500000, "users": 1500, ... }
}
```

- `version` must match `config.SAVE_SCHEMA_VERSION`.
- `timestamp` is stored in ISO 8601 UTC.
- `turn` and `rng_seed` are integers used to resume deterministic runs.
- `startup` contains the serialised startup metrics returned by `Startup.snapshot()`.

The helper `save_system.load_game()` validates these keys before restoring a session.

## How to Test

The project includes a small test suite using `pytest`.

```bash
pytest
```

The tests cover financial helpers, event loading, and the save system utilities.
