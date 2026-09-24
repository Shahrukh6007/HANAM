import os
import time
from pathlib import Path
from dotenv import load_dotenv
from app.core.task_classifier import classify_task
from app.llm.openai_client import ask_hanam_cloud
from app.llm.ollama_client import ask_hanam as ask_ollama_local
from app.core.provider_state import load_provider_state, save_provider_state
from app.core.provider_stats import record_success, record_failure
from app.core.provider_score import rank_providers

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

COOLDOWN_SECONDS = 60
RATE_LIMIT_COOLDOWN_SECONDS = 300

PROVIDERS = [
    {
        "name": "Groq",
        "model": "openai/gpt-oss-120b",
        "api_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "tasks": ["general", "coding"],
    },
    {
        "name": "OllamaCloud",
        "model": "gpt-oss:120b-cloud",
        "api_key": "OLLAMA_API_KEY",
        "base_url": "https://ollama.com/v1",
        "tasks": ["coding", "general", "reasoning"],
    },
    {
        "name": "Gemini",
        "model": "gemini-3.6-flash",
        "api_key": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "tasks": ["knowledge", "reasoning", "general"],
    },
    {
        "name": "OpenRouter",
        "model": "openrouter/free",
        "api_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "tasks": ["general", "reasoning", "coding", "knowledge"],
    },
    {
        "name": "NVIDIA",
        "model": "nvidia/nemotron-3-super-120b-a12b",
        "api_key": "NVIDIA_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "tasks": ["general", "coding", "reasoning"],
    },
    {
        "name": "SambaNova",
        "model": "DeepSeek-V3.2",
        "api_key": "SAMBANOVA_API_KEY",
        "base_url": "https://api.sambanova.ai/v1",
        "tasks": ["coding", "reasoning"],
    },
]

provider_health = {
    provider["name"]: load_provider_state(provider["name"]) for provider in PROVIDERS
}


def classify_error(error):
    error_text = str(error).lower()

    if (
        "api key is empty" in error_text
        or "api key is missing" in error_text
        or ("api_key" in error_text and "none" in error_text)
    ):
        return "permanent"

    if (
        "401" in error_text
        or "unauthorized" in error_text
        or "invalid api key" in error_text
    ):
        return "permanent"

    if (
        "402" in error_text
        or "payment_required" in error_text
        or "payment method" in error_text
    ):
        return "permanent"

    if (
        "404" in error_text
        or "not found" in error_text
        or ("model" in error_text and "available" in error_text)
    ):
        return "permanent"

    if (
        "429" in error_text
        or "rate limit" in error_text
        or "too many requests" in error_text
    ):
        return "rate_limit"

    if (
        "timeout" in error_text
        or "timed out" in error_text
        or "connection" in error_text
        or "connecterror" in error_text
        or "network" in error_text
    ):
        return "temporary"

    return "temporary"


def mark_failure(provider, error):
    error_type = classify_error(error)
    health = provider_health[provider]

    if error_type == "permanent":
        health["disabled"] = True
        health["failed_at"] = time.time()
        health["cooldown"] = 0

        print(
            f"HANAM System: {provider} disabled "
            f"because the error appears permanent."
        )

    elif error_type == "rate_limit":
        health["failed_at"] = time.time()
        health["cooldown"] = RATE_LIMIT_COOLDOWN_SECONDS

        print(
            f"HANAM System: {provider} rate limited. "
            f"Cooldown: {RATE_LIMIT_COOLDOWN_SECONDS}s."
        )

    else:
        health["failed_at"] = time.time()
        health["cooldown"] = COOLDOWN_SECONDS

        print(
            f"HANAM System: {provider} temporary failure. "
            f"Cooldown: {COOLDOWN_SECONDS}s."
        )

    save_provider_state(provider, health)


def provider_available(provider):
    health = provider_health[provider]

    if health["disabled"]:
        print(f"HANAM System: {provider} is disabled. Skipping.")
        return False

    if health["failed_at"] == 0:
        return True

    cooldown = health["cooldown"]

    if time.time() - health["failed_at"] >= cooldown:
        health["failed_at"] = 0
        health["cooldown"] = 0

        print(f"HANAM System: {provider} cooldown expired. Retrying...")

        save_provider_state(provider, health)
        return True

    remaining = int(cooldown - (time.time() - health["failed_at"]))

    print(
        f"HANAM System: {provider} is cooling down. "
        f"Skipping ({remaining}s remaining)."
    )

    return False


def mark_healthy(provider):
    provider_health[provider]["failed_at"] = 0
    provider_health[provider]["cooldown"] = 0
    provider_health[provider]["disabled"] = False

    save_provider_state(provider, provider_health[provider])


def get_provider_order(task):
    preferred = []
    fallback = []

    for provider in PROVIDERS:
        if task in provider["tasks"]:
            preferred.append(provider)
        else:
            fallback.append(provider)

    return preferred + fallback


def ask_provider(provider, prompt, task, messages=None, use_tools=True):
    name = provider["name"]

    if not provider_available(name):
        return None

    api_key = os.getenv(provider["api_key"])

    print(f"HANAM System: Routing to {name}...")

    start_time = time.time()

    try:
        response = ask_hanam_cloud(
            prompt=prompt,
            model=provider["model"],
            api_key=api_key,
            base_url=provider["base_url"],
            messages=messages,
            use_tools=use_tools,
        )

        response_time = time.time() - start_time

        record_success(name, task, response_time)

        mark_healthy(name)

        return response

    except Exception as error:
        record_failure(name, task)

        mark_failure(name, error)

        print(f"HANAM System: {name} failed ({error}). " f"Falling back...")

        return None


def ask_hanam_bulletproof(prompt, messages=None, use_tools=True):
    task = classify_task(prompt)

    print(f"HANAM System: Task classified as '{task}'.")

    providers = rank_providers(get_provider_order(task), task)

    for provider in providers:
        response = ask_provider(provider, prompt, task, messages, use_tools=use_tools)

        if response is not None:
            return response

    try:
        print(
            "HANAM System: Cloud offline, " "falling back to local Ollama (qwen3:4b)..."
        )

        return ask_ollama_local(prompt, messages=messages)

    except Exception as error:
        return f"Critical Error: All AI providers failed. " f"Details: {error}"
