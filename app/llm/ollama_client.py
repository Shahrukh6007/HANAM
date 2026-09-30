import ollama

from app.agent.tool_loop import run_tool_loop
from app.tools.registry import get_schemas

MODEL = "qwen3:4b"
MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = (
    "You are HANAM, a local coding and general-purpose assistant.\n\n"
    "You have access to tools for reading, creating, editing, and "
    "listing files, searching the codebase, running shell commands, "
    "and inspecting the system.\n\n"
    "CRITICAL RULES:\n"
    "1. When a task requires a tool, call it via the function-calling "
    "mechanism. NEVER write a tool call as text in your reply. Never "
    'output JSON like {"name": "list_files", "arguments": {}} as content.\n'
    "2. Prefer calling a tool over describing what you would do.\n"
    "3. Be concise. Show code, not descriptions of code."
)

client = ollama.Client(timeout=180)


def _strip_thinking(content):
    """Remove a leading thinking block if present."""
    if not content:
        return content
    if "</think>" in content:
        return content.split("</think>", 1)[-1].strip()
    return content


def _tool_dict(tool_call, result):
    """Build the tool-result message for Ollama."""
    return {
        "role": "tool",
        "name": tool_call["name"],
        "content": result,
    }


def ask_hanam(prompt, messages=None):
    """Send a prompt to the local Ollama model with tool support."""

    if messages is None:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
    else:
        messages = list(messages)

    def call_model(msgs):
        response = client.chat(
            model=MODEL,
            messages=msgs,
            tools=get_schemas(),
            think=False,
        )
        msg = response.message
        content = _strip_thinking(msg.content or "")

        raw_calls = getattr(msg, "tool_calls", None) or []
        tool_calls = None
        if raw_calls:
            tool_calls = [
                {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                    "id": None,  # Ollama doesn't use tool_call_ids
                }
                for tc in raw_calls
            ]

        return content, tool_calls, msg

    def build_assistant(raw, content, tool_calls):
        # Ollama's SDK accepts its own Message object back into messages.
        return raw

    return run_tool_loop(
        call_model=call_model,
        messages=messages,
        build_assistant=build_assistant,
        build_tool=_tool_dict,
        max_rounds=MAX_TOOL_ROUNDS,
        verbose=True,
    )
