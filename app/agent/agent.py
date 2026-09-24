from app.memory.memory_manager import get_memory_answer, set_favorite
from app.llm.cloud_router import ask_hanam_bulletproof
from app.core.intent_detector import detect_intent
from app.memory.memory_classifier import classify_memory
from app.tools.shell_tools import run_command
from app.tools.file_tools import (
    read_file,
    list_files,
    create_file,
    write_file,
    grep,
    grep_project,
)
from app.tools.system_tools import get_system_info
from app.agent.llm_tools import try_llm_tools
from app.memory.memory_manager import (
    add_fact,
    get_facts,
    remove_fact,
    set_user_info,
    get_user_info,
    add_preference,
    get_preferences,
    remove_preference,
    remove_favorite,
)


def get_filename_from_prompt(prompt):
    words = prompt.split()

    for word in words:
        cleaned = word.strip("`'\".,:!?")

        if "." in cleaned and not cleaned.startswith("http"):
            return cleaned

    return None


def process_request(prompt):
    """Handle tool and memory requests before sending other requests to the AI."""
    intent = detect_intent(prompt)

    memory_answer = get_memory_answer(prompt)

    if memory_answer is not None:
        return memory_answer

    memory_type = classify_memory(prompt)

    if memory_type:
        memory_category, value = memory_type

        if memory_category == "forget_favorite_programming_language":
            remove_favorite("programming_language")
            return "I forgot your favorite programming language."

    if intent == "remember_fact":
        fact = prompt.strip()

        if fact.lower().startswith("remember that "):
            fact = fact[14:].strip()
        elif fact.lower().startswith("remember "):
            fact = fact[9:].strip()

        if not fact:
            return "Please tell me what you want me to remember."

        memory_type, value = classify_memory(fact)

        if memory_type == "user_name":
            set_user_info("name", value)
            return f"I'll remember that your name is {value}."

        if memory_type == "preference":
            add_preference(value)
            return f"I'll remember that you like {value}."

        if memory_type == "favorite_programming_language":
            set_favorite("programming_language", value)
            return f"I'll remember that your favorite programming language is {value}."

        add_fact(value)
        return f"I'll remember that: {value}"

    if intent == "recall_memory":
        user = get_user_info()
        preferences = get_preferences()
        facts = get_facts()

        memories = []

        if user:
            for key, value in user.items():
                memories.append(f"{key}: {value}")

        memories.extend(f"Preference: {preference}" for preference in preferences)

        memories.extend(f"Fact: {fact}" for fact in facts)

        if not memories:
            return "I don't have any saved memories yet."

        return "Here's what I remember:\n" + "\n".join(
            f"- {memory}" for memory in memories
        )

    if intent == "forget_fact":
        fact = prompt.strip()

        if fact.lower().startswith("forget that "):
            fact = fact[12:].strip()
        elif fact.lower().startswith("forget "):
            fact = fact[7:].strip()

        if not fact:
            return "Please tell me what you want me to forget."

        memory_type, value = classify_memory(fact)

        if memory_type == "user_name":
            current_name = get_user_info("name")

            if current_name == value:
                set_user_info("name", None)

                memory = get_user_info()

                if "name" in memory:
                    del memory["name"]

                from app.memory.memory_manager import load_memory, save_memory

                data = load_memory()
                data["user"] = memory
                save_memory(data)

            return f"I forgot that your name is {value}."

        if memory_type == "preference":
            remove_preference(value)
            return f"I forgot that you like {value}."

        remove_fact(value)
        return f"I forgot that: {value}"

    if intent == "list_files":
        return list_files()

    if intent == "read_file":
        prompt_lower = prompt.lower().strip()

        read_triggers = [
            "read file ",
            "read ",
            "open ",
            "show me ",
            "can you open ",
            "please read ",
            "what does ",
            "what's inside ",
            "whats inside ",
            "what is inside ",
            "show me what's in ",
            "show me whats in ",
            "show me the contents of ",
        ]

        for trigger in read_triggers:
            if prompt_lower.startswith(trigger):
                filename = prompt[len(trigger) :].strip()
                filename = filename.strip("`'\".,!?")

                if filename:
                    return read_file(filename)

                return "Please specify a filename."

        filename = get_filename_from_prompt(prompt)

        if filename:
            return read_file(filename)

        return "Please specify a filename."

    if intent == "create_file":
        filename = get_filename_from_prompt(prompt)

        if not filename:
            return "Please specify a filename."

        generation_prompt = (
            f"The user wants to create a file based on this request: '{prompt}'.\n"
            "Generate ONLY the raw code or text content that should go inside this file. "
            "Do not include markdown code block backticks unless they are part of the file. "
            "Do not include conversational filler text. "
            "Just output the clean file contents."
        )

        file_content = ask_hanam_bulletproof(generation_prompt)

        return create_file(filename, file_content)

    if intent == "edit_file":
        prompt_lower = prompt.lower().strip()

        # Only handle the explicit "edit file x.txt: content" syntax here.
        # Everything else falls through to the LLM tool path (edit_file
        # with old_text/new_text) — that's where surgical edits belong.
        if prompt_lower.startswith("edit file "):
            data = prompt[10:].strip()

            if ":" not in data:
                return "Use: edit file filename.txt: new content"

            filename, content = data.split(":", 1)

            filename = filename.strip("`'\" .,!?")
            content = content.strip()

            if not filename:
                return "Please specify a filename."

            return write_file(filename, content)

        # Not the explicit format — let the LLM handle it.
        return None

    if intent == "get_system_info":
        return get_system_info()

    if intent == "test_and_fix":
        from app.agent.test_loop import test_and_fix

        return test_and_fix()

    if intent == "run_command":
        cmd = prompt.strip()
        for trigger in [
            "run the command ",
            "run command ",
            "execute command ",
            "execute ",
            "run ",
            "$ ",
        ]:
            if cmd.lower().startswith(trigger):
                cmd = cmd[len(trigger) :].strip()
                break
        if not cmd:
            return "Please specify a command to run."
        return run_command(cmd)

    if intent == "grep_project":
        pattern = prompt.strip()

        # Strip leading trigger words.
        for trigger in [
            "find ",
            "search for ",
            "search ",
            "where is ",
            "where are ",
            "grep ",
            "locate ",
        ]:
            if pattern.lower().startswith(trigger):
                pattern = pattern[len(trigger) :].strip()
                break

        # Strip trailing "in the codebase" / "in the project" etc.
        for suffix in [
            " in the codebase",
            " in the project",
            " in the source",
            " in hanam",
            " in the app",
            " in app",
            " in my code",
            " in the code",
            " across the project",
            " across the codebase",
        ]:
            if pattern.lower().endswith(suffix):
                pattern = pattern[: -len(suffix)].strip()
                break

        # Strip filler words from both ends. These are words users add
        # naturally but aren't part of the identifier they're looking for.
        FILLER = {
            "the",
            "a",
            "an",
            "defined",
            "declared",
            "located",
            "used",
            "called",
            "imported",
            "instantiated",
            "referenced",
            "function",
            "class",
            "method",
            "variable",
        }
        words = pattern.split()
        while words and words[0].lower() in FILLER:
            words.pop(0)
        while words and words[-1].lower() in FILLER:
            words.pop()
        pattern = " ".join(words)

        if not pattern:
            return "Please specify what to search for."

        return grep_project(pattern)

    if intent == "grep":
        pattern = prompt.strip()

        # Strip polite prefixes first ("can you ", "please ", etc.)
        for prefix in [
            "can you ",
            "could you ",
            "please ",
            "i want to ",
            "i need to ",
            "help me ",
            "would you ",
        ]:
            if pattern.lower().startswith(prefix):
                pattern = pattern[len(prefix) :].strip()
                break

        # Now strip the search trigger word.
        for trigger in [
            "find ",
            "search for ",
            "search ",
            "where is ",
            "where are ",
            "grep ",
            "locate ",
        ]:
            if pattern.lower().startswith(trigger):
                pattern = pattern[len(trigger) :].strip()
                break

        # Drop trailing "in X" (e.g. " in the workspace").
        pattern = pattern.split(" in ")[0].strip("`'\".,!?")

        # Strip filler words from both ends (same as grep_project does).
        FILLER = {
            "the", "a", "an",
            "defined", "declared", "located", "used", "called",
        }
        words = pattern.split()
        while words and words[0].lower() in FILLER:
            words.pop(0)
        while words and words[-1].lower() in FILLER:
            words.pop()
        pattern = " ".join(words)

        if not pattern:
            return "Please specify what to search for."
        return grep(pattern)

    # --- Smart path (LLM tool calling) ---
    prompt_lower = prompt.lower()

    # Skip for content generation — those use the old fast path.
    content_words = ("create", "write", "generate", "make a file", "new file")
    if any(word in prompt_lower for word in content_words):
        return None

    # Ask the fast local gate: does this need a tool?
    from app.agent.intent_gate import needs_tool

    if not needs_tool(prompt):
        return None  # plain chat — skip tool calling entirely

    result = try_llm_tools(prompt)
    if result is not None:
        return result

    return None


def ask_hanam(prompt):
    """Send a normal request through HANAM's cloud/local AI fallback."""
    return ask_hanam_bulletproof(prompt)
