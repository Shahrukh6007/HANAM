import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)


PROVIDERS = [
    {"name": "Groq", "model": "openai/gpt-oss-120b", "env": "GROQ_API_KEY", "url": "https://api.groq.com/openai/v1"},
    {"name": "OpenRouter", "model": "openrouter/free", "env": "OPENROUTER_API_KEY", "url": "https://openrouter.ai/api/v1"},
    {"name": "Gemini", "model": "gemini-3.6-flash", "env": "GEMINI_API_KEY", "url": "https://generativelanguage.googleapis.com/v1beta/openai/"},
    {"name": "OllamaCloud", "model": "gpt-oss:120b-cloud", "env": "OLLAMA_API_KEY", "url": "https://ollama.com/v1"},
    {"name": "NVIDIA", "model": "nvidia/nemotron-3-super-120b-a12b", "env": "NVIDIA_API_KEY", "url": "https://integrate.api.nvidia.com/v1"},
    {"name": "SambaNova", "model": "DeepSeek-V3.2", "env": "SAMBANOVA_API_KEY", "url": "https://api.sambanova.ai/v1"},
]


def test_provider(p):
    key = os.getenv(p["env"])
    if not key:
        return "MISSING", "no key in .env", 0.0

    try:
        client = OpenAI(api_key=key, base_url=p["url"])
        t = time.time()
        r = client.chat.completions.create(
            model=p["model"],
            messages=[{"role": "user", "content": "say hi"}],
        )
        elapsed = time.time() - t
        reply = (r.choices[0].message.content or "").strip()[:50]
        return "OK", reply, elapsed

    except Exception as e:
        err = str(e)
        if "401" in err:
            return "401 AUTH", "invalid key", 0.0
        if "402" in err:
            return "402 PAY", "payment required", 0.0
        if "404" in err:
            return "404 MODEL", "model wrong or retired", 0.0
        if "429" in err:
            return "429 LIMIT", "rate limited", 0.0
        return "ERROR", err[:140], 0.0


print(f"{'Provider':<14} {'Status':<12} {'Time':<8} Reply")
print("-" * 90)

for p in PROVIDERS:
    status, msg, elapsed = test_provider(p)
    time_str = f"{elapsed:.2f}s" if elapsed else "—"
    print(f"{p['name']:<14} {status:<12} {time_str:<8} {msg}")