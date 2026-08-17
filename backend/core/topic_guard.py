"""
core/topic_guard.py
────────────────────────────────────────────────────────────────────────
Restricts chat to Jyotish / Vedic astrology topics only.
"""

import re
from typing import List, Optional

# Strong astrology signals (English + common Hindi transliteration)
ASTRO_SIGNALS = frozenset([
    "dasha", "mahadasha", "antardasha", "pratyantar", "lagna", "ascendant", "rashi",
    "kundali", "kundli", "chart", "horoscope", "planet", "graha", "bhav", "house",
    "marriage", "vivah", "career", "naukri", "job", "wealth", "dhana", "health",
    "transit", "gochar", "gochara", "nakshatra", "yoga", "yog", "jyotish", "jyotishi",
    "astrology", "astrologer", "muhurta", "muhurat", "remedy", "upay", "puja", "mantra",
    "ketu", "rahu", "saturn", "shani", "venus", "shukra", "jupiter", "guru", "mars",
    "mangal", "mercury", "budh", "sun", "surya", "moon", "chandra", "magha", "rohini",
    "prediction", "forecast", "future", "timing", "prashna", "hora", "panchang",
    "panchanga", "ashtakavarga", "shadbala", "divisional", "d9", "navamsa", "d10",
    "dashamsha", "sade sati", "sadesati", "retrograde", "vakri", "exalted", "debilitated",
    "neech", "uchcha", "combust", "aspect", "drishti", "lord", "swami", "patrika",
    "janam", "janampatri", "match", "kundli milan", "gun milan", "compatibility",
    "partnership", "relationship", "spouse", "husband", "wife", "child", "santan",
    "business", "property", "foreign", "travel", "spiritual", "moksha", "karma",
    "raashi", "mesh", "vrishabh", "mithun", "kark", "simha", "kanya", "tula",
    "vrishchik", "dhanu", "makar", "kumbh", "meen", "aries", "taurus", "gemini",
    "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn",
    "aquarius", "pisces", "consultation", "reading", "guruji",
])

# Clear off-topic (no astro context)
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

LIFE_DOMAIN_WORDS = frozenset([
    "when will", "will i", "should i", "marriage", "job", "money", "health",
    "partner", "love", "business", "career", "future", "happen", "timing",
    "kab", "kya hoga", "shaadi", "naukri", "paisa", "swasthya",
])

REFUSAL_MESSAGE = (
    "🙏 Main sirf Jyotish / Vedic astrology par baat karta hoon — kundali, dasha, "
    "gochar, marriage, career, remedies, muhurta, aise topics.\n\n"
    "Is sawal ka jawab is system ke scope se bahar hai. Kripya apni kundali, "
    "dasha, ya kisi life area (career, vivah, wealth, health) se related kuch poochhiye."
)


def _has_devanagari(text: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F]", text))


def check_astrology_topic(
    question: str,
    conversation_history: Optional[List[dict]] = None,
) -> dict:
    """
    Returns {allowed: bool, reason: str, message?: str}
    """
    if not question or not question.strip():
        return {"allowed": False, "reason": "empty", "message": REFUSAL_MESSAGE}

    q = question.strip().lower()
    q_raw = question.strip()

    if GREETING_PATTERN.match(q_raw):
        return {"allowed": True, "reason": "greeting"}

    # Hindi astro terms in Devanagari
    hindi_astro = ["कुंडली", "दशा", "ग्रह", "लग्न", "राशि", "नक्षत्र", "गोचर", "ज्योतिष", "विवाह", "शादी"]
    if any(h in q_raw for h in hindi_astro):
        return {"allowed": True, "reason": "hindi_astro"}

    # Follow-up in ongoing reading
    if conversation_history:
        recent = " ".join(
            (m.get("content") or "") for m in conversation_history[-6:]
        ).lower()
        if any(s in recent for s in list(ASTRO_SIGNALS)[:40]):
            if len(q) < 120:
                return {"allowed": True, "reason": "followup"}

    astro_hits = sum(1 for s in ASTRO_SIGNALS if s in q)
    if _has_devanagari(q_raw):
        astro_hits += 1  # bias toward allow for Hindi script queries

    off_topic = any(re.search(p, q, re.I) for p in OFF_TOPIC_PATTERNS)

    if off_topic and astro_hits == 0:
        return {"allowed": False, "reason": "off_topic", "message": REFUSAL_MESSAGE}

    if astro_hits >= 1:
        return {"allowed": True, "reason": "astro_keywords"}

    if any(d in q for d in LIFE_DOMAIN_WORDS):
        return {"allowed": True, "reason": "life_domain"}

    # Questions with ? often life-related in this app
    if "?" in q_raw and len(q_raw) > 12:
        return {"allowed": True, "reason": "question_lenient"}

    return {"allowed": False, "reason": "no_astro_signal", "message": REFUSAL_MESSAGE}
