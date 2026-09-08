"""Rich terminal rendering for application events."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager

from rich.console import Console
from rich.theme import Theme

_THEME = Theme(
    {
        "step": "cyan",
        "success": "green",
        "header": "bold white",
    }
)


class RichApplicationEvents:
    """CLI event handler with Rich spinners and color when stderr is a TTY."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console(stderr=True, theme=_THEME, soft_wrap=True)

    def begin_session(self, message: str) -> None:
        if self._use_rich_ui():
            self._console.print(f"[header]{message}[/]")
            return
        self._plain(f"→ {message}")

    def end_session(self, message: str) -> None:
        if self._use_rich_ui():
            self._console.print(f"[success]✓[/] [step]{message}[/]")
            return
        self._plain(f"→ {message}")

    def log_event(self, message: str) -> None:
        if self._use_rich_ui():
            self._console.print(f"[success]✓[/] [step]{message}[/]")
            return
        self._plain(f"✓ {message}")

    def log_stage(self, step: int, total: int, message: str) -> None:
        label = f"[{step}/{total}] {message}"
        if self._use_rich_ui():
            self._console.print(f"[success]✓[/] [step]{label}[/]")
            return
        self._plain(f"→ {label}")

    @contextmanager
    def log_wait(self, step: int, total: int, message: str) -> Iterator[None]:
        label = f"[{step}/{total}] {message}"
        if self._use_rich_ui():
            with self._console.status(
                f"[step]{label}[/]",
                spinner="dots",
                spinner_style="cyan",
            ):
                yield
            self._console.print(f"[success]✓[/] [step]{label}[/]")
            return

        self._plain(f"→ {label}")
        yield

    @staticmethod
    def _use_rich_ui() -> bool:
        if os.environ.get("NO_COLOR"):
            return False
        return sys.stderr.isatty()

    @staticmethod
    def _plain(message: str) -> None:
        print(message, file=sys.stderr, flush=True)
