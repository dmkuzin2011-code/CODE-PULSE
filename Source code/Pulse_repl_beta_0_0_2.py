from __future__ import annotations
import json
import re
import os
import shlex
import time
import base64
from dataclasses import dataclass
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.completion import NestedCompleter, PathCompleter
from rich.console import Console
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
CONFIG={}
base_data={
    "user_local_name":None,
    "based_color":"#013220"
}
file_path="config.json"
def start_config_checkout():
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as file_beta:
            json.dump(base_data, file_beta)
    if os.path.exists(file_path):
        with open(file_path,"r",encoding="utf-8") as file_data:
            global CONFIG
            CONFIG=json.load(file_data)
def save_config():
    global CONFIG
    with open(file_path,"w",encoding="utf-8") as file:
        json.dump(CONFIG,file)
start_config_checkout()
console = Console()

HISTORY_FILE = Path(os.path.expanduser("~/.config/code-pulse/history.json"))
VAULT_FILE = Path(os.path.expanduser("~/.config/code-pulse/vault.json"))
VAULT_MAX_ATTEMPTS = 5
VAULT_KDF_ITERATIONS = 480_000


# ---------------------------------------------------------------------------
# Autocompletion
# ---------------------------------------------------------------------------

completer_structure = NestedCompleter.from_nested_dict({
    "scan": {
        "path=": PathCompleter(only_directories=True),
        "test": None,
        "history": None,
    },
    "diagram": {
        "layer=": PathCompleter(only_directories=True),
    },
    "save":{"scan_path"},
    "history_delete": None,
    "support": None,
    "version":None,
    "config":{"check":None,"theme=":None,"localname=":None},
    "vault": {
        "init": None,
        "add=": None,
        "get=": None,
        "delete=": None,
        "list": None,
        "status": None,
        "reset": None,
    },
    "exit": None,
    "quit": None,
})


# ---------------------------------------------------------------------------
# Scan history storage-currently just a simple JSON file.
# ---------------------------------------------------------------------------
@dataclass
class HistoryResult:
    success:bool
    data:list[dict]
    message:str
def _load_history() -> HistoryResult  :
    if not HISTORY_FILE.is_file():
        return HistoryResult(False,[],"history is empty")
    try:
        return HistoryResult(True,json.loads(HISTORY_FILE.read_text(encoding="utf-8")),"Great")
    except json.JSONDecodeError:
        return HistoryResult(False,[],"file_error")
    except OSError:
        return HistoryResult(False,[],"Os error.")


