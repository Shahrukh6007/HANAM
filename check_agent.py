from app.agent.agent import process_request

tests = [
    ("list the files", "keyword path"),
    ("what files exist in my workspace", "smart path"),
    ("remember my name is Test", "memory path"),
    ("what is 2+2", "should return None (chat)"),
]

for prompt, expected in tests:
    result = process_request(prompt)
    print(f"[{expected}]")
    print(f"  in:  {prompt}")
    print(f"  out: {repr(result)[:100]}")
    print()