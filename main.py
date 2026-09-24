import threading

from app.memory.context_builder import build_context
from app.memory.summarizer import summarize_current_session
from app.agent.agent import process_request
from app.llm.cloud_router import ask_hanam_bulletproof as ask_hanam
from app.memory.conversation import (
    add_message,
    get_current_session_id,
    list_sessions,
    load_latest_session,
    load_session,
    start_new_session,
)
from app.memory.memory_classifier import classify_memory
from app.memory.memory_manager import (
    set_user_info,
    add_preference,
    add_fact,
    set_favorite,
)


def show_sessions():
    sessions = list_sessions()
    if not sessions:
        print("HANAM: No saved sessions yet.")
        return
    print("HANAM: Sessions (newest first):")
    current = get_current_session_id()
    for s in sessions[:20]:
        marker = " <- current" if s["id"] == current else ""
        print(f"  {s['id']}  ({s['message_count']} msgs){marker}")


def handle_slash(prompt):
    """Return True if the prompt was a command we handled."""
    text = prompt.strip()

    if text == "/help":
        print("HANAM: Commands:")
        print("  /new           — start a new session")
        print("  /sessions      — list all sessions")
        print("  /resume <id>   — load a specific session")
        print("  /summarize     — summarize this session into memory")
        print("  /id            — show current session id")
        print("  /help          — show this help")
        print("  quit / exit    — exit HANAM")
        return True

    if text == "/id":
        print(f"HANAM: Current session: {get_current_session_id()}")
        return True

    if text == "/new":
        sid = start_new_session()
        print(f"HANAM: Started new session: {sid}")
        return True

    if text == "/summarize":
        print("HANAM: Summarizing this session...")
        summary = summarize_current_session()
        if summary:
            print(f"HANAM: Summary saved: {summary}")
        else:
            print("HANAM: Nothing to summarize (session is empty).")
        return True

    if text == "/sessions":
        show_sessions()
        return True

    if text.startswith("/resume "):
        sid = text[8:].strip()
        if load_session(sid):
            print(f"HANAM: Resumed session {sid}.")
        else:
            print(f"HANAM: Session '{sid}' not found.")
        return True

    return False


print("HANAM is starting...")

_resumed = load_latest_session()
if _resumed is None:
    start_new_session()
    print("HANAM: New session started.")
else:
    print(f"HANAM: Resumed session {_resumed}.")
print("Type /help for commands.\n")


# Pre-warm the intent gate so the first user message isn't slow.
# Runs in the background while you read the welcome message.
def _prewarm():
    try:
        from app.agent.intent_gate import needs_tool

        needs_tool("hello")
    except Exception:
        pass


threading.Thread(target=_prewarm, daemon=True).start()

while True:
    prompt = input("You: ")

    if prompt.lower() in ["exit", "quit"]:
        print("HANAM: Session saved. Goodbye!")
        break

    if prompt.startswith("/"):
        if handle_slash(prompt):
            continue

    tool_result = process_request(prompt)

    if tool_result is not None:
        print("HANAM:", tool_result)
        add_message("user", prompt)
        add_message("assistant", str(tool_result)[:2000])
        continue

    memory_type = classify_memory(prompt)

    if memory_type:
        memory_category, value = memory_type

        if memory_category == "user_name":
            set_user_info("name", value)
        elif memory_category == "preference":
            add_preference(value)
        elif memory_category == "fact":
            add_fact(value)
        elif memory_category == "favorite_programming_language":
            set_favorite("programming_language", value)

    add_message("user", prompt)

    messages = build_context()

    prompt_lower = prompt.lower()
    tool_hints = (
        "file",
        "folder",
        "directory",
        "read",
        "open",
        "show",
        "list",
        "find",
        "search",
        "run",
        "execute",
        "system",
        "info",
        "code",
        "project",
        "delete",
        "remove",
        "rename",
    )
    use_tools = any(hint in prompt_lower for hint in tool_hints)

    try:
        response = ask_hanam(prompt, messages=messages, use_tools=use_tools)
        add_message("assistant", response)
        print("HANAM:", response)
    except Exception as error:
        print("HANAM: I'm unable to reach my AI service right now.")
        print(f"HANAM system: {error}")