def _save_history(entries: list[dict]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_history(path: str, total_files: int, total_bytes: int) -> None:
    result = _load_history()
    entries = result.data if result.success else []
    if not result.success:
        console.print(f"[yellow]{result.message}[/]")
    entries.append({"path":path,
                    "timestamp":int(time.time()),
                    "total_files":total_files,
                    "total_bytes":total_bytes})
    _save_history(entries)


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def _walk_stats(path: str) -> tuple[int, int, dict[str, int]]:
    """Returns (total_files, total_bytes, {ext: count})."""
    total_files = 0
    total_bytes = 0
    by_ext: dict[str, int] = {}

    for root, dirs, files in os.walk(path, onerror=lambda e: console.print(f"[yellow]нет доступа: {e.filename}[/yellow]")):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            full = os.path.join(root, fname)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            total_files += 1
            total_bytes += size
            ext = os.path.splitext(fname)[1].lstrip(".").lower() or "(noext)"
            by_ext[ext] = by_ext.get(ext, 0) + 1

    return total_files, total_bytes, by_ext


def cmd_scan_info(path: str) -> None:
    if not os.path.isdir(path):
        console.print(f"[red]The directory does not exist, or you are hiding something: {path}[/red]")
        return

    total_files, total_bytes, by_ext = _walk_stats(path)
    console.print(f"[bold cyan]{os.path.abspath(path)}[/bold cyan]")
    console.print(f"Files: [green]{total_files}[/green]   Size: [green]{_human_size(total_bytes)}[/green]")

    top = sorted(by_ext.items(), key=lambda kv: -kv[1])[:5]
    if top:
        console.print("Top extensions:")
        for ext, count in top:
            console.print(f"  .{ext:<10} {count}")

    _append_history(os.path.abspath(path), total_files, total_bytes)


def cmd_scan_struct(path: str) -> None:
    """Prints a directory tree showing the numbers of files in each folder (also works with inaccessible folders)."""
    if not os.path.isdir(path):
        console.print(f"[red]Directory error: {path}[/red]")
        return

    root_abs = os.path.abspath(path)

    def walk(current: str, prefix: str = "") -> None:
        try:
            entries = sorted(os.listdir(current))
        except PermissionError:
            console.print(f"{prefix}[red](Access restricted)[/red]")
            return

        dirs = [e for e in entries if os.path.isdir(os.path.join(current, e)) and not e.startswith(".")]
        files = [e for e in entries if os.path.isfile(os.path.join(current, e))]

        console.print(f"{prefix}[dim]{len(files)} paths inside[/dim]")
        for i, d in enumerate(dirs):
            is_last = i == len(dirs) - 1
            branch = "└── " if is_last else "├── "
            console.print(f"{prefix}{branch}[cyan]{d}/[/cyan]")
            next_prefix = prefix + ("    " if is_last else "│   ")
            walk(os.path.join(current, d), next_prefix)

    console.print(f"[bold cyan]{root_abs}[/bold cyan]")
    walk(root_abs)

def cmd_export(args:list[str])->None:
    result =_load_history()
    if not result.success or not result.data:
        console.print("[yellow]History is empty.[/]")
        return
    entries=result.data
    if not args:
        console.print("[bold cyan]Scan history[/]")
        for i,e in enumerate(entries,1):
            ts=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(e["timestamp"]))
            console.print(f"[{i}]{ts}{e["path"]}({e["total_files"]} files,{_human_size(e["total_bytes"])})")
        console.print("\n[dim]Use export <number>[file=<path>][/]")
    try:
        idx=int(args[0])-1
        if idx <0 or idx >= len(entries):
            raise ValueError
    except ValueError:
        console.print(f"[red]Invalid number.Use 1-{len(entries)}[/]")
        return
    entry = entries[idx]

    out_path = None
    for a in args[1:]:
        if a.startswith("file="):
            out_path = a[5:]
            break

    if out_path is None:
        ts_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(entry["timestamp"]))
        safe_name = Path(entry["path"]).name.replace(" ", "_") or "scan"
        out_path = f"pulse_report_{safe_name}_{ts_str}.json"

    report = {
        "generated_at": time.strftime("%Y-%m-%d_%H:%M:%S",time.localtime(time.time())),
        "pulse_version": "0.0.1",
        "scan": {
            "path": entry["path"],
            "timestamp": entry["timestamp"],
            "scanned_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["timestamp"])),
            "total_files": entry["total_files"],
            "total_bytes": entry["total_bytes"],
            "total_size_human": _human_size(entry["total_bytes"]),
        }
    }
    try:
        Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"[green]Report saved:[/green] {os.path.abspath(out_path)}")
        return
    except OSError as exc:
        console.print(f"[red]Failed to save: {exc}[/red]")
def cmd_scan_test() -> None:
    console.print("[dim]Test scan of the current directory[/dim]")
    cmd_scan_info(".")

def cmd_scan_history() -> None:
    entries = _load_history()
    if not entries.success or not entries.data:
        console.print("[yellow]History is empty[/yellow]")
        return
    for e in entries.data[-20:]:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e["timestamp"]))
        console.print(f"[green]{ts}[/]  [yellow]{e['path']}[/] Files=[green]{e['total_files']}[/]  [magenta]{_human_size(e['total_bytes'])}[/]")


def cmd_scan(args: list[str]) -> None:
    if not args:
        console.print("[yellow]Usage:scan path=<> info|struct|scan test|scan history[/yellow]")
        return

    if args[0] == "test":
        cmd_scan_test()
        return
    if args[0] == "history":
        cmd_scan_history()
        return

    if args[0].startswith("path="):
        path = args[0][len("path="):]
        mode = args[1] if len(args) > 1 else "info"
        if mode == "info":
            cmd_scan_info(path)
        elif mode == "struct":
            cmd_scan_struct(path)
        else:
            console.print(f"[red]unknown mode: {mode} (expected info|struct)[/red]")
        return

    console.print(f"[red]unknown argument for scan: {args[0]}[/red]")


# ---------------------------------------------------------------------------
# diagram — diagram of changes
# ---------------------------------------------------------------------------

