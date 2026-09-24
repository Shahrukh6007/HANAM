from app.tools.file_tools import (
    read_file,
    list_files,
    create_file,
    edit_file,
    write_file,
    grep,
    grep_project,
)
from app.tools.system_tools import get_system_info
from app.tools.shell_tools import run_command

TOOLS = {
    "read_file": read_file,
    "list_files": list_files,
    "create_file": create_file,
    "edit_file": edit_file,
    "write_file": write_file,
    "get_system_info": get_system_info,
    "grep": grep,
    "grep_project": grep_project,
    "run_command": run_command,
}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read and return the contents of a text file inside the "
                "HANAM workspace. Use this before editing a file you "
                "haven't seen yet."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": (
                            "Filename relative to the workspace, "
                            "e.g. 'check.txt' or 'notes.txt'. "
                            "Do NOT prefix with 'workspace/'."
                        ),
                    }
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List all files in the HANAM workspace (where user-created "
                "files live). Use this to see what files exist before "
                "reading or editing. Do NOT use run_command with 'ls' or "
                "'dir' — use this tool instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": (
                "Create a NEW file in the workspace with the given "
                "contents. Fails if the file already exists. Use this only "
                "when the user asks to make a new file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": (
                            "Name of the new file, e.g. 'notes.txt'. "
                            "Do NOT prefix with 'workspace/'."
                        ),
                    },
                    "content": {
                        "type": "string",
                        "description": "Full contents to write into the file.",
                    },
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Surgically replace a specific piece of text in an existing file. "
                "old_text must appear exactly once in the file. Use this for "
                "targeted edits like changing a line, fixing a bug, or renaming "
                "something. Read the file first to see its exact current contents."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": (
                            "Name of the file to edit, e.g. 'check.txt'. "
                            "Do NOT prefix with 'workspace/'."
                        ),
                    },
                    "old_text": {
                        "type": "string",
                        "description": (
                            "The exact text to find and replace. Must appear "
                            "exactly once. Include surrounding lines for uniqueness."
                        ),
                    },
                    "new_text": {
                        "type": "string",
                        "description": (
                            "The replacement text. Leave empty to delete the "
                            "matched text."
                        ),
                    },
                },
                "required": ["filename", "old_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Create a new file or completely overwrite an existing one. "
                "Use this only when the user explicitly asks to rewrite a file. "
                "For targeted changes, use edit_file instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": (
                            "Name of the file, e.g. 'check.txt'. "
                            "Do NOT prefix with 'workspace/'."
                        ),
                    },
                    "content": {
                        "type": "string",
                        "description": "Full contents to write.",
                    },
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": (
                "Return basic information about the host system: OS, CPU, "
                "RAM, GPU, and Python version. Use when the user asks about "
                "the machine HANAM is running on."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": (
                "Search for a text pattern across files in the HANAM "
                "workspace. Returns matching lines with file:line_number. "
                "Use this to find where a function, variable, or string "
                "appears inside the workspace folder."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Text or regex pattern to search for.",
                    },
                    "path": {
                        "type": "string",
                        "description": (
                            "Subfolder to search in. Defaults to the whole "
                            "workspace."
                        ),
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_project",
            "description": (
                "Search the HANAM project's own source code for a pattern. "
                "Use this when the user asks about HANAM's implementation, "
                "e.g. 'where is ask_hanam defined' or 'find provider_score in "
                "the codebase'. Do NOT use this for workspace files — use "
                "grep instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": (
                            "The text or regex to search for. Just the "
                            "pattern — do not include phrases like 'find' "
                            "or 'in the codebase'."
                        ),
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a shell command on the user's machine from the project root. "
                "The user is shown the command and must approve it before it runs. "
                "On Windows, use Windows commands (dir, type, where, tasklist). "
                "Do NOT use Unix commands (ls, cat, which, grep). Use this for "
                "running tests, git commands, pip installs, or running scripts. "
                "Do NOT use it to list project files — the project structure is "
                "already in your system prompt. Do NOT use it to read files — "
                "use read_file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "The shell command to run, e.g. 'pytest', "
                            "'git status', 'pip install requests'."
                        ),
                    },
                },
                "required": ["command"],
            },
        },
    },
]


def get_tool(name: str):
    """Look up a tool callable by name."""
    return TOOLS.get(name)


def get_schemas() -> list:
    """Return the list of tool schemas for LLM function calling."""
    return TOOL_SCHEMAS


def list_tools() -> list:
    """Return the names of all registered tools."""
    return list(TOOLS.keys())
