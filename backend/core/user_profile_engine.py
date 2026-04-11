"""
core/user_profile_engine.py
────────────────────────────────────────────────────────────────────────
Multi-User Profile Engine for Astro.AI

Computes a complete 12-layer Jyotish profile from birth data using
kerykeion (Swiss Ephemeris, Sidereal/Lahiri) and stores it per user.

Storage layout:
  data/users/<user_id>/
      birth_data.yaml   — raw birth input
      profile.json      — full computed 12-layer profile
      life_events.db    — user's personal event memory (created by memory.py)

Public API:
  create_user_profile(birth_info: dict) -> str   (returns user_id)
  load_user_profile(user_id: str) -> dict
  list_users() -> list[dict]
  get_active_user_id() -> str
  set_active_user(user_id: str) -> None
  get_active_profile() -> dict
────────────────────────────────────────────────────────────────────────
"""

import os
import json
import yaml
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional
from kerykeion import AstrologicalSubject
from dotenv import load_dotenv
from core.astro_engine import calculate_vimshottari_dasha

# ─────────────────────────────────────────────────────────────────────────────
# Reference Tables (Jyotish constants — same as multi_layer_engine.py)
# ─────────────────────────────────────────────────────────────────────────────

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
SIGN_IDX = {s: i for i, s in enumerate(SIGNS)}
SIGN_LORDS = {
    "Aries": "Mars",   "Taurus": "Venus",   "Gemini": "Mercury",  "Cancer": "Moon",
    "Leo": "Sun",      "Virgo": "Mercury",  "Libra": "Venus",     "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}
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
NAKSHATRA_LORDS = {
    "Ashwini": "Ketu",   "Bharani": "Venus",     "Krittika": "Sun",
    "Rohini": "Moon",    "Mrigashira": "Mars",    "Ardra": "Rahu",
    "Punarvasu": "Jupiter", "Pushya": "Saturn",   "Ashlesha": "Mercury",
    "Magha": "Ketu",     "Purva Phalguni": "Venus", "Uttara Phalguni": "Sun",
    "Hasta": "Moon",     "Chitra": "Mars",        "Swati": "Rahu",
    "Vishakha": "Jupiter", "Anuradha": "Saturn",  "Jyeshtha": "Mercury",
    "Mula": "Ketu",      "Purva Ashadha": "Venus", "Uttara Ashadha": "Sun",
    "Shravana": "Moon",  "Dhanishtha": "Mars",    "Dhanishta": "Mars",
    "Shatabhisha": "Rahu", "Purva Bhadrapada": "Jupiter", "Uttara Bhadrapada": "Saturn",
    "Revati": "Mercury"
}
NAKSHATRA_SEQUENCE = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]
DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

SPECIAL_ASPECTS = {"Mars": [4, 8], "Jupiter": [5, 9], "Saturn": [3, 10]}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
UPACHAYA = {3, 6, 10, 11}
DUSTHANA = {6, 8, 12}
MARAKA = {2, 7}
MOVABLE_SIGNS = {"Aries", "Cancer", "Libra", "Capricorn"}
FIXED_SIGNS   = {"Taurus", "Leo", "Scorpio", "Aquarius"}
DUAL_SIGNS    = {"Gemini", "Virgo", "Sagittarius", "Pisces"}
ODD_SIGNS     = {"Aries", "Gemini", "Leo", "Libra", "Sagittarius", "Aquarius"}
HEAVY_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
BENEFICS       = {"Jupiter", "Venus", "Mercury", "Moon"}

