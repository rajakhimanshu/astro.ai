"""
core/agent.py — Master Orchestrator (World-Class Upgrade)
FIXES:
  1. Conversation history passed to LLM for multi-turn awareness
  2. Lived experience extracted AND re-injected into SAME request
  3. Pattern engine activated in context building
  4. Forecast engine activated for forward-looking questions
  5. Transit engine receives profile for personalized narratives
  6. Per-user memory search
  7. set_llm_mode / set_groq_model exported for main.py
"""

import ollama
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Generator, List
from groq import Groq

# ── Master Data Prompt (pre-validated chart data — injected before every call) ─
_MASTER_DATA_PROMPT = ""
for _candidate in [
    Path(__file__).parent.parent.parent / "antigravity_master_data_prompt.md",
    Path(__file__).parent.parent / "antigravity_master_data_prompt.md",
    Path("antigravity_master_data_prompt.md"),
]:
    if _candidate.exists():
        _MASTER_DATA_PROMPT = _candidate.read_text(encoding="utf-8")
        print(f"[AGENT] Master data loaded: {_candidate}")
        break

# ── LLM CONFIG ────────────────────────────────────────────────────────────────
LLM_MODE = os.getenv("LLM_MODE", "ollama")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

# Groq free tier ~12k TPM — cap injected chart context (~5.5k tokens)
MAX_GROQ_INPUT_CHARS = 22000

client_groq = None
if GROQ_API_KEY:
    client_groq = Groq(api_key=GROQ_API_KEY)
    if os.getenv("LLM_MODE") is None:
        LLM_MODE = "groq"


def set_llm_mode(mode: str) -> bool:
    global LLM_MODE
    if mode.lower() not in ("ollama", "groq"):
        return False
    LLM_MODE = mode.lower()
    return True


def set_groq_model(model: str):
    global GROQ_MODEL
    GROQ_MODEL = model


def _clip(text: str, max_len: int, label: str = "") -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    tag = f" [{label}]" if label else ""
    return text[:max_len] + f"\n...{tag} trimmed for token limit..."


def _fit_system_prompt(text: str) -> str:
    if len(text) <= MAX_GROQ_INPUT_CHARS:
        return text
    return text[:MAX_GROQ_INPUT_CHARS] + "\n...[chart context capped for Groq 12k token limit]"


def _stream_groq(messages: list):
    """Yield tokens from Groq streaming API."""
    stream = client_groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        stream=True,
        temperature=0.7,
        max_tokens=2048,
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def _stream_ollama(full_system: str, question: str, conversation_history: list):
    ollama_msgs = [{"role": "system", "content": _fit_system_prompt(full_system)}]
    for msg in (conversation_history or [])[-4:]:
        role = "user" if msg.get("role") == "user" else "assistant"
        ollama_msgs.append({"role": role, "content": msg.get("content", "")[:800]})
    ollama_msgs.append({"role": "user", "content": _build_instruction(question)})
    stream = ollama.chat(model="mistral", messages=ollama_msgs, stream=True)
    for chunk in stream:
        yield chunk["message"]["content"]


# ── ENGINE IMPORTS ────────────────────────────────────────────────────────────
from core.astro_engine import (
    get_natal_chart, get_natal_chart_from_profile, get_current_sky, calculate_vimshottari_dasha,
    load_birth_data, get_nakshatra_and_pada, SIGNS
)
from core.kundali_profile import get_full_kundali_text, get_current_dasha_summary, KUNDALI_PROFILE
from core.transit_engine import get_transit_analysis, format_recent_transit_report
from core.memory import search_events, analyze_planetary_empirical_performance
from core.knowledge_base import search_knowledge
from core.pattern_engine import find_similar_past_periods, format_pattern_report
from core.multi_layer_engine import get_all_12_layers, SIGN_MAP
from core.user_profile_engine import (
    get_active_user_id, get_active_profile, load_user_profile,
    profile_to_context_text, list_users, update_lived_experience
)
from core.forecast_engine import generate_12_month_forecast
from core.bhrigu_nadi import BhriguNadiEngine, format_bhrigu_report
from core.jaimini_padas import JaiminiPadaEngine, format_pada_report
from core.yogini_engine import get_yogini_dasha, format_yogini_report
from core.convergence_scorer import score_convergence, format_convergence_report, detect_topic as detect_convergence_topic
from core.prashna_engine import run_prashna_analysis, format_prashna_report
from core.tajika_engine import TajikaEngine, format_tajika_report
from core.karmic_engine import KarmicNarrativeEngine, format_karmic_report
from core.remedial_engine import RemedialEngine, format_remedial_report
from core.nakshatra_gochara_engine import format_gochara_report, analyze_nakshatra_activations
from core.kakshya_engine import format_kakshya_report
from core.gochara_bala_engine import format_gochara_bala_report
from core.prediction_ledger import log_prediction, format_pending_for_agent
from core.accuracy_engine import format_accuracy_report
from core.topic_guard import check_astrology_topic, REFUSAL_MESSAGE


# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
_STATIC_SYSTEM_PROMPT = """GURUJI — MASTER PERSONA & INTERACTION PROTOCOL
You are Guruji. A living, breathing Jyotishi with 30 years of experience. You are sharp, direct, visceral, and never robotic.

SCOPE LOCK — JYOTISH ONLY:
You ONLY answer Vedic astrology / Jyotish questions: kundali, dasha, transits, marriage, career, health, remedies, muhurta, prashna.
If asked anything outside astrology, politely refuse and redirect to a chart-related question.
Never write code, recipes, general knowledge, politics, or non-astro advice.

═══════════════════════════════════════════════════════════════
THE ONBOARDING MANDATE (Lived Experience First)
═══════════════════════════════════════════════════════════════
If the [LIVED EXPERIENCE] section is marked as "Not shared yet" or significantly incomplete, connect with the human first.
Use: "Before we look at your chart, tell me a bit about where you are in life right now. What are you actively working on, what's feeling stuck, and what does the next chapter look like for you?"

═══════════════════════════════════════════════════════════════
CONVERSATION CONTINUITY RULE
═══════════════════════════════════════════════════════════════
The [CONVERSATION HISTORY] section below contains the prior exchange. You MUST reference it naturally.
If the user mentioned something earlier (a job, a person, an event), use it. Never pretend you don't know.

═══════════════════════════════════════════════════════════════
EMPIRICAL LEARNING RULE
═══════════════════════════════════════════════════════════════
The [EMPIRICAL FEEDBACK] section contains REAL data from this person's lived events.
If a planet is marked "Highly Challenging (Empirically)" — that overrides textbook theory.
Say it explicitly: "In your chart, I've seen that Saturn periods have been consistently difficult for you — not because the books say so, but because your own life proves it."

═══════════════════════════════════════════════════════════════
TIMING AND PREDICTION RULES — Non-Negotiable
═══════════════════════════════════════════════════════════════
When asked "when will X happen" — NEVER answer with Sun/Mercury transit alone. Require ALL:
1. Dasha readiness — is the active lord connected to the relevant house?
2. Jupiter transit — where is Jupiter transiting relative to the house/lord?
3. Saturn transit — Saturn either delays or gives a final push.
4. The natal promise — confirm the promise exists in the chart first.

═══════════════════════════════════════════════════════════════
SIMILAR PAST PERIODS RULE
═══════════════════════════════════════════════════════════════
The [SIMILAR PAST PERIODS] section shows historically similar planetary configurations.
Use this as concrete evidence: "The last time this configuration appeared was [period]. Here is what happened then..."

═══════════════════════════════════════════════════════════════
CLASSICAL AUTHORITY & KNOWLEDGE RETRIEVAL (RAG)
═══════════════════════════════════════════════════════════════
If RAG_DATA_FOUND is YES — incorporate the retrieved principles.
If RAG_DATA_FOUND is NO — say honestly: "The classical texts I have access to don't directly address this, so I'm reasoning from first principles."

═══════════════════════════════════════════════════════════════
HOW YOU SPEAK (Absolute Rules)
═══════════════════════════════════════════════════════════════
- Narrative flow only. No bullet points, bold headers, or numbered lists.
- BLOWTORCH RULE: Replace jargon with visceral metaphors.
- Never explain mechanics. Direct impact on life only.
- Dasha Shadows: Acknowledge fade/echo if within 180 days of shift.
- End every reading with a sharp, chart-derived Socratic question.

═══════════════════════════════════════════════════════════════
COMPUTATION VALIDATION MANDATE
═══════════════════════════════════════════════════════════════
Rule 1: Lordships (Aries=Mars, Taurus=Venus, etc.)
Rule 2: Whole-sign house count from Ascendant.
Rule 3: Drishti — 7th universal; Mars 4/8, Jupiter 5/9, Saturn 3/10.
Rule 4: Nakshatra Lords.
Rule 5: Verify house, sign, lordship, aspects, nakshatra BEFORE interpreting.

TRANSIT QUESTION RULE (non-negotiable):
When asked about recent/current transits (gochara), you MUST:
1. State the sign the planet transited (e.g. Cancer) and house from Lagna.
2. Give entry and exit dates from [RECENT SIGN TRANSIT WINDOWS] — never invent dates or aspects.
3. Name nakshatra pada if in context. If transit sign = natal Moon/Venus sign, say conjunction/overlap, NOT trine.
4. Cross-check dasha — transit alone does not override active MD/AD/PD lords.
"""