def cmd_diagram(args: list[str]) -> None:
    if not args or not args[0].startswith("layer="):
        console.print(f"[{CONFIG["based_color"]}]Usage: diagram layer=<path>[/]")
        return

    layer = os.path.abspath(args[0][len("layer="):])
    entries = [e for e in _load_history().data if e["path"] == layer]

    if not entries:
        console.print(f"[{CONFIG["based_color"]}]No scan history {layer}. To begin perform scan path={layer} info[/]")
        return

    console.print(f"[bold cyan]Dynamic of files: {layer}[/bold cyan]\n")

    max_files = max(e["total_files"] for e in entries) or 1
    width = 30
    for e in entries[-15:]:
        ts = time.strftime("%m-%d %H:%M", time.localtime(e["timestamp"]))
        filled = max(1, round(width * e["total_files"] / max_files)) if e["total_files"] else 0
        bar = "█" * filled + "░" * (width - filled)
        console.print(f"{ts}  {bar}  {e['total_files']} files  ({_human_size(e['total_bytes'])})")


# ---------------------------------------------------------------------------
# history_delete
# ---------------------------------------------------------------------------

def cmd_history_delete() -> None:
    entries = _load_history()
    if not entries.success:
        console.print(f"[{CONFIG["based_color"]}]History is empty[/]")
        return

    answer = prompt(f"Delete all history ({len(entries.data)} records)? [y/N] ").strip().lower()
    if answer == "y" or answer=="Y":
        _save_history([])
        console.print("[green]History deleted[/green]")
    else:
        console.print("[dim]Cancelled[/dim]")


# ---------------------------------------------------------------------------
# support
# ---------------------------------------------------------------------------

def cmd_support() -> None:
    console.print("[bold yellow]Available commands:[/]")
    console.print("  scan path=<> info          — base information about folder or path.")
    console.print("  scan path=<> struct        — directory/folder tree.")
    console.print("  scan test                  — test scan.")
    console.print("  scan history               — history of scan.")
    console.print("  diagram layer=<path>       — diagram of changes about folder.")
    console.print("  history_delete             — deleting history with confirmation.")
    console.print("  support                    — help.")
    console.print("  version                    — you can control [yellow]version[/].")
    console.print("  save scan_path             — you can save information about scan.")
    console.print("  config check               — you can check your config file.")
    console.print("  config theme=<>            — you can change your colortheme.")
    console.print("  config localname=<>        — you can change your local name.")
    console.print("  vault init                 — create a password-protected secrets vault.")
    console.print("  vault add=<name>           — store a secret (prompts for value).")
    console.print("  vault get=<name>           — reveal a stored secret.")
    console.print("  vault delete=<name>        — remove a stored secret.")
    console.print("  vault list                 — list secret names (no values).")
    console.print("  vault status               — show remaining unlock attempts.")
    console.print("  vault reset                — delete the vault (manual, with confirmation).")
    console.print("  exit / quit                — bye.")
# ---------------------------------------------------------------------------
# Auxiliary
# ---------------------------------------------------------------------------

def _human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0 or unit == "TB":
            return f"{size:.1f}{unit}" if unit != "B" else f"{int(size)}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"

#----------------------------------------------------------------------------
# Config
#----------------------------------------------------------------------------
def is_valid_hex(color:str)->bool:
    if not isinstance(color,str):
        return False
    return bool(re.match(r'#[0-9A-Fa-f]{6}$',color))
def config_cmd(args:list[str])->None:
    if not os.path.exists(file_path):
        with open(file_path,"w",encoding="utf-8") as file:
            json.dump(base_data,file)
    if not args:
        console.print(f"[{CONFIG["based_color"]}]Usage:config check[/]")
        return
    if args[0]=="check":
        if os.path.exists(file_path):
            with open(file_path,"r",encoding="utf-8") as file2:
                data=json.load(file2)
                console.print(f"[{CONFIG["based_color"]}]Your local name:{data["user_local_name"]}[/]")
                console.print(f"[{CONFIG["based_color"]}]Your based color:{data["based_color"]}[/]")
    if args[0].startswith("theme="):
        color=args[0][len("theme="):]
        if not is_valid_hex(color):
            console.print("[red]Color error")
            return
        if is_valid_hex(color):
            CONFIG["based_color"]=color
            save_config()
            return
    if args[0].startswith("localname="):
        name=args[0][len("theme="):]
        CONFIG["user_local_name"]=name
        save_config()

