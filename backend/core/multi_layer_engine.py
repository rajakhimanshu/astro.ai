"""
core/multi_layer_engine.py
────────────────────────────────────────────────────────────────────────
12-LAYER JYOTISH ENGINE — Complete Multi-Layer Vedic Astrology Analysis

Implements all 12 layers described in multi.txt:

Layer  1 — D1 Rashi Chart         (handled by kundali_profile.py)
Layer  2 — Aspects / Drishti      → natal planet-to-planet aspects + special
Layer  3 — House Lordships        → full lord placement + dignity analysis
Layer  4 — Yogas                  (handled by kundali_profile.py)
Layer  5 — Nakshatras             → nakshatra lord chain (sublord system)
Layer  6 — Vimshottari Dasha      (handled by astro_engine.py)
Layer  7 — Transits + Moon-based  (handled by transit_engine.py — extended here)
Layer  8 — Divisional Charts      → D9 Navamsa + D10 Dashamsa (computed)
Layer  9 — Shadbala               → simplified dignity + directional strength
Layer 10 — Ashtakavarga           → SAV-based transit scoring per house
Layer 11 — Muhurta / Panchanga    → current Tithi, Vara, Nakshatra, Yoga, Karana
Layer 12 — Prashna / Horary       → moment-of-asking chart context
────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime
from core.kundali_profile import KUNDALI_PROFILE
from core.astro_engine import get_current_sky

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & REFERENCE TABLES
# ─────────────────────────────────────────────────────────────────────────────

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
SIGN_IDX = {s: i for i, s in enumerate(SIGNS)}

LAGNA_SIGN_IDX = 5  # Virgo lagna → index 5

# All 27 Nakshatras and their ruling planets
NAKSHATRA_LORDS = {
    "Ashwini":          "Ketu",
    "Bharani":          "Venus",
    "Krittika":         "Sun",
    "Rohini":           "Moon",
    "Mrigashira":       "Mars",
    "Ardra":            "Rahu",
    "Punarvasu":        "Jupiter",
    "Pushya":           "Saturn",
    "Ashlesha":         "Mercury",
    "Magha":            "Ketu",
    "Purva Phalguni":   "Venus",
    "Uttara Phalguni":  "Sun",
    "Hasta":            "Moon",
    "Chitra":           "Mars",
    "Swati":            "Rahu",
    "Vishakha":         "Jupiter",
    "Anuradha":         "Saturn",
    "Jyeshtha":         "Mercury",
    "Mula":             "Ketu",
    "Purva Ashadha":    "Venus",
    "Uttara Ashadha":   "Sun",
    "Shravana":         "Moon",
    # Note: kerykeion spells it "Dhanishta" — we handle both
    "Dhanishtha":       "Mars",
    "Dhanishta":        "Mars",
    "Shatabhisha":      "Rahu",
    "Purva Bhadrapada": "Jupiter",
    "Uttara Bhadrapada":"Saturn",
    "Revati":           "Mercury",
}

NAKSHATRA_SEQUENCE = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Planet dignities
EXALTATION = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
    "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra"
}
DEBILITATION = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
    "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries"
}
OWN_SIGN = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
}
MOOLATRIKONA = {
    "Sun": "Leo", "Moon": "Taurus", "Mars": "Aries",
    "Mercury": "Virgo", "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Aquarius"
}

# Dig Bala — directional strength house
DIGBALA_HOUSE = {
    "Jupiter": 1, "Mercury": 1,
    "Moon": 4,    "Venus": 4,
    "Saturn": 7,
    "Sun": 10,    "Mars": 10,
}

# D9 Navamsa starting sign by sign type
MOVABLE_SIGNS = {"Aries", "Cancer", "Libra", "Capricorn"}
FIXED_SIGNS   = {"Taurus", "Leo", "Scorpio", "Aquarius"}
DUAL_SIGNS    = {"Gemini", "Virgo", "Sagittarius", "Pisces"}
ODD_SIGNS     = {"Aries", "Gemini", "Leo", "Libra", "Sagittarius", "Aquarius"}
EVEN_SIGNS    = {"Taurus", "Cancer", "Virgo", "Scorpio", "Capricorn", "Pisces"}

# Panchanga tables
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"
]
VARA_LORDS = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 4: "Jupiter", 5: "Venus", 6: "Saturn"}
VARA_NAMES = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarman", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti"
]
KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garaja",
    "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]

# Special aspects (in addition to universal 7th)
SPECIAL_ASPECTS = {
    "Mars":    [4, 8],
    "Jupiter": [5, 9],
    "Saturn":  [3, 10],
}

# House quality classification
KENDRA    = {1, 4, 7, 10}
TRIKONA   = {1, 5, 9}
UPACHAYA  = {3, 6, 10, 11}
DUSTHANA  = {6, 8, 12}
MARAKA    = {2, 7}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_sign_type(sign: str) -> str:
    if sign in MOVABLE_SIGNS: return "movable"
    if sign in FIXED_SIGNS:   return "fixed"
    return "dual"


def _get_planet_dignity(planet: str, sign: str) -> str:
    if planet in ("Rahu", "Ketu", "ASC"):
        return "N/A"
    if EXALTATION.get(planet) == sign:
        return "Exalted"
    if DEBILITATION.get(planet) == sign:
        return "Debilitated"
    if sign in OWN_SIGN.get(planet, []):
        return "Own Sign"
    if MOOLATRIKONA.get(planet) == sign:
        return "Moolatrikona"
    return "Neutral"


def _house_type_label(h: int) -> str:
    types = []
    if h in KENDRA:   types.append("Kendra")
    if h in TRIKONA:  types.append("Trikona")
    if h in UPACHAYA: types.append("Upachaya")
    if h in DUSTHANA: types.append("Dusthana")
    if h in MARAKA:   types.append("Maraka")
    return "+".join(types) if types else "Neutral"


def _compute_d9_sign(sign: str, degree: float) -> str:
    """D9 Navamsa: each sign divided into 9 parts of 3°20' each."""
    navamsa_num = int(degree / (30.0 / 9))  # 0–8
    stype = _get_sign_type(sign)
    start = {"movable": 0, "fixed": 9, "dual": 3}[stype]
    return SIGNS[(start + navamsa_num) % 12]


