import json
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / "provider_state.json"


def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)


def save_provider_state(provider, health):
    state = load_state()

    state[provider] = {
        "failed_at": health["failed_at"],
        "cooldown": health["cooldown"],
        "disabled": health["disabled"]
    }

    save_state(state)


def load_provider_state(provider):
    state = load_state()

    return state.get(
        provider,
        {
            "failed_at": 0,
            "cooldown": 0,
            "disabled": False
        }
    )