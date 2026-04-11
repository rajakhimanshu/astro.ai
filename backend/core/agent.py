"""
core/agent.py
────────────────────────────────────────────────────
Jyotish AI — Master Orchestrator (Multi-User)
Combines:
  1. Per-user profile (computed 12-layer chart from user_profile_engine)
  2. Live transit analysis (where planets are TODAY relative to user's chart)
  3. Vimshottari Dasha (MD → AD → PD, computed to the day)
  4. Pattern Engine (astrologically similar past life periods)
  5. Life Event Memory (semantic search of logged events per user)
  6. RAG Knowledge Base (BPHS, classical texts — indexed chunks)
  7. Ollama LLM (streaming synthesis) — conversational, demand-driven
────────────────────────────────────────────────────
"""

import ollama
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.astro_engine import (
    get_natal_chart,
    get_current_sky,
    calculate_vimshottari_dasha,
    load_birth_data,
    get_nakshatra_and_pada,
)
from core.kundali_profile import get_full_kundali_text, get_current_dasha_summary, KUNDALI_PROFILE
from core.transit_engine import get_transit_analysis
from core.memory import search_events
from core.knowledge_base import search_knowledge
from core.pattern_engine import find_similar_past_periods, format_pattern_report
from core.multi_layer_engine import get_all_12_layers
from core.user_profile_engine import (
    get_active_user_id, get_active_profile, load_user_profile,
    profile_to_context_text, list_users
)
from core.forecast_engine import generate_12_month_forecast


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic System Prompt Builder
# ─────────────────────────────────────────────────────────────────────────────

_STATIC_SYSTEM_PROMPT = """You are Astro.AI — a master Vedic Astrology oracle.

You are NOT a generic horoscope bot. You are a precision oracle operating on the
complete personal natal chart and 12-layer Jyotish analysis of the user below.
All your knowledge of their chart is in the context provided with every message.

═══════════════════════════════════════════════════════════════
HOW TO REASON (hold all 12 layers simultaneously, look for convergence):
═══════════════════════════════════════════════════════════════

1. D1 Natal Promise (L1+L3+L4): Check relevant house, lord, dignity, yogas.
2. Strength (L9+L5): Shadbala score + nakshatra lord chain (sub-ruler).
3. D9/D10 Confirmation (L8): Does Navamsa/Dashamsa confirm the D1 promise?
4. Dasha Timing (L6): Is the right planetary period active to trigger this?
5. Transit Weather (L7+L10): ALWAYS cite SAV score with transit house.
   BAD: 'Saturn in 7H is hard' | GOOD: 'Saturn in 7H (SAV=22 <25 = confirmed difficult)'
6. Natal Aspects (L2): What aspects modify the relevant house?
7. Timing precision (L11+L12): Panchanga Vara lord + Prashna Moon's house.

═══════════════════════════════════════════════════════════════
ABSOLUTE RULES:
═══════════════════════════════════════════════════════════════

• Answer DIRECTLY and personally — cite this user's exact chart data every time, as addressing them in person.
• DO NOT give a generic textbook answer. Every paragraph must reference their chart in an engaging way.
• NEVER say 'I cannot predict'. Give your BEST reading with conviction.
• NEVER give transit interpretations without citing the SAV score.
• Always check D9/D10 before confident predictions.
• Always state current MD > AD > PD when timing matters.
• Reference classical texts (BPHS, Phaladeepika) natively in conversation.
• CONNECT past life events to present patterns intuitively.
• End your response with ONE concrete, specific action or timing window.

TONE: Speak as a wise, warm, and highly skilled human astrologer conversing directly with the user.
FORMAT RESTRICTIONS:
- NO rigid sections, headers, or bulleted report styles. Write in flowing, cohesive paragraphs.
- DO NOT divide your response into multi-section analyses (e.g., absolutely NO "12 sections").
- If discussing multiple topics, seamlessly transition between them like a natural conversation.
- Use paragraphs, natural emphasis, and an empathetic yet data-driven voice.
"""