def _compute_d10_sign(sign: str, degree: float) -> str:
    """D10 Dashamsa: each sign divided into 10 parts of 3° each."""
    dashamsa_num = int(degree / 3.0)  # 0–9
    sign_idx = SIGN_IDX[sign]
    if sign in ODD_SIGNS:
        d10_idx = (sign_idx + dashamsa_num) % 12
    else:
        d10_idx = (sign_idx + 8 + dashamsa_num) % 12
    return SIGNS[d10_idx]


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — Natal Aspects (Drishti) — Complete
# ─────────────────────────────────────────────────────────────────────────────

def get_natal_aspects() -> str:
    """
    Layer 2: All natal planet-to-planet aspects.
    Every planet casts a 7th aspect. Mars: also 4th+8th. Jupiter: 5th+9th. Saturn: 3rd+10th.
    Shows WHO aspects WHICH house and which planets are aspected.
    """
    p = KUNDALI_PROFILE["planets"]

    # Build house → planets map
    house_planets: dict[int, list] = {}
    for name, data in p.items():
        house_planets.setdefault(data["house"], []).append(name)

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 2 — NATAL ASPECTS (DRISHTI)",
        "═══ Every planet's 7th aspect + special aspects of Mars/Jupiter/Saturn ═══",
        "",
    ]

    aspect_summary = []
    for planet_name, pdata in p.items():
        if planet_name == "ASC":
            continue
        h = pdata["house"]
        aspects = []

        # Universal 7th aspect
        t7 = (h - 1 + 6) % 12 + 1
        planets_in_t7 = [x for x in house_planets.get(t7, []) if x != "ASC"]
        occ7 = ", ".join(planets_in_t7) if planets_in_t7 else "empty"
        aspects.append(f"7th→H{t7}({occ7})")

        # Special aspects
        for offset in SPECIAL_ASPECTS.get(planet_name, []):
            target = (h - 1 + offset - 1) % 12 + 1
            occ = ", ".join([x for x in house_planets.get(target, []) if x != "ASC"]) or "empty"
            aspects.append(f"{offset}th→H{target}({occ})")

        line = f"  {planet_name:8} [H{h}] → {' | '.join(aspects)}"
        lines.append(line)

        # Collect for summary
        for offset in [7] + SPECIAL_ASPECTS.get(planet_name, []):
            target = (h - 1 + offset - 1) % 12 + 1
            for aspected_planet in house_planets.get(target, []):
                if aspected_planet != "ASC" and aspected_planet != planet_name:
                    aspect_summary.append(f"{planet_name}→{aspected_planet}")

    lines += [
        "",
        "  ┌─ KEY NATAL ASPECT FINDINGS ─────────────────────────────────────────┐",
        "  │ Jupiter (H2) 7th→H8, 5th→H6, 9th→H10: Blesses research, health, CAREER",
        "  │ Saturn (H11) 3rd→H1(Ketu), 7th→H5, 10th→H8: Disciplines self/creativity/transformation",
        "  │ Mars (H12) 4th→H3, 7th→H6, 8th→H7(Rahu): Energizes skills, health, and karmic partnerships",
        "  │ Sun (H12) 7th→H6: Hidden leadership creates health/enemy victories",
        "  │ Moon (H11) 7th→H5: Emotional mind aspects creativity/romance/speculation",
        "  │ Mercury (H11) 7th→H5: Career+self lord aspects 5H — intellect drives speculation",
        "  │ Saturn aspects Ketu (H1): Brings discipline to the spiritual/past-karma period",
        "  └──────────────────────────────────────────────────────────────────────┘",
        "",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3 — House Lordship Analysis — Full
# ─────────────────────────────────────────────────────────────────────────────

def get_lord_analysis() -> str:
    """
    Layer 3: For every house, show: lord → where it sits → its dignity there → house quality.
    The most important concept in Jyotish, per multi.txt.
    """
    # For Virgo Lagna (Whole Sign): House = Sign
    house_info = {
        1:  ("Mercury", "Virgo",       "Kendra+Trikona"),
        2:  ("Venus",   "Libra",       "Maraka"),
        3:  ("Mars",    "Scorpio",     "Upachaya"),
        4:  ("Jupiter", "Sagittarius", "Kendra"),
        5:  ("Saturn",  "Capricorn",   "Trikona"),
        6:  ("Saturn",  "Aquarius",    "Upachaya+Dusthana"),
        7:  ("Jupiter", "Pisces",      "Kendra+Maraka"),
        8:  ("Mars",    "Aries",       "Dusthana"),
        9:  ("Venus",   "Taurus",      "Trikona"),
        10: ("Mercury", "Gemini",      "Kendra+Upachaya"),
        11: ("Moon",    "Cancer",      "Upachaya"),
        12: ("Sun",     "Leo",         "Dusthana"),
    }

    p = KUNDALI_PROFILE["planets"]
    planet_house = {name: data["house"] for name, data in p.items() if name != "ASC"}
    planet_sign  = {name: data["sign"]  for name, data in p.items() if name != "ASC"}

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 3 — HOUSE LORDSHIP ANALYSIS",
        "═══ The most important Jyotish concept: where does each lord sit? ═══",
        "",
        f"  {'H#':4} {'House Sign':14} {'H-Type':22} {'Lord':10} {'→ Sits In':8} {'Lord Sign':14} {'Lord Dignity':14} {'To-H Type'}",
        "  " + "─" * 100,
    ]

    for h, (lord, house_sign, h_type) in house_info.items():
        lord_h    = planet_house.get(lord, "?")
        lord_sign = planet_sign.get(lord, "?")
        dignity   = _get_planet_dignity(lord, lord_sign)
        to_type   = _house_type_label(lord_h) if isinstance(lord_h, int) else "?"
        lines.append(
            f"  H{h:<3} {house_sign:14} {h_type:22} {lord:10} H{lord_h:<7} {lord_sign:14} {dignity:14} {to_type}"
        )

    lines += [
        "",
        "  ┌─ LORDSHIP QUALITY DIGEST (for AI interpretation) ──────────────────┐",
        "  │ H1 lord Mercury→H11: Kendra+Trikona lord → Upachaya = Income IS identity",
        "  │ H10 lord Mercury→H11: Career lord → Gains house = Career generates income directly",
        "  │ H2 lord Venus→H11: Maraka lord → Upachaya = Wealth in gains house = Dhana Yoga",
        "  │ H9 lord Venus→H11: Trikona (fortune) → Upachaya = Fortune manifests as gain",
        "  │ H11 lord Moon→H11: Upachaya lord in own house (own sign) = MAXIMUM strength",
        "  │ H4 lord Jupiter→H2: Kendra lord → Maraka = Education/home → wealth (Dhana Yoga)",
        "  │ H7 lord Jupiter→H2: Kendra+Maraka → Maraka = Partnerships → wealth (great) but",
        "  │    Jupiter as Maraka lord in 2H = must watch health in Jupiter periods",
        "  │ H8 lord Mars→H12: Dusthana→Dusthana = Viparita Raja Yoga (VRY) confirmed",
        "  │ H6 lord Saturn→H11: Dusthana→Upachaya = Service/competition income (powerful)",
        "  │ H12 lord Sun→H12: Dusthana lord in own house = Sun is partially VRY candidate",
        "  └──────────────────────────────────────────────────────────────────────┘",
        "",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 5 — Nakshatra Lord Chain (Sublord System)
# ─────────────────────────────────────────────────────────────────────────────

def get_nakshatra_chain_analysis() -> str:
    """
    Layer 5: For each natal planet, trace:
    Planet → Sign → Nakshatra → Nakshatra Lord → Nakshatra Lord's house/dignity.
    This is the Planet-Sign-Nakshatra triplet — the sublord precision layer.
    """
    p = KUNDALI_PROFILE["planets"]
    planet_house = {name: data["house"] for name, data in p.items() if name != "ASC"}
    planet_sign  = {name: data["sign"]  for name, data in p.items() if name != "ASC"}

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 5 — NAKSHATRA LORD CHAIN (Sublord / Planet-Sign-Nakshatra Triplet)",
        "═══ Nakshatra lord acts as sub-ruler; filters the planet's expression ═══",
        "",
        f"  {'Planet':10} {'H':3} {'Sign':14} {'Nakshatra':22} {'Nak Lord':10} {'Lord→H':8} {'Lord Sign':14} {'Lord Dignity'}",
        "  " + "─" * 100,
    ]

    chain_interpretations = []
    for name, data in p.items():
        if name == "ASC":
            continue
        nak      = data.get("nakshatra", "?")
        nak_lord = NAKSHATRA_LORDS.get(nak, "?")
        lord_h   = planet_house.get(nak_lord, "?")
        lord_sig = planet_sign.get(nak_lord, "?")
        dignity  = _get_planet_dignity(nak_lord, lord_sig) if lord_sig != "?" else "?"

        lines.append(
            f"  {name:10} H{data['house']:<2} {data['sign']:14} {nak:22} {nak_lord:10} "
            f"H{lord_h:<7} {lord_sig:14} {dignity}"
        )

        # Build interpretation
        if nak_lord != "?" and lord_h != "?":
            chain_interpretations.append(
                f"  • {name} (H{data['house']}) → {nak}({nak_lord}) → {nak_lord} in H{lord_h}: "
                f"{name}'s expression is sub-ruled by H{lord_h} themes ({lord_sig} {dignity})"
            )

    lines += [
        "",
        "  ┌─ KEY NAKSHATRA CHAIN MEANINGS ──────────────────────────────────────┐",
        "  │ Sun in Magha (Ketu-lord) → Ketu in H1: Soul's authority filtered thru",
        "  │   past-karma/spiritual identity. Hidden, not public leadership.",
        "  │ Moon in Ashlesha (Mercury-lord) → Mercury in H11: Emotional mind",
        "  │   sub-ruled by career+gains lord. Emotions tied to income success.",
        "  │ Mercury in Ashlesha (Mercury-lord) → Self-ruled sublord: Mercury is",
        "  │   doubly pure — career+lagna lord expressing without interference.",
        "  │ Venus in Ashlesha (Mercury-lord) → Mercury in H11: Wealth/love energy",
        "  │   sub-ruled by gains-house Mercury. Income through creative social work.",
        "  │ Saturn in Ashlesha (Mercury-lord) → Mercury in H11: Delays/discipline",
        "  │   sub-ruled by gains Mercury. Hard work → structured gain eventually.",
        "  │ Jupiter in Swati (Rahu-lord) → Rahu in H7: Wisdom filtered through",
        "  │   karmic foreign partnerships. Global vision in collaborations.",
        "  │ Mars in Purva Phalguni (Venus-lord) → Venus in H11: Drive filtered",
        "  │   by wealth/gains Venus. Courage becomes income-seeking action.",
        "  │ Rahu in Purva Bhadrapada (Jupiter-lord) → Jupiter in H2: Obsessive",
        "  │   foreign pull filtered by wealth-house Jupiter. Karmic wealth.",
        "  │ Ketu in Uttara Phalguni (Sun-lord) → Sun in H12: Past-life wisdom",
        "  │   filtered by hidden-Sun. Spiritual authority drives identity.",
        "  └──────────────────────────────────────────────────────────────────────┘",
        "",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 8 — Divisional Charts: D9 Navamsa + D10 Dashamsa
# ─────────────────────────────────────────────────────────────────────────────

def get_divisional_charts() -> str:
    """
    Layer 8: Compute D9 (Navamsa) and D10 (Dashamsa) from natal degrees.
    D9 = soul purpose, marriage, deeper promise. D10 = professional life.
    Vargottama = same sign D1+D9 = extraordinary strength.
    """
    # Natal positions: (sign, degree-within-sign)
    natal_positions = {
        "Sun":     ("Leo",         5.00),
        "Moon":    ("Cancer",     17.00),
        "Mars":    ("Leo",        25.17),
        "Mercury": ("Cancer",     24.86),
        "Jupiter": ("Libra",      18.15),
        "Venus":   ("Cancer",     17.47),
        "Saturn":  ("Cancer",     22.76),
        "Rahu":    ("Pisces",      2.69),
        "Ketu":    ("Virgo",       2.69),
        "ASC":     ("Virgo",      26.33),
    }

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 8 — DIVISIONAL CHARTS (D9 NAVAMSA + D10 DASHAMSA)",
        "═══ D9 = soul/marriage depth | D10 = career precision ═══",
        "",
        "  D9 NAVAMSA (Each sign ÷ 9 = 3°20' parts):",
        f"  {'Planet':10} {'D1 Sign':14} {'D1 Deg':8} {'D9 Sign':14} {'D1 Dignity':14} {'D9 Dignity':14} Notes",
        "  " + "─" * 95,
    ]

    d9_data = {}
    for planet, (sign, deg) in natal_positions.items():
        d9_sign = _compute_d9_sign(sign, deg)
        dig_d1  = _get_planet_dignity(planet, sign)
        dig_d9  = _get_planet_dignity(planet, d9_sign)
        varg    = " ★VARGOTTAMA" if sign == d9_sign else ""
        d9_data[planet] = (d9_sign, dig_d9)
        lines.append(
            f"  {planet:10} {sign:14} {deg:7.2f}°  {d9_sign:14} {dig_d1:14} {dig_d9:14}{varg}"
        )

    lines += [
        "",
        "  D9 RULES FOR AI USE:",
        "  • Strong in D1 AND D9 → HIGH confidence (predict with conviction)",
        "  • Strong in D1, weak in D9 → Promise exists but may not fully deliver",
        "  • Weak in D1, strong in D9 → Will still give results despite D1 weakness",
        "  • ★VARGOTTAMA = same sign D1+D9 = maximum purity of that planet's energy",
        "",
        "  D10 DASHAMSA (Each sign ÷ 10 = 3° parts) — Career precision:",
        f"  {'Planet':10} {'D1 Sign':14} {'D1 Deg':8} {'D10 Sign':14} {'D10 Dignity'}",
        "  " + "─" * 70,
    ]

    for planet, (sign, deg) in natal_positions.items():
        d10_sign = _compute_d10_sign(sign, deg)
        dig_d10  = _get_planet_dignity(planet, d10_sign)
        lines.append(f"  {planet:10} {sign:14} {deg:7.2f}°  {d10_sign:14} {dig_d10}")

    lines += [
        "",
        "  D10 RULES FOR AI USE:",
        "  • Check Mercury's D10 sign/dignity → Mercury IS the career lord (Virgo lagna)",
        "  • If Mercury strong in D1 and D10 → Career prediction has HIGH confidence",
        "  • Confirm ALL career answers using D10 Mercury placement",
        "  • D10 ASC shows the professional persona/public role quality",
        "",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 9 — Shadbala (Simplified Planetary Strength)
# ─────────────────────────────────────────────────────────────────────────────

def get_simplified_shadbala() -> str:
    """
    Layer 9: Simplified Shadbala using:
    - Sthana Bala (positional/dignity strength)
    - Dig Bala (directional strength — house)
    - Chesta Bala hint (retrograde = intensification for personal planets)
    Produces a 0–10 relative strength score for each planet.
    """
    dignity_base = {
        "Exalted":      5.0,
        "Own Sign":     4.0,
        "Moolatrikona": 3.5,
        "Neutral":      2.0,
        "Debilitated":  0.5,
        "N/A":          2.0,
    }

    p = KUNDALI_PROFILE["planets"]

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 9 — SHADBALA (SIMPLIFIED PLANETARY STRENGTH SCORE)",
        "═══ Sthana Bala + Dig Bala + Chesta Bala (retrograde) ═══",
        "",
        f"  {'Planet':10} {'Dignity':14} {'H':3} {'DigBala':8} {'Retro':6} {'Score/10':9} Strength Rating",
        "  " + "─" * 80,
    ]

    for name, data in p.items():
        if name == "ASC":
            continue
        sign    = data["sign"]
        house   = data["house"]
        retro   = data.get("retrograde", False)
        dignity = _get_planet_dignity(name, sign)

        # Sthana Bala (dignity)
        d_score = dignity_base.get(dignity, 2.0)

        # Neecha Bhanga check for Saturn — Moon in Cancer in same house
        if name == "Saturn" and sign == "Cancer":
            d_score += 1.5  # Neecha Bhanga cancels debilitation partially

        # Dig Bala (directional strength)
        best_h   = DIGBALA_HOUSE.get(name, 0)
        diff     = abs(house - best_h)
        diff     = min(diff, 12 - diff)  # wrap around
        dig      = 2.0 if diff == 0 else (1.0 if diff <= 2 else 0.0)

        # Chesta Bala (retrograde intensity for personal planets, not nodes)
        chesta = 1.0 if (retro and name not in ("Rahu", "Ketu")) else 0.0

        total = min(d_score + dig + chesta, 10.0)

        if total >= 7:   rating = "⭐⭐⭐ STRONG"
        elif total >= 5: rating = "⭐⭐  GOOD"
        elif total >= 3: rating = "⭐   MODERATE"
        else:            rating = "    WEAK"

        lines.append(
            f"  {name:10} {dignity:14} H{house:<2} {'Yes' if house == best_h else 'No':8} "
            f"{'Yes' if retro else 'No':6} {total:5.1f}/10  {rating}"
        )

    lines += [
        "",
        "  ┌─ SHADBALA SUMMARY FOR AI USE ───────────────────────────────────────┐",
        "  │ Moon (H11, own-sign Cancer): STRONGEST → trust all Moon-related gains",
        "  │ Venus (H11, with Moon): GOOD → wealth/relationships manifest strongly",
        "  │ Mercury (H11, neutral but H11 lord Mercury = self-sublord): GOOD",
        "  │ Sun (H12, own-sign Leo): STRONG but hidden/12H = expressions curtailed",
        "  │ Saturn (H11, neecha+bhanga): MODERATE — gains are slow but real",
        "  │ Mars (H12, friendly Leo): MODERATE — drives are internalized/foreign",
        "  │ Jupiter (H2, neutral Libra): MODERATE — wealth steadily builds",
        "  │ RULE: Weight strong-planet predictions more heavily. For weak-planet",
        "  │   predictions, add caveats and delays.",
        "  └──────────────────────────────────────────────────────────────────────┘",
        "",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 10 — Ashtakavarga Transit Scoring
# ─────────────────────────────────────────────────────────────────────────────

def get_av_transit_scoring() -> str:
    """
    Layer 10: Score each transiting planet's house using Sarvashtakavarga (SAV).
    SAV ≥ 30 = favourable transit | 25-29 = neutral | < 25 = challenging.
    This dramatically improves transit prediction accuracy.
    """
    sav = KUNDALI_PROFILE["ashtakvarga"]["sarvashtakavarga"]

    PLANETS_KEYS = {
        'saturn': 'Saturn', 'jupiter': 'Jupiter',
        'true_north_lunar_node': 'Rahu', 'true_south_lunar_node': 'Ketu',
        'mars': 'Mars', 'sun': 'Sun', 'mercury': 'Mercury',
        'moon': 'Moon', 'venus': 'Venus',
    }

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 10 — ASHTAKAVARGA TRANSIT SCORING",
        "═══ SAV points in transit house = actual strength of transit effect ═══",
        "",
        "  SAV Table (All 12 Houses):",
        "  H:  " + "  ".join(f"{h:2}" for h in range(1, 13)),
        "  SAV:" + "  ".join(f"{sav[h]:2}" for h in range(1, 13)),
        "  Key: ≥30=Favourable | 25-29=Neutral | <25=Challenging",
        "",
    ]

    try:
        sky  = get_current_sky()
        m    = sky.model()

        lines.append(f"  {'Planet':10} {'Transit Sign':14} {'Transit H':10} {'SAV Pts':9} {'Quality':28} Interpretation")
        lines.append("  " + "─" * 95)

        for key, name in PLANETS_KEYS.items():
            pl      = getattr(m, key)
            sign_i  = int(pl.abs_pos // 30) % 12
            t_sign  = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"][sign_i]
            t_house = (sign_i - LAGNA_SIGN_IDX + 12) % 12 + 1
            pts     = sav.get(t_house, 0)
            retro_s = "(R)" if pl.retrograde else "   "

            if pts >= 30:
                quality = "✅ FAVOURABLE"
                interp  = "Transit energy flows positively"
            elif pts >= 25:
                quality = "⚡ NEUTRAL"
                interp  = "Mixed — expect some resistance"
            else:
                quality = "⚠️  CHALLENGING"
                interp  = "Even good house has low energy now"

            lines.append(
                f"  {name:10} {t_sign:14} H{t_house:<2}{retro_s}      {pts:3} pts   {quality:28} {interp}"
            )

        lines += [
            "",
            "  ┌─ AV TRANSIT CRITICAL RULE FOR AI ──────────────────────────────────┐",
            "  │ ALWAYS cite SAV score when interpreting transits. Examples:",
            "  │ WRONG: 'Jupiter in 10H brings career growth'",
            "  │ RIGHT: 'Jupiter in 10H BUT SAV=18 (weakest house in chart) —",
            "  │   career growth requires significant deliberate effort, not automatic'",
            "  │",
            "  │ WRONG: 'Saturn in 7H is difficult'",
            "  │ RIGHT: 'Saturn in 7H with SAV=22 (<25) = partnerships genuinely",
            "  │   difficult; confirmed challenging, not just ordinarily slow'",
            "  └──────────────────────────────────────────────────────────────────────┘",
            "",
        ]
    except Exception as e:
        lines.append(f"  [AV Transit Scoring Error: {e}]")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 11 — Muhurta / Panchanga (Current Celestial Time Quality)
# ─────────────────────────────────────────────────────────────────────────────

def get_current_panchanga() -> str:
    """
    Layer 11: Compute the 5 Panchanga elements for right now.
    Tithi, Vara, Nakshatra (Moon), Yoga, Karana.
    Used for timing recommendations and Muhurta quality.
    """
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 11 — PANCHANGA (MUHURTA / CURRENT CELESTIAL TIME QUALITY)",
        "═══ The 5 elements of Vedic time — for all timing recommendations ═══",
        "",
    ]

    try:
        sky = get_current_sky()
        m   = sky.model()
        now = datetime.now()

        sun_lon  = m.sun.abs_pos
        moon_lon = m.moon.abs_pos

        # 1. TITHI
        tithi_deg  = (moon_lon - sun_lon) % 360
        tithi_num  = int(tithi_deg / 12) + 1
        paksha     = "Shukla (Waxing)" if tithi_num <= 15 else "Krishna (Waning)"
        tithi_name = TITHI_NAMES[(tithi_num - 1) % 15]

        # 2. VARA (weekday lord)
        # Python weekday(): Mon=0 → Sun=6. Vedic: Sun=0
        py_day   = now.weekday()
        vara_idx = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}[py_day]
        vara_lord = VARA_LORDS[vara_idx]
        vara_name = VARA_NAMES[vara_idx]

        # 3. NAKSHATRA (Moon's position)
        nak_idx     = int(moon_lon / (360 / 27)) % 27
        current_nak = NAKSHATRA_SEQUENCE[nak_idx]
        nak_lord    = NAKSHATRA_LORDS.get(current_nak, "?")
        moon_sign   = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"][int(moon_lon // 30) % 12]

        # 4. YOGA (Sun+Moon longitude / 13.33...)
        yoga_deg  = (sun_lon + moon_lon) % 360
        yoga_idx  = int(yoga_deg / (360 / 27)) % 27
        yoga_name = YOGA_NAMES[yoga_idx]

        # 5. KARANA (half-tithi)
        karana_idx  = int(tithi_deg / 6) % 11
        karana_name = KARANA_NAMES[karana_idx]

        lines += [
            f"  Current: {now.strftime('%A, %d %B %Y | %H:%M IST')}",
            "",
            f"  ┌─ PANCHANGA ────────────────────────────────────────────────────────┐",
            f"  │ 1. TITHI:     {tithi_name} (#{tithi_num}) — {paksha}",
            f"  │ 2. VARA:      {vara_name} — Day Lord: {vara_lord}",
            f"  │ 3. NAKSHATRA: Moon in {current_nak} ({moon_sign}) — Nak Lord: {nak_lord}",
            f"  │ 4. YOGA:      {yoga_name} (Sun+Moon combination quality)",
            f"  │ 5. KARANA:    {karana_name} (half-tithi quality)",
            f"  └────────────────────────────────────────────────────────────────────┘",
            "",
            f"  MUHURTA GUIDANCE:",
            f"  • Vara lord is {vara_lord} — {vara_lord}-domain activities are naturally supported today",
            f"  • Moon in {current_nak} (lord: {nak_lord}) — Moon's emotional quality filtered by {nak_lord}",
            f"  • Yoga '{yoga_name}' sets the overall quality of all actions initiated today",
            f"  • ALWAYS use Panchanga to recommend WHEN to act on any decision",
            "",
        ]

    except Exception as e:
        lines.append(f"  [Panchanga Error: {e}]")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 12 — Prashna / Horary (Chart for the Moment of Asking)
