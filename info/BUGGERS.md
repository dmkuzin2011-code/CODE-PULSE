# Code-Pulse Known Bugs Archive

> Historical record of bugs found and fixed across beta versions.

---

## Beta 0.0.1

### Critical
- **None**

### Minor
- **Config localname parsing** — `config localname=John` extracts `me=John` instead of `John`
  - *Cause:* `name = args[0][len("theme="):]` uses wrong prefix length
  - *Status:* Fixed in 0.0.4

---

## Beta 0.0.2

### Critical
- **None**

### Minor
- **Version string mismatch** — `version` command prints "Beta 0.0.1" instead of "Beta 0.0.2"
  - *Cause:* Hardcoded string not updated during release
  - *Status:* Fixed in 0.0.3

- **Config localname parsing** — inherited from 0.0.1, same bug
  - *Status:* Fixed in 0.0.4

---

## Beta 0.0.3

### Critical
- **None**

### Minor
- **Config localname parsing** — inherited from 0.0.1–0.0.2, bug moved to external `config.py` module
  - *Status:* Fixed in 0.0.4

---

## Beta 0.0.4

### All known issues resolved ✅

---

## Bug Fix Summary

| Bug | Introduced | Fixed | Description |
|-----|------------|-------|-------------|
| Config localname slice | 0.0.1 | 0.0.4 | Wrong `len()` in string slicing |
| Version string | 0.0.2 | 0.0.3 | Hardcoded old version number |

---
*Last updated: Beta 0.0.4*
