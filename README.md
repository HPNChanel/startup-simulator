# Startup Simulator (FinTech Edition)

Startup Simulator is a turn-based strategy and narrative experience that puts you in
charge of a scrappy FinTech startup. Balance growth, morale, product quality, and
cashflow while reacting to dynamic events and choosing pivotal monthly actions.

## Requirements

* Python 3.12+
* No external dependencies – the standard library is enough.

## Getting Started

```bash
python main.py --seed 1234
```

The optional `--seed` argument ensures deterministic outcomes for testing and
comparison runs. You can also load custom data using `--data-path` if you want to
experiment with your own actions, events, or profiles.

## Gameplay Overview

Each month you will:

1. Review the previous month's highlights and financial summary.
2. Experience persistent or surprise events that shift your metrics.
3. Select up to three strategic actions such as hiring, marketing, or shipping features.
4. Watch the consequences unfold as your company's value, runway, and reputation evolve.

Win by achieving an IPO-level valuation or a lucrative acquisition. Lose if you run out
of cash or morale and value fail to keep pace. A high-morale neutral exit is also
possible.

## Saving and Loading

Choose `save` at action prompts or the end-of-month confirmation to write a JSON save
file. Use the main menu's **Load Game** option to resume from any saved state.
