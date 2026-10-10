"""
core/topic_guard.py
────────────────────────────────────────────────────────────────────────
Allows all life questions (they map onto the chart). Blocks only clear
non-Jyotish tasks: code, recipes, sports scores, homework, politics.
"""

import re
from typing import List, Optional

# Clear off-topic (no life/chart context)
OFF_TOPIC_PATTERNS = [
    r"\b(write|debug|fix)\s+(code|script|program|app|website)\b",
    r"\b(python|javascript|typescript|react|sql|api)\s+(code|function|error)\b",
    r"\b(recipe|cook|ingredient|bake)\b",
    r"\b(football|cricket score|ipl|movie review|netflix)\b",
    r"\b(stock tip|crypto|bitcoin|forex signal)\b",
    r"\b(homework|math problem|physics question|chemistry)\b",
    r"\b(political opinion|election|bjp|congress party)\b",
    r"\b(write essay|poem|story)\s+(about|on)\s+(?!.*(marriage|career|life))\w+",
]

GREETING_PATTERN = re.compile(
    r"^(hi|hello|hey|namaste|namaskar|pranam|thanks|thank you|ok|okay|ji|haan|ha|yes|no)[\s!.?]*$",
    re.I,
)

REFUSAL_MESSAGE = (
    "🙏 Main coding, recipes, sports scores, ya politics nahi karta — "
    "yeh Jyotish consultation hai.\n\n"
    "Apni life ke baare mein poochhiye: exams, job, internship, business, "
    "love, marriage, health, timing — sab kundali se padha jaayega."
)


def check_astrology_topic(
    question: str,
    conversation_history: Optional[List[dict]] = None,
) -> dict:
    """
    Returns {allowed: bool, reason: str, message?: str}

    Default is ALLOW. Life stories, exams, internships, relationships,
    startups, and follow-ups are all in scope. Only hard off-topic is blocked.
    """
    if not question or not question.strip():
        return {"allowed": False, "reason": "empty", "message": REFUSAL_MESSAGE}

    q = question.strip().lower()
    q_raw = question.strip()

    if GREETING_PATTERN.match(q_raw):
        return {"allowed": True, "reason": "greeting"}

    off_topic = any(re.search(p, q, re.I) for p in OFF_TOPIC_PATTERNS)
    if off_topic:
        return {"allowed": False, "reason": "off_topic", "message": REFUSAL_MESSAGE}

    # Follow-up, story, or any personal question — always in scope
    _ = conversation_history
    return {"allowed": True, "reason": "life_in_scope"}
