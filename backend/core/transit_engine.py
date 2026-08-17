"""
core/transit_engine.py — Personalized Live Transit Analysis (World-Class Upgrade)

UPGRADE: get_transit_analysis() now accepts natal_planets and natal_houses dicts
so every transit narrative is cross-referenced with THIS user's actual natal chart.
- Reports which natal planets sit in each transited house
- Flags transit planets within 3° of natal planets by degree
- Personalizes slow-planet narratives with actual house occupants
"""

from datetime import datetime, timedelta
from core.astro_engine import get_current_sky, get_natal_chart, get_nakshatra_and_pada, get_sky_on_date

LAGNA_SIGN_IDX = 5  # Virgo — only used when no profile passed

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS_KEYS = {
    'sun': 'Sun', 'moon': 'Moon', 'mercury': 'Mercury', 'venus': 'Venus',
    'mars': 'Mars', 'jupiter': 'Jupiter', 'saturn': 'Saturn',
    'true_north_lunar_node': 'Rahu', 'true_south_lunar_node': 'Ketu',
}


def abs_pos_to_house(abs_pos: float, lagna_sign_idx: int = LAGNA_SIGN_IDX) -> int:
    sign_idx = int(abs_pos // 30) % 12
    return (sign_idx - lagna_sign_idx + 12) % 12 + 1


def get_aspect_type(diff_deg: float):
    diff = diff_deg % 360
    if diff > 180:
        diff = 360 - diff
    aspect_table = [
        (0, "Conjunct", 8.0), (60, "Sextile", 5.0),
        (90, "Square", 7.0), (120, "Trine", 7.0), (180, "Oppose", 8.0),
    ]
    for deg, name, orb in aspect_table:
        if abs(diff - deg) <= orb:
            return (name, abs(diff - deg))
    return None


def _get_natal_occupants(house_num: int, natal_planets: dict) -> list:
    """Return names of natal planets in a given house."""
    if not natal_planets:
        return []
    return [
        name for name, pd in natal_planets.items()
        if name != "ASC" and pd.get("house") == house_num
    ]


def _degree_conjunctions(transit_abs: float, natal_planets: dict, orb: float = 3.0) -> list:
    """Find natal planets within `orb` degrees of a transiting planet."""
    if not natal_planets:
        return []
    hits = []
    for name, pd in natal_planets.items():
        if name == "ASC":
            continue
        diff = abs(transit_abs - pd.get("abs_pos", 0)) % 360
        if diff > 180:
            diff = 360 - diff
        if diff <= orb:
            hits.append((name, round(diff, 2)))
    return hits


def get_transit_analysis(
    lagna_sign_idx: int = LAGNA_SIGN_IDX,
    natal_planets: dict = None,
    natal_houses: dict = None
) -> str:
    """
    Master transit function. Fully personalized when natal_planets is provided.
    """
    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y %H:%M IST")

    try:
        sky = get_current_sky()
    except Exception as e:
        return f"[Transit Engine Error: {e}]"

    m_sky = sky.model()

    # ── Natal positions: use profile when provided (fixes wrong-chart bug) ───
    natal_data = {}
    if natal_planets:
        for name, pd in natal_planets.items():
            if name == "ASC":
                if pd.get("abs_pos") is not None:
                    natal_data["ASC"] = float(pd["abs_pos"])
            elif pd.get("abs_pos") is not None:
                natal_data[name] = float(pd["abs_pos"])
    if not natal_data or len(natal_data) < 2:
        try:
            natal = get_natal_chart()
            m_nat = natal.model()
            for key, name in PLANETS_KEYS.items():
                p = getattr(m_nat, key)
                natal_data[name] = p.abs_pos
            natal_data["ASC"] = m_nat.ascendant.abs_pos
        except Exception:
            pass

    # ── Collect transit positions ─────────────────────────────────────────────
    transit_data = {}
    for key, name in PLANETS_KEYS.items():
        p = getattr(m_sky, key)
        nak, pada = get_nakshatra_and_pada(p.abs_pos)
        natal_house = abs_pos_to_house(p.abs_pos, lagna_sign_idx)
        occupants = _get_natal_occupants(natal_house, natal_planets)
        degree_hits = _degree_conjunctions(p.abs_pos, natal_planets)

        transit_data[name] = {
            'abs_pos': p.abs_pos,
            'sign': p.sign,
            'degree': round(p.position, 2),
            'nakshatra': nak,
            'pada': pada,
            'retrograde': p.retrograde,
            'natal_house': natal_house,
            'natal_occupants': occupants,
            'degree_conjunctions': degree_hits,
        }

    # ── Calculate aspects (against correct natal chart) ───────────────────────
    slow_planets = {'Jupiter', 'Saturn', 'Rahu', 'Ketu'}
    medium_planets = {'Mars', 'Sun', 'Venus'}
    aspects = []

    for t_name, t_info in transit_data.items():
        for n_name, n_abs in natal_data.items():
            if n_name == 'ASC':
                continue
            diff = abs(t_info['abs_pos'] - n_abs) % 360
            result = get_aspect_type(diff)
            if result is None:
                continue
            aspect_name, orb = result
            n_house = abs_pos_to_house(n_abs, lagna_sign_idx)
            if t_name in slow_planets or (t_name in medium_planets and aspect_name == "Conjunct"):
                aspects.append({
                    'transit': t_name, 't_house': t_info['natal_house'],
                    'retro': t_info['retrograde'], 'aspect': aspect_name,
                    'natal': n_name, 'n_house': n_house, 'orb': round(orb, 2),
                })
    aspects.sort(key=lambda x: x['orb'])

    # ── Transit Alerts ────────────────────────────────────────────────────────
    alerts = []
    for a in aspects:
        if a['orb'] < 3.0 and a['transit'] in slow_planets:
            if a['aspect'] == 'Conjunct':
                impact = "Major restructuring beginning — exact pressure point."
            elif a['aspect'] == 'Oppose':
                impact = "External relationship/partnership climax."
            else:
                impact = "Significant life event unfolding."
            retro = "(R)" if a['retro'] else ""
            alerts.append(
                f"TRANSIT ALERT: {a['transit']}{retro} (H{a['t_house']}) is exactly "
                f"{a['aspect']} your natal {a['natal']} (H{a['n_house']}) | "
                f"Orb: {a['orb']}° — {impact}"
            )

    # ── Build output ──────────────────────────────────────────────────────────
    lines = [f"[LIVE TRANSIT ANALYSIS] {date_str}", "=" * 70]

    if alerts:
        lines.append("")
        lines.extend(alerts)
        lines.append("-" * 70)

    lines.extend([
        "", "  TRANSITING POSITIONS:",
        f"  {'Planet':<10} {'Sign':<14} {'Deg':>6}  {'Nakshatra':<18} {'H'} {'R':<4}  Natal Occupants",
        "  " + "-" * 85,
    ])

    for name, info in transit_data.items():
        retro = "(R)" if info['retrograde'] else "   "
        occ = ", ".join(info['natal_occupants']) if info['natal_occupants'] else "Empty"
        lines.append(
            f"  {name:<10} {info['sign']:<14} {info['degree']:>6.2f}°  "
            f"{info['nakshatra']:<18} H{info['natal_house']} {retro:<4}  [{occ}]"
        )

    # ── Degree-level conjunctions ─────────────────────────────────────────────
    degree_hits_found = False
    for name, info in transit_data.items():
        if info['degree_conjunctions']:
            if not degree_hits_found:
                lines.extend(["", "  EXACT DEGREE CONJUNCTIONS (Transit planet within 3° of natal planet):"])
                degree_hits_found = True
            for natal_p, orb in info['degree_conjunctions']:
                lines.append(
                    f"  *** {name} (transiting H{info['natal_house']}) is {orb}° "
                    f"from natal {natal_p} — This is active and powerful right now ***"
                )

    # ── Personalized slow-planet narratives ───────────────────────────────────
    lines.extend(["", "  SLOW-PLANET TRANSIT NARRATIVES (Personalized to Your Chart):"])

    sat_h = transit_data['Saturn']['natal_house']
    jup_h = transit_data['Jupiter']['natal_house']
    rah_h = transit_data['Rahu']['natal_house']
    ket_h = transit_data['Ketu']['natal_house']
    sat_r = transit_data['Saturn']['retrograde']
    jup_r = transit_data['Jupiter']['retrograde']
    sat_occ = transit_data['Saturn']['natal_occupants']
    jup_occ = transit_data['Jupiter']['natal_occupants']
    rah_occ = transit_data['Rahu']['natal_occupants']
    ket_occ = transit_data['Ketu']['natal_occupants']

    def occ_str(occ):
        return f" [Contains natal: {', '.join(occ)}]" if occ else " [Empty house]"

    lines.append(f"\n  [SATURN] H{sat_h} {'(Retrograde)' if sat_r else '(Direct)'}{occ_str(sat_occ)}")
    lines.append(f"    {_saturn_house_narrative(sat_h)}")
    if sat_occ:
        lines.append(f"    PERSONAL: Saturn is directly pressuring your natal {' and '.join(sat_occ)} — the themes of those planets are under Saturnine restructuring.")

    lines.append(f"\n  [JUPITER] H{jup_h} {'(Retrograde)' if jup_r else '(Direct)'}{occ_str(jup_occ)}")
    lines.append(f"    {_jupiter_house_narrative(jup_h)}")
    if jup_occ:
        lines.append(f"    PERSONAL: Jupiter is expanding and blessing your natal {' and '.join(jup_occ)} — their significations are growing now.")

    lines.append(f"\n  [RAHU] H{rah_h}{occ_str(rah_occ)}")
    lines.append(f"    {_rahu_house_narrative(rah_h)}")
    if rah_occ:
        lines.append(f"    PERSONAL: Rahu is amplifying and obsessing your natal {' and '.join(rah_occ)} — intense, karmic energy on these planets.")

    lines.append(f"\n  [KETU] H{ket_h}{occ_str(ket_occ)}")
    lines.append(f"    {_ketu_house_narrative(ket_h)}")
    if ket_occ:
        lines.append(f"    PERSONAL: Ketu is detaching and spiritualizing your natal {' and '.join(ket_occ)} — past-life themes surfacing.")

    mars_h = transit_data['Mars']['natal_house']
    mars_occ = transit_data['Mars']['natal_occupants']
    lines.extend([
        f"\n  [MARS] H{mars_h}{occ_str(mars_occ)}",
        f"    {_mars_house_narrative(mars_h)}",
    ])
    if mars_occ:
        lines.append(f"    PERSONAL: Mars is energizing/conflicting your natal {' and '.join(mars_occ)}.")

    # ── Major aspects ─────────────────────────────────────────────────────────
    if aspects:
        lines.extend(["", "  MAJOR TRANSIT ASPECTS TO NATAL PLANETS:"])
        for a in aspects[:12]:
            retro = "(R)" if a['retro'] else ""
            lines.append(
                f"    {a['transit']:8}{retro:3} (H{a['t_house']:<2}) {a['aspect']:10} "
                f"Natal {a['natal']:8} (H{a['n_house']:<2}) | Orb: {a['orb']:.1f}°"
            )

    # ── Key synthesis ─────────────────────────────────────────────────────────
    lines.extend([
        "", "  KEY SYNTHESIS:",
        f"    Saturn H{sat_h} + Jupiter H{jup_h} = "
        f"{'Constructive tension' if abs(sat_h - jup_h) in [4,5,8,9] else 'Challenging dynamic'}. "
        f"Rahu-Ketu axis H{rah_h}/H{ket_h} = primary karmic pressure right now.",
        "", "=" * 70,
    ])

    return "\n".join(lines)


_SKY_KEYS = {
    "Jupiter": "jupiter",
    "Venus": "venus",
    "Saturn": "saturn",
    "Mars": "mars",
    "Sun": "sun",
    "Mercury": "mercury",
}


def _planet_sign_at(dt: datetime, planet: str, city: str, nation: str) -> dict:
    key = _SKY_KEYS[planet]
    m = get_sky_on_date(dt.year, dt.month, dt.day, 12, 0, city, nation).model()
    p = getattr(m, key)
    abs_pos = float(p.abs_pos)
    sign_idx = int(abs_pos // 30) % 12
    nak, pada = get_nakshatra_and_pada(abs_pos)
    return {
        "abs_pos": abs_pos,
        "sign": p.sign,
        "sign_idx": sign_idx,
        "degree": round(float(p.position), 2),
        "nakshatra": nak,
        "pada": pada,
        "retrograde": bool(p.retrograde),
    }


def get_recent_sign_transit_windows(
    profile: dict,
    planets: list[str] | None = None,
    months_back: int = 18,
    months_ahead: int = 6,
) -> list[dict]:
    """Sign-level ingress/egress windows (Lahiri sidereal) for recent transit questions."""
    birth = profile["meta"]["birth"]
    city, nation = birth["city"], birth["nation"]
    lagna_idx = profile["lagna"]["sign_idx"]
    planets = planets or ["Jupiter", "Venus"]
    start = datetime.now() - timedelta(days=months_back * 30)
    end = datetime.now() + timedelta(days=months_ahead * 30)

    windows: list[dict] = []
    for planet in planets:
        if planet not in _SKY_KEYS:
            continue
        prev_sign = None
        window_start = None
        d = start
        while d <= end:
            info = _planet_sign_at(d, planet, city, nation)
            sign_idx = info["sign_idx"]
            if prev_sign is not None and sign_idx != prev_sign:
                if window_start is not None:
                    windows.append({
                        "planet": planet,
                        "sign": SIGN_NAMES[prev_sign],
                        "sign_idx": prev_sign,
                        "house_from_lagna": (prev_sign - lagna_idx + 12) % 12 + 1,
                        "start": window_start.strftime("%Y-%m-%d"),
                        "end": (d - timedelta(days=1)).strftime("%Y-%m-%d"),
                        "retrograde_exit": info["retrograde"],
                    })
                window_start = d
            elif window_start is None:
                window_start = d
            prev_sign = sign_idx
            d += timedelta(days=1)
        if window_start and prev_sign is not None:
            windows.append({
                "planet": planet,
                "sign": SIGN_NAMES[prev_sign],
                "sign_idx": prev_sign,
                "house_from_lagna": (prev_sign - lagna_idx + 12) % 12 + 1,
                "start": window_start.strftime("%Y-%m-%d"),
                "end": "ongoing" if end >= datetime.now() else end.strftime("%Y-%m-%d"),
                "retrograde_exit": False,
            })
    windows.sort(key=lambda w: w["start"], reverse=True)
    return windows


def format_recent_transit_report(
    profile: dict,
    question: str = "",
    planets: list[str] | None = None,
) -> str:
    """Recent sign transits with dates + personalization for the user's chart."""
    q = question.lower()
    if planets is None:
        planets = ["Jupiter", "Venus"]
        if "saturn" in q:
            planets.append("Saturn")
        if "mars" in q:
            planets.append("Mars")

    lagna_idx = profile["lagna"]["sign_idx"]
    natal_planets = profile.get("planets", {})
    windows = get_recent_sign_transit_windows(profile, planets=planets)

    # Optional filter: user asked about a specific sign
    sign_filter = None
    for sign in SIGN_NAMES:
        if sign.lower() in q:
            sign_filter = sign
            break

    lines = [
        "=" * 70,
        "RECENT SIGN TRANSIT WINDOWS (Lahiri Sidereal — use these dates verbatim)",
        f"As of: {datetime.now().strftime('%d %B %Y')}",
        "=" * 70,
        "",
        "RULE: When user asks 'recent transit', cite sign entry/exit dates from here.",
        "Do NOT invent trines/squares — state sign, house-from-lagna, nakshatra, dates.",
        "",
    ]

    shown = 0
    for w in windows:
        if sign_filter and w["sign"] != sign_filter:
            continue
        h = w["house_from_lagna"]
        occupants = _get_natal_occupants(h, natal_planets)
        occ_txt = f"Natal in H{h}: {', '.join(occupants)}" if occupants else f"H{h} empty natally"
        end_txt = w["end"] if w["end"] != "ongoing" else "still in sign"
        retro_note = " (re-entered after retrograde)" if w.get("retrograde_exit") else ""
        lines.append(
            f"  {w['planet']} in {w['sign']} (H{h} from {profile['lagna']['sign']} Lagna): "
            f"{w['start']} -> {end_txt}{retro_note}"
        )
        lines.append(f"    {occ_txt}")
        # Degree conjunctions at window midpoint if occupants exist
        if occupants and w["end"] != "ongoing":
            try:
                mid = datetime.strptime(w["start"], "%Y-%m-%d") + (
                    datetime.strptime(w["end"], "%Y-%m-%d") - datetime.strptime(w["start"], "%Y-%m-%d")
                ) / 2
                info = _planet_sign_at(mid, w["planet"], profile["meta"]["birth"]["city"], profile["meta"]["birth"]["nation"])
                for occ in occupants:
                    natal_abs = natal_planets.get(occ, {}).get("abs_pos")
                    if natal_abs is None:
                        continue
                    diff = abs(info["abs_pos"] - natal_abs) % 360
                    if diff > 180:
                        diff = 360 - diff
                    if diff <= 5:
                        lines.append(
                            f"    *** Near-conjunction: transit {w['planet']} passed within {diff:.1f}° of natal {occ} "
                            f"({natal_planets[occ].get('nakshatra', '?')}) during this window ***"
                        )
            except Exception:
                pass
        lines.append("")
        shown += 1
        if shown >= 12:
            break

    if shown == 0:
        lines.append("No matching sign windows in scan range.")

    # Current snapshot for requested planets
    birth = profile["meta"]["birth"]
    lines.append("CURRENT POSITIONS:")
    for planet in planets:
        if planet not in _SKY_KEYS:
            continue
        info = _planet_sign_at(datetime.now(), planet, birth["city"], birth["nation"])
        h = (info["sign_idx"] - lagna_idx + 12) % 12 + 1
        lines.append(
            f"  {planet}: {info['sign']} H{h} {info['degree']}° {info['nakshatra']} P{info['pada']}"
            f"{' (R)' if info['retrograde'] else ''}"
        )
    lines.append("=" * 70)
    return "\n".join(lines)


# ─── House Narratives ─────────────────────────────────────────────────────────

def _saturn_house_narrative(h: int) -> str:
    M = {
        1: "Saturn tests the body and identity. Sade Sati possible. Restructuring of self through hardship. Discipline required.",
        2: "Finances under Saturn's lens. Save money; avoid speculation. Speech must be honest. Income delays possible.",
        3: "Hard work on skills and communication. Courage tested. Disciplined writing and media work rewarded.",
        4: "Home and property issues require patience. Emotional foundation being restructured. Real estate decisions — don't rush.",
        5: "Creative work requires discipline. Romance faces delays. Avoid speculation. Authenticity in creative expression demanded.",
        6: "Saturn in 6H is strong — excellent for defeating enemies, competition. Health routines bring long-term results.",
        7: "Partnerships under serious evaluation. Commitment requires maturity. Business partnerships may restructure.",
        8: "Transformation through hardship. Research, occult. Financial restructuring. Long-term over fast gains.",
        9: "Philosophical discipline. Father's relationship tests. Higher education through hard work. Dharmic restructuring.",
        10: "Career PEAK demands — consolidation through hard work. Public recognition comes but requires sustained effort.",
        11: "Gains come slowly but surely. Friendships based on mutual value. Income increases through persistent effort.",
        12: "Expenses and foreign focus. Spiritual disciplines rewarded. Isolation can be productive. Past karma resolution.",
    }
    return M.get(h, f"Saturn in H{h}: Focus, discipline, and patience required.")


def _jupiter_house_narrative(h: int) -> str:
    M = {
        1: "Jupiter blesses the self — health, optimism, new beginning. Lucky period for starting new chapters.",
        2: "Wealth and income expand. Family grows or prospers. Speech is eloquent. Good time for investments.",
        3: "Skills and communication improve dramatically. Short travel beneficial. Siblings prosper.",
        4: "Home environment improves. Property gains. Emotional grounding. Higher education supported.",
        5: "Peak creative period. Romance possible. Children-related joy. Intelligence shines.",
        6: "Health improves. Enemies defeated through wisdom. Discipline brings results. Legal matters resolve favorably.",
        7: "Partnerships expand. Marriage timing favorable. Business collaborations grow.",
        8: "Hidden resources surface. Research deepens. Spiritual transformation. Inheritance resolves.",
        9: "PEAK LUCK PERIOD. Bhagya house = maximum Jupiter benefit. Travel, wisdom, father prospers.",
        10: "Career peak. Promotions and recognition. Authority expands. Government backing possible.",
        11: "Maximum gains phase. Wish fulfillment. Income surges. Social circle expands beautifully.",
        12: "Spiritual depth and foreign gains. Meditation beneficial. Hidden assets or foreign income.",
    }
    return M.get(h, f"Jupiter in H{h}: Expansion, wisdom, and fortune active.")


def _rahu_house_narrative(h: int) -> str:
    M = {
        1: "Identity in rapid transformation. Unusual influences on self. New obsessions about health/appearance.",
        2: "Unusual income sources. Foreign wealth. Speech becomes unconventional. Obsession with money.",
        3: "Tech, digital, or foreign media success. Unconventional communication style works.",
        4: "Home through foreign/unusual means. Domestic life unsettled. Real estate in unusual locations.",
        5: "Creative experimentation. Foreign romance possible. Digital creative work. Speculation can amplify.",
        6: "Victory over enemies through technology. Health issues surface unexpectedly.",
        7: "Foreign/unconventional partnerships. Karmic relationships enter. Business from different backgrounds.",
        8: "Hidden matters surface dramatically. Sudden financial changes. Unexpected transformation.",
        9: "Unconventional philosophy. Foreign guru or mentor. Non-traditional higher education.",
        10: "Rapid career rise through technology, foreign connections. Digital/global career focus.",
        11: "Extraordinary gains through digital or foreign means. Income spikes from unexpected sources.",
        12: "Foreign lands, isolation, spiritual experiences, unusual expenses. Gains from foreign sources.",
    }
    return M.get(h, f"Rahu in H{h}: Amplified, obsessive, unconventional energy.")


def _ketu_house_narrative(h: int) -> str:
    M = {
        1: "Detachment from ego and physical identity. Spiritual focus. Past-life wisdom surfacing.",
        2: "Detachment from wealth and family. Spiritual use of speech. Past-life wealth karma resolving.",
        3: "Intuitive communication. Detachment from siblings. Spiritual writing or communication.",
        4: "Detachment from home comforts. Mother may go through changes. Spiritual home practices.",
        5: "Spiritual creativity. Detachment from romance/children. Past-life creative talents awakened.",
        6: "Hidden enemies surface and resolve. Spiritual service. Alternative healing approaches work.",
        7: "Detachment from partnerships. Karmic partners enter or exit. Past-life partnership karma.",
        8: "Spiritual transformation. Research into past lives. Deep psychological insights.",
        9: "Spiritual philosophy deepens. Detachment from dogma. Past-life guru connections activated.",
        10: "Detachment from career recognition. Spiritual purpose in public work. Service-oriented.",
        11: "Detachment from material gains. Spiritual social circles. Gains through spiritual means.",
        12: "MOKSHA focus. Maximum detachment. Meditation highly rewarded. Liberation-oriented period.",
    }
    return M.get(h, f"Ketu in H{h}: Detachment, past karma, and spiritual energy.")


def _mars_house_narrative(h: int) -> str:
    M = {
        1: "Energy surge. Personal drive is high. Good for physical work and assertiveness.",
        2: "Aggressive approach to wealth. Family disputes possible. Slow down on financial decisions.",
        3: "Communication becomes forceful. Skills energized. Good for digital work and writing.",
        4: "Home energy activated — renovation or disruption. Property decisions come to a head.",
        5: "Creative energy peaks. Romance heats up. Speculation risk higher. Competitive edge.",
        6: "Mars in 6H is STRONG — excellent for defeating enemies, competition, legal wins, fitness.",
        7: "Partnership conflicts possible. High energy in relationships. Legal matters active.",
        8: "Hidden events accelerate. Research intensity. Sudden financial changes. Transformation.",
        9: "Energy toward philosophy, travel, higher learning. Long travel for work.",
        10: "Career energy surges. Assertive public image. Good for bold career moves.",
        11: "Income from effort. Social activities energized. Good period to pursue gains aggressively.",
        12: "Hidden work. Foreign energy. Expenses on health or spiritual matters. Hidden enemies.",
    }
    return M.get(h, f"Mars in H{h}: Action, drive, and conflict energy active.")


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

# ─── Sade Sati & Kantaka Shani & Full Transit Analysis ────────────────────────

def calculate_sade_sati(natal_moon_sign_idx: int, saturn_transit_sign_idx: int) -> dict:
    """
    Sade Sati = Saturn transiting 12th, 1st, or 2nd from natal Moon sign
    7.5 years total (3 x 2.5 years per sign)
    """
    distance = (saturn_transit_sign_idx - natal_moon_sign_idx) % 12
    
    phases = {
        11: {"phase": "Rising", "effect": "Mental pressure, family issues"},
        0:  {"phase": "Peak",   "effect": "Maximum intensity, identity crisis"},
        1:  {"phase": "Setting","effect": "Financial pressure, gradual relief"},
    }
    
    if distance in phases:
        return {"active": True, **phases[distance]}
    return {"active": False}

def calculate_kantaka_shani(natal_moon_sign_idx: int, saturn_transit_sign_idx: int) -> str:
    """
    Kantaka Saturn = transiting 1st, 4th, 7th, or 10th from natal Moon
    Also called Ashtama Shani when in 8th from Moon
    """
    distance = (saturn_transit_sign_idx - natal_moon_sign_idx) % 12
    
    kantaka = {
        0:  "Janma Shani — identity under pressure",
        3:  "Ardhashtama Shani — home and peace disrupted",
        7:  "Ashtama Shani — most challenging, hidden dangers",
        9:  "Kantaka Shani — career and public life blocked",
    }
    
    return kantaka.get(distance, None)

def analyze_transit(transiting_planet: str, transit_sign_idx: int,
                    natal_sign_idx: int, natal_house: int, natal_asc_sign_idx: int,
                    ashtakavarga_scores: dict, natal_planet_positions: dict) -> dict:
    """
    Complete transit analysis combining multiple factors
    """
    # 1. House transit from Ascendant
    transit_house_from_asc = (transit_sign_idx - natal_asc_sign_idx) % 12 + 1
    
    # 2. House transit from natal Moon (critical for timing)
    natal_moon_abs = natal_planet_positions.get("Moon", 0)
    natal_moon_sign = int(natal_moon_abs // 30)
    transit_house_from_moon = (transit_sign_idx - natal_moon_sign) % 12 + 1
    
    # 3. SAV score for transit house (requires BAV array for the planet)
    # ashtakavarga_scores should be the BAV dictionary for all planets
    planet_bav = ashtakavarga_scores.get(transiting_planet, {})
    # Note: planet_bav is often keyed by house 1-12 from Aries, or from Lagna. 
    # Assuming it's from Aries (0-11 sign index map to H1-12)
    # the target is transit_sign_idx + 1 if BAV is 1-indexed from Aries
    sav_score = planet_bav.get(transit_sign_idx + 1, 28) if isinstance(planet_bav, dict) else 28
    
    # 4. Vedha (obstruction check)
    VEDHA_PAIRS = {
        1:[8], 2:[7], 3:[12], 4:[11], 5:[9], 6:[10]
    }  # if good transit, check if another malefic blocks it
    
    # 5. Transit dignity
    from core.astro_engine import calculate_planet_dignity
    transit_sign_dignity = calculate_planet_dignity(transiting_planet, SIGN_NAMES[transit_sign_idx], 15.0).get("dignity", "Neutral")
    
    # 6. Aspect on natal houses
    from core.dosha_engine import get_aspected_houses
    aspected_houses = get_aspected_houses(transiting_planet, transit_house_from_asc)
    
    # 7. SAV threshold interpretation
    if sav_score >= 30:   sav_quality = "Excellent"
    elif sav_score >= 28: sav_quality = "Good"
    elif sav_score >= 25: sav_quality = "Neutral"
    elif sav_score >= 20: sav_quality = "Difficult"
    else:                 sav_quality = "Very Difficult"
    
    return {
        "planet": transiting_planet,
        "transit_house_asc": transit_house_from_asc,
        "transit_house_moon": transit_house_from_moon,
        "sav_score": sav_score,
        "sav_quality": sav_quality,
        "dignity": transit_sign_dignity,
        "aspects_natal_houses": aspected_houses,
        "sade_sati": calculate_sade_sati(natal_moon_sign, transit_sign_idx) if transiting_planet == "Saturn" else None,
        "kantaka_shani": calculate_kantaka_shani(natal_moon_sign, transit_sign_idx) if transiting_planet == "Saturn" else None,
    }