def _build_dynamic_system_prompt(profile: dict) -> str:
    """Build a personalized system prompt from the user's computed profile."""
    meta = profile["meta"]
    lagna = profile["lagna"]
    rashi = profile["rashi"]
    dasha = profile["dasha"]
    birth = meta["birth"]

    # Strongest planets
    shadbala = profile.get("shadbala", {})
    strong = [p for p, s in sorted(shadbala.items(), key=lambda x: -x[1])[:3]]

    # Key yogas summary
    yoga_names = [y["name"] for y in profile.get("yogas", [])][:4]
    yoga_str = ", ".join(yoga_names) if yoga_names else "None detected"

    # 11H stellium check
    h11_planets = profile["houses"].get("11") or profile["houses"].get(11)
    h11_occ = ", ".join(h11_planets["occupants"]) if h11_planets else ""

    user_section = f"""
═══════════════════════════════════════════════════════════════
ACTIVE USER CHART QUICK REFERENCE & PERSONALIZED APPROACH:
═══════════════════════════════════════════════════════════════
User Name: {meta['name']} (Address them by this name warmly and respectfully!)
Birth: {birth['year']}-{birth['month']:02d}-{birth['day']:02d} {birth['hour']:02d}:{birth['minute']:02d} | {birth['city']}, {birth['nation']}

Lagna (Ascendant): {lagna['sign']} {lagna['degree']:.1f}° ({lagna['nakshatra']} Pada {lagna['pada']})
Lagna Lord: {lagna['lord']} in H{lagna['lord_house']}
Rashi (Moon Sign): {rashi['sign']} | Moon Nakshatra: {rashi['nakshatra']}
Current Dasha: {dasha['summary']}
Active Period: {dasha['current_md']} MD → {dasha['current_ad']} AD → {dasha['current_pd']} PD

Dominant Planets (Shadbala): {', '.join(strong)}
Key Yogas: {yoga_str}
H11 Occupants: {h11_occ if h11_occ else 'Empty'}

CUSTOMIZED CONVERSATION DIRECTIVES FOR {meta['name'].upper()}:
- Because their Lagna is {lagna['sign']}, they filter the world through its ruling element and lord ({lagna['lord']}). Frame your insights using imagery related to {lagna['lord']} and {lagna['sign']}.
- They have strong {', '.join(strong[:2])}. Acknowledge these powerful placements as their inherent gifts and speak to the high manifestation of these planets.
- Adjust your tone to resonate with their chart: if Mars/Sun are dominant, be bold and direct; if Moon/Venus, be gentle and empathetic; if Jupiter/Saturn, impart wisdom and structure.
- Always remember you are speaking TO {meta['name']}, not about {meta['name']}. Connect their current {dasha['current_md']} Mahadasha deeply to their core nature.
"""
    return _STATIC_SYSTEM_PROMPT + user_section


# ─────────────────────────────────────────────────────────────────────────────
# Context Builder — The Intelligence Aggregator
# ─────────────────────────────────────────────────────────────────────────────

