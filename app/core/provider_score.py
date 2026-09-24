from app.core.provider_stats import get_provider_stats

MIN_SAMPLES = 5


def success_rate(successes, requests):
    if requests == 0:
        return 0.0

    return successes / requests


def get_task_score(provider, task):
    stats = get_provider_stats(provider)

    task_stats = stats.get("tasks", {}).get(task)

    if not task_stats:
        return None

    requests = task_stats["requests"]
    successes = task_stats["successes"]
    failures = task_stats["failures"]
    total_response_time = task_stats["total_response_time"]

    if requests == 0:
        return None

    task_success_rate = success_rate(
        successes,
        requests
    )

    average_response_time = (
        total_response_time / successes
        if successes > 0
        else 0
    )

    return {
        "provider": provider,
        "task": task,
        "requests": requests,
        "successes": successes,
        "failures": failures,
        "success_rate": task_success_rate,
        "average_response_time": average_response_time,
        "enough_data": requests >= MIN_SAMPLES
    }


def calculate_score(provider, task):
    result = get_task_score(provider, task)

    if result is None:
        return None

    score = result["success_rate"] * 70

    if result["average_response_time"] > 0:
        speed_score = max(
            0,
            30 - result["average_response_time"] * 3
        )
        score += speed_score

    if not result["enough_data"]:
        score *= 0.5

    result["score"] = round(score, 2)

    return result

def rank_providers(providers, task):
    scored = []
    unscored = []

    for provider in providers:
        result = calculate_score(provider["name"], task)

        if result is None or not result["enough_data"]:
            unscored.append(provider)
            continue

        scored.append((provider, result["score"]))

    scored.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return (
        [provider for provider, score in scored]
        + unscored
    )