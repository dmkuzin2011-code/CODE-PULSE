from __future__ import annotations
import json
import os
import shlex
import time
from dataclasses import dataclass
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.completion import NestedCompleter, PathCompleter
from rich.console import Console

console = Console()

HISTORY_FILE = Path(os.path.expanduser("~/.config/code-pulse/history.json"))


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
    "version":{"control":None},
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
    entries = result.data

    if not args:
        console.print("[bold cyan]Scan history:[/bold cyan]")
        for i, e in enumerate(entries, 1):
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e["timestamp"]))
            console.print(f"  [{i}] {ts}  {e['path']}  ({e['total_files']} files, {_human_size(e['total_bytes'])})")
        console.print("\n[dim]Use: export <number> [file=<path>][/dim]")
        return
    try:
        idx = int(args[0]) - 1
        if idx < 0 or idx >= len(entries):
            raise ValueError
    except ValueError:
        console.print(f"[red]Invalid number. Use 1-{len(entries)}[/red]")
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
        console.print("[yellow]Usage: diagram layer=<path>[/yellow]")
        return

    layer = os.path.abspath(args[0][len("layer="):])
    entries = [e for e in _load_history().data if e["path"] == layer]

    if not entries:
        console.print(f"[yellow]No scan history {layer}. To begin perform scan path={layer} info[/yellow]")
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
    if not entries:
        console.print("[yellow]History is empty[/yellow]")
        return

    answer = prompt(f"Delete all history ({len(entries.data)} records)? [y/N] ").strip().lower()
    if answer == "y":
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
    console.print("  version control            — you can control [yellow]version[/].")
    console.print("  exit / quit                — bye.")
    console.print("  save scan_path             — you can save information about scan.")

# ---------------------------------------------------------------------------
# Вспомогательное
# ---------------------------------------------------------------------------

def _human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0 or unit == "TB":
            return f"{size:.1f}{unit}" if unit != "B" else f"{int(size)}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"


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
        console.print("[yellow]Beta 0.0.1[/]")
    elif cmd == "scan_path":
        cmd_export(args)
    else:
        console.print(f"[red]Unknown command: {cmd}[/red]  (type [bold yellow]support[/] for the list)")

    return True


def main() -> None:
    console.print("[bold cyan]CODE_PULSE[/bold cyan][red]⁓[/] — type [bold]support[/bold] for the list of commands, [bold]exit[/bold] to exit the program\n.")
    while True:
        try:
            text = prompt("» ", completer=completer_structure)
        except (KeyboardInterrupt, EOFError):
            break

        if not dispatch(text):
            break


if __name__ == "__main__":
    main()
