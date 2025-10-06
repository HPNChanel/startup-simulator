from contextlib import contextmanager
import tempfile
from pathlib import Path
from typing import Any, Generator, Tuple, Type


class PatchManager:
    """Simple attribute patcher that restores values after use."""

    def __init__(self) -> None:
        self._patches: list[Tuple[Any, str, Any, bool]] = []

    def setattr(self, obj: Any, name: str, value: Any) -> None:
        has_original = hasattr(obj, name)
        original = getattr(obj, name, None)
        setattr(obj, name, value)
        self._patches.append((obj, name, original, has_original))

    def reset(self) -> None:
        while self._patches:
            obj, name, original, has_original = self._patches.pop()
            if has_original:
                setattr(obj, name, original)
            else:
                delattr(obj, name)

    def __enter__(self) -> "PatchManager":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.reset()


@contextmanager
def expect_raises(exception: Type[BaseException], match: str | None = None) -> Generator[None, None, None]:
    """Context manager asserting that *exception* is raised."""

    try:
        yield
    except exception as exc:  # pragma: no cover - exercised in tests
        if match is not None and match not in str(exc):
            raise AssertionError(f"Expected '{match}' to appear in '{exc}'.") from exc
    else:
        raise AssertionError(f"Expected {exception.__name__} to be raised.")


@contextmanager
def temporary_save_path(save_module: Any) -> Generator[Path, None, None]:
    """Provide a temporary save path patched into *save_module*."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "save.json"
        with PatchManager() as patches:
            patches.setattr(save_module, "SAVE_PATH", path)
            yield path