# ---------------------------------------------------------------------------
# Vault — encrypted storage for secrets (passwords, tokens, notes)
# ---------------------------------------------------------------------------
#
# Design:
#   * A master password derives a symmetric key via PBKDF2-HMAC-SHA256.
#   * That key encrypts a JSON blob {name: secret} with Fernet (AES128-CBC + HMAC).
#   * The derived key is never stored — correctness is verified by whether
#     Fernet can decrypt the blob (it fails loudly via InvalidToken).
#   * Wrong-password attempts are counted. When attempts run out, the
#     encrypted blob is permanently wiped (no recovery) — this is the
#     max-security tradeoff the user asked for.

def _vault_derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=VAULT_KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def _vault_read_raw() -> dict | None:
    if not VAULT_FILE.is_file():
        return None
    try:
        return json.loads(VAULT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _vault_write_raw(record: dict) -> None:
    VAULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    VAULT_FILE.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _vault_wipe(reason: str) -> None:
    if VAULT_FILE.exists():
        VAULT_FILE.unlink()
    console.print(f"[bold red]Vault wiped: {reason}. All secrets are permanently lost.[/]")
    console.print("[dim]Run 'vault init' to create a new vault.[/]")


def vault_init() -> None:
    if VAULT_FILE.exists():
        console.print(f"[{CONFIG["based_color"]}]Vault already exists. Use 'vault reset' first if you want to start over.[/]")
        return

    pw1 = prompt("Set master password: ", is_password=True)
    if not pw1:
        console.print("[red]Password cannot be empty.[/]")
        return
    pw2 = prompt("Confirm master password: ", is_password=True)
    if pw1 != pw2:
        console.print("[red]Passwords do not match.[/]")
        return

    salt = os.urandom(16)
    key = _vault_derive_key(pw1, salt)
    token = Fernet(key).encrypt(json.dumps({}).encode("utf-8"))

    record = {
        "salt": base64.b64encode(salt).decode("ascii"),
        "data": token.decode("ascii"),
        "attempts_left": VAULT_MAX_ATTEMPTS,
        "max_attempts": VAULT_MAX_ATTEMPTS,
    }
    _vault_write_raw(record)
    console.print("[green]Vault created.[/] Use 'vault add=<name>' to store a secret.")


def _vault_unlock() -> tuple[bytes, dict] | None:
    """Prompts for the master password and returns (key, secrets) on success, else None."""
    record = _vault_read_raw()
    if record is None:
        console.print(f"[{CONFIG["based_color"]}]No vault found. Use 'vault init' first.[/]")
        return None

    password = prompt("Master password: ", is_password=True)
    salt = base64.b64decode(record["salt"])
    key = _vault_derive_key(password, salt)

    try:
        decrypted = Fernet(key).decrypt(record["data"].encode("ascii"))
    except InvalidToken:
        attempts_left = record.get("attempts_left", VAULT_MAX_ATTEMPTS) - 1
        if attempts_left <= 0:
            _vault_wipe("too many failed unlock attempts")
            return None
        record["attempts_left"] = attempts_left
        _vault_write_raw(record)
        console.print(f"[red]Wrong password. Attempts left: {attempts_left}[/]")
        return None

    if record.get("attempts_left", VAULT_MAX_ATTEMPTS) != record.get("max_attempts", VAULT_MAX_ATTEMPTS):
        record["attempts_left"] = record.get("max_attempts", VAULT_MAX_ATTEMPTS)
        _vault_write_raw(record)

    return key, json.loads(decrypted.decode("utf-8"))


def _vault_persist(key: bytes, secrets: dict) -> None:
    record = _vault_read_raw()
    if record is None:
        return
    token = Fernet(key).encrypt(json.dumps(secrets).encode("utf-8"))
    record["data"] = token.decode("ascii")
    _vault_write_raw(record)


def vault_add(name: str) -> None:
    unlocked = _vault_unlock()
    if unlocked is None:
        return
    key, secrets = unlocked
    value = prompt(f"Secret value for '{name}': ", is_password=True)
    secrets[name] = value
    _vault_persist(key, secrets)
    console.print(f"[green]Stored '{name}' in vault.[/]")


def vault_get(name: str) -> None:
    unlocked = _vault_unlock()
    if unlocked is None:
        return
    _key, secrets = unlocked
    if name not in secrets:
        console.print(f"[yellow]No entry named '{name}'.[/]")
        return
    console.print(f"[bold]{name}[/]:", markup=True)
    console.print(secrets[name], markup=False)


def vault_delete(name: str) -> None:
    unlocked = _vault_unlock()
    if unlocked is None:
        return
    key, secrets = unlocked
    if name not in secrets:
        console.print(f"[yellow]No entry named '{name}'.[/]")
        return
    del secrets[name]
    _vault_persist(key, secrets)
    console.print(f"[green]Deleted '{name}' from vault.[/]")


def vault_list() -> None:
    unlocked = _vault_unlock()
    if unlocked is None:
        return
    _key, secrets = unlocked
    if not secrets:
        console.print("[yellow]Vault is empty.[/]")
        return
    console.print("[bold cyan]Vault entries:[/]")
    for name in secrets:
        console.print(f"  - {name}")


def vault_status() -> None:
    record = _vault_read_raw()
    if record is None:
        console.print("[yellow]No vault found. Use 'vault init' to create one.[/]")
        return
    console.print(f"[bold cyan]Vault status[/]")
    console.print(f"  Attempts left: {record.get('attempts_left')}/{record.get('max_attempts')}")
    console.print(f"  Location: {VAULT_FILE}")


def vault_reset() -> None:
    if not VAULT_FILE.exists():
        console.print("[yellow]No vault to reset.[/]")
        return
    answer = prompt("This deletes the vault and ALL secrets permanently. Continue? [y/N] ").strip().lower()
    if answer == "y":
        VAULT_FILE.unlink()
        console.print("[green]Vault deleted.[/]")
    else:
        console.print("[dim]Cancelled[/dim]")


def cmd_vault(args: list[str]) -> None:
    if not args:
        console.print("[yellow]Usage: vault init|add=<name>|get=<name>|delete=<name>|list|status|reset[/yellow]")
        return

    sub = args[0]
    if sub == "init":
        vault_init()
    elif sub == "list":
        vault_list()
    elif sub == "status":
        vault_status()
    elif sub == "reset":
        vault_reset()
    elif sub.startswith("add="):
        vault_add(sub[len("add="):])
    elif sub.startswith("get="):
        vault_get(sub[len("get="):])
    elif sub.startswith("delete="):
        vault_delete(sub[len("delete="):])
    else:
        console.print(f"[red]unknown vault subcommand: {sub}[/red]")

# ---------------------------------------------------------------------------
# Dispatcher and main
# ---------------------------------------------------------------------------

def dispatch(text: str) -> bool:
    """Returns false if repl needs to be competed."""
    try:
        parts = shlex.split(text)
    except ValueError as exc:
        console.print(f"[red]Command error: {exc}[/red]")
        return True

    if not parts:
        return True

    cmd, *args = parts

    if cmd in ("exit", "quit"):
        return False
    elif cmd == "scan":
        cmd_scan(args)
    elif cmd == "diagram":
        cmd_diagram(args)
    elif cmd == "history_delete":
        cmd_history_delete()
    elif cmd == "support":
        cmd_support()
    elif cmd == "version":
        console.print("[yellow]Beta 0.0.2[/]")
    elif cmd == "scan_path":
        cmd_export(args)
    elif cmd=="config":
         config_cmd(args)
    elif cmd == "vault":
        cmd_vault(args)
    else:
        console.print(f"[red]Unknown command: {cmd}[/red]  (type [bold yellow]support[/] for the list)")
    return True


def main() -> None:
    console.print("[red]CODE_PULSE[/] — type [bold]support[/bold] for the list of commands, [bold]exit[/bold] to exit the program\n.")
    console.print(r"""[red]
    
    
           /\  
          /  \
      ___/    \    /‾‾‾
               \  /
                \/

    [/]""")
    if not CONFIG["user_local_name"]:
        new_name=prompt("Enter your name:").strip()
        CONFIG["user_local_name"]=new_name or "user"
        save_config()
    console.print(f"Hi, {CONFIG["user_local_name"]}")
    while True:
        try:
            text = prompt("» ", completer=completer_structure)
        except (KeyboardInterrupt, EOFError):
            break

        if not dispatch(text):
            break


if __name__ == "__main__":
    main()
