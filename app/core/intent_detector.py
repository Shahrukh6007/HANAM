def detect_intent(prompt):
    text = prompt.lower().strip()

    if any(
        phrase in text
        for phrase in [
            "list files",
            "list the files",
            "list all files",
            "list my files",
            "list workspace files",
            "show workspace files",
            "show me my workspace files",
            "show the files",
            "what files are in my workspace",
            "what files have i created",
            "what files exist",
            "files in my workspace",
            "files in the workspace",
            "files are in my workspace",
        ]
    ):
        return "list_files"

    if any(
        phrase in text
        for phrase in [
            "test and fix",
            "tests and fix",
            "fix the tests",
            "fix failing tests",
            "run tests and fix",
            "auto fix tests",
        ]
    ):
        return "test_and_fix"

    # run_command.
    if text.startswith("run ") or text.startswith("execute ") or text.startswith("$ "):
        return "run_command"

    # --- Search intents ---
    # Must have a search verb, otherwise it's just chat.
    has_search_verb = any(
        phrase in text
        for phrase in [
            "find ",
            "search for ",
            "search ",
            "where is ",
            "where are ",
            "grep ",
            "locate ",
        ]
    )

    if has_search_verb:
        if any(
            phrase in text
            for phrase in [
                "in the codebase",
                "in the project",
                "in the source",
                "in hanam",
                "in app",
                "in the app",
                "hanam's source",
                "in my code",
                "in the code",
                "across the project",
                "across the codebase",
            ]
        ):
            return "grep_project"

        return "grep"

    if any(
        phrase in text
        for phrase in [
            "read file",
            "read ",
            "open ",
            "show ",
            "what's inside",
            "whats inside",
            "what is inside",
            "show me what's in",
            "show me whats in",
            "show me the contents of",
            "what does",
        ]
    ):
        return "read_file"

    if any(
        phrase in text
        for phrase in [
            "create file",
            "create a file",
            "write file",
            "save file",
            "make a file",
            "make me a file",
        ]
    ):
        return "create_file"

    if text.startswith("edit file "):
        return "edit_file"

    if any(phrase in text for phrase in ["change ", "modify ", "update "]):
        return "edit_file"

    if any(
        phrase in text
        for phrase in [
            "system information",
            "system info",
            "computer information",
            "computer specs",
            "my computer specs",
            "what are my computer specs",
        ]
    ):
        return "get_system_info"

    if text.startswith("remember "):
        return "remember_fact"

    if text.startswith("remember that "):
        return "remember_fact"

    if any(
        phrase in text
        for phrase in [
            "what do you remember",
            "what do you know about me",
            "show my memory",
            "show me my memory",
            "show remembered facts",
        ]
    ):
        return "recall_memory"

    if text.startswith("forget "):
        return "forget_fact"

    if text.startswith("forget that "):
        return "forget_fact"

    return "chat"
