"""LLM-driven tool dispatch — the smart path.

Runs only when keyword dispatch and the intent gate both say "maybe".
Uses the shared tool loop. Returns the model's answer if a tool was
called, or None if the prompt was just chat.
"""

import ollama

from app.agent.tool_loop import run_tool_loop
from app.context.repo_map import get_repo_map
from app.tools.registry import get_schemas

MODEL = "qwen3:4b"
MAX_TOOL_ROUNDS = 3
TIMEOUT = 120

SYSTEM_PROMPT = (
    "You are HANAM. You have tools for file and system operations.\n\n"
    "Project structure:\n{repo_map}\n\n"
    "If the user's request requires a tool, call it.\n"
    "If the request is just chat (no tool needed), reply with exactly "
    "the word NONE and nothing else."
)

_client = ollama.Client(timeout=TIMEOUT)


def _strip_thinking(content):
    if content and "</think>" in content:
        return content.split("</think>", 1)[-1].strip()
    return content or ""


def _tool_dict(tool_call, result):
    return {
        "role": "tool",
        "name": tool_call["name"],
        "content": result,
    }


def try_llm_tools(prompt):
    """Try to handle a prompt via LLM-driven tool calling.

    Returns:
        str  — the model's answer after running tools
        None — no tool was called, caller should fall through to chat
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(repo_map=get_repo_map())},
        {"role": "user", "content": prompt},
    ]

    # Mutable so the closure can set it.
    called_any_tool = [False]

    def call_model(msgs):
        try:
            response = _client.chat(
                model=MODEL,
                messages=msgs,
                tools=get_schemas(),
                think=False,
            )
        except Exception:
            # Timeout, connection issue — fall through to normal chat.
            return None, None, None

        msg = response.message
        content = _strip_thinking(msg.content or "")

        raw_calls = getattr(msg, "tool_calls", None) or []
        tool_calls = None
        if raw_calls:
            called_any_tool[0] = True
            tool_calls = [
                {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                    "id": None,
                }
                for tc in raw_calls
            ]

        return content, tool_calls, msg

    def build_assistant(raw, content, tool_calls):
        # Ollama's SDK accepts its own Message object back into messages.
        return raw

    result = run_tool_loop(
        call_model=call_model,
        messages=messages,
        build_assistant=build_assistant,
        build_tool=_tool_dict,
        max_rounds=MAX_TOOL_ROUNDS,
        verbose=True,
    )

    # No tool was ever called → treat as chat, fall through.
    if not called_any_tool[0]:
        return None

    # Final content came back as the NONE sentinel → also chat.
    if result and result.strip().upper() == "NONE":
        return None

    return result or None