def _build_context(question: str, user_id: Optional[str] = None) -> str:
    """
    Assembles a comprehensive, multi-layered astrological context block.
    Uses the per-user computed profile + live transits + dasha + memory + RAG.
    """
    today = datetime.now().strftime("%A, %d %B %Y | %H:%M IST")

    # ── Load active user's profile ────────────────────────────────────────────
    profile = None
    profile_text = "[User profile not loaded]"
    try:
        if user_id:
            profile = load_user_profile(user_id)
        else:
            profile = get_active_profile()
        profile_text = profile_to_context_text(profile)
    except Exception as e:
        # Fallback to legacy hardcoded profile
        profile_text = get_full_kundali_text()
        print(f"  [WARNING] User profile engine unavailable: {e} — using legacy profile")

    # ── Live Transit Engine ───────────────────────────────────────────────────
    try:
        transit_text = get_transit_analysis()
    except Exception as e:
        transit_text = f"[Transit Engine Error: {e}]"

    # ── Vimshottari Dasha ─────────────────────────────────────────────────────
    dasha_text = "[Dasha computation unavailable]"
    transitions_text = "No transitions computed."
    try:
        natal = get_natal_chart()
        m = natal.model()
        birth_dt = datetime(m.year, m.month, m.day, m.hour, m.minute)
        moon_lon = m.moon.abs_pos
        dasha_info = calculate_vimshottari_dasha(birth_dt, moon_lon)
        dasha_text = dasha_info.get('summary', '[Dasha summary unavailable]')
        transitions = dasha_info.get('upcoming_transitions', [])
        t_lines = []
        for t in transitions[:6]:
            t_lines.append(
                f"  • {t['type']} ends {t['date'].strftime('%d %b %Y')}: "
                f"{t['md']} MD > {t['ad']} AD > {t['pd']} PD → next: {t['to_lord']}"
            )
        transitions_text = "\n".join(t_lines) if t_lines else "  No transitions computed."
    except Exception as e:
        dasha_text = f"[Dasha engine error: {e}]"

    # ── Pattern Engine ────────────────────────────────────────────────────────
    pattern_report = "[Pattern engine unavailable]"
    try:
        similar = find_similar_past_periods(top_n=3)
        pattern_report = format_pattern_report(similar)
    except Exception as e:
        pattern_report = f"Pattern engine offline: {e}"

    # ── Life Event Memory ─────────────────────────────────────────────────────
    history_text = "No life events logged yet. Add events via the 'Add Life Event' tab."
    try:
        results = search_events(question, n_results=5)
        events_list = []
        if results.get('documents') and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                dasha_snap = meta.get('dasha', '')
                events_list.append(
                    f"  [{meta.get('date','?')}] ({meta.get('domain','?')}) "
                    f"Emotion{meta.get('emotion',0):+d} | Dasha: {dasha_snap[:60]}...\n"
                    f"    Event: {doc[:200]}"
                )
        if events_list:
            history_text = "\n".join(events_list)
    except Exception as e:
        history_text = f"Life memory offline: {e}"

    # ── Classical Knowledge Base (RAG) ────────────────────────────────────────
    knowledge_text = "Knowledge base not yet indexed."
    try:
        chunks = search_knowledge(question, n_results=4)
        if chunks:
            knowledge_text = "\n\n---\n\n".join(chunks)
    except Exception as e:
        knowledge_text = f"Knowledge base offline: {e}"

    # ── Multi-Layer Live Engine (Aspects, Panchanga, Prashna, AV transits) ────
    print("  [2b/3] Computing live 12-layer context (Panchanga, Prashna, AV transits)...")
    multi_layer_text = "[Multi-layer engine unavailable]"
    try:
        multi_layer_text = get_all_12_layers()
    except Exception as e:
        multi_layer_text = f"[Multi-layer engine error: {e}]"

    # ── 12-Month Annual/Monthly Forecast ─────────────────────────────────────
    print("  [2c/3] Generating 12-month Panchaka-style forecast...")
    forecast_text = "[Forecast unavailable]"
    try:
        forecast_text = generate_12_month_forecast(user_id=user_id)
    except Exception as e:
        forecast_text = f"[Forecast engine error: {e}]"

    # ── Assemble Final Context ────────────────────────────────────────────────
    user_name = profile["meta"]["name"] if profile else "User"
    context = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║          COMPLETE 12-LAYER ASTROLOGICAL CONTEXT — {user_name.upper():<30}     ║
╚════════════════════════════════════════════════════════════════════════════╝
[TODAY]: {today}

━━━ NATAL CHART + ALL LAYERS PROFILE (Layers 1, 3, 4, 6, 8, 9, 10) ━━━
{profile_text}

━━━ LAYER 7: LIVE TRANSIT ANALYSIS (THE CURRENT WEATHER OVER THE CHART) ━━━
{transit_text}

━━━ LAYER 6: DASHA TRANSITIONS ━━━
Current Dasha: {dasha_text}
Upcoming transitions:
{transitions_text}

━━━ LAYERS 2, 5, 11, 12: LIVE MULTI-LAYER ENGINE (Aspects, Panchanga, Prashna) ━━━
{multi_layer_text}

━━━ LIFE EVENT MEMORY (SEMANTIC MATCH TO QUESTION) ━━━
{history_text}

