"""Simple test runner allowing ``python -m startup_simulator.tests``."""
from __future__ import annotations

import importlib
import pkgutil
import sys
import traceback
from types import ModuleType
from typing import Callable

PACKAGE_NAME = "startup_simulator.tests"


def iter_test_functions(module: ModuleType) -> list[tuple[str, Callable[[], None]]]:
    functions: list[tuple[str, Callable[[], None]]] = []
    for name in dir(module):
        if not name.startswith("test_"):
            continue
        obj = getattr(module, name)
        if callable(obj):
            functions.append((name, obj))
    return functions


def main() -> None:
    package = importlib.import_module(PACKAGE_NAME)
    failures = 0

    for module_info in pkgutil.iter_modules(package.__path__):
        if not module_info.name.startswith("test_"):
            continue
        module = importlib.import_module(f"{PACKAGE_NAME}.{module_info.name}")
        for func_name, func in iter_test_functions(module):
            try:
                func()
            except Exception:
                failures += 1
                print(f"FAILED: {module_info.name}.{func_name}")
                traceback.print_exc()

    if failures:
        print(f"{failures} test(s) failed.")
        sys.exit(1)

    print("All tests passed.")


if __name__ == "__main__":
    main()
