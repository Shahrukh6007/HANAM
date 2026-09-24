"""LLM-driven tool dispatch — an isolated experiment.

Nothing uses this yet. That's on purpose.
It tries to handle a prompt using the LLM + tools.
  - If the LLM calls a tool → runs it, returns the final answer.
  - If the LLM doesn't call a tool → returns None, so the caller
    falls through to the normal chat path.
"""

import json
import ollama

from app.tools.registry import TOOLS, get_schemas
from app.context.repo_map import get_repo_map

MODEL = "qwen3:4b"
MAX_ROUNDS = 3
TIMEOUT = 90

SYSTEM_PROMPT = (
    "You are HANAM. You have tools for file and system operations.\n\n"
    "Project structure:\n{repo_map}\n\n"
    "If the user's request requires a tool, call it.\n"
    "If the request is just chat (no tool needed), reply with exactly "
    "the word NONE and nothing else."
)

_client = ollama.Client(timeout=TIMEOUT)


def _run_tool(name, arguments):
    """Execute a tool. Never raises."""
    tool = TOOLS.get(name)
    if tool is None:
        return f"Tool '{name}' not found."

    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = {}

    try:
        return str(tool(**arguments))
    except Exception as error:
        return f"Tool error: {error}"


def _strip_thinking(content):
    if content and "</think>" in content:
        return content.split("</think>", 1)[-1].strip()
    return content or ""


def try_llm_tools(prompt):
    """Try to handle a prompt via LLM-driven tool calling.

    Returns:
        str  — the model's answer after running tools
        None — the model didn't call a tool, caller should fall through
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(repo_map=get_repo_map())},
        {"role": "user", "content": prompt},
    ]

    called_any_tool = False

    for _ in range(MAX_ROUNDS):
        try:
            response = _client.chat(
                model=MODEL,
                messages=messages,
                tools=get_schemas(),
                think=False,
            )
        except Exception:
            # Timeout, connection issue — fall through to normal chat.
            return None

        msg = response.message
        tool_calls = getattr(msg, "tool_calls", None) or []

        if not tool_calls:
            if not called_any_tool:
                # No tool called on the first round → not a tool request.
                return None

            # We already ran tools. This is the final answer.
            content = _strip_thinking(msg.content)
            if content.strip().upper() == "NONE":
                return None
            return content or None

        called_any_tool = True
        messages.append(msg)

        for tc in tool_calls:
            result = _run_tool(tc.function.name, tc.function.arguments)
            messages.append(
                {
                    "role": "tool",
                    "name": tc.function.name,
                    "content": result,
                }
            )

    return "I couldn't finish that task in the allowed number of steps."
