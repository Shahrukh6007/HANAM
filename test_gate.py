import time
from app.agent.intent_gate import needs_tool

tests = [
    ("hello", False),
    ("thanks", False),
    ("what's 2+2", False),
    ("explain how recursion works", False),
    ("list my files", True),
    ("read config.txt", True),
    ("find the auth function", True),
    ("run pytest", True),
]

for prompt, expected in tests:
    t = time.time()
    result = needs_tool(prompt)
    elapsed = time.time() - t
    mark = "OK" if result == expected else "FAIL"
    print(f"[{mark}] {prompt!r:35} -> {result} ({elapsed:.1f}s)")