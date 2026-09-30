"""Quiet-mode-aware logging for HANAM.

When HANAM_QUIET=1 (env var) or /quiet has been toggled on at runtime,
log() does nothing. Only user-facing output and safety prompts remain.
"""

import os


_quiet = os.getenv("HANAM_QUIET", "0") == "1"


def is_quiet():
    return _quiet


def set_quiet(value):
    """Turn quiet mode on or off at runtime."""
    global _quiet
    _quiet = bool(value)


def log(*args, **kwargs):
    """Print unless quiet mode is on."""
    if not _quiet:
        print(*args, **kwargs)


def log_system(msg):
    """Convenience for the standard HANAM System: prefix."""
    if not _quiet:
        print(f"HANAM System: {msg}")