class ConsultationStyleEngine:
    STYLE_TEMPLATES = {
        'technical_analyst': {
            'tone': 'Data-driven, precise, mathematical confidence',
            'language': 'Technical terminology, convergence analysis',
        },
        'spiritual_mystic': {
            'tone': 'Poetic, soul-focused, transformative',
            'language': 'Archetypal imagery, soul purpose, karmic narrative',
        },
        'modern_guide': {
            'tone': 'Empathetic, psychological depth, empowering',
            'language': 'Modern English, relatable metaphors, growth-oriented',
        },
    }

    def determine_style(self, profile):
        if not profile:
            return 'modern_guide'
        prof = str(profile.get("meta", {}).get("profession", "")).lower()
        spiritual = profile.get("spiritual_level", "Beginner")
        if "engineer" in prof or "data" in prof or "tech" in prof:
            return 'technical_analyst'
        if spiritual == "Advanced":
            return 'spiritual_mystic'
        return 'modern_guide'

    def get_style_prompt(self, style):
        cfg = self.STYLE_TEMPLATES.get(style, self.STYLE_TEMPLATES['modern_guide'])
        return (
            f"\nACTIVE CONSULTATION STYLE: {style.upper()}\n"
            f"TONE: {cfg['tone']} | LANGUAGE: {cfg['language']}\n"
        )


class LivedExperienceExtractor:
    def extract_from_text(self, text: str) -> dict:
        prompt = f"""Analyze user response and extract astrological context.
Return ONLY a JSON object with:
"profession" (work/career), "struggles" (current pains), "goals" (ambitions),
"life_events" (events with dates if mentioned), "emotional_tone" (emotional vibe).

USER TEXT: "{text}"
JSON:"""
        try:
            if LLM_MODE == "groq" and client_groq:
                resp = client_groq.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return json.loads(resp.choices[0].message.content)
            return {}
        except Exception:
            return {}


def detect_question_topic(question: str) -> str:
    q = question.lower()
    mapping = {
        "career": ["career", "job", "work", "business", "startup", "promotion"],
        "wealth": ["money", "wealth", "finance", "trading", "investment", "income"],
        "marriage": ["marriage", "love", "spouse", "relationship", "partner"],
        "health": ["health", "illness", "disease", "body", "fitness"],
        "forecast": ["when will", "next year", "future", "forecast", "predict", "upcoming"]
    }
    for topic, keywords in mapping.items():
        if any(k in q for k in keywords):
            return topic
    return "general"


