import os
from dotenv import load_dotenv

load_dotenv()

keys = [
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "OLLAMA_API_KEY",
    "NVIDIA_API_KEY",
    "SAMBANOVA_API_KEY",
]

for k in keys:
    v = os.getenv(k) or ""
    if not v:
        print(f"{k}: MISSING")
    else:
        print(f"{k}: len={len(v)} first4={v[:4]}")