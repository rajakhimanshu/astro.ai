"""
core/consultation_engine.py
────────────────────────────────────────────────────────────────────────
Engine-first consultation brief. The LLM narrates this — it does not invent.

Every chat answer is grounded in: topic, convergence gate, dasha, signals,
lived experience, and optional horizon forecast snippet.
────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from core.convergence_scorer import score_convergence, detect_topic, TOPIC_MAP
from core.forecast_engine import generate_horizon_forecast, format_horizon_forecast
from core.moon_chart import build_moon_chart, format_moon_chart_for_agent
from core.gemstone_engine import detect_gemstone_query, analyze_gemstone, format_gemstone_report
from core.memory import get_all_events
from core.timing_engine import scan_timing_windows, format_timing_windows
from core.topic_chart_engine import (
    build_topic_chart_analysis,
    format_topic_chart_analysis,
    build_topic_direct_answer,
)


def _fmt_dasha_date(val) -> str:
    if not val or val == "?":
        return "?"
    s = str(val)
    try:
        if "T" in s:
            dt = datetime.fromisoformat(s.replace("Z", ""))
        else:
            dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except Exception:
        return s[:10]


def _format_dasha_dates(dasha: dict) -> str:
    """Exact dasha boundaries — LLM must use these, not guess."""
    md = dasha.get("current_md", "?")
    ad = dasha.get("current_ad", "?")
    pd = dasha.get("current_pd", "?")
    ad_end = _fmt_dasha_date(dasha.get("ad_end") or dasha.get("ad_end_display"))
    md_end = _fmt_dasha_date(dasha.get("md_end") or dasha.get("md_end_display"))
    pd_end = _fmt_dasha_date(dasha.get("pd_end") or dasha.get("pd_end_display"))
    ad_start = _fmt_dasha_date(dasha.get("ad_start"))
    return (
        f"MD {md} until {md_end} | AD {ad} ({ad_start} → {ad_end}) | PD {pd} until {pd_end}."
    )


def _build_direct_answer(profile: dict, question: str, topic: str, conv: dict) -> str:
    """Chart-grounded answer — houses, varga, aspects, full dasha layers."""
    lived = _lived_summary(profile)
    return build_topic_direct_answer(profile, topic, question, conv, lived)


def _pick_forecast_horizon(question: str) -> Optional[str]:
    q = question.lower()
    if any(k in q for k in ["today", "aaj", "this day"]):
        return "today"
    if any(k in q for k in ["30 day", "30 days", "this month", "next month", "weeks"]):
        return "30d"
    if any(k in q for k in ["5 year", "5 years", "five year"]):
        return "5y"
    if any(k in q for k in ["my life", "life overview", "whole life", "birth chart"]):
        return "life"
    if any(k in q for k in ["this year", "next year", "12 month", "one year", "1 year", "forecast"]):
        return "1y"
    if any(k in q for k in ["when will", "future", "predict", "upcoming"]):
        return "30d"
    return None


def _timing_question(question: str) -> bool:
    q = question.lower()
    return any(
        k in q
        for k in [
            "when", "date", "month", "year", "timing", "kab", "कब",
            "marriage", "married", "job", "business", "promotion",
            "profit", "trade", "trading", "exam", "pass", "intern",
            "propose", "girl", "will i",
        ]
    )


def _active_signal_lines(conv: dict, max_n: int = 5) -> List[str]:
    lines = []
    for s in conv.get("signals", []):
        if not s.get("active"):
            continue
        lines.append(f"{s['signal']} (+{s['weight']}): {s['detail'][:160]}")
        if len(lines) >= max_n:
            break
    return lines


def _dissenting_signals(conv: dict) -> List[str]:
    return [
        f"{s['signal']}: {s['detail'][:120]}"
        for s in conv.get("signals", [])
        if not s.get("active")
    ][:3]


def _lived_summary(profile: dict) -> Dict[str, str]:
    lived = profile.get("lived_experience") or {}
    conv_ins = profile.get("conversation_insights") or {}
    merged = {**lived}
    for k, v in conv_ins.items():
        if k.startswith("_"):
            continue
        if v and not merged.get(k):
            merged[k] = v
    out = {}
    for k, v in merged.items():
        if not v or k not in ("profession", "struggles", "goals", "life_events", "emotional_tone", "relationships", "trading"):
            continue
        if isinstance(v, list):
            bits = []
            for item in v[-8:]:
                if isinstance(item, dict):
                    bits.append(str(item.get("title") or item.get("description") or item.get("date") or item)[:120])
                else:
                    bits.append(str(item)[:120])
            out[k] = " | ".join(b for b in bits if b and "Rahu" not in str(b)[:20])[:400]
        else:
            out[k] = str(v)[:300]
    return out


def build_consultation_brief(
    profile: dict,
    question: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Structured authoritative brief for one consultation turn."""
    topic = detect_topic(question)
    cfg = TOPIC_MAP.get(topic, TOPIC_MAP["general"])
    conv = score_convergence(profile, topic=topic, question=question)

    dasha = profile.get("dasha", {})
    meta = profile.get("meta", {})
    birth = meta.get("birth", {})

    precision = "themes_only"
    if conv.get("can_narrow_window"):
        precision = "seasonal_window"
    elif conv.get("can_predict_timing"):
        precision = "broad_window"

    forbidden: List[str] = []
    allowed: List[str] = ["Natal themes", "Dasha chapter", "Planet strengths/weaknesses", "Remedial direction"]
    if conv.get("can_narrow_window"):
        allowed.append("Quarter-level window (3–6 months) ONLY if dasha + Jupiter/Saturn agree")
    elif conv.get("can_predict_timing"):
        allowed.append("Broad 6–18 month thematic period")
    else:
        forbidden.extend([
            "Exact calendar dates",
            "Single-day muhurta unless from engine muhurta scan",
            "Marriage month/year promises",
            "Guaranteed trading outcomes",
        ])

    timing = None
    timing_text = ""
    is_timing = _timing_question(question)
    if is_timing:
        try:
            timing = scan_timing_windows(profile, topic=topic, question=question)
            timing_text = format_timing_windows(timing)
        except Exception as e:
            timing_text = f"[Timing scan unavailable: {e}]"
    future_window_ok = bool(
        timing and timing["natal_promise"]["active"]
        and any(w["confidence"] in ("HIGH", "MEDIUM") for w in timing["windows"])
    )
    timing_rule = conv["timing_rule"]
    if future_window_ok:
        allowed.append("Future month-ranges listed in TIMING WINDOWS (with their reasons)")
        forbidden = [f for f in forbidden if f != "Marriage month/year promises"]
        if precision == "themes_only":
            precision = "broad_window"
        timing_rule += (
            " FUTURE: quote only the TIMING WINDOWS ranges exactly as listed (they override the"
            " 3–6 month limit). Lead with window #1 (strongest), then mention the others by confidence."
        )

    forecast_block = None
    forecast_text = ""
    horizon = _pick_forecast_horizon(question)
    if horizon and user_id:
        try:
            packed = generate_horizon_forecast(user_id, horizon=horizon)
            forecast_block = packed.get("horizons", {}).get(horizon)
            forecast_text = format_horizon_forecast(forecast_block or {})
            if len(forecast_text) > 2500:
                forecast_text = forecast_text[:2500] + "\n...[trimmed]"
        except Exception as e:
            forecast_text = f"[Forecast unavailable: {e}]"

    verdict_lines = []
    if conv["confidence"] >= 65:
        verdict_lines.append(f"Strong thematic support for {cfg['label']} ({conv['confidence']}/100).")
    elif conv["confidence"] >= 40:
        verdict_lines.append(f"Mixed support for {cfg['label']} ({conv['confidence']}/100) — speak in conditions.")
    else:
        verdict_lines.append(f"Weak convergence for {cfg['label']} ({conv['confidence']}/100) — refuse narrow timing.")

    if conv.get("birth_time_confidence") == "low":
        verdict_lines.append("Birth time unverified — downgrade all date-level claims.")

    moon_chart = profile.get("moon_chart") or build_moon_chart(profile)
    gem_planet = detect_gemstone_query(question)
    gemstone_analysis = analyze_gemstone(profile, gem_planet) if gem_planet else None
    topic_analysis = build_topic_chart_analysis(profile, topic, conv, question)
    topic_chart_text = format_topic_chart_analysis(topic_analysis)

    brief = {
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "topic": topic,
        "topic_label": cfg["label"],
        "question": question,
        "is_timing_question": is_timing,
        "confidence": conv["confidence"],
        "active_signals": conv["active_signals"],
        "total_signals": conv["total_signals"],
        "can_predict_timing": conv["can_predict_timing"] or future_window_ok,
        "can_narrow_window": conv["can_narrow_window"],
        "precision": precision,
        "timing_rule": timing_rule,
        "timing_windows": timing,
        "timing_text": timing_text,
        "birth_time_confidence": conv.get("birth_time_confidence", "unverified"),
        "allowed_claims": allowed,
        "forbidden_claims": forbidden,
        "verdict_lines": verdict_lines,
        "active_signal_lines": _active_signal_lines(conv),
        "dissenting_signals": _dissenting_signals(conv),
        "dasha_summary": dasha.get("summary", "?"),
        "dasha_dates_exact": _format_dasha_dates(dasha),
        "direct_answer": _build_direct_answer(profile, question, topic, conv),
        "topic_chart_analysis": topic_analysis,
        "topic_chart_text": topic_chart_text,
        "moon_chart_text": format_moon_chart_for_agent(moon_chart),
        "gemstone_analysis": gemstone_analysis,
        "native": {
            "name": meta.get("name"),
            "lagna": profile.get("lagna", {}).get("sign"),
            "moon": profile.get("rashi", {}).get("sign") or profile.get("planets", {}).get("Moon", {}).get("sign"),
            "birth": f"{birth.get('day')}/{birth.get('month')}/{birth.get('year')} {birth.get('city')}",
        },
        "lived_context": _lived_summary(profile),
        "forecast_horizon": horizon,
        "forecast_block": forecast_block,
        "forecast_text": forecast_text,
        "convergence": conv,
        "recent_life_events": [],
        "logged_events_this_turn": [],
    }
    if user_id:
        try:
            brief["recent_life_events"] = get_all_events(user_id)[:12]
        except Exception:
            pass
    brief["formatted"] = format_consultation_brief(brief, forecast_text)
    return brief