PLANET_REMEDIES = {
    "Sun": {
        "mantra": "Om Hram Hreem Hroum Sah Suryaya Namah",
        "gemstone": "Ruby (Manik) - *Consult before wearing*",
        "charity": "Donate wheat, jaggery, or copper on Sunday mornings; feed father-figures."
    },
    "Moon": {
        "mantra": "Om Shram Shreem Shroum Sah Chandraya Namah",
        "gemstone": "Pearl (Moti)",
        "charity": "Donate milk, rice, or silver on Mondays; help mothers and young children."
    },
    "Mars": {
        "mantra": "Om Kram Kreem Kroum Sah Bhaumaya Namah",
        "gemstone": "Red Coral (Moonga)",
        "charity": "Donate red lentils (masoor dal) or red clothes on Tuesdays; donate blood."
    },
    "Mercury": {
        "mantra": "Om Bram Breem Broum Sah Budhaya Namah",
        "gemstone": "Emerald (Panna)",
        "charity": "Donate green moong dal on Wednesdays; support education or students."
    },
    "Jupiter": {
        "mantra": "Om Gram Greem Groum Sah Gurave Namah",
        "gemstone": "Yellow Sapphire (Pukhraj)",
        "charity": "Donate chana dal, bananas, or books on Thursdays; respect teachers."
    },
    "Venus": {
        "mantra": "Om Dram Dreem Droum Sah Shukraya Namah",
        "gemstone": "Diamond/White Sapphire",
        "charity": "Donate sugar, rice, or white clothes on Fridays; support women in need."
    },
    "Saturn": {
        "mantra": "Om Pram Preem Proum Sah Shanaishcharaya Namah",
        "gemstone": "Blue Sapphire (Neelam) - *Caution: strict trial needed*",
        "charity": "Donate mustard oil, black sesame, or black shoes on Saturdays; feed the poor/disabled."
    },
    "Rahu": {
        "mantra": "Om Bhram Bhreem Bhroum Sah Rahave Namah",
        "gemstone": "Hessonite (Gomed)",
        "charity": "Donate black blankets or lead to the poor; feed street dogs."
    },
    "Ketu": {
        "mantra": "Om Sram Sreem Sroum Sah Ketave Namah",
        "gemstone": "Cat's Eye (Lehsuniya)",
        "charity": "Donate mixed-color blankets or black sesame; feed fish or stray dogs."
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

USERS_DIR = Path("data/users")
ACTIVE_USER_FILE = Path("data/active_user.txt")


def _user_dir(user_id: str) -> Path:
    return USERS_DIR / user_id


def _profile_path(user_id: str) -> Path:
    return _user_dir(user_id) / "profile.json"


def _birth_path(user_id: str) -> Path:
    return _user_dir(user_id) / "birth_data.yaml"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    """Convert a name to a safe filesystem-compatible user_id."""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_-]+", "_", name)
    return name[:40]


def _get_dignity(planet: str, sign: str) -> str:
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


def _house_from_lagna(planet_sign: str, lagna_sign: str) -> int:
    """Whole-sign house system: count from lagna."""
    return (SIGN_IDX[planet_sign] - SIGN_IDX[lagna_sign] + 12) % 12 + 1


def _get_nakshatra(abs_pos: float) -> tuple[str, int]:
    """Returns (nakshatra_name, pada) from absolute longitude."""
    nak_idx = int(abs_pos / (360 / 27)) % 27
    pada = int((abs_pos % (360 / 27)) / (360 / 27 / 4)) + 1
    return NAKSHATRA_SEQUENCE[nak_idx], min(pada, 4)


def _house_type(h: int) -> str:
    types = []
    if h in KENDRA:   types.append("Kendra")
    if h in TRIKONA:  types.append("Trikona")
    if h in UPACHAYA: types.append("Upachaya")
    if h in DUSTHANA: types.append("Dusthana")
    if h in MARAKA:   types.append("Maraka")
    return "+".join(types) if types else "Neutral"


def _compute_d9_sign(sign: str, deg: float) -> str:
    navamsa_num = int(deg / (30.0 / 9))
    if sign in MOVABLE_SIGNS: start = 0
    elif sign in FIXED_SIGNS: start = 9
    else: start = 3
    return SIGNS[(start + navamsa_num) % 12]


def _compute_d10_sign(sign: str, deg: float) -> str:
    dashamsa_num = int(deg / 3.0)
    idx = SIGN_IDX[sign]
    if sign in ODD_SIGNS:
        return SIGNS[(idx + dashamsa_num) % 12]
    return SIGNS[(idx + 8 + dashamsa_num) % 12]


# ─────────────────────────────────────────────────────────────────────────────
# Yoga Detector
# ─────────────────────────────────────────────────────────────────────────────

def _detect_yogas(planets: dict, lagna_sign: str) -> list[dict]:
    """Detect major yogas from planetary positions."""
    yogas = []
    lagna_lord = SIGN_LORDS.get(lagna_sign)

    def in_same_house(p1, p2):
        return planets.get(p1, {}).get("house") == planets.get(p2, {}).get("house")

    def planet_house(p):
        return planets.get(p, {}).get("house", 0)

    def planet_sign(p):
        return planets.get(p, {}).get("sign", "")

    # Gajakesari Yoga: Jupiter in Kendra from Moon
    jup_h = planet_house("Jupiter")
    moon_h = planet_house("Moon")
    if jup_h and moon_h:
        diff = abs(jup_h - moon_h)
        if diff in (0, 3, 6, 9):
            yogas.append({
                "name": "Gajakesari Yoga",
                "planets": ["Jupiter", "Moon"],
                "effect": "Wisdom, fame, and prosperity — Jupiter in kendra from Moon amplifies intelligence and social standing."
            })

    # Dhana Yoga: 2H/11H lords in 2H/11H/5H/9H
    h2_lord = SIGN_LORDS.get(SIGNS[(SIGN_IDX[lagna_sign] + 1) % 12])
    h11_lord = SIGN_LORDS.get(SIGNS[(SIGN_IDX[lagna_sign] + 10) % 12])
    if h2_lord and planet_house(h2_lord) in {2, 5, 9, 11}:
        yogas.append({
            "name": "Dhana Yoga (2H Lord)",
            "planets": [h2_lord],
            "effect": f"{h2_lord} (2H lord) placed in wealth/trikona house — wealth accumulation is indicated, especially during {h2_lord}'s dasha."
        })
    if h11_lord and h11_lord != h2_lord and planet_house(h11_lord) in {2, 5, 9, 11}:
        yogas.append({
            "name": "Dhana Yoga (11H Lord)",
            "planets": [h11_lord],
            "effect": f"{h11_lord} (11H lord) placed in gains/trikona house — income and gains are supported by planetary promise."
        })

    # Viparita Raja Yoga: Dusthana lords in other Dusthanas
    dusthana_lords = []
    for h in (6, 8, 12):
        sign_at_h = SIGNS[(SIGN_IDX[lagna_sign] + h - 1) % 12]
        dusthana_lords.append((h, SIGN_LORDS.get(sign_at_h), sign_at_h))

    for h, lord, sign in dusthana_lords:
        if lord and planet_house(lord) in (6, 8, 12):
            yogas.append({
                "name": f"Viparita Raja Yoga (H{h} lord)",
                "planets": [lord],
                "effect": f"{lord} (H{h} lord) in another dusthana — hardships convert to strength. Unexpected rise from difficult circumstances."
            })

    # Neecha Bhanga: Debilitated planet getting cancellation
    for planet, deb_sign in DEBILITATION.items():
        if planet_sign(planet) == deb_sign:
            deb_lord = SIGN_LORDS.get(deb_sign)
            # Cancellation: lord of debilitation sign in Kendra from Moon or Lagna
            if deb_lord and planet_house(deb_lord) in KENDRA:
                yogas.append({
                    "name": f"Neecha Bhanga for {planet}",
                    "planets": [planet, deb_lord],
                    "effect": f"{planet} is debilitated in {deb_sign} but {deb_lord} in a Kendra cancels the debilitation — initial struggle leads to greater strength."
                })

    # Raja Yoga: Kendra + Trikona lords in conjunction or mutual aspect
    kendra_lords = {SIGN_LORDS.get(SIGNS[(SIGN_IDX[lagna_sign] + h - 1) % 12]) for h in KENDRA}
    trikona_lords = {SIGN_LORDS.get(SIGNS[(SIGN_IDX[lagna_sign] + h - 1) % 12]) for h in TRIKONA}
    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl and tl and kl != tl and in_same_house(kl, tl):
                yogas.append({
                    "name": f"Raja Yoga ({kl}+{tl})",
                    "planets": [kl, tl],
                    "effect": f"Kendra lord {kl} + Trikona lord {tl} conjunct — power, authority, and leadership are strongly indicated during their periods."
                })

    return yogas


# ─────────────────────────────────────────────────────────────────────────────
# Simplified Ashtakavarga (Standard Reference Tables)
# ─────────────────────────────────────────────────────────────────────────────

# These are the standard Bhinnashtakavarga values from BPHS tradition.
# For a full personal SAV, one must compute based on precise positions.
# We use a positional approximation until full SAV computation is added.
_SAV_DEFAULT_BY_HOUSE = {1: 28, 2: 25, 3: 27, 4: 26, 5: 24, 6: 30,
                          7: 22, 8: 23, 9: 29, 10: 25, 11: 31, 12: 20}


def _approximate_sav(lagna_sign: str, planets: dict) -> dict[int, int]:
    """
    Returns a house-indexed SAV score dict.
    Currently uses default reference values shifted by benefic/malefic planet occupancy.
    Full computation requires per-planet binnashtakavarga tables (future enhancement).
    """
    sav = dict(_SAV_DEFAULT_BY_HOUSE)
    for name, pdata in planets.items():
        h = pdata.get("house", 0)
        if not h:
            continue
        if name in BENEFICS:
            sav[h] = min(sav.get(h, 25) + 2, 56)
        elif name in HEAVY_MALEFICS:
            sav[h] = max(sav.get(h, 25) - 1, 10)
    return sav


# ─────────────────────────────────────────────────────────────────────────────
# Core Profile Generator
# ─────────────────────────────────────────────────────────────────────────────

def _compute_profile_from_kerykeion(birth_info: dict) -> dict:
    """
    Uses kerykeion + Swiss Ephemeris to compute the real natal chart,
    then enriches it with all 12 Jyotish layers.
    """
    load_dotenv()

    geonames_user = os.getenv("GEONAMES_USERNAME", "himanshurajak_22")

    subject = AstrologicalSubject(
        birth_info["name"],
        int(birth_info["year"]),
        int(birth_info["month"]),
        int(birth_info["day"]),
        int(birth_info["hour"]),
        int(birth_info["minute"]),
        birth_info["city"],
        birth_info["nation"],
        geonames_username=geonames_user,
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI",
        houses_system_identifier="W"
    )
    m = subject.model()

    # ── Step 1: Extract raw positions ───────────────────────────────────────
    PLANET_KEYS = {
        "sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus",
        "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn",
        "true_north_lunar_node": "Rahu", "true_south_lunar_node": "Ketu"
    }

    house_map = {
        "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
        "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
        "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12
    }

    lagna_abs = float(m.ascendant.abs_pos)
    lagna_sign = SIGNS[int(lagna_abs // 30) % 12]
    lagna_deg = lagna_abs % 30
    lagna_nak, lagna_pada = _get_nakshatra(lagna_abs)

    planets = {}
    for key, name in PLANET_KEYS.items():
        p = getattr(m, key)
        abs_pos = float(p.abs_pos)
        sign = SIGNS[int(abs_pos // 30) % 12]
        deg = abs_pos % 30
        nak, pada = _get_nakshatra(abs_pos)
        house = _house_from_lagna(sign, lagna_sign)
        dignity = _get_dignity(name, sign)
        nak_lord = NAKSHATRA_LORDS.get(nak, "?")
        retro = bool(p.retrograde)

        # D9 / D10
        d9_sign = _compute_d9_sign(sign, deg)
        d10_sign = _compute_d10_sign(sign, deg)
        d9_dignity = _get_dignity(name, d9_sign)
        d10_dignity = _get_dignity(name, d10_sign)
        vargottama = sign == d9_sign

        planets[name] = {
            "sign": sign,
            "house": house,
            "degree": round(deg, 2),
            "abs_pos": round(abs_pos, 2),
            "nakshatra": nak,
            "pada": pada,
            "nakshatra_lord": nak_lord,
            "dignity": dignity,
            "retrograde": retro,
            "d9_sign": d9_sign,
            "d9_dignity": d9_dignity,
            "d10_sign": d10_sign,
            "d10_dignity": d10_dignity,
            "vargottama": vargottama,
        }

    # ── Step 2: House map ────────────────────────────────────────────────────
    houses = {}
    for h in range(1, 13):
        h_sign = SIGNS[(SIGN_IDX[lagna_sign] + h - 1) % 12]
        lord = SIGN_LORDS.get(h_sign, "?")
        occupants = [n for n, pd in planets.items() if pd["house"] == h]
        h_type = _house_type(h)
        lord_house = planets.get(lord, {}).get("house", "?")
        summary = (
            f"H{h} ({h_sign}) — [{h_type}] — Lord: {lord} in H{lord_house} | "
            f"Occupants: {', '.join(occupants) if occupants else 'Empty'}"
        )
        houses[h] = {
            "sign": h_sign,
            "lord": lord,
            "lord_house": lord_house,
            "house_type": h_type,
            "occupants": occupants,
            "summary": summary,
        }

    # ── Step 3: Yogas ────────────────────────────────────────────────────────
    yogas = _detect_yogas(planets, lagna_sign)

    # ── Step 4: Vimshottari Dasha ────────────────────────────────────────────
    birth_dt = datetime(int(birth_info["year"]), int(birth_info["month"]),
                        int(birth_info["day"]), int(birth_info["hour"]), int(birth_info["minute"]))
    moon_lon = planets["Moon"]["abs_pos"]
    dasha_info = calculate_vimshottari_dasha(birth_dt, moon_lon)
    dasha_summary = dasha_info.get("summary", "Dasha unavailable")

    # ── Step 5: Ashtakavarga (approximated) ──────────────────────────────────
    sav = _approximate_sav(lagna_sign, planets)
    sav_interpretation = (
        f"H11 is the strongest gains house (SAV={sav[11]}). "
        f"H10 career: SAV={sav[10]}. "
        f"H7 partnerships: SAV={sav[7]}. "
        "Scores ≥30 = favourable transits | 25–29 = neutral | <25 = challenging."
    )

    # ── Step 6: Shadbala approximation ───────────────────────────────────────
    DIGBALA = {"Jupiter": 1, "Mercury": 1, "Moon": 4, "Venus": 4, "Saturn": 7, "Sun": 10, "Mars": 10}
    dignity_score = {"Exalted": 5.0, "Own Sign": 4.0, "Moolatrikona": 3.5, "Neutral": 2.0, "Debilitated": 0.5, "N/A": 2.0}

    shadbala = {}
    for name, pd in planets.items():
        d = dignity_score.get(pd["dignity"], 2.0)
        best_h = DIGBALA.get(name, 0)
        diff = abs(pd["house"] - best_h) if best_h else 6
        diff = min(diff, 12 - diff)
        dig = 2.0 if diff == 0 else (1.0 if diff <= 2 else 0.0)
        chesta = 1.0 if pd["retrograde"] and name not in ("Rahu", "Ketu") else 0.0
        # Neecha Bhanga bonus
        if pd["dignity"] == "Debilitated":
            deb_lord = SIGN_LORDS.get(DEBILITATION.get(name, ""), "")
            if deb_lord and planets.get(deb_lord, {}).get("house", 0) in KENDRA:
                d += 1.5
        total = min(d + dig + chesta, 10.0)
        shadbala[name] = round(total, 1)

    # ── Step 7: Lagna Lord analysis ──────────────────────────────────────────
    lagna_lord = SIGN_LORDS.get(lagna_sign, "?")
    lagna_lord_house = planets.get(lagna_lord, {}).get("house", "?")
    rashi_sign = planets.get("Moon", {}).get("sign", "?")
    rashi_nak = planets.get("Moon", {}).get("nakshatra", "?")

    # ── Step 8: Remedy Library Integration ───────────────────────────────────
    remedies = []
    # Identify weak planets from shadbala (score < 5.0)
    for name, score in shadbala.items():
        if score < 5.0 and name in PLANET_REMEDIES:
            rem = PLANET_REMEDIES[name]
            remedies.append({
                "planet": name, "reason": f"Weak Shadbala ({score}/10)",
                "mantra": rem['mantra'], "gemstone": rem['gemstone'], "charity": rem['charity']
            })
    
    # Check Rahu/Ketu placements in difficult houses (6, 8, 12 or with Lagna/Moon)
    for node in ["Rahu", "Ketu"]:
        h = planets.get(node, {}).get("house", 0)
        if h in [1, 6, 8, 12] or h == planets.get("Moon", {}).get("house", 0):
            rem = PLANET_REMEDIES[node]
            remedies.append({
                "planet": node, "reason": f"Placed in sensitive H{h}",
                "mantra": rem['mantra'], "gemstone": "Usually Avoided for Nodes", "charity": rem['charity']
            })

    if not remedies:
        remedies.append({"planet": "General", "reason": "Well-balanced chart", "mantra": "Gayatri Mantra or Maha Mrityunjaya", "gemstone": "None required", "charity": "Regular food donations"})

    # Build the assembled profile
    profile = {
        "meta": {
            "user_id": _slugify(birth_info["name"]),
            "name": birth_info["name"],
            "gender": birth_info.get("gender", ""),
            "birth": {
                "year": int(birth_info["year"]),
                "month": int(birth_info["month"]),
                "day": int(birth_info["day"]),
                "hour": int(birth_info["hour"]),
                "minute": int(birth_info["minute"]),
                "city": birth_info["city"],
                "nation": birth_info["nation"],
                "timezone": birth_info.get("timezone", "UTC"),
            },
            "generated_at": datetime.now().isoformat(),
        },
        "lagna": {
            "sign": lagna_sign,
            "degree": round(lagna_deg, 2),
            "abs_pos": round(lagna_abs, 2),
            "nakshatra": lagna_nak,
            "pada": lagna_pada,
            "lord": lagna_lord,
            "lord_house": lagna_lord_house,
        },
        "rashi": {
            "sign": rashi_sign,
            "nakshatra": rashi_nak,
        },
        "planets": planets,
        "houses": houses,
        "yogas": yogas,
        "dasha": {
            "summary": dasha_summary,
            "current_md": dasha_info.get("current_mahadasha", {}).get("lord", "?"),
            "current_ad": dasha_info.get("current_antardasha", {}).get("lord", "?"),
            "current_pd": dasha_info.get("current_pratyantardasha", {}).get("lord", "?"),
        },
        "ashtakvarga": {
            "sarvashtakavarga": sav,
            "interpretation": sav_interpretation,
        },
        "shadbala": shadbala,
        "remedies": remedies,
    }

    return profile


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def create_user_profile(birth_info: dict) -> str:
    """
    Computes a full 12-layer profile and saves it to disk.
    Returns the user_id (slugified name).
    birth_info keys: name, year, month, day, hour, minute, city, nation, gender (opt), timezone (opt)
    """
    user_id = _slugify(birth_info["name"])
    udir = _user_dir(user_id)
    udir.mkdir(parents=True, exist_ok=True)

    # Save raw birth data
    with open(_birth_path(user_id), "w") as f:
        yaml.dump({
            "name": birth_info["name"],
            "gender": birth_info.get("gender", ""),
            "year": int(birth_info["year"]),
            "month": int(birth_info["month"]),
            "day": int(birth_info["day"]),
            "hour": int(birth_info["hour"]),
            "minute": int(birth_info["minute"]),
            "city": birth_info["city"],
            "nation": birth_info["nation"],
            "Timezone": birth_info.get("timezone", "UTC"),
        }, f, default_flow_style=False)

    # Compute the profile
    profile = _compute_profile_from_kerykeion(birth_info)

    # Save profile JSON
    with open(_profile_path(user_id), "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False, default=str)

    print(f"  [OK] Profile created: {user_id} -- saved to {_profile_path(user_id)}")
    return user_id


def load_user_profile(user_id: str) -> dict:
    """Loads profile.json for the given user_id. Raises FileNotFoundError if missing."""
    p = _profile_path(user_id)
    if not p.exists():
        raise FileNotFoundError(f"No profile found for user '{user_id}'. Create one first.")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def list_users() -> list[dict]:
    """Returns a list of available user profiles with summary info."""
    if not USERS_DIR.exists():
        return []
    result = []
    for d in sorted(USERS_DIR.iterdir()):
        if d.is_dir() and _profile_path(d.name).exists():
            with open(_profile_path(d.name), "r", encoding="utf-8") as f:
                try:
                    p = json.load(f)
                    result.append({
                        "user_id": d.name,
                        "name": p["meta"]["name"],
                        "lagna": p["lagna"]["sign"],
                        "rashi": p["rashi"]["sign"],
                        "dasha": p["dasha"]["summary"][:60] + "...",
                    })
                except Exception:
                    result.append({"user_id": d.name, "name": d.name})
    return result


def get_active_user_id() -> str:
    """Returns the currently selected user_id. Defaults to first user found."""
    if ACTIVE_USER_FILE.exists():
        uid = ACTIVE_USER_FILE.read_text().strip()
        if uid and _profile_path(uid).exists():
            return uid
    users = list_users()
    if users:
        return users[0]["user_id"]
    return ""


def set_active_user(user_id: str) -> None:
    """Sets the active user_id persistently."""
    ACTIVE_USER_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_USER_FILE.write_text(user_id)


def get_active_profile() -> dict:
    """Returns the profile dict for the currently active user."""
    uid = get_active_user_id()
    if not uid:
        raise RuntimeError("No user profiles found. Create a profile first.")
    return load_user_profile(uid)


def profile_to_context_text(profile: dict) -> str:
    """
    Converts a loaded profile dict into a rich multi-layer text context
    for the AI agent — replaces what KUNDALI_PROFILE + multi_layer_engine produce.
    """
    meta = profile["meta"]
    lagna = profile["lagna"]
    rashi = profile["rashi"]
    planets = profile["planets"]
    houses = profile["houses"]
    yogas = profile["yogas"]
    dasha = profile["dasha"]
    sav = profile["ashtakvarga"]["sarvashtakavarga"]
    shadbala = profile["shadbala"]
    remedies = profile.get("remedies", [])

    birth = meta["birth"]
    lines = [
        f"╔══════════════════════════════════════════════════════════════════════════════╗",
        f"║  USER: {meta['name']:40}                        ║",
        f"║  Born: {birth['year']}-{birth['month']:02d}-{birth['day']:02d} {birth['hour']:02d}:{birth['minute']:02d} | {birth['city']}, {birth['nation']}    ║",
        f"╚══════════════════════════════════════════════════════════════════════════════╝",
        "",
        f"LAGNA: {lagna['sign']} {lagna['degree']:.1f}° | Nakshatra: {lagna['nakshatra']} Pada {lagna['pada']}",
        f"RASHI: {rashi['sign']} | Moon Nakshatra: {rashi['nakshatra']}",
        f"LAGNA LORD: {lagna['lord']} in H{lagna['lord_house']}",
        "",
        "━━━ PLANETARY POSITIONS (Layer 1) ━━━",
    ]

    for name, pd in planets.items():
        retro = " ®" if pd["retrograde"] else ""
        varg = " ★VARG" if pd["vargottama"] else ""
        lines.append(
            f"  {name:10} H{pd['house']:<2} {pd['sign']:14} {pd['nakshatra']:22} Pada {pd['pada']} | "
            f"Dignity: {pd['dignity']:12} | Nak Lord: {pd['nakshatra_lord']}{retro}{varg}"
        )

    lines += ["", "━━━ HOUSE SUMMARY (Layer 3) ━━━"]
    for h in range(1, 13):
        hd = houses.get(str(h)) or houses.get(h)
        if hd:
            lines.append(f"  {hd['summary']}")

    lines += ["", "━━━ YOGAS (Layer 4) ━━━"]
    if yogas:
        for y in yogas:
            lines.append(f"  ★ {y['name']}: {y['effect']}")
    else:
        lines.append("  No major yogas detected from available data.")

    lines += ["", "━━━ VIMSHOTTARI DASHA (Layer 6) ━━━",
              f"  {dasha['summary']}",
              f"  Current: {dasha['current_md']} MD → {dasha['current_ad']} AD → {dasha['current_pd']} PD"]

    lines += ["", "━━━ DIVISIONAL CHARTS (Layer 8) ━━━"]
    for name, pd in planets.items():
        v = " ★VARGOTTAMA" if pd["vargottama"] else ""
        lines.append(
            f"  {name:10} D1: {pd['sign']:14} D9: {pd['d9_sign']:14}({pd['d9_dignity']}) | D10: {pd['d10_sign']:14}({pd['d10_dignity']}){v}"
        )

    lines += ["", "━━━ SHADBALA — STRENGTH SCORES (Layer 9) ━━━"]
    for name, score in shadbala.items():
        bar = "[***] STRONG" if score >= 7 else ("[**]  GOOD" if score >= 5 else ("[*]   MOD" if score >= 3 else "[ ]   WEAK"))
        lines.append(f"  {name:10} {score:4.1f}/10  {bar}")

    lines += ["", "━━━ ASHTAKAVARGA SAV BY HOUSE (Layer 10) ━━━",
              "  H:   " + "  ".join(f"{h:2}" for h in range(1, 13)),
              "  SAV: " + "  ".join(f"{sav.get(h, sav.get(str(h), 0)):2}" for h in range(1, 13)),
              "  Key: ≥30=Favourable | 25-29=Neutral | <25=Challenging",
              f"  {profile['ashtakvarga']['interpretation']}"]

    lines += ["", "━━━ RECOMMENDED REMEDIES (Based on Weak/Afflicted Planets) ━━━"]
    for rem in remedies:
        lines.append(f"  ★ For {rem['planet']} ({rem['reason']}):")
        lines.append(f"      Mantra:  {rem['mantra']}")
        lines.append(f"      Gem:     {rem['gemstone']}")
        lines.append(f"      Charity: {rem['charity']}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Migration helper — wrap Himanshu's hardcoded profile into JSON format
# ─────────────────────────────────────────────────────────────────────────────

def migrate_himanshu_from_yaml():
    """
    Seeds Himanshu's profile from the existing config/birth_data.yaml
    by running the full kerykeion computation. Run once.
    """
    yaml_path = Path("config/birth_data.yaml")
    if not yaml_path.exists():
        print("  No config/birth_data.yaml found.")
        return None
    with open(yaml_path) as f:
        bd = yaml.safe_load(f)
    birth_info = {
        "name": bd["name"],
        "gender": bd.get("gender", ""),
        "year": bd["year"], "month": bd["month"], "day": bd["day"],
        "hour": bd["hour"], "minute": bd["minute"],
        "city": bd["city"], "nation": bd["nation"],
        "timezone": bd.get("Timezone", "UTC"),
    }
    return create_user_profile(birth_info)


if __name__ == "__main__":
    print("Migrating Himanshu's profile from yaml...")
    uid = migrate_himanshu_from_yaml()
    print(f"Done. user_id = {uid}")
    p = load_user_profile(uid)
    print(profile_to_context_text(p)[:1000])