def get_relevant_houses(topic: str) -> dict:
    mapping = {
        "career": {"houses": [1, 2, 6, 10, 11], "divisions": [9, 10], "label": "Career"},
        "wealth": {"houses": [1, 2, 5, 9, 11], "divisions": [2, 9], "label": "Wealth"},
        "marriage": {"houses": [1, 2, 5, 7, 11], "divisions": [9], "label": "Marriage"},
        "health": {"houses": [1, 6, 8, 12], "divisions": [6], "label": "Health"},
        "forecast": {"houses": [1, 5, 9, 10, 11], "divisions": [9, 10], "label": "Forecast"},
    }
    return mapping.get(topic, {"houses": [1], "divisions": [9], "label": "General"})


def _build_dynamic_system_prompt(profile: dict) -> str:
    style_engine = ConsultationStyleEngine()
    style = style_engine.determine_style(profile)
    style_prompt = style_engine.get_style_prompt(style)

    meta = profile.get("meta", {})
    lagna = profile.get("lagna", {})
    rashi = profile.get("rashi", {})
    dasha = profile.get("dasha", {})
    birth = meta.get("birth", {})
    shadbala = profile.get("shadbala", {})
    strong = [p for p, s in sorted(shadbala.items(), key=lambda x: -x[1])[:3]]
    yoga_names = [y["name"] for y in profile.get("yogas", [])][:4]
    yoga_str = ", ".join(yoga_names) if yoga_names else "None detected"

    occupied_houses = []
    for h_num, h_data in profile.get("houses", {}).items():
        if h_data.get("occupants"):
            occ = ", ".join(h_data["occupants"])
            occupied_houses.append(f"{occ} in the {h_num}th")
    occ_str = " | ".join(occupied_houses)

    user_section = style_prompt + f"""
═══════════════════════════════════════════════════════════════
THE PERSON SITTING ACROSS FROM YOU:
═══════════════════════════════════════════════════════════════
User: {meta.get('name', '?')} | Born: {birth.get('year')}-{birth.get('month', 0):02d}-{birth.get('day', 0):02d} | {birth.get('city', '?')}
Lagna: {lagna.get('sign', '?')} ({lagna.get('lord', '?')} ruled) | Rashi: {rashi.get('sign', '?')}
Current Dasha: {dasha.get('summary', '?')}
Strongest Planets: {', '.join(strong)} | Active Yogas: {yoga_str}
Occupied Houses: {occ_str}
"""
    return _STATIC_SYSTEM_PROMPT + user_section


