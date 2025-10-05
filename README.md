# Startup Simulator

Startup Simulator is a lightweight command-line prototype that simulates the early days of running a startup. The project scaffolding provides data-driven actions and events, a minimal CLI, and supporting modules that can be expanded into a richer experience.

## How to Run

1. Ensure you have Python 3.10 or later installed.
2. From the repository root, execute:

   ```bash
   python startup_simulator/main.py
   ```

   Optional arguments:

   - `--seed` – set the random seed used for the session (defaults to 42).
   - `--autosave` – immediately writes a minimal save file to `save.json`.

## How to Play

Running the CLI prints a banner, loads the default startup profile, and lists the available actions and random events defined in `startup_simulator/data`. This scaffold is a starting point for further gameplay logic such as processing turns, applying actions, and resolving events.

## How to Test

The project includes a small test suite using `pytest`.

```bash
pytest
```

The tests cover financial helpers, event loading, and the save system utilities.
