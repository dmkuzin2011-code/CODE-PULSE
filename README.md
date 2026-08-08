# CODE-PULSE

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-beta%200.0.4-orange)](info/UPDATE_BETA_0_0_4.md)

**Code-pulse** is a CLI tool for analyzing and monitoring file structures, inspired by Git and other console utilities.
<div style="text-align: center">
<img src="code-pulse.png" width="50%" height="50%" alt="Code-Pulse icon">
</div>

## About the Project

Code-pulse helps track changes in file structures, maintain scan history, and securely store sensitive data. The current version implements basic functionality in Python with an extensible architecture.

> **Note:** This is a beta version. The project will be rewritten in TypeScript and Node.js for the production release with full functionality.

## Features

- 📊 **Directory Scanning** — analyze files, sizes, and extensions
- 📈 **Change Diagrams** — visualize file dynamics over time
- 📜 **Scan History** — save and export results
- 🔐 **Secure Storage** — vault module for sensitive data with encryption
- ⚙️ **Configuration** — personalize themes and names
- 🎇 **Plugins and add-ons** -plugin support is provided.

## Installation

### Requirements

- Python 3.8 or higher
- Dependencies (install via pip):

```bash
pip install prompt-toolkit rich cryptography
```

### Running

```bash
python "Source code/Pulse_repl_beta_0_0_4.py"
```

## Usage

After launching, type `support` to view all available commands.

### Main Commands

#### Scanning

```bash
scan path=<path> info          # Basic information about directory
scan path=<path> struct        # Directory tree
scan test                      # Test scan of current directory
scan history                   # Scan history
```

#### Diagrams

```bash
diagram layer=<path>           # File changes diagram
```

#### History Management

```bash
history_delete                 # Delete all history
export <number>                # Export report to JSON
```

#### Configuration

```bash
config check                   # View current configuration
config theme=<color>           # Change color theme (hex, e.g. #013220)
config localname=<name>        # Change local name
```

#### Secure Storage (Vault)

```bash
vault init                     # Create new storage
vault add=<name>               # Store a secret
vault get=<name>               # Retrieve a secret
vault delete=<name>            # Remove a secret
vault list                     # List secret names (no values)
vault status                   # Show remaining unlock attempts
vault reset                    # Delete the vault
```

#### Other

```bash
support                        # Command help
version                        # Current version
exit / quit                    # Exit
```

## Security

The **vault** module uses:
- **PBKDF2-HMAC-SHA256** with 480,000 iterations for key derivation
- **Fernet (AES-128-CBC + HMAC)** for data encryption
- 16 bytes of random salt
- 5 password attempt limit (data is destroyed after max attempts)

## Project Structure

```
Code Pulse Beta on Python/
├── README.md                   # Documentation
├── LICENSE                     # AGPL-3.0 License
├── info/
│   ├── BUGGERS.md             # Fixed bugs
│   └── UPDATE_BETA_....md   # Update history
├── Pulse exe/exe+config etc.
└── Source code/
    ├──Pulse_repl_beta_0_0_4.py  # Source code
    ├──plugins/
    ├──config.py
    ├──plugin_api.py
    ├──plugin_loader.py
    └──code-pulse.ico
```

## License

This project is licensed under the **GNU Affero General Public License v3**. See the [LICENSE](LICENSE) file for details.

## Contributing

I fully support the distribution and development of this project. If you want to contribute:

1. Fork the repository
2. Create a branch for new feature (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Contact

If you have questions or suggestions, create an issue in the repository.

---

**Status:** Beta 0.0.4 — active development

**Last Update:** See [info/UPDATE_BETA_0_0_4.md](info/UPDATE_BETA_0_0_4.md)
