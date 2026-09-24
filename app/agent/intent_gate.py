"""Fast YES/NO classifier: does this prompt need a tool?

Uses a small non-thinking model. Runs only when keywords miss —
gate between chat (fast) and tool calling (slow).
"""

import ollama

MODEL = "qwen2.5-coder:7b"
TIMEOUT = 30

PROMPT_TEMPLATE = """Classify each message. Reply with one word: YES or NO.

hello
NO

thanks
NO

what is 2+2
NO

explain how recursion works
NO

tell me a joke
NO

list my files
YES

read config.txt
YES

what is in check.txt
YES

find the auth function
YES

run pytest
YES

git status
YES

{user_message}
"""

_client = ollama.Client(timeout=TIMEOUT)


def needs_tool(prompt):
    """Return True if the prompt likely needs a tool.

    On error, returns False — chat stays fast.
    """
    try:
        response = _client.chat(
            model=MODEL,
            messages=[
                {"role": "user", "content": PROMPT_TEMPLATE.format(user_message=prompt)}
            ],
            think=False,
        )
        content = (response.message.content or "").strip().upper()
    except Exception as error:
        print(f"HANAM System: intent gate failed ({error}). Assuming chat.")
        return False

    word = content.split()[0] if content.split() else ""
    return word.startswith("YES")