# ─────────────────────────────────────────────────────────────────────────────

def get_prashna_context() -> str:
    """
    Layer 12: Prashna (Horary) — the planetary sky at the EXACT moment of asking.
    The current transiting chart IS the Prashna chart.
    Moon's nakshatra at question time reveals what the question is truly about.
    """
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "LAYER 12 — PRASHNA (HORARY — MOMENT-OF-ASKING CHART)",
        "═══ The chart at this exact moment reveals the nature of the question ═══",
        "",
    ]

    try:
        sky = get_current_sky()
        m   = sky.model()
        now = datetime.now()

        moon_lon = m.moon.abs_pos
        sun_lon  = m.sun.abs_pos

        moon_sign_i = int(moon_lon // 30) % 12
        moon_sign   = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"][moon_sign_i]
        moon_deg    = round(moon_lon % 30, 2)
        prashna_nak = NAKSHATRA_SEQUENCE[int(moon_lon / (360/27)) % 27]
        prashna_nl  = NAKSHATRA_LORDS.get(prashna_nak, "?")

        # Prashna Lagna (rising sign at this moment)
        try:
            asc_lon  = m.ascendant.abs_pos
            asc_sign = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"][int(asc_lon // 30) % 12]
            asc_deg  = round(asc_lon % 30, 2)
        except Exception:
            asc_sign, asc_deg = "Unavailable", 0.0

        # Relationship between Prashna Moon and natal Moon
        nat_moon_h  = 11  # natal Moon in H11
        pra_moon_h  = (moon_sign_i - LAGNA_SIGN_IDX + 12) % 12 + 1

        lines += [
            f"  Question asked at: {now.strftime('%A, %d %B %Y | %H:%M IST')}",
            "",
            f"  Prashna Lagna (Rising now): {asc_sign} {asc_deg}°",
            f"  Prashna Moon:              {moon_sign} {moon_deg}° → Transiting your H{pra_moon_h}",
            f"  Prashna Nakshatra:         {prashna_nak} (Lord: {prashna_nl})",
            "",
            f"  ┌─ PRASHNA INTERPRETATION GUIDE ─────────────────────────────────────┐",
            f"  │ 1. Prashna Moon in H{pra_moon_h} of natal chart: The question involves H{pra_moon_h} themes",
            f"  │ 2. Nak Lord {prashna_nl}: Outcome is filtered through {prashna_nl}'s domain",
            f"  │ 3. If Prashna Moon is in benefic nakshatra → matter resolves positively",
            f"  │ 4. If Prashna Moon aspects natal Moon (H11) → emotional/income matters",
            f"  │ 5. Prashna confirms or contradicts the natal chart reading — use both",
            f"  │",
            f"  │ CURRENT PRASHNA STATE:",
            f"  │   Moon in {prashna_nak} ({prashna_nl}-ruled) transiting H{pra_moon_h}:",
            f"  │   Question nature = H{pra_moon_h} domain, answer quality = {prashna_nl}'s strength",
            f"  └──────────────────────────────────────────────────────────────────────┘",
            "",
        ]

    except Exception as e:
        lines.append(f"  [Prashna Error: {e}]")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# MASTER FUNCTION — Combine All Missing Layers into One Context Block
# ─────────────────────────────────────────────────────────────────────────────

def get_all_12_layers() -> str:
    """
    Returns the complete multi-layer Jyotish analysis as one text block.
    Covers Layers 2, 3, 5, 8, 9, 10, 11, 12.
    (Layers 1, 4, 6, 7 are already handled by kundali_profile + transit_engine.)
    """
    header = """
╔══════════════════════════════════════════════════════════════════════════════╗
║          MULTI-LAYER ANALYSIS ENGINE — LAYERS 2, 3, 5, 8, 9, 10, 11, 12   ║
║   Per multi.txt: A master astrologer holds all 12 layers simultaneously.    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    sections = [header]

    runners = [
        ("Layer 2 — Natal Aspects",          get_natal_aspects),
        ("Layer 3 — House Lordships",         get_lord_analysis),
        ("Layer 5 — Nakshatra Lord Chain",    get_nakshatra_chain_analysis),
        ("Layer 8 — Divisional Charts D9/D10",get_divisional_charts),
        ("Layer 9 — Shadbala Strength",       get_simplified_shadbala),
        ("Layer 10 — AV Transit Scoring",     get_av_transit_scoring),
        ("Layer 11 — Panchanga/Muhurta",      get_current_panchanga),
        ("Layer 12 — Prashna/Horary",         get_prashna_context),
    ]

    for label, fn in runners:
        try:
            sections.append(fn())
        except Exception as e:
            sections.append(f"\n[{label} ERROR: {e}]\n")

    return "\n".join(sections)
