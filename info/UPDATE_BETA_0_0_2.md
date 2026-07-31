# Beta 0.0.2 Release Notes

## New Module: Vault

The vault module adds a secure storage area for highly sensitive data to Code-pulse.

### New Commands

1. `vault init` — create a new password-protected storage
2. `vault add=<name>` — store a secret under a specified name
3. `vault get=<name>` — decrypt and retrieve a secret by name
4. `vault delete=<name>` — delete a stored secret by name
5. `vault list` — list all secret names (values are not displayed)
6. `vault status` — show remaining unlock attempts and file path
7. `vault reset` — permanently delete the vault storage

### How It Works

For every operation, the password and stored salt are processed using **PBKDF2-HMAC-SHA256** with **480,000 iterations**, yielding a **256-bit key**.

- The salt consists of **16 random bytes** and is stored unencrypted
- Maximum of **5 login attempts** before the vault is permanently wiped
- Uses **Fernet (AES-128-CBC + HMAC)** for encryption

---

**Release Date:** Beta 0.0.2

**Status:** Active Development