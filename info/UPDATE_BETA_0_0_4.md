# Pulse Beta 0.0.4 — Release Notes

## Highlights

- **`cd` command** — change working directory directly from the REPL
  - No need to exit Code-Pulse to navigate the filesystem
  - Integrates with existing `scan` and `diagram` commands

## Bug Fixes

- `config localname=<name>` parsing fixed
  - Changed `args[0][len("theme="):]` → `args[0][len("localname="):]`
  - Local name now correctly extracted from command argument
- `config theme=<color>` validation streamlined
  - Removed redundant double-check after hex validation

## Notes

- All previously known issues from 0.0.1–0.0.3 are now resolved
- Plugin system remains fully functional and extensible

---
**Release Date:** Beta 0.0.4
**Status:** Active Development + AI support (Kimi, Claude)