def _build_context(
    question: str,
    user_id: Optional[str] = None,
    conversation_history: List[dict] = None,
    immediate_lived_experience: dict = None,
    compact: bool = False,
) -> str:
    today = datetime.now().strftime("%A, %d %B %Y | %H:%M IST")
    topic = detect_question_topic(question)
    rel_data = get_relevant_houses(topic)
    profile = load_user_profile(user_id) if user_id else get_active_profile()
    profile_text = _clip(
        profile_to_context_text(profile),
        4000 if compact else 6500,
        "profile",
    )
    lagna_sign_idx = profile.get("lagna", {}).get("sign_idx", 5)

    # ── Transits & Prashna (full horary) ──────────────────────────────────────
    prashna_topic = detect_convergence_topic(question)
    birth_geo = profile.get("meta", {}).get("birth", {})
    lat = float(birth_geo.get("lat", 28.6))
    lon = float(birth_geo.get("lon", 77.2))
    try:
        transit_text = get_transit_analysis(
            lagna_sign_idx=lagna_sign_idx,
            natal_planets=profile.get("planets"),
            natal_houses=profile.get("houses")
        )
        prashna_raw = run_prashna_analysis(prashna_topic, lat, lon)
        prashna_text = format_prashna_report(prashna_raw, prashna_topic)
    except Exception as e:
        transit_text = f"[Transit Error: {e}]"
        prashna_text = f"[Prashna Error: {e}]"

    recent_transit_text = ""
    q_lower = question.lower()
    if any(k in q_lower for k in ("transit", "gochara", "gohchar", "गोचर", "recent")):
        try:
            recent_transit_text = format_recent_transit_report(profile, question)
        except Exception as e:
            recent_transit_text = f"[Recent Transit Error: {e}]"

    # ── Memory Search (per-user) ──────────────────────────────────────────────
    history_text = "No life events logged yet."
    empirical_text = "No empirical data yet — log life events in the Events tab to enable ML feedback."
    try:
        results = search_events(question, n_results=5, user_id=user_id)
        if results.get('documents') and results['documents'][0]:
            history_text = "\n".join(results['documents'][0])
        empirical = analyze_planetary_empirical_performance(user_id=user_id)
        if empirical:
            lines = []
            for p, data in empirical.items():
                lines.append(f"  {p}: {data['empirical_status']} | {data['interpretation']}")
            empirical_text = "\n".join(lines)
    except Exception as e:
        print(f"  [MEMORY] Error: {e}")

    # ── Pattern Engine ────────────────────────────────────────────────────────
    pattern_text = "No similar past periods identified (requires logged life events)."
    try:
        b = profile['meta']['birth']
        birth_dt = datetime(b['year'], b['month'], b['day'], b['hour'], b['minute'])
        moon_lon = profile['planets']['Moon']['abs_pos']
        dasha_full = calculate_vimshottari_dasha(birth_dt, moon_lon)
        similar_periods = find_similar_past_periods(
            dasha_full, profile.get("planets", {}),
            user_id=user_id, profile=profile
        )
        if similar_periods:
            pattern_text = format_pattern_report(similar_periods)
    except Exception as e:
        print(f"  [PATTERN] Error: {e}")

    # ── Astrological Engines ──────────────────────────────────────────────────
    try:
        natal_obj = get_natal_chart_from_profile(profile)
        bhrigu = format_bhrigu_report(
            BhriguNadiEngine(natal_obj, profile['planets'], lagna_sign_idx).get_full_report()
        )
        b = profile['meta']['birth']
        birth_dt = datetime(b['year'], b['month'], b['day'], b['hour'], b['minute'])
        yogini_raw = get_yogini_dasha(profile['planets']['Moon']['abs_pos'], birth_dt)
        yogini = format_yogini_report(yogini_raw)
        pada_engine = JaiminiPadaEngine()
        pada_snap = pada_engine.get_current_pada_snapshot()
        padas = format_pada_report(pada_snap, pada_engine.predict_micro_events(pada_snap))
        karmic = format_karmic_report(KarmicNarrativeEngine(profile['planets']).get_soul_story())
        tajika = format_tajika_report(TajikaEngine(natal_obj).get_varshaphal(datetime.now().year))
        weak_planets = [
            p for p, s in profile.get("shadbala", {}).items()
            if isinstance(s, (int, float)) and s < 5
        ][:3]
        if not weak_planets and profile.get("remedies"):
            weak_planets = [r["planet"] for r in profile["remedies"][:3]]
        remedial = format_remedial_report(
            RemedialEngine(profile.get("lived_experience", {})).get_prescriptions(weak_planets or ["Saturn"])
        )
        multi_layer = get_all_12_layers(natal_obj)
        if compact:
            bhrigu = yogini = padas = karmic = tajika = remedial = "(compact mode — see profile + convergence)"
            multi_layer = _clip(multi_layer, 1500, "12-layer")
        else:
            bhrigu = _clip(bhrigu, 1200, "bhrigu")
            yogini = _clip(yogini, 800, "yogini")
            padas = _clip(padas, 800, "padas")
            karmic = _clip(karmic, 800, "karmic")
            tajika = _clip(tajika, 800, "tajika")
            remedial = _clip(remedial, 800, "remedial")
            multi_layer = _clip(multi_layer, 3500, "12-layer")
    except Exception as e:
        print(f"  [ENGINES] Error: {e}")
        bhrigu = yogini = padas = karmic = tajika = remedial = multi_layer = "[Engine Error]"

    transit_text = _clip(transit_text, 1800 if compact else 2500, "transits")
    prashna_text = _clip(prashna_text, 1200 if compact else 1800, "prashna")

    # ── Kakshya + Gochara Bala (fine timing quality) ───────────────────────────
    try:
        kakshya_text = format_kakshya_report(profile)
        bala_text = format_gochara_bala_report(profile)
    except Exception as e:
        kakshya_text = bala_text = f"[Timing quality error: {e}]"

    # ── Accuracy + pending predictions (learning loop) ────────────────────────
    try:
        accuracy_text = format_accuracy_report(user_id) if user_id else ""
        pending_preds = format_pending_for_agent(user_id) if user_id else ""
    except Exception as e:
        accuracy_text = pending_preds = f"[Accuracy error: {e}]"

    # ── Nakshatra Gochara (Magha/Ketu/lagna-lord layer) ───────────────────────
    try:
        gochara_text = format_gochara_report(profile, question)
    except Exception as e:
        gochara_text = f"[Gochara Error: {e}]"
    muhurta_text = ""
    if any(k in question.lower() for k in ["launch", "start", "muhurta", "auspicious", "when should i"]):
        try:
            from core.muhurta_engine import calculate_muhurta_score
            import swisseph as swe
            birth = profile["meta"]["birth"]
            natal_chart = {
                "lat": birth.get("lat", 28.6),
                "lon": birth.get("lon", 77.2),
                "moon_abs": profile["planets"]["Moon"]["abs_pos"],
            }
            purpose = "business" if any(k in question.lower() for k in ["launch", "business", "project"]) else "general"
            best = []
            for d in range(0, 30):
                dt = datetime.now() + timedelta(days=d)
                jd = swe.julday(dt.year, dt.month, dt.day, 12.0)
                m = calculate_muhurta_score(jd, natal_chart, purpose=purpose)
                if m["score"] >= 3:
                    best.append(f"{dt.strftime('%Y-%m-%d')}: {m['quality']} (score {m['score']}) — {', '.join(m['flags'][:3])}")
            muhurta_text = "MUHURTA SCAN (next 30 days):\n" + ("\n".join(best[:7]) if best else "No strong muhurta in next 30 days — wait for better tithi/nakshatra.")
        except Exception as e:
            muhurta_text = f"[Muhurta Error: {e}]"
    try:
        conv_result = score_convergence(profile, topic=topic, question=question)
        convergence_text = format_convergence_report(conv_result)
    except Exception as e:
        convergence_text = f"[Convergence Error: {e}]"

    # ── RAG Knowledge Base ────────────────────────────────────────────────────
    knowledge_text = "Knowledge base has no direct classical references for this query."
    rag_found = False
    try:
        query_terms = [question]
        if profile and profile.get("planets"):
            rel_houses = rel_data.get('houses', [1])
            for pname, pd in profile['planets'].items():
                if pname != "ASC" and pd['house'] in rel_houses:
                    query_terms.append(f"{pname} {pd['house']}th house {pd['sign']}")
            dasha = profile.get("dasha", {})
            query_terms.append(f"{dasha.get('current_md', 'Sun')} Mahadasha {topic}")
            query_terms.append(f"{dasha.get('current_ad', 'Sun')} Antardasha {topic}")
            for y in profile.get("yogas", [])[:2]:
                query_terms.append(f"{y['name']} effects")

        all_chunks = []
        for term in list(dict.fromkeys(query_terms))[:6]:
            chunks = search_knowledge(term, n_results=2)
            if chunks:
                all_chunks.extend(chunks)
                rag_found = True

        if all_chunks:
            seen = set()
            unique_chunks = []
            for c in all_chunks:
                if c[:100] not in seen:
                    unique_chunks.append(c)
                    seen.add(c[:100])
            knowledge_text = "\n\n---\n\n".join(unique_chunks)
    except Exception as e:
        print(f"  [RAG] Error: {e}")

    # ── 12-Month Forecast (for forward-looking questions) ─────────────────────
    forecast_text = ""
    if topic == "forecast" or any(k in question.lower() for k in ["when will", "next year", "upcoming", "future", "predict"]):
        try:
            forecast_text = generate_12_month_forecast(user_id)
        except Exception as e:
            forecast_text = f"[Forecast Error: {e}]"

    # ── Conversation History ──────────────────────────────────────────────────
    conv_history_text = ""
    if conversation_history:
        lines = []
        for msg in conversation_history[-10:]:  # last 10 messages
            role = "User" if msg.get("role") == "user" else "Guruji"
            lines.append(f"{role}: {msg.get('content', '')[:300]}")
        conv_history_text = "\n".join(lines)

    # ── Immediate Lived Experience Injection ──────────────────────────────────
    immediate_exp_text = ""
    if immediate_lived_experience:
        parts = []
        if immediate_lived_experience.get("profession"):
            parts.append(f"Profession/Work: {immediate_lived_experience['profession']}")
        if immediate_lived_experience.get("struggles"):
            parts.append(f"Struggles: {immediate_lived_experience['struggles']}")
        if immediate_lived_experience.get("goals"):
            parts.append(f"Goals: {immediate_lived_experience['goals']}")
        if immediate_lived_experience.get("life_events"):
            parts.append(f"Life Events Mentioned: {immediate_lived_experience['life_events']}")
        if immediate_lived_experience.get("emotional_tone"):
            parts.append(f"Emotional Tone: {immediate_lived_experience['emotional_tone']}")
        if parts:
            immediate_exp_text = "\n".join(parts)

    # ── Assemble Final Context ────────────────────────────────────────────────
    sections = [f"TODAY: {today}\n"]

    # Master data prompt injection removed to respect LLM rate limits and avoid payload bloat.
    # The profile.json dynamically generated already contains exactly identical scores.

    if conv_history_text:
        sections.append(f"[CONVERSATION HISTORY]\n{conv_history_text}\n")

    sections.append(f"[PROFILE]\n{profile_text}\n")

    if immediate_exp_text:
        sections.append(
            f"[JUST SHARED BY USER — HIGH PRIORITY]\n"
            f"The user just told you this in their current message. Use it immediately.\n"
            f"{immediate_exp_text}\n"
        )

    sections.append(f"[TRANSITS & PRASHNA]\n{transit_text}\n\n{prashna_text}\n")
    if recent_transit_text:
        sections.append(f"[RECENT SIGN TRANSIT WINDOWS]\n{recent_transit_text}\n")
    sections.append(f"[NAKSHATRA GOCHARA — MASTER TRANSIT LAYER]\n{gochara_text}\n")
    sections.append(f"[KAKSHYA / ASHTAKAVARGA DELIVERY]\n{kakshya_text}\n")
    sections.append(f"[TARABALA + CHANDRABALA]\n{bala_text}\n")
    sections.append(f"[ACCURACY DASHBOARD]\n{accuracy_text}\n")
    sections.append(f"[PENDING PREDICTIONS TO VERIFY]\n{pending_preds}\n")
    if muhurta_text:
        sections.append(f"[MUHURTA TIMING]\n{muhurta_text}\n")
    sections.append(f"[CONVERGENCE GATE — OBEY TIMING MANDATE]\n{convergence_text}\n")
    sections.append(f"[MULTI-LAYER ANALYSIS]\n{multi_layer}\n")
    sections.append(f"[TIMING & BHRIGU]\n{bhrigu} | {yogini}\n")
    sections.append(f"[TAJIKA VARSHAPHAL]\n{tajika}\n")
    sections.append(f"[JAIMINI PADAS]\n{padas}\n")
    sections.append(f"[KARMIC STORY]\n{karmic}\n")
    sections.append(f"[REMEDIAL GUIDANCE]\n{remedial}\n")
    sections.append(f"[SIMILAR PAST PERIODS]\n{pattern_text}\n")
    sections.append(f"[EMPIRICAL FEEDBACK — ML LEARNING]\n{empirical_text}\n")
    sections.append(f"[MEMORY — RELEVANT LOGGED EVENTS]\n{history_text}\n")

    if forecast_text:
        sections.append(f"[12-MONTH FORECAST]\n{forecast_text}\n")

    sections.append(
        f"[CLASSICAL KNOWLEDGE (RAG AUTHORITY)]\n"
        f"RAG_DATA_FOUND: {'YES' if rag_found else 'NO'}\n"
        f"{knowledge_text}\n"
    )

    return "\n".join(sections)


