import json
import time
from pathlib import Path

STATS_FILE = Path(__file__).resolve().parent / "provider_stats.json"


def create_provider_stats():
    return {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "total_response_time": 0.0,
        "last_success": 0,
        "last_failure": 0,
        "tasks": {}
    }


def create_task_stats():
    return {
        "requests": 0,
        "successes": 0,
        "failures": 0,
        "total_response_time": 0.0
    }


def load_stats():
    if not STATS_FILE.exists():
        return {}

    try:
        with open(STATS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as file:
        json.dump(stats, file, indent=4)


def get_provider_stats(provider):
    stats = load_stats()

    return stats.get(
        provider,
        create_provider_stats()
    )


def record_success(provider, task, response_time):
    stats = load_stats()

    provider_stats = stats.setdefault(
        provider,
        create_provider_stats()
    )

    provider_stats["total_requests"] += 1
    provider_stats["successful_requests"] += 1
    provider_stats["total_response_time"] += response_time
    provider_stats["last_success"] = time.time()

    task_stats = provider_stats["tasks"].setdefault(
        task,
        create_task_stats()
    )

    task_stats["requests"] += 1
    task_stats["successes"] += 1
    task_stats["total_response_time"] += response_time

    save_stats(stats)


def record_failure(provider, task):
    stats = load_stats()

    provider_stats = stats.setdefault(
        provider,
        create_provider_stats()
    )

    provider_stats["total_requests"] += 1
    provider_stats["failed_requests"] += 1
    provider_stats["last_failure"] = time.time()

    task_stats = provider_stats["tasks"].setdefault(
        task,
        create_task_stats()
    )

    task_stats["requests"] += 1
    task_stats["failures"] += 1

    save_stats(stats)