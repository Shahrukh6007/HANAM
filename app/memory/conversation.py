"""Persistent conversation sessions for HANAM.

Every session is saved to app/memory/sessions/<id>.json.
The LLM only sees the last MAX_MESSAGES turns — the full history
stays on disk.
"""

import json
from datetime import datetime
from pathlib import Path

SESSION_DIR = Path(__file__).parent / "sessions"
MAX_MESSAGES = 20

_conversation = []
_current_session_id = None


def _ensure_dir():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)


def _path_for(session_id):
    return SESSION_DIR / f"{session_id}.json"


def _new_id():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def _save_current():
    if _current_session_id is None:
        return
    _ensure_dir()
    path = _path_for(_current_session_id)
    now = datetime.now().isoformat(timespec="seconds")

    created_at = now
    if path.exists():
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
            created_at = old.get("created_at", now)
        except Exception:
            pass

    data = {
        "id": _current_session_id,
        "created_at": created_at,
        "updated_at": now,
        "messages": _conversation,
    }
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def start_new_session():
    """Start a fresh session. The old one stays on disk."""
    global _conversation, _current_session_id
    _conversation = []
    _current_session_id = _new_id()
    _save_current()
    return _current_session_id


def load_session(session_id):
    """Load a specific session by id. Returns True on success."""
    global _conversation, _current_session_id
    path = _path_for(session_id)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    _conversation = data.get("messages", [])
    _current_session_id = session_id
    return True


def load_latest_session():
    """Load the most recent session. Returns its id, or None."""
    _ensure_dir()
    files = sorted(SESSION_DIR.glob("*.json"))
    if not files:
        return None
    latest_id = files[-1].stem
    if load_session(latest_id):
        return latest_id
    return None


def list_sessions():
    """Return a list of all sessions, newest first."""
    _ensure_dir()
    sessions = []
    for f in sorted(SESSION_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        sessions.append(
            {
                "id": f.stem,
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "message_count": len(data.get("messages", [])),
            }
        )
    return sessions


def get_current_session_id():
    return _current_session_id


def add_message(role, content):
    """Append a message and save to disk immediately."""
    _conversation.append({"role": role, "content": content})
    _save_current()


def get_conversation():
    """Return the recent window for the LLM context."""
    return _conversation[-MAX_MESSAGES:]


def get_full_conversation():
    """Return the entire current session history."""
    return list(_conversation)


def clear_conversation():
    """Deprecated — use start_new_session(). Kept for compatibility."""
    return start_new_session()
