"""Summarize a conversation session and store the summary in memory."""

from app.llm.cloud_router import ask_hanam_bulletproof
from app.memory.conversation import (
    get_current_session_id,
    get_full_conversation,
)
from app.memory.memory_manager import add_summary

SUMMARIZE_PROMPT = (
    "Summarize this conversation in 2–3 short sentences. "
    "Focus on: what the user worked on, decisions made, and anything "
    "worth remembering for future sessions. "
    "Do NOT include greetings, thanks, or filler. "
    "Do NOT say 'the user asked' — just state the substance.\n\n"
    "Conversation:\n"
    "{conversation}"
)


def summarize_current_session():
    """Summarize the current session. Returns the summary string, or None."""
    messages = get_full_conversation()

    if len(messages) < 2:
        return None

    # Build a readable transcript, capped so we don't blow the context.
    lines = []
    for m in messages:
        role = m.get("role", "?")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        # Cap each message
        if len(content) > 500:
            content = content[:500] + "..."
        lines.append(f"{role}: {content}")

    transcript = "\n".join(lines)
    if len(transcript) > 6000:
        transcript = transcript[-6000:]

    prompt = SUMMARIZE_PROMPT.format(conversation=transcript)

    try:
        summary = ask_hanam_bulletproof(prompt)
    except Exception as error:
        return f"(summarization failed: {error})"

    summary = (summary or "").strip()
    if not summary:
        return None

    session_id = get_current_session_id() or "unknown"
    add_summary(session_id, summary)
    return summary
