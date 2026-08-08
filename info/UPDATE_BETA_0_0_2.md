# Pulse Beta 0.0.2 — Release Notes

## Highlights

- **Vault system** — added encrypted storage for secrets (passwords, tokens, notes)
  - PBKDF2-HMAC-SHA256 key derivation (480,000 iterations)
  - Fernet encryption (AES-128-CBC + HMAC)
  - Brute-force protection: 5 attempts max, then auto-wipe
  - Commands: `vault init`, `vault add=`, `vault get=`, `vault delete=`, `vault list`, `vault status`, `vault reset`

## Bug Fixes

- None (initial vault release)

## Known Issues

- Version string still reports "Beta 0.0.1" in `version` command
- `config localname=<name>` parses incorrectly due to wrong slice length (`len("theme=")` instead of `len("localname=")`)

---
**Release Date:** Beta 0.0.2
**Status:** Active Development + AI support (Kimi, Claude)