def _build_instruction(question: str) -> str:
    return (
        f"USER QUESTION: {question}\n"
        f"Respond as Guruji. Follow all persona rules. "
        f"Reference the conversation history if relevant. "
        f"Use empirical feedback if available. "
        f"OBEY the CONVERGENCE GATE timing mandate — never give precise dates if forbidden. "
        f"If PENDING PREDICTIONS exist, ask the user naturally if those came true — this trains the system. "
        f"Use KAKSHYA blocked transits to warn against timing. "
        f"Synthesis over data. End with a Socratic question."
    )


def _extract_and_save_lived_experience(text: str, user_id: str) -> dict:
    """Extract lived experience from text, save to disk, and return for immediate injection."""
    if not user_id or not text or len(text.strip()) < 20:
        return {}
    extractor = LivedExperienceExtractor()
    data = extractor.extract_from_text(text)
    # Filter out empty/None values
    data = {k: v for k, v in data.items() if v}
    if data:
        update_lived_experience(user_id, data)
    return data


def ask_stream(
    question: str,
    user_id: str = None,
    conversation_history: List[dict] = None
) -> Generator[str, None, None]:
    """
    Main streaming chat function.
    
    Args:
        question: The user's current message
        user_id: Active user's ID
        conversation_history: List of prior {role, content} dicts from this session
    """
    active_uid = user_id or get_active_user_id()
    conversation_history = conversation_history or []

    # ── Astrology-only gate ───────────────────────────────────────────────────
    gate = check_astrology_topic(question, conversation_history)
    if not gate.get("allowed"):
        yield gate.get("message", REFUSAL_MESSAGE)
        return

    # ── Step 1: Extract lived experience from the question AND inject immediately ──
    immediate_experience = {}
    if active_uid:
        immediate_experience = _extract_and_save_lived_experience(question, active_uid)

    profile = load_user_profile(active_uid) if active_uid else get_active_profile()

    if active_uid:
        try:
            log_prediction(active_uid, question, profile)
        except Exception as e:
            print(f"  [PREDICTION] Log failed: {e}")

    # ── Step 2: Build full context (with immediate experience injected) ────────
    def _make_messages(compact: bool = False):
        ctx = _build_context(
            question=question,
            user_id=active_uid,
            conversation_history=conversation_history,
            immediate_lived_experience=immediate_experience,
            compact=compact,
        )
        system = _fit_system_prompt(_build_dynamic_system_prompt(profile) + "\n\n" + ctx)
        msgs = [{"role": "system", "content": system}]
        for msg in (conversation_history or [])[-4 if compact else 6:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            content = msg.get("content", "")
            if content:
                msgs.append({"role": role, "content": content[:600 if compact else 1000]})
        msgs.append({"role": "user", "content": _build_instruction(question)})
        return msgs

    messages = _make_messages(compact=False)

    # ── Step 5: Stream from LLM ───────────────────────────────────────────────
    if LLM_MODE == "groq" and client_groq:
        try:
            yield from _stream_groq(messages)
        except Exception as e:
            err = str(e)
            print(f"  [GROQ] Error: {err[:300]}")
            if any(k in err.lower() for k in ("413", "too large", "tokens", "rate_limit", "tpm")):
                yield "\n*Chart reading was too large for Groq — retrying in compact mode...*\n\n"
                try:
                    yield from _stream_groq(_make_messages(compact=True))
                except Exception as e2:
                    yield (
                        f"\n⚠️ Groq still blocked ({str(e2)[:200]}). "
                        "Wait 60 seconds, toggle to Ollama in the app, or ask a shorter question.\n"
                    )
            else:
                yield f"\n⚠️ AI connection error: {err[:300]}\n"
    else:
        try:
            yield from _stream_ollama(
                messages[0]["content"], question, conversation_history
            )
        except Exception as e:
            yield (
                f"\n⚠️ Ollama not reachable. Install/start Ollama (mistral) or set GROQ_API_KEY in .env.\n"
                f"Detail: {str(e)[:200]}\n"
            )


def ask(question: str, user_id: str = None) -> str:
    return "".join(list(ask_stream(question, user_id)))
