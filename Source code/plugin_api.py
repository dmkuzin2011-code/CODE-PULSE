from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any
from rich.console import Console
from config import save_config

class PluginAPI:
    """Api."""

    def __init__(self, console: Console, config: dict, history_file: Path):
        self.console = console
        self.config = config
        self._history_file = history_file

    # --- Вывод ---
    def print(self, text: str, **kwargs) -> None:
        """Print text into console"""
        self.console.print(text, **kwargs)
    @staticmethod
    def input( prompt_text: str, is_password: bool = False) -> str:
        """Request input from the user."""
        from prompt_toolkit import prompt
        return prompt(prompt_text, is_password=is_password)

    # --- Config ---
    def get_config(self, key: str, default: Any = None) -> Any:
        """Read the value from config.json."""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Save value to config.json."""
        self.config[key] = value
        save_config()

    # --- History of scan ---
    def get_history(self) -> list[dict]:
        """Restore scan history"""
        if not self._history_file.is_file():
            return []
        try:
            return json.loads(self._history_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def get_last_scan(self) -> dict | None:
        """Return the last scan or None."""
        history = self.get_history()
        return history[-1] if history else None

    def get_scan_by_path(self, path: str) -> list[dict]:
        """Return the scans as instructed."""
        return [h for h in self.get_history() if h.get("path") == path]

    # --- Utilities ---
    @staticmethod
    def human_size( num_bytes: int) -> str:
        from Pulse_repl_beta_0_0_4 import _human_size
        return _human_size(num_bytes)
    @staticmethod
    def now_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Current time in the line."""
        return time.strftime(fmt, time.localtime())