━━━ ASTROLOGICAL PATTERN MATCHING (SIMILAR PAST PERIODS) ━━━
{pattern_report}

━━━ 12-MONTH ANNUAL FORECAST ━━━
{forecast_text}

━━━ CLASSICAL JYOTISH KNOWLEDGE BASE (BPHS & CLASSICAL TEXTS — RAG) ━━━
{knowledge_text}
"""
    return context




# ─────────────────────────────────────────────────────────────────────────────
# Instruction Formatter
# ─────────────────────────────────────────────────────────────────────────────

def _build_instruction(question: str) -> str:
    """
    Builds a concise, conversational instruction prompt.
    The AI adapts its response format to the question — not always 12 sections.
    """
    return f"""USER'S QUESTION: "{question}"

Answer this now as a master Jyotishi who has read all the context above.
Reason through all relevant layers internally, then give a direct, personal, confident answer.

FORMAT RULES:
• ABSOLUTELY NO structured reports or '12 sections'. Speak organically.
• Respond in flowing conversational paragraphs. No rigid headers or bulleted lists.
• Always cite specific chart data naturally within your sentences: house, sign, planet, SAV score.
• Always cite SAV score when mentioning any transit planet.
• State current Dasha (MD > AD > PD) when timing is relevant.
• End the conversation gracefully with ONE concrete action, timing window, or suggested remedy.
• Tone: warm, direct, wise — like a trusted personal astrologer having a deep conversation with the user.
"""




# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def ask(question: str, user_id: str = None) -> str:
    """Synchronous — returns complete answer as a string."""
    print(f"\n{'='*70}")
    print(f"  Astro.AI — QUESTION: {question}")
    print(f"{'='*70}")

    print("  [1/3] Building comprehensive astrological context...")
    context  = _build_context(question, user_id=user_id)
    instruction = _build_instruction(question)

    # Load profile for dynamic system prompt
    system_prompt = _STATIC_SYSTEM_PROMPT
    try:
        profile = load_user_profile(user_id) if user_id else get_active_profile()
        system_prompt = _build_dynamic_system_prompt(profile)
    except Exception as e:
        print(f"  [WARNING] Could not build dynamic system prompt: {e}")

    print("  [2/3] Sending to Ollama (mistral) with 12-layer context...")
    response = ollama.chat(
        model='mistral',
        messages=[
            {'role': 'system', 'content': system_prompt + "\n\n[12-LAYER CONTEXT]\n" + context},
            {'role': 'user',   'content': instruction}
        ],
        options={'num_ctx': 32768}
    )

    print("  [3/3] Response received.")
    return response['message']['content']


def ask_stream(question: str, user_id: str = None):
    """
    Streaming version — yields text chunks for real-time Gradio display.
    Re-uses the same context builder and instruction formatter.
    """
    print(f"\n  ★ STREAM — QUESTION: {question}")
    context  = _build_context(question, user_id=user_id)
    instruction = _build_instruction(question)

    system_prompt = _STATIC_SYSTEM_PROMPT
    try:
        profile = load_user_profile(user_id) if user_id else get_active_profile()
        system_prompt = _build_dynamic_system_prompt(profile)
    except Exception as e:
        print(f"  [WARNING] Could not build dynamic system prompt: {e}")

    stream = ollama.chat(
        model='mistral',
        messages=[
            {'role': 'system', 'content': system_prompt + "\n\n[12-LAYER CONTEXT]\n" + context},
            {'role': 'user',   'content': instruction}
        ],
        stream=True,
        options={'num_ctx': 32768}
    )

    for chunk in stream:
        yield chunk['message']['content']


# ─────────────────────────────────────────────────────────────────────────────
# CLI Mode
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('🕉️  Astro.AI — Interactive Oracle Mode')
    print('   Type your question. Type "quit" to exit.\n')
    while True:
        q = input('You: ').strip()
        if not q:
            continue
        if q.lower() in ('quit', 'exit', 'q'):
            print('Namaste. 🙏')
            break
        print('\n🔮 Astro.AI is reading your chart...\n')
        print(ask(q))
        print('\n' + '─' * 70)
