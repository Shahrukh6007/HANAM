"""Shell command execution for HANAM.

Every command requires explicit user approval before running.
The blocklist catches catastrophic mistakes even if the user
approves without reading.
"""

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MAX_OUTPUT = 8000
TIMEOUT = 120

# Never allowed, even with approval. Catches muscle-memory disasters.
BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf *",
    "format c:",
    "format d:",
    "del /f /s /q c:\\",
    "del /f /s /q d:\\",
    "mkfs",
    "shutdown",
    "reboot",
    ":(){ :|:& };:",
    "> /dev/sda",
]


def _looks_dangerous(cmd: str) -> bool:
    lower = cmd.lower().strip()
    return any(pattern in lower for pattern in BLOCKED_PATTERNS)


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT:
        return text
    return (
        text[:MAX_OUTPUT]
        + f"\n... ({len(text) - MAX_OUTPUT} more chars truncated)"
    )


def run_command(command: str) -> str:
    """Run a shell command in the project root, after user approval."""
    command = (command or "").strip()
    if not command:
        return "No command provided."

    if _looks_dangerous(command):
        return f"Command blocked for safety: {command}"

    print()
    print("[HANAM wants to run]")
    print(f"  {command}")
    try:
        answer = input("Proceed? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "Command cancelled."

    if answer not in ("y", "yes"):
        return f"Command cancelled by user: {command}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return f"Command timed out after {TIMEOUT}s: {command}"
    except Exception as error:
        return f"Command failed to start: {error}"

    parts = []
    if result.stdout:
        parts.append(_truncate(result.stdout.rstrip()))
    if result.stderr:
        parts.append("[stderr]\n" + _truncate(result.stderr.rstrip()))

    output = "\n".join(parts) if parts else "(no output)"
    return f"[exit {result.returncode}]\n{output}"