"""
core/transit_engine.py
────────────────────────────────────────────────────
Live Transit Analysis Engine
Calculates:
  1. Where every planet is transiting TODAY
  2. Which natal houses each transit planet occupies
  3. Aspects from transiting planets to natal planets
  4. Sign-based transits of slow planets (Saturn/Jupiter/Rahu-Ketu)
  5. Narrative interpretation for each slow-planet transit
────────────────────────────────────────────────────
"""

from datetime import datetime
from core.astro_engine import get_current_sky, get_natal_chart, get_nakshatra_and_pada

# Natal house cusp — precomputed from chart
# Virgo Lagna Whole Sign: House N starts at sign (start_sign_idx + N - 1) % 12
# Signs: Ari=0, Tau=1, Gem=2, Can=3, Leo=4, Vir=5, Lib=6, Sco=7, Sag=8, Cap=9, Aqu=10, Pis=11
LAGNA_SIGN_IDX = 5  # Virgo = index 5

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS_KEYS = {
    'sun': 'Sun',
    'moon': 'Moon',
    'mercury': 'Mercury',
    'venus': 'Venus',
    'mars': 'Mars',
    'jupiter': 'Jupiter',
    'saturn': 'Saturn',
    'true_north_lunar_node': 'Rahu',
    'true_south_lunar_node': 'Ketu',
}


