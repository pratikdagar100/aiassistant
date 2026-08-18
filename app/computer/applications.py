"""Generic application launching (spec section 21) — NOT hardcoded to a
fixed list of apps. Resolution order: exact file path, then PATH lookup,
then Windows' own App Paths / protocol resolution via os.startfile (this is
how `notepad`, `calc`, `chrome`, or even a URL all just work without this
module knowing anything about them specifically).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class ApplicationError(RuntimeError):
    pass


def launch(target: str, args: list[str] | None = None) -> dict:
    args = args or []

    p = Path(target)
    if p.exists():
        if args:
            subprocess.Popen([str(p), *args])
        else:
            os.startfile(str(p))  # noqa: S606 — intentional, this is the tool's purpose
        return {"launched": str(p), "method": "path"}

    resolved = shutil.which(target)
    if resolved:
        subprocess.Popen([resolved, *args])
        return {"launched": resolved, "method": "PATH"}

    try:
        os.startfile(target)  # noqa: S606 — handles registered app names, URLs, protocols
        return {"launched": target, "method": "startfile"}
    except OSError as exc:
        raise ApplicationError(f"Could not launch '{target}': {exc}") from exc


def close_by_process_name(process_name: str) -> dict:
    name = process_name if process_name.lower().endswith(".exe") else f"{process_name}.exe"
    proc = subprocess.run(
        ["taskkill", "/IM", name, "/F"], capture_output=True, text=True, timeout=10
    )
    if proc.returncode != 0:
        raise ApplicationError(f"taskkill failed for '{name}': {proc.stderr.strip() or proc.stdout.strip()}")
    return {"closed_process": name}


def list_processes() -> list[dict]:
    proc = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=10
    )
    processes = []
    for line in proc.stdout.splitlines():
        parts = [f.strip('"') for f in line.split('","')]
        if len(parts) >= 2:
            processes.append({"name": parts[0].strip('"'), "pid": parts[1]})
    return processes