def format_consultation_brief(brief: dict, forecast_text: str = "") -> str:
    """Text block injected at top of LLM context — AUTHORITATIVE."""
    lines = [
        "═══════════════════════════════════════════════════════════════",
        "CONSULTATION BRIEF — ENGINE OUTPUT (YOU MUST OBEY THIS)",
        "═══════════════════════════════════════════════════════════════",
        f"Topic: {brief['topic_label']} | Confidence: {brief['confidence']}/100",
        f"Precision allowed: {brief['precision']}",
        f"TIMING MANDATE: {brief['timing_rule']}",
        f"Birth time confidence: {brief['birth_time_confidence']}",
        "",
        "VERDICT:",
    ]
    for v in brief.get("verdict_lines", []):
        lines.append(f"  • {v}")

    lines.append("")
    lines.append("ALLOWED TO SAY:")
    for a in brief.get("allowed_claims", []):
        lines.append(f"  ✓ {a}")

    if brief.get("forbidden_claims"):
        lines.append("")
        lines.append("FORBIDDEN (do NOT say):")
        for f in brief["forbidden_claims"]:
            lines.append(f"  ✗ {f}")

    lines.append("")
    lines.append("DIRECT ANSWER (say this FIRST in plain language — weave in chart facts below):")
    lines.append(brief.get("direct_answer", ""))

    if brief.get("topic_chart_text"):
        lines.append("")
        lines.append(brief["topic_chart_text"])

    lines.append("")
    lines.append(f"Dasha (EXACT dates — do not guess): {brief.get('dasha_dates_exact', brief.get('dasha_summary', '?'))}")

    if brief.get("timing_text"):
        lines.append("")
        lines.append(brief["timing_text"])

    if brief.get("moon_chart_text"):
        lines.append("")
        lines.append(brief["moon_chart_text"])

    if brief.get("gemstone_analysis"):
        lines.append("")
        lines.append(format_gemstone_report(brief["gemstone_analysis"]))

    lines.append("")
    lines.append("ACTIVE SIGNALS (use sparingly — max 2 in reply):")
    for s in brief.get("active_signal_lines", []):
        lines.append(f"  • {s}")

    dissent = brief.get("dissenting_signals") or []
    if dissent:
        lines.append("")
        lines.append("WEAK / INACTIVE (mention if user pushes for dates):")
        for d in dissent:
            lines.append(f"  • {d}")

    lived = brief.get("lived_context") or {}
    if lived:
        lines.append("")
        lines.append("LIVED CONTEXT (user-specific — prioritize over generic text):")
        for k, v in lived.items():
            lines.append(f"  {k}: {v}")

    logged = brief.get("logged_events_this_turn") or []
    if logged:
        lines.append("")
        lines.append("JUST RECORDED INTO THE LIFE ARCHIVE (acknowledge, then read through the chart):")
        for ev in logged:
            lines.append(f"  • {ev.get('date')} — {ev.get('title')} [{ev.get('domain')}]")

    recent = brief.get("recent_life_events") or []
    if recent:
        lines.append("")
        lines.append("LIFE ARCHIVE (use these dated facts — do not ignore or refuse):")
        for ev in recent[:8]:
            lines.append(f"  • {ev.get('date')} — {ev.get('title')} ({ev.get('domain')})")

    if forecast_text:
        lines.append("")
        lines.append("FORECAST TABLE (timing must match this):")
        lines.append(forecast_text)

    lines.append("")
    lines.append(
        "RULE: Lead with DIRECT ANSWER. Cite specific houses, lords, divisional chart, aspects, "
        "and MD/AD/PD from TOPIC CHART ANALYSIS above — never a generic 'wait for Venus MD' unless "
        "the chart facts support it. Use lived context and recorded events. "
        "If events were just recorded, acknowledge in one line. "
        "Do not repeat the same paragraph from the previous turn."
    )
    lines.append("═══════════════════════════════════════════════════════════════")
    return "\n".join(lines)