def abs_pos_to_house(abs_pos: float, lagna_sign_idx: int = LAGNA_SIGN_IDX) -> int:
    """Returns which natal house (1–12) a given ecliptic degree falls in (Whole Sign)."""
    sign_idx = int(abs_pos // 30) % 12
    return (sign_idx - lagna_sign_idx + 12) % 12 + 1


def get_aspect_type(diff_deg: float) -> tuple[str, float] | None:
    """
    Checks if diff_deg matches a Vedic major aspect.
    Returns (aspect_name, orb_away) or None.
    Aspects checked: Conjunction (0°), Square (90°), Trine (120°), Opposition (180°).
    Also sextile (60°) with tighter orb.
    """
    diff = diff_deg % 360
    if diff > 180:
        diff = 360 - diff

    aspect_table = [
        (0,   "Conjunct",   8.0),
        (60,  "Sextile",    5.0),
        (90,  "Square",     7.0),
        (120, "Trine",      7.0),
        (180, "Oppose",     8.0),
    ]
    for deg, name, orb in aspect_table:
        if abs(diff - deg) <= orb:
            return (name, abs(diff - deg))
    return None


def get_transit_analysis() -> str:
    """
    Master function. Returns a richly formatted text block covering:
    - Current positions of all transiting planets
    - Which natal house each is in
    - Aspects to natal planets
    - Slow-planet transit narratives
    """
    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y %H:%M IST")

    try:
        sky = get_current_sky()
        natal = get_natal_chart()
    except Exception as e:
        return f"[Transit Engine Error: {e}]"

    m_sky = sky.model()
    m_nat = natal.model()

    # ── 1. Collect transit positions ─────────────────────────────────────────
    transit_data = {}
    for key, name in PLANETS_KEYS.items():
        p = getattr(m_sky, key)
        nak, pada = get_nakshatra_and_pada(p.abs_pos)
        transit_data[name] = {
            'abs_pos': p.abs_pos,
            'sign': p.sign,
            'degree': round(p.position, 2),
            'nakshatra': nak,
            'pada': pada,
            'retrograde': p.retrograde,
            'natal_house': abs_pos_to_house(p.abs_pos),
        }

    # ── 2. Collect natal positions ───────────────────────────────────────────
    natal_data = {}
    for key, name in PLANETS_KEYS.items():
        p = getattr(m_nat, key)
        natal_data[name] = p.abs_pos
    natal_data['ASC'] = m_nat.ascendant.abs_pos

    # ── 3. Calculate aspects from TRANSITING to NATAL ────────────────────────
    slow_planets  = {'Jupiter', 'Saturn', 'Rahu', 'Ketu'}
    medium_planets = {'Mars', 'Sun', 'Venus'}

    aspects = []
    for t_name, t_info in transit_data.items():
        for n_name, n_abs in natal_data.items():
            diff = abs(t_info['abs_pos'] - n_abs) % 360
            result = get_aspect_type(diff)
            if result is None:
                continue
            aspect_name, orb = result
            # Filter: only log slow planets for all aspects; medium for conjunctions only
            if t_name in slow_planets or (t_name in medium_planets and aspect_name == "Conjunct"):
                aspects.append({
                    'transit':  t_name,
                    'retro':    t_info['retrograde'],
                    'aspect':   aspect_name,
                    'natal':    n_name,
                    'orb':      round(orb, 2),
                })

    aspects.sort(key=lambda x: x['orb'])  # tightest first

    # ── 3.5 Transit Alert System ─────────────────────────────────────────────
    alerts = []
    for a in aspects:
        if a['orb'] < 3.0 and a['natal'] in ['ASC', 'Moon', 'Sun'] and a['transit'] in slow_planets:
            if a['aspect'] == 'Conjunct':
                impact = "Major restructuring or heavy karma processing beginning!"
            elif a['aspect'] == 'Oppose':
                impact = "Partnership or external relationship climax/tension!"
            else:
                impact = "Significant unfolding of events."
            retro = "(R)" if a['retro'] else ""
            alerts.append(f"🚨 TRANSIT ALERT: {a['transit']}{retro} is {a['aspect']} your natal {a['natal']} (Orb: {a['orb']}°). {impact}")

    # ── 4. Build the output ──────────────────────────────────────────────────
    lines = [
        f"[LIVE TRANSIT ANALYSIS] {date_str}",
        "=" * 70,
    ]
    
    if alerts:
        lines.append("")
        lines.extend(alerts)
        lines.append("-" * 70)

    lines.extend([
        "",
        "  TRANSITING PLANET POSITIONS:",
        f"  {'Planet':<10} {'Sign':<14} {'Deg':>6}  {'Nakshatra':<18} {'Pada'} {'Retro':<5} -> Natal House",
        "  " + "-"*80,
    ])

    for name, info in transit_data.items():
        retro = "(R)" if info['retrograde'] else "   "
        lines.append(
            f"  {name:<10} {info['sign']:<14} {info['degree']:>6.2f} deg  "
            f"{info['nakshatra']:<18} {info['pada']}    {retro:<5}  House {info['natal_house']}"
        )

    # 5. Transit-over-natal-house narratives for slow planets
    lines.extend(["", "  SLOW-PLANET TRANSIT OVER YOUR NATAL HOUSES (KEY NARRATIVES):"])

    sat_h  = transit_data['Saturn']['natal_house']
    jup_h  = transit_data['Jupiter']['natal_house']
    rah_h  = transit_data['Rahu']['natal_house']
    ket_h  = transit_data['Ketu']['natal_house']
    sat_r  = transit_data['Saturn']['retrograde']
    jup_r  = transit_data['Jupiter']['retrograde']

    lines.append(f"\n  [SATURN] Transiting House {sat_h} {'(Retrograde)' if sat_r else '(Direct)'}")
    lines.append(f"    {_saturn_house_narrative(sat_h)}")

    lines.append(f"\n  [JUPITER] Transiting House {jup_h} {'(Retrograde)' if jup_r else '(Direct)'}")
    lines.append(f"    {_jupiter_house_narrative(jup_h)}")

    lines.append(f"\n  [RAHU] Transiting House {rah_h}")
    lines.append(f"    {_rahu_house_narrative(rah_h)}")

    lines.append(f"\n  [KETU] Transiting House {ket_h}")
    lines.append(f"    {_ketu_house_narrative(ket_h)}")

    # 6. Major transit aspects
    if aspects:
        lines.extend(["", "  MAJOR TRANSIT ASPECTS TO YOUR NATAL PLANETS:"])
        for a in aspects[:15]:
            retro = "(R)" if a['retro'] else ""
            lines.append(
                f"    Transit {a['transit']:8}{retro:3} {a['aspect']:10} "
                f"Natal {a['natal']:8} | Orb: {a['orb']:.1f}°"
            )
    else:
        lines.append("\n  No major transit aspects calculated.")

    # ── 7. Mars transit (always relevant being 3H/8H lord) ───────────────────
    mars_h = transit_data['Mars']['natal_house']
    lines.extend([
        "",
        f"  [MARS] Transiting House {mars_h}",
        f"    {_mars_house_narrative(mars_h)}",
        "",
        "  KEY SYNTHESIS NOTE:",
        f"    Saturn in H{sat_h} + Jupiter in H{jup_h} creates a "
        f"{'constructive' if abs(sat_h - jup_h) in [4,5,8,9] else 'challenging'} dynamic. "
        f"Rahu-Ketu axis on {rah_h}H-{ket_h}H is the primary karmic pressure point right now.",
        "",
        "=" * 70,
    ])

    return "\n".join(lines)


# ─── House Narratives for Slow Planets ────────────────────────────────────────

def _saturn_house_narrative(h: int) -> str:
    M = {
        1:  "Saturn tests the body and self. Sade Sati influence possible. Health discipline required. Identity is being restructured through hardship. Work on physical fitness and discipline.",
        2:  "Finances are under Saturn's lens. Save money; avoid speculation. Family responsibilities increase. Speech must be careful and honest. Delays in income possible.",
        3:  "Hard work on skills and communication. Courage is tested. Siblings may face challenges. Short travel for work. Disciplined writing and media work rewarded.",
        4:  "Home and property issues require patience. Mother's health may need attention. Emotional foundation being restructured. Real estate decisions should not be rushed.",
        5:  "Creative work requires discipline. Romance faces delays or tests. Children-related responsibilities. Avoid speculation. Saturn demands authenticity in creative expression.",
        6:  "Saturn in 6H is strong — excellent for defeating enemies and competition. Service work is rewarded. Health routines (gym, diet) bring long-term benefits. Legal matters can be won.",
        7:  "Partnerships under serious evaluation. Marriage decisions need careful consideration. Business partnerships may slow down or get restructured. Commitment requires maturity now.",
        8:  "Transformation through hardship. Research and occult work. Financial restructuring through inheritance or partners. Long-term investments over fast gains.",
        9:  "Philosophical and spiritual discipline. Father's health or relationship tests. Long-distance travel with purpose. Higher education through hard work. Dharmic restructuring.",
        10: "Career PEAK demands — Saturn in 10H is classic for career consolidation through hard work. Public recognition comes but through sustained effort. Authority is earned, not given. Critical career period.",
        11: "Gains come slowly but surely. Social network discipline. Friendships based on mutual value. Income increases through persistent effort. Elder siblings may require support.",
        12: "Expenses and foreign focus. Spiritual disciplines rewarded. Isolation can be productive. Past karma resolution. Foreign work or residence possible.",
    }
    return M.get(h, f"Saturn transiting House {h}: Focus, discipline, and patience are required in House {h} themes.")


def _jupiter_house_narrative(h: int) -> str:
    M = {
        1:  "Jupiter blesses the self — health, optimism, and new beginning. Personal growth phase. Lucky period for starting new chapters. Weight gain possible.",
        2:  "Wealth and income expand. Family grows or prospers. Speech is eloquent and influential. Good time for investments and financial decisions.",
        3:  "Skills and communication improve dramatically. Short travel beneficial. Siblings prosper. Media/writing projects succeed. Learning new things.",
        4:  "Home environment improves. Property gains. Mother's wellbeing. Emotional grounding. Higher education pursuits supported. Domestic happiness.",
        5:  "Peak creative period. Romance possible. Children related joy. Speculative gains possible (moderate). Intelligence shines. Education excels.",
        6:  "Health improves. Enemies defeated through wisdom. Service work recognized. Discipline brings results. Legal matters resolve favorably.",
        7:  "Partnerships expand and prosper. Marriage timing highly favorable. Business collaborations grow. Foreign connections through partners.",
        8:  "Hidden resources and investments surface. Research deepens. Spiritual transformation. Inheritance matters resolve. Long-term investments mature.",
        9:  "PEAK LUCK PERIOD. Bhagya (fortune) house = maximum Jupiter benefit. Travel, higher wisdom, father prospers, dharmic alignment. Opportunities flow.",
        10: "Career peak. Promotions and recognition. Authority expands. Public image improves. Government or institutional backing. Jupiter in 10H = Hamsa Yoga influence.",
        11: "Maximum gains phase. Wish fulfillment. Social circle expands beautifully. Income surges. Elder siblings prosper. Desires manifest easily.",
        12: "Spiritual depth and foreign gains. Moksha focus. Meditation and retreat beneficial. Hidden assets or foreign income. Spiritual teacher may appear.",
    }
    return M.get(h, f"Jupiter transiting House {h}: Expansion, wisdom and fortune are active in House {h} themes.")


def _rahu_house_narrative(h: int) -> str:
    M = {
        1:  "Identity in rapid transformation. Unusual or foreign influences on self-image. New obsessions about personal appearance/health. Risk-taking in self-expression.",
        2:  "Unusual income sources. Foreign connections bring wealth. Speech becomes unconventional or tech-related. Family dynamics shift. Obsession with money.",
        3:  "Tech, digital, or foreign media success. Unconventional communication style works. Siblings may have unusual events. Short travel to foreign places.",
        4:  "Home and property through foreign/unusual means. Mother's health requires attention. Real estate in unusual locations. Domestic life is unsettled.",
        5:  "Creative experimentation. Foreign romance possible. Unconventional children's matters. Speculation can amplify (caution). Digital creative work.",
        6:  "Victory over enemies through technology/foreign means. Health issues may surface unexpectedly. Service in tech or foreign domains.",
        7:  "Foreign or unconventional partnerships amplified. Karmic relationships enter life. Business partners from different backgrounds. Marriage timing karmic — proceed with caution.",
        8:  "Hidden matters surface dramatically. Sudden financial changes. Research into occult or foreign systems. Unexpected transformation.",
        9:  "Unconventional philosophy or spirituality. Foreign guru or mentor. Non-traditional higher education. Travel to unusual places.",
        10: "Rapid career rise possible through technology, foreign connections, or unconventional path. Public exposure increases suddenly. Digital/global career.",
        11: "Extraordinary gains possible through digital or foreign means. Unusual network of contacts. Income spikes from unexpected sources.",
        12: "Foreign lands, isolated environments, spiritual experiences, and unusual expenses. Hidden enemies possible. Also: gains from foreign sources.",
    }
    return M.get(h, f"Rahu transiting House {h}: Amplified, obsessive, and unconventional energy in House {h} themes.")


def _ketu_house_narrative(h: int) -> str:
    M = {
        1:  "Detachment from ego and physical identity. Spiritual focus on self. Health requires mindfulness. Past-life wisdom surfacing. Feeling 'different' or out of mainstream.",
        2:  "Detachment from wealth and family. Spiritual use of speech. Past-life wealth karma resolving. Family matters require detachment.",
        3:  "Intuitive communication. Detachment from siblings. Past-life courage rewarded subtly. Spiritual writing or communication.",
        4:  "Detachment from home comforts. Past-life home karma. Focus shifts inward. Mother may go through changes. Spiritual home practices.",
        5:  "Spiritual creativity. Detachment from romance/children. Past-life creative talents awakened. Moksha through creative expression.",
        6:  "Hidden enemies surface and resolve. Spiritual service. Past-life health karma processing. Alternative healing approaches work.",
        7:  "Detachment from partnerships. Karmic partners enter (or exit). Spiritual view of relationships. Past-life partnership karma resolving.",
        8:  "Spiritual transformation. Research into past lives. Hidden karma surfacing. Deep psychological insights. Detachment from crisis.",
        9:  "Spiritual philosophy deepens. Detachment from dogma. Past-life guru connections activated. Dharmic clarity through detachment.",
        10: "Detachment from career recognition. Spiritual purpose in public work. Service-oriented career. Past-life professional karma.",
        11: "Detachment from material gains. Spiritual social circles. Past-life network karma. Gains come through spiritual or charitable means.",
        12: "MOKSHA focus. Foreign spiritual experiences. Maximum detachment. Meditation highly rewarded. Liberation-oriented karmic period.",
    }
    return M.get(h, f"Ketu transiting House {h}: Detachment, past karma, and spiritual energy in House {h} themes.")


def _mars_house_narrative(h: int) -> str:
    M = {
        1:  "Energy surge. Personal drive is high. Health focus. Good for physical work and assertiveness. Can bring conflict in relationships.",
        2:  "Aggressive approach to wealth. Family disputes possible. Financial decisions made quickly — slow down.",
        3:  "Communication becomes forceful. Skills energized. Short travel for work. Sibling dynamics active. Good for writing and digital work.",
        4:  "Home energy activated — renovation or disruption. Mother may be more assertive. Property decisions come to a head.",
        5:  "Creative energy peaks. Romance heats up. Speculation risk is higher. Children-related activity. Competitive edge in creative work.",
        6:  "Mars in 6H is STRONG — excellent for defeating enemies, competition, legal wins, physical fitness. High energy for service.",
        7:  "Partnership conflicts possible. Business negotiations require tact. High energy in relationships. Legal matters active.",
        8:  "Hidden events accelerate. Research intensity. Sudden financial changes. Joint assets matter. Transformation through conflict.",
        9:  "Energy toward philosophy, travel, and higher learning. Father matters active. Long travel for work.",
        10: "Career energy surges. Assertive public image. Work demands increase. Authority challenges. Good for bold career moves.",
        11: "Income from effort. Social activities energized. Network competition. Elder siblings active. Good period to pursue gains aggressively.",
        12: "Hidden work. Foreign energy. Expenses on health or spiritual matters. Research in private. Hidden enemies possible.",
    }
    return M.get(h, f"Mars transiting House {h}: Action, drive, and conflict energy are active in House {h} themes.")


def get_transit_house_summary() -> dict:
    """Returns a simple dict of {planet_name: natal_house} for current transits."""
    try:
        sky = get_current_sky()
        m = sky.model()
        result = {}
        for key, name in PLANETS_KEYS.items():
            p = getattr(m, key)
            result[name] = abs_pos_to_house(p.abs_pos)
        return result
    except Exception as e:
        return {"error": str(e)}
