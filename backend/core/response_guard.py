"""
core/response_guard.py — Post-process LLM output to enforce convergence timing gates.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple

# Patterns that imply false precision when timing is blocked
_DATE_PATTERNS = [
    r"\b(?:on|by|in)\s+(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+\d{4})?\b",
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4}\b",
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b(?:exactly|precisely|definitely)\s+(?:on|by|in)\s+\w+",
    r"\bmarriage\s+(?:will|shall)\s+(?:happen|occur)\s+(?:in|on|by)\b",
    r"\b(?:will|shall)\s+(?:marry|get married)\s+(?:in|on|by)\b",
    r"\bguaranteed\s+(?:profit|income|success)\b",
]


def enforce_timing_gate(text: str, brief: dict) -> Tuple[str, Dict]:
    """
    If timing is not allowed, redact date-like claims and append correction.
    Returns (cleaned_text, audit dict).
    """
    audit = {"modified": False, "violations": [], "appended_note": False}
    if not text or not brief:
        return text, audit

    can_time = brief.get("can_predict_timing") or brief.get("can_narrow_window")
    if can_time:
        return text, audit

    cleaned = text
    for pat in _DATE_PATTERNS:
        for m in re.finditer(pat, cleaned, flags=re.IGNORECASE):
            audit["violations"].append(m.group(0))
        cleaned = re.sub(pat, "[timing not converged — theme only]", cleaned, flags=re.IGNORECASE)

    if audit["violations"]:
        audit["modified"] = True
        note = (
            "\n\n—\n*Guruji note: Narrow timing was withheld because your chart signals "
            f"did not fully converge ({brief.get('confidence', '?')}/100). "
            f"{brief.get('timing_rule', '')}*"
        )
        if note.strip() not in cleaned:
            cleaned += note
            audit["appended_note"] = True

    return cleaned, audit


def build_refusal_preamble(brief: dict) -> str:
    """When confidence is very low on timing questions, optional hard preamble."""
    if not brief.get("is_timing_question"):
        return ""
    if brief.get("confidence", 0) >= 35:
        return ""
    return (
        f"[Engine: {brief.get('topic_label')} confidence {brief.get('confidence')}/100 — "
        f"themes only, no dates.]\n\n"
    )
