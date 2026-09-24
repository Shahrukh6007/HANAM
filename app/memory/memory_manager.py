import json
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "memory.json"


def load_memory():
    with open(MEMORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=4)


def add_fact(fact):
    memory = load_memory()

    if fact not in memory["facts"]:
        memory["facts"].append(fact)

    save_memory(memory)


def get_facts():
    memory = load_memory()
    return memory["facts"]


def remove_fact(fact):
    memory = load_memory()

    if fact in memory["facts"]:
        memory["facts"].remove(fact)

    save_memory(memory)


def set_user_info(key, value):
    memory = load_memory()

    if "user" not in memory:
        memory["user"] = {}

    memory["user"][key] = value

    save_memory(memory)


def get_user_info(key=None):
    memory = load_memory()
    user = memory.get("user", {})

    if key is None:
        return user

    return user.get(key)


def add_preference(preference):
    memory = load_memory()

    if "preferences" not in memory:
        memory["preferences"] = []

    if preference not in memory["preferences"]:
        memory["preferences"].append(preference)

    save_memory(memory)


def get_preferences():
    memory = load_memory()
    return memory.get("preferences", [])


def remove_preference(preference):
    memory = load_memory()

    preferences = memory.get("preferences", [])

    if preference in preferences:
        preferences.remove(preference)

    save_memory(memory)


def set_favorite(category, value):
    memory = load_memory()

    if "favorites" not in memory:
        memory["favorites"] = {}

    memory["favorites"][category] = value

    save_memory(memory)


def get_favorite(category):
    memory = load_memory()
    favorites = memory.get("favorites", {})

    return favorites.get(category)


def remove_favorite(category):
    memory = load_memory()

    favorites = memory.get("favorites", {})

    if category in favorites:
        del favorites[category]

    save_memory(memory)


def add_summary(session_id, summary_text):
    """Store or replace a summary for a session. Keeps the last 20."""
    memory = load_memory()

    if "summaries" not in memory:
        memory["summaries"] = []

    # Replace if a summary for this session already exists
    memory["summaries"] = [
        s for s in memory["summaries"] if s.get("session_id") != session_id
    ]

    memory["summaries"].append(
        {
            "session_id": session_id,
            "summary": summary_text,
        }
    )

    memory["summaries"] = memory["summaries"][-20:]

    save_memory(memory)


def get_summaries(limit=None):
    """Return recent session summaries."""
    memory = load_memory()
    summaries = memory.get("summaries", [])
    if limit:
        return summaries[-limit:]
    return summaries


def get_memory_context():
    memory = load_memory()

    parts = []

    user = memory.get("user", {})

    if user:
        for key, value in user.items():
            parts.append(f"{key}: {value}")

    preferences = memory.get("preferences", [])

    if preferences:
        parts.append("Preferences: " + ", ".join(preferences))

    facts = memory.get("facts", [])

    if facts:
        parts.append("Facts:\n" + "\n".join(f"- {fact}" for fact in facts))

    summaries = memory.get("summaries", [])

    if summaries:
        recent = summaries[-3:]
        parts.append(
            "Recent sessions:\n"
            + "\n".join(
                f"- [{s.get('session_id', '?')}] {s.get('summary', '')}" for s in recent
            )
        )

    return "\n".join(parts)


def get_memory_answer(question):
    text = question.lower().strip()
    memory = load_memory()

    if text in [
        "what is my name?",
        "what is my name",
        "what's my name?",
        "what's my name",
    ]:
        name = memory.get("user", {}).get("name")

        if name:
            return f"Your name is {name}."

        return "I don't know your name yet."

    if text in [
        "what do i like?",
        "what do i like",
        "what do i prefer?",
        "what do i prefer",
        "what are my preferences?",
        "what are my preferences",
    ]:
        preferences = memory.get("preferences", [])

        if preferences:
            return "You like: " + ", ".join(preferences) + "."

        return "I don't have any saved preferences yet."

    if text in [
        "what am i building?",
        "what am i building",
        "what are you helping me build?",
        "what are you helping me build",
    ]:
        facts = memory.get("facts", [])

        for fact in facts:
            if "building HANAM" in fact:
                return "You're building HANAM, your local personal AI assistant."

        return "I don't have that information saved."

    if text in [
        "what is my favorite programming language?",
        "what is my favorite programming language",
        "what's my favorite programming language?",
        "what's my favorite programming language",
    ]:
        language = memory.get("favorites", {}).get("programming_language")

        if language:
            return f"Your favorite programming language is {language}."

        return "I don't know your favorite programming language yet."

    return None
