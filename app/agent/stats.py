"""Reads provider health/stats and memory counts, formats them for display."""

import time
from pathlib import Path
import json

from app.core.provider_state import load_provider_state
from app.core.provider_stats import get_provider_stats
from app.llm.cloud_router import PROVIDERS


def _status_icon(health):
    if health.get("disabled"):
        return "❌ disabled"
    failed_at = health.get("failed_at", 0)
    cooldown = health.get("cooldown", 0)
    if failed_at and cooldown:
        remaining = int(cooldown - (time.time() - failed_at))
        if remaining > 0:
            return f"⏸ cooling ({remaining}s)"
    return "✅ healthy"


def _format_providers():
    lines = []
    lines.append(
        f"{'Provider':<15} {'Status':<18} {'Calls':<7} {'Success':<9} {'Avg':<8}"
    )
    lines.append("─" * 62)

    for p in PROVIDERS:
        name = p["name"]
        health = load_provider_state(name)
        stats = get_provider_stats(name)

        total = stats.get("total_requests", 0)
        success = stats.get("successful_requests", 0)
        total_time = stats.get("total_response_time", 0.0)

        if total > 0:
            success_rate = f"{success / total * 100:.0f}%"
            avg = f"{total_time / success:.2f}s" if success else "—"
        else:
            success_rate = "—"
            avg = "—"

        status = _status_icon(health)
        lines.append(f"{name:<15} {status:<18} {total:<7} {success_rate:<9} {avg:<8}")

    return "\n".join(lines)


def format_providers():
    """Short provider-only view."""
    lines = ["Cloud providers:", "", _format_providers()]
    lines.append("")
    lines.append("Local fallback:")
    lines.append(f"{'Ollama':<15} {'✅ ready':<18} {'—':<7} {'—':<9} {'—':<8}")
    return "\n".join(lines)


def format_stats():
    """Full stats: providers + memory + session."""
    lines = []

    lines.append("Providers")
    lines.append(_format_providers())

    # --- Memory ---
    memory_path = Path(__file__).resolve().parents[1] / "memory" / "memory.json"
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            memory = json.load(f)
    except Exception:
        memory = {}

    facts = len(memory.get("facts", []))
    prefs = len(memory.get("preferences", []))
    favs = len(memory.get("favorites", {}))
    summaries = len(memory.get("summaries", []))
    user_keys = len(memory.get("user", {}))

    lines.append("")
    lines.append("Memory")
    lines.append(f"  User info:     {user_keys}")
    lines.append(f"  Facts:         {facts}")
    lines.append(f"  Preferences:   {prefs}")
    lines.append(f"  Favorites:     {favs}")
    lines.append(f"  Summaries:     {summaries}")

    # --- Session ---
    try:
        from app.memory.conversation import (
            get_current_session_id,
            get_full_conversation,
        )

        session_id = get_current_session_id() or "(none)"
        msg_count = len(get_full_conversation())
    except Exception:
        session_id = "(unknown)"
        msg_count = 0

    lines.append("")
    lines.append("Session")
    lines.append(f"  ID:            {session_id}")
    lines.append(f"  Messages:      {msg_count}")

    return "\n".join(lines)
