"""Watch mode: rebuild the PDF whenever content, assets or code change.

Same approach as the lookbook and the brochure. Every rebuild runs in a fresh
Python process: Python caches imported modules, so rebuilding in-process would
ignore edits to the code itself (``theme.py``, the faces, ...). Change detection polls
modification times: no extra dependency and, for a few dozen files, no cost.
"""

from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from .builder import BuildOptions

PACKAGE_DIR = Path(__file__).resolve().parent
POLL_INTERVAL = 0.5  # seconds between scans
SETTLE_DELAY = 0.3  # editors may write a file in several steps
IGNORED_PARTS = frozenset({"__pycache__"})

Snapshot = dict[Path, int]


def snapshot(roots: Iterable[Path]) -> Snapshot:
    """Modification time (ns) of every file under ``roots``."""
    files: Snapshot = {}
    for root in roots:
        for path in root.rglob("*"):
            if IGNORED_PARTS.intersection(path.parts):
                continue
            try:
                if path.is_file():
                    files[path] = path.stat().st_mtime_ns
            except FileNotFoundError:  # deleted while scanning
                continue
    return files


def changed_files(before: Snapshot, after: Snapshot) -> set[Path]:
    """Files added, removed or modified between two snapshots."""
    modified = {path for path in before.keys() & after.keys() if before[path] != after[path]}
    return (before.keys() ^ after.keys()) | modified


def build_command(options: BuildOptions) -> list[str]:
    flags = (
        (["--no-bleed"] if not options.bleed else [])
        + (["--marks"] if options.marks else [])
        + (["--guides"] if options.guides else [])
    )
    return [
        sys.executable,
        "-m",
        "monpiz_segnalibro",
        "build",
        "--content",
        str(options.content_file),
        "--assets",
        str(options.assets_dir),
        "--output",
        str(options.output),
        "--dpi",
        str(options.dpi),
        *flags,
    ]


def _rebuild(command: list[str], reason: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {reason}", flush=True)
    subprocess.run(command, check=False)  # output and errors go straight to the terminal


def watch(options: BuildOptions) -> None:
    """Build the PDF once, then again on every change until interrupted (Ctrl+C)."""
    roots = [options.content_file.parent, options.assets_dir, PACKAGE_DIR]
    command = build_command(options)
    print("In ascolto su: " + ", ".join(str(root) for root in roots), flush=True)
    print("Premi Ctrl+C per uscire.", flush=True)

    previous = snapshot(roots)
    _rebuild(command, "Build iniziale")
    while True:
        time.sleep(POLL_INTERVAL)
        if not changed_files(previous, snapshot(roots)):
            continue
        time.sleep(SETTLE_DELAY)
        current = snapshot(roots)
        changes = changed_files(previous, current)
        previous = current
        if changes:  # empty when an editor's temporary file is already gone
            _rebuild(command, "Modificato: " + ", ".join(sorted(path.name for path in changes)))
