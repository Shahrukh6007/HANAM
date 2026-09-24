"""Generate a compact tree of the HANAM project for the LLM.

Cached for 30 seconds so we don't walk the filesystem on every turn.
"""

import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SKIP_DIRS = {
    ".git", "venv", ".venv", "__pycache__", "node_modules",
    "dist", "build", "app_v4_backup", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".idea", ".vscode",
}

SKIP_SUFFIXES = {".pyc", ".pyo", ".log", ".tmp", ".bak"}

SKIP_FILES = {
    "structure.txt",
    "main_v4_backup.py",
    ".env",
}

MAX_ENTRIES = 200
MAX_DEPTH = 4
CACHE_TTL = 30

_cache = None
_cache_time = 0.0


def _should_include(path: Path) -> bool:
    if path.name in SKIP_DIRS or path.name in SKIP_FILES:
        return False
    if path.suffix in SKIP_SUFFIXES:
        return False
    return True


def _walk(path: Path, prefix: str, depth: int, lines: list) -> None:
    if depth > MAX_DEPTH or len(lines) >= MAX_ENTRIES:
        return

    try:
        entries = sorted(
            [e for e in path.iterdir() if _should_include(e)],
            key=lambda e: (not e.is_dir(), e.name.lower()),
        )
    except (PermissionError, OSError):
        return

    for i, entry in enumerate(entries):
        if len(lines) >= MAX_ENTRIES:
            return
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if is_last else "│   "
            _walk(entry, prefix + extension, depth + 1, lines)


def build_repo_map() -> str:
    """Build a fresh tree of the project."""
    lines: list = []
    _walk(PROJECT_ROOT, "", 0, lines)

    if not lines:
        return "(empty project)"

    if len(lines) >= MAX_ENTRIES:
        lines.append(f"... (truncated at {MAX_ENTRIES} entries)")

    return "\n".join(lines)


def get_repo_map() -> str:
    """Return a cached repo map. Refreshes every 30 seconds."""
    global _cache, _cache_time
    now = time.time()
    if _cache is None or (now - _cache_time) > CACHE_TTL:
        _cache = build_repo_map()
        _cache_time = now
    return _cache


def invalidate_cache() -> None:
    """Force the next call to rebuild the map."""
    global _cache, _cache_time
    _cache = None
    _cache_time = 0.0