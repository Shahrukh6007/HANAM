"""Unified tool-calling loop for HANAM.

Each provider's only job is to call its model and return a normalized
(content, tool_calls, raw) tuple. This module handles the loop:
send → detect tool calls → execute → append results → repeat.
"""

import json

from app.tools.registry import TOOLS
from app.core.log import log


def execute_tool(name, arguments):
    """Run a tool by name. Never raises."""
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


def run_tool_loop(
    call_model,
    messages,
    build_assistant,
    build_tool,
    max_rounds=5,
    verbose=True,
):
    """Run the tool-calling loop.

    Args:
        call_model(messages) -> (content, tool_calls, raw)
            content: str or None
            tool_calls: list of {"name", "arguments", "id"} or None
            raw: the provider's original response (passed back to build_assistant)

        messages: message list. Mutated in place.

        build_assistant(raw, content, tool_calls) -> dict
            Message to append after a round that produced tool calls.

        build_tool(tool_call, result) -> dict
            Message to append for each tool result.

        max_rounds: safety cap.
        verbose: print each tool call and a short result preview.

    Returns:
        Final text content from the model.
    """
    last_content = ""

    for round_num in range(max_rounds):
        content, tool_calls, raw = call_model(messages)
        last_content = content or ""

        if not tool_calls:
            return last_content

        if verbose:
            log(f"HANAM System: round {round_num + 1} →")

        messages.append(build_assistant(raw, content, tool_calls))

        for tc in tool_calls:
            if verbose:
                log(f"  tool: {tc['name']}({tc['arguments']})")

            result = execute_tool(tc["name"], tc["arguments"])

            if verbose:
                preview = result[:120] + ("..." if len(result) > 120 else "")
                log(f"  result: {preview}")

            messages.append(build_tool(tc, result))

    return last_content or "(max tool rounds reached)"
