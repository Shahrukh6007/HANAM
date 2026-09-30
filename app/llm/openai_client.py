import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from app.agent.tool_loop import run_tool_loop
from app.tools.registry import get_schemas

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


MAX_TOOL_ROUNDS = 5


def _assistant_dict(content, tool_calls):
    """Convert normalized tool calls back into an OpenAI assistant message."""
    entry = {"role": "assistant", "content": content or ""}
    if tool_calls:
        entry["tool_calls"] = [
            {
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": tc["arguments"],
                },
            }
            for tc in tool_calls
        ]
    return entry


def _tool_dict(tool_call, result):
    """Build the tool-result message for the OpenAI API."""
    return {
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": result,
    }


def _make_client(api_key, base_url):
    timeout = httpx.Timeout(connect=10.0, read=120.0, write=15.0, pool=10.0)
    http_client = httpx.Client(trust_env=False, timeout=timeout)
    return OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)


def ask_hanam_cloud(prompt, model, api_key, base_url, messages=None, use_tools=True):
    """Send messages to a cloud provider.

    Two modes:
      - messages=None  → generation mode (single prompt, no tools).
      - messages=...   → chat mode. Uses tools unless use_tools=False.
    """
    if not api_key:
        raise ValueError(f"API key is empty or None for model: {model}")

    client = _make_client(api_key, base_url)

    # --- Generation mode: single prompt, no tools ---
    if messages is None:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    # --- Chat mode ---
    messages = list(messages)

    # No tools requested → single call, return content.
    if not use_tools:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    # Tools requested → run the loop.
    def call_model(msgs):
        response = client.chat.completions.create(
            model=model,
            messages=msgs,
            tools=get_schemas(),
        )
        msg = response.choices[0].message
        content = msg.content or ""

        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                    "id": tc.id,
                }
                for tc in msg.tool_calls
            ]

        return content, tool_calls, msg

    return run_tool_loop(
        call_model=call_model,
        messages=messages,
        build_assistant=lambda raw, content, tcs: _assistant_dict(content, tcs),
        build_tool=_tool_dict,
        max_rounds=MAX_TOOL_ROUNDS,
        verbose=True,
    )
