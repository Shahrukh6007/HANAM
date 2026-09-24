def classify_task(prompt: str) -> str:
    """Classify a request locally without using an AI provider."""

    text = prompt.lower().strip()

    if not text:
        return "general"

    scores = {
        "coding": 0,
        "reasoning": 0,
        "knowledge": 0,
        "general": 0
    }

    coding_keywords = [
        "code",
        "coding",
        "python",
        "javascript",
        "html",
        "css",
        "php",
        "sql",
        "program",
        "programming",
        "function",
        "debug",
        "debugging",
        "bug",
        "error",
        "script",
        "api",
        "variable",
        "class",
        "database"
    ]

    reasoning_keywords = [
        "analyze",
        "analyse",
        "compare",
        "evaluate",
        "reason",
        "solve",
        "calculate",
        "why",
        "explain why",
        "pros and cons",
        "advantages",
        "disadvantages",
        "difference between"
    ]

    knowledge_keywords = [
        "who is",
        "who was",
        "what is",
        "what was",
        "when was",
        "where is",
        "where was",
        "history",
        "meaning",
        "definition",
        "capital",
        "president",
        "king",
        "war",
        "empire",
        "country",
        "date"
    ]

    for keyword in coding_keywords:
        if keyword in text:
            scores["coding"] += 2

    for keyword in reasoning_keywords:
        if keyword in text:
            scores["reasoning"] += 2

    for keyword in knowledge_keywords:
        if keyword in text:
            scores["knowledge"] += 2

    if any(word in text for word in [
        "write",
        "create",
        "build",
        "make"
    ]):
        scores["coding"] += 1

    if any(word in text for word in [
        "explain",
        "how does",
        "how do"
    ]):
        scores["reasoning"] += 1

    best_task = max(
        scores,
        key=scores.get
    )

    if scores[best_task] == 0:
        return "general"

    return best_task