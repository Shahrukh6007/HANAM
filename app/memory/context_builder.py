import platform

from app.memory.memory_manager import get_memory_context
from app.memory.conversation import get_conversation
from app.context.repo_map import get_repo_map


def build_context():
    memory_context = get_memory_context()
    repo_map = get_repo_map()
    os_name = f"{platform.system()} {platform.release()}"

    system_content = (
        "You are HANAM, a local coding and general-purpose assistant.\n\n"
        f"Operating system: {os_name}\n"
        "Use Windows commands (dir, type, where, tasklist) — not Unix "
        "commands (ls, cat, which, grep) — unless the user is clearly "
        "asking about Unix.\n\n"
        "Project structure (the workspace you can read and write):\n"
        f"{repo_map}\n\n"
        "If the user asks about the project structure, answer directly "
        "from the project tree above. Do not run commands to inspect the "
        "project — you already have the tree.\n\n"
        "You have access to tools for reading, creating, editing, and "
        "listing files, searching the codebase, running shell commands, "
        "and inspecting the system. Prefer calling a tool over describing "
        "what you would do.\n\n"
        "Be concise. Skip pleasantries. Show code, not descriptions of code."
    )

    if memory_context:
        system_content += (
            "\n\nHere is the user's persistent memory. Use it when relevant, "
            "but do not mention the memory system unless the user asks about it.\n\n"
            f"{memory_context}"
        )

    system_message = {
        "role": "system",
        "content": system_content,
    }

    return [system_message] + get_conversation()
