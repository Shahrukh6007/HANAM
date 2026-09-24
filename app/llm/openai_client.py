import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from app.tools.registry import TOOLS, get_schemas

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


MAX_TOOL_ROUNDS = 5


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


def _assistant_message_dict(msg):
    """Convert an OpenAI assistant message (with tool_calls) to a dict."""
    entry = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        entry["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return entry


def _make_client(api_key, base_url):
    timeout = httpx.Timeout(connect=10.0, read=120.0, write=15.0, pool=10.0)
    http_client = httpx.Client(trust_env=False, timeout=timeout)
    return OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)


def ask_hanam_cloud(prompt, model, api_key, base_url, messages=None, use_tools=True):
    """Send messages to a cloud provider.

    Two modes:
      - messages=None  → generation mode (single prompt, no tools).
                          Used by agent.py's create_file.
      - messages=...   → chat mode with tool calling.
                          Used by main.py's chat path.
    """
    if not api_key:
        raise ValueError(f"API key is empty or None for model: {model}")

    client = _make_client(api_key, base_url)

    # --- Generation mode: no tools, single prompt ---
    if messages is None:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    # --- Chat mode: tools + loop ---
    messages = list(messages)

    for round_num in range(MAX_TOOL_ROUNDS):
        kwargs = {"model": model, "messages": messages}
        if use_tools:
            kwargs["tools"] = get_schemas()
        response = client.chat.completions.create(**kwargs)

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or ""

        # DEBUG — shows what the model is calling each round
        print(f"HANAM System: round {round_num + 1} →")
        for tc in msg.tool_calls:
            print(f"  tool: {tc.function.name}({tc.function.arguments})")

        messages.append(_assistant_message_dict(msg))

        for tc in msg.tool_calls:
            result = _run_tool(tc.function.name, tc.function.arguments)
            print(f"  result: {result[:120]}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    return msg.content or "(max tool rounds reached)"
