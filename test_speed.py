import time
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

# Test 1: minimal — no tools, tiny prompt
t = time.time()
r = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "hello"}],
)
print(f"Test 1 (no tools, tiny prompt): {time.time()-t:.1f}s")

# Test 2: with 1 dummy tool
tools = [{"type": "function", "function": {
    "name": "dummy", "description": "dummy",
    "parameters": {"type": "object", "properties": {}},
}}]
t = time.time()
r = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "hello"}],
    tools=tools,
)
print(f"Test 2 (with 1 dummy tool): {time.time()-t:.1f}s")

# Test 3: with all HANAM tools
from app.tools.registry import get_schemas
t = time.time()
r = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "hello"}],
    tools=get_schemas(),
)
print(f"Test 3 (with {len(get_schemas())} HANAM tools): {time.time()-t:.1f}s")