from __future__ import annotations
import importlib.util
import os
import sys
import traceback
from pathlib import Path
from typing import Callable
from rich.console import Console
from plugin_api import PluginAPI


class PluginLoader:
    """Loads plugins from the plugins folder."""

    def __init__(self, console: Console, config: dict, history_file: Path):
        self.console = console
        self.config = config
        self.api = PluginAPI(console, config, history_file)
        self._plugins: dict[str, object] = {}      # name -> plugin instance
        self._commands: dict[str, Callable] = {}   # "plugin cmd" -> method
        if getattr(sys,"frozen",False):
            base_dir=Path(sys.executable).parent
        else:
            base_dir=Path(__file__).parent
        self._plugin_dir = base_dir/"plugins"
        self._load_all()

    # --- Download ---
    def _load_all(self) -> None:
        if not self._plugin_dir.is_dir():
            return
        for entry in sorted(self._plugin_dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith("_"):
                self._load_one(entry)

    def _load_one(self, folder: Path) -> None:
        plugin_file = folder / "plugin.py"
        if not plugin_file.is_file():
            plugin_file = folder / "__init__.py"
            if not plugin_file.is_file():
                return

        module_name = f"codepulse_plugin_{folder.name}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec is None or spec.loader is None:
                return
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception as exc:
            self.console.print(f"[yellow]Failed to load plugin '{folder.name}': {exc}[/]")
            return

        # Looking for the plugin class
        plugin_class = getattr(module, "Plugin", None)
        if plugin_class is None:
            # Looking for any class with a name attribute
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and hasattr(attr, "name"):
                    plugin_class = attr
                    break

        if plugin_class is None:
            self.console.print(f"[yellow]Plugin '{folder.name}' has no Plugin class[/]")
            return

        try:
            instance = plugin_class()
            instance.init(self.api)
        except Exception as exc:
            self.console.print(f"[yellow]Plugin '{folder.name}' init failed: {exc}[/]")
            return

        name = getattr(instance, "name", folder.name)
        self._plugins[name] = instance
        # Register commands
        raw_commands = getattr(instance, "commands", {})
        if callable(raw_commands):
            commands = raw_commands()
        else:
            commands = raw_commands

        if not isinstance(commands, dict):
            self.console.print(f"[{self.config['based_color']}]Plugin '{name}': commands must return dict[/]")
            return   

        for cmd, handler in commands.items():
            full_cmd = f"{name} {cmd}".strip()
            self._commands[full_cmd] = handler

    # --- Call ---
    def has_command(self, cmd: str) -> bool:
        return cmd in self._commands

    def run(self, cmd: str, args: list[str]) -> None:
        handler = self._commands.get(cmd)
        if handler is None:
            self.console.print(f"[red]Plugin command not found: {cmd}[/]")
            return
        try:
            handler(args)
        except Exception as exc:
            self.console.print(f"[red]Plugin error in '{cmd}': {exc}[/]")
            if os.getenv("PULSE_DEBUG"):
                traceback.print_exc()

    # --- Auto T9 ---
    def completions(self) -> dict:
        """Restore the structure for NesterCompleter."""
        result: dict = {}
        for full_cmd in self._commands:
            parts = full_cmd.split()
            d = result
            for part in parts[:-1]:
                if part not in d:
                    d[part] = {}
                d = d[part]
            d[parts[-1]] = None
        return result

    def list_plugins(self) -> list[str]:
        """List of plugins."""
        return list(self._plugins.keys())
