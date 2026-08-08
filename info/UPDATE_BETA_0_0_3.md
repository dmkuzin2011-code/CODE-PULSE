# Pulse Beta 0.0.3 — Release Notes

## Highlights

- **Plugin system** — modular architecture via `PluginLoader`
  - External plugins can register commands and completions
  - Plugins receive access to `console`, `CONFIG`, and `HISTORY_FILE`
- **Config modularization** — config logic moved to separate `config.py` module
  - `start_config_checkout()`, `save_config()`, `config_cmd()` now imported externally
  - Cleaner main file, easier maintenance

## Bug Fixes

- Version string corrected to "Beta 0.0.2" in `version` command

## Known Issues

- `config localname=<name>` still parses incorrectly (bug inherited from 0.0.1, not yet fixed)
  - Workaround: the bug exists in external `config.py` module

---
**Release Date:** Beta 0.0.3
**Status:** Active Development + AI support (Kimi, Claude)
