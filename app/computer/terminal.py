"""Terminal access (spec section 20). Every call returns stdout, stderr, and
returncode explicitly — callers (the agent, Phase 8) must check returncode
themselves rather than assuming success from the absence of an exception.
"""

from __future__ import annotations

import subprocess


class TerminalResult:
    def __init__(self, command: str, returncode: int, stdout: str, stderr: str, timed_out: bool = False):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out
        self.success = returncode == 0 and not timed_out

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "timed_out": self.timed_out,
            "success": self.success,
        }


def _run(args: list[str], timeout: float) -> TerminalResult:
    command_str = " ".join(args)
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return TerminalResult(command_str, proc.returncode, proc.stdout, proc.stderr)
    except subprocess.TimeoutExpired as exc:
        return TerminalResult(
            command_str, -1, exc.stdout or "", (exc.stderr or "") + "\n[timed out]", timed_out=True
        )


def run_powershell(command: str, timeout: float = 60.0) -> TerminalResult:
    return _run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command], timeout)


def run_cmd(command: str, timeout: float = 60.0) -> TerminalResult:
    return _run(["cmd.exe", "/c", command], timeout)


def run_python(code: str, timeout: float = 60.0) -> TerminalResult:
    import sys

    return _run([sys.executable, "-c", code], timeout)
