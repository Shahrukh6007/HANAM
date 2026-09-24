import ollama
from app.memory.memory_manager import get_facts
from app.tools.registry import TOOLS

MODEL = "qwen3:4b"
MAX_TOOL_ROUNDS = 5

client = ollama.Client(timeout=60)


def ask_hanam(prompt, messages=None):
    facts = get_facts()

    memory_context = ""

    if facts:
        memory_context = "\n\nKnown facts about the user:\n"
        for fact in facts:
            memory_context += f"- {fact}\n"

    if messages is None:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are HANAM, a local personal AI assistant. "
                    "Be helpful, concise, and accurate. "
                    "Use tools when the user's request requires them."
                ),
            }
        ]

    messages = list(messages)

    messages.append({"role": "user", "content": prompt + memory_context})

    response = None

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat(
            model=MODEL, messages=messages, tools=list(TOOLS.values()), think=False
        )

        if not response.message.tool_calls:
            break

        messages.append(response.message)

        for tool_call in response.message.tool_calls:
            function = tool_call.function
            tool = TOOLS.get(function.name)

            if not tool:
                result = f"Tool '{function.name}' was not found."
            else:
                try:
                    result = tool(**function.arguments)
                except Exception as error:
                    result = f"Tool error: {error}"

            messages.append({"role": "tool", "content": str(result)})

    if response is None:
        return "I couldn't get a response from the local AI."

    content = response.message.content or ""

    if "</think>" in content:
        content = content.split("</think>", 1)[1].strip()

    return content
