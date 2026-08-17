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

def _fmt_dt(d, fmt='%b %Y'):
    """Format a date that may be a datetime object or an ISO string."""
    if isinstance(d, str):
        try:
            return datetime.fromisoformat(d).strftime(fmt)
        except Exception:
            return d[:7]  # fallback: return YYYY-MM portion
    try:
        return d.strftime(fmt)
    except Exception:
        return str(d)[:7]
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

# Ensure we use a consistent data directory regardless of where the script is called from
BASE_DIR = Path(__file__).resolve().parent.parent  # Points to 'backend/'
USERS_DIR = BASE_DIR / "data" / "users"
ACTIVE_USER_FILE = BASE_DIR / "data" / "active_user.txt"


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
    Supports ground_truth.json override for verified precision.
    """
    load_dotenv()
    user_id = _slugify(birth_info["name"])
    udir = _user_dir(user_id)
    gt_path = udir / "ground_truth.json"
    ground_truth = {}
    if gt_path.exists():
        try:
            with open(gt_path, "r", encoding="utf-8") as f:
                ground_truth = json.load(f)
                print(f"  [INFO] Ground truth found for {user_id}. Using for overrides.")
        except Exception as e:
            print(f"  [WARN] Failed to load ground truth for {user_id}: {e}")

    geonames_user = os.getenv("GEONAMES_USERNAME", "demo_user")
    # ... rest of kerykeion setup ...

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

    lagna_abs = float(m.ascendant.abs_pos)
    lagna_sign = SIGNS[int(lagna_abs // 30) % 12]
    lagna_lord = SIGN_LORDS.get(lagna_sign, "?")
    lagna_deg = lagna_abs % 30
    lagna_nak, lagna_pada = _get_nakshatra(lagna_abs)

    from core.astro_engine import calculate_varga_position

    # Supported divisions as requested
    DIVISIONS = {
        1: "Rashi", 2: "Hora", 3: "Drekkana", 4: "Chaturthamsa", 7: "Saptamsa",
        9: "Navamsa", 10: "Dasamsa", 12: "Dwadasamsa", 16: "Shodasamsa",
        20: "Vimsamsa", 24: "Chaturvimsamsa", 27: "Sapta-vimshamsa",
        30: "Trimsamsa", 40: "Khavedamsa", 45: "Akshavedamsa", 60: "Shashtyamsa"
    }

    planets = {}
    divisional_charts = {str(d): {} for d in DIVISIONS.keys()}

    def _compute_multi_chart_convergence(p_name: str, d1_dig: str, d9_sign_idx: int, d10_sign_idx: int) -> dict:
        """
        Computes the dignity gap and narrative across D1, D9, and D10.
        """
        d9_dig = _get_dignity(p_name, SIGNS[d9_sign_idx])
        d10_dig = _get_dignity(p_name, SIGNS[d10_sign_idx])

        def score_dig(d):
            if d in ("Exalted", "Moolatrikona", "Own Sign", "Own"): return 3
            if d in ("Friend", "Friendly"): return 2
            if d in ("Neutral", "N/A"): return 1
            return 0 # Enemy, Debilitated

        s1 = score_dig(d1_dig)
        s9 = score_dig(d9_dig)
        s10 = score_dig(d10_dig)

        is_d1_strong = s1 >= 2
        is_d9_strong = s9 >= 2
        is_d10_strong = s10 >= 2

        if not is_d1_strong and is_d9_strong and is_d10_strong:
            narrative = "Planet underperforms in surface personality but delivers powerfully at soul and career level. Person works harder than they appear to. Late recognition. Solid foundation."
            score_label = "Strong (Hidden)"
        elif is_d1_strong and not is_d9_strong and is_d10_strong:
            narrative = "Planet expresses well in personality and career but soul-level purpose feels uncertain. Outward success that sometimes feels hollow inside."
            score_label = "Mixed (Surface)"
        elif is_d1_strong and is_d9_strong and not is_d10_strong:
            narrative = "Planet is powerful personally and karmically but struggles to translate into professional outcomes. Potential that career structures don't fully capture."
            score_label = "Mixed (Internal)"
        elif not is_d1_strong and not is_d9_strong and not is_d10_strong:
            narrative = "Planet is genuinely challenged across all levels. Be honest about this. Name the specific life areas this affects without softening it."
            score_label = "Weak"
        elif is_d1_strong and is_d9_strong and is_d10_strong:
            narrative = "This is a cornerstone planet in this chart. Everything this planet touches tends to deliver. Name it as exceptional — don't understate it."
            score_label = "Very Strong"
        else:
            narrative = "Planet has fluctuating support across physical, soul, and career dimensions. Requires conscious effort to align these layers."
            score_label = "Fluctuating"

        return {
            "d1_dignity": d1_dig,
            "d9_dignity": d9_dig,
            "d10_dignity": d10_dig,
            "score": score_label,
            "narrative": narrative
        }

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

        # Compute all Vargas
        vargas = {}
        for d in DIVISIONS.keys():
            v_pos = calculate_varga_position(abs_pos, d)
            v_lagna_pos = calculate_varga_position(lagna_abs, d)
            v_house = (v_pos['sign_idx'] - v_lagna_pos['sign_idx'] + 12) % 12 + 1
            v_pos['house'] = v_house
            vargas[str(d)] = v_pos
            divisional_charts[str(d)][name] = v_pos

        convergence = {}
        if name not in ("ASC", "Rahu", "Ketu"):
            convergence = _compute_multi_chart_convergence(
                name, dignity, vargas['9']['sign_idx'], vargas['10']['sign_idx']
            )

        def get_d60_deity(sign_idx, deg):
            """Simplified D60 Deity proxy for odd/even signs."""
            part = int(deg / 0.5)
            # 60 deities exist; as proxy, we categorize into benefic/malefic/mixed
            is_odd = sign_idx % 2 == 0
            if is_odd:
                if part in [1, 2, 8, 9, 10, 11, 16, 30, 31, 32, 33, 34, 35, 39, 40, 42, 43, 44, 48, 51, 52, 59]:
                    return "Kroora (Fierce/Malefic)"
                return "Saumya (Gentle/Benefic)"
            else:
                # Reverse for even signs
                if (59 - part) in [1, 2, 8, 9, 10, 11, 16, 30, 31, 32, 33, 34, 35, 39, 40, 42, 43, 44, 48, 51, 52, 59]:
                    return "Kroora (Fierce/Malefic)"
                return "Saumya (Gentle/Benefic)"

        planets[name] = {
            "sign": sign,
            "house": house,
            "degree": round(deg, 2),
            "abs_pos": round(abs_pos, 2),
            "sign_idx": int(abs_pos // 30) % 12,
            "nakshatra": nak,
            "pada": pada,
            "nakshatra_lord": nak_lord,
            "dignity": dignity,
            "retrograde": retro,
            "vargas": vargas,
            "vargottama": sign == vargas['9']['sign'],
            "convergence": convergence,
            "d60_devata": get_d60_deity(int(abs_pos // 30) % 12, deg)
        }

    # Add Lagna to planets for UI
    planets['ASC'] = {
        "sign": lagna_sign,
        "sign_idx": SIGN_IDX[lagna_sign],
        "degree": round(lagna_deg, 2),
        "abs_pos": round(lagna_abs, 2),
        "house": 1,
        "nakshatra": lagna_nak,
        "pada": lagna_pada,
        "nakshatra_lord": NAKSHATRA_LORDS.get(lagna_nak, "?"),
    }

    # Add Lagna to Divisional Charts
    for d in DIVISIONS.keys():
        v_lagna_pos = calculate_varga_position(lagna_abs, d)
        v_lagna_pos['house'] = 1
        divisional_charts[str(d)]['ASC'] = v_lagna_pos

    lagna_lord_house = planets.get(lagna_lord, {}).get("house", "?")
    rashi_sign = planets.get("Moon", {}).get("sign", "?")
    rashi_nak = planets.get("Moon", {}).get("nakshatra", "?")

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

    # ── Step 4: Vimshottari & Jaimini Chara Dasha ────────────────────────────
    birth_dt = datetime(int(birth_info["year"]), int(birth_info["month"]),
                        int(birth_info["day"]), int(birth_info["hour"]), int(birth_info["minute"]))
    moon_lon = planets["Moon"]["abs_pos"]
    dasha_info = calculate_vimshottari_dasha(birth_dt, moon_lon)
    dasha_summary = dasha_info.get("summary", "Dasha unavailable")

    from core.jaimini_engine import calculate_chara_dasha
    chara_dasha_info = calculate_chara_dasha(birth_dt, SIGN_IDX[lagna_sign], planets)


    # ── Step 5: Ashtakavarga (Full Parashara Computation) ───────────────────
    from core.ashtakavarga import calculate_ashtakavarga
    av_data = calculate_ashtakavarga(subject)
    sav = av_data["sarvashtakavarga"]
    
    # OVERRIDE SAV
    if "ashtakavarga" in ground_truth:
        gt_sav = ground_truth["ashtakavarga"].get("sarvashtakavarga")
        if gt_sav:
            # Handle string keys from JSON
            sav = {int(k): v for k, v in gt_sav.items()}
            av_data["sarvashtakavarga"] = sav
            
            # Map house-based SAV back to signs (sign_sav is 1-indexed Aries=1)
            sign_sav = {}
            for h, pts in sav.items():
                s_idx = (SIGN_IDX[lagna_sign] + h - 1) % 12
                sign_sav[s_idx + 1] = pts
            av_data["sarvashtakavarga_by_sign"] = sign_sav
            print(f"  [OVERRIDE] SAV points (House & Sign) applied.")
    
    # ── Step 6: Shadbala & Bhava Bala (High-Precision Calibration) ─────────
    from core.shadbala_engine import calculate_shadbala_rupas, calculate_bhava_bala
    shadbala_full = calculate_shadbala_rupas(subject)
    bhava_bala = calculate_bhava_bala(subject)
    
    # OVERRIDE SHADBALA
    if "shadbala" in ground_truth:
        gt_shad = ground_truth["shadbala"].get("shadbala_full")
        if gt_shad:
            for p, data in gt_shad.items():
                if p in shadbala_full:
                    shadbala_full[p].update(data)
            print(f"  [OVERRIDE] Shadbala Rupas applied.")

    # OVERRIDE BHAVA BALA
    if "bhava_bala" in ground_truth:
        gt_bhava = ground_truth.get("bhava_bala")
        if gt_bhava:
            # Re-rank based on override values
            temp_bhava = {int(k): v for k, v in gt_bhava.items()}
            sorted_h = sorted(temp_bhava.items(), key=lambda x: -x[1]["rupas"])
            rank_map = {h: i + 1 for i, (h, _) in enumerate(sorted_h)}
            for h, data in temp_bhava.items():
                data["rank"] = rank_map[h]
                bhava_bala[h] = data
            print(f"  [OVERRIDE] Bhava Bala Rupas applied.")

    # Simple shadbala dict for other internal logic (using rupas)
    shadbala = {p: data["rupas"] for p, data in shadbala_full.items()}

    # Identify sign names for each house to show in UI
    house_to_sign = {}
    for h in range(1, 13):
        s_idx = (SIGN_IDX[lagna_sign] + h - 1) % 12
        house_to_sign[h] = SIGNS[s_idx]

    # Find peak SAV house
    peak_sav_h = max(sav, key=sav.get)
    # Find peak Bhava Bala house
    peak_bhava_h = max(bhava_bala, key=lambda x: bhava_bala[x]['rupas'])

    sav_interpretation = (
        f"H{peak_sav_h} ({house_to_sign[peak_sav_h]}) is the peak manifestation point (SAV={sav[peak_sav_h]}). "
        f"H{peak_bhava_h} ({house_to_sign[peak_bhava_h]}) is the strongest house by absolute potency (Bhava Bala)."
    )

    # ── Step 7: Karakas (Jaimini System) ─────────────────────────────────────
    from core.karaka_engine import calculate_chara_karakas, get_sthira_karakas
    chara_karakas = calculate_chara_karakas(planets)
    sthira_karakas = get_sthira_karakas()

    # ── Step 8: Multi-Layered Remedial Engine ───────────────────────────────
    from core.remedial_engine import RemedialEngine
    # Find planets with shadbala rupas < 5.5
    weak_planets = [p for p, data in shadbala_full.items() if data.get("rupas", 6) < 5.5]
    if not weak_planets: weak_planets = ["Saturn", "Moon"]

    rem_engine = RemedialEngine(birth_info)
    structured_remedies = rem_engine.get_prescriptions(weak_planets[:3])

    remedies = []
    for r in structured_remedies:
        remedies.append({
            "planet": r["planet"],
            "reason": "Affliction / Lower Rupa Strength",
            "mantra": r["spiritual"],
            "gemstone": "Consult for specifics",
            "charity": r["material"] + " | Behavioral: " + r["behavioral"]
        })

    if not remedies:

        remedies.append({"planet": "General", "reason": "Well-balanced chart", "mantra": "Gayatri Mantra or Maha Mrityunjaya", "gemstone": "None required", "charity": "Regular food donations"})

    # ── Step 9: Structured Aspects & Lordships for UI ───────────────────────
    structured_aspects = []
    PLANETS_LIST = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    
    for p_name in PLANETS_LIST:
        if p_name not in planets: continue
        h = planets[p_name]['house']
        # 7th aspect
        t7 = (h - 1 + 6) % 12 + 1
        structured_aspects.append({"planet": p_name, "type": "7th", "target_house": t7})
        
        # Specials
        if p_name == "Mars":
            for off in [4, 8]:
                structured_aspects.append({"planet": p_name, "type": f"{off}th", "target_house": (h - 1 + off - 1) % 12 + 1})
        elif p_name == "Jupiter":
            for off in [5, 9]:
                structured_aspects.append({"planet": p_name, "type": f"{off}th", "target_house": (h - 1 + off - 1) % 12 + 1})
        elif p_name == "Saturn":
            for off in [3, 10]:
                structured_aspects.append({"planet": p_name, "type": f"{off}th", "target_house": (h - 1 + off - 1) % 12 + 1})

    # ── Step 10: Advanced Calculations ─────────────────────────────────────
    from core.panchanga_engine import calculate_panchanga
    from core.bhava_chalit import get_bhava_madhya, get_bhava_chalit_house
    from core.jaimini_engine import calculate_all_arudhas
    from core.graha_maitri import graha_maitri_score
    from core.ishta_kashta import ishta_kashta_phala
    from core.graha_avastha import get_graha_avastha
    from core.dosha_engine import check_doshas

    # 1. Birth Panchanga
    from core.astro_engine import datetime_to_jd
    birth_jd = datetime_to_jd(birth_dt)
    panchanga = calculate_panchanga(birth_jd, birth_info["lat"] if "lat" in birth_info else 28.6, birth_info["lon"] if "lon" in birth_info else 77.2)

    # 2. Bhava Chalit
    bhava_madhyas = get_bhava_madhya(lagna_abs)
    bhava_chalit = {}
    for name, pd in planets.items():
        if name == "ASC": continue
        bhava_chalit[name] = get_bhava_chalit_house(pd["abs_pos"], bhava_madhyas)

    # 3. Jaimini Arudhas
    house_lords_map = {h: houses[h]["lord"] for h in range(1, 13)}
    planet_houses_map = {name: pd["house"] for name, pd in planets.items()}
    arudhas = calculate_all_arudhas(house_lords_map, planet_houses_map)

    # 4. Planetary Relationships & Details
    relationships = {}
    planets_for_rel = [p for p in planets.keys() if p != "ASC"]
    for p1 in planets_for_rel:
        relationships[p1] = {}
        for p2 in planets_for_rel:
            if p1 == p2: continue
            relationships[p1][p2] = graha_maitri_score(p1, p2, planet_houses_map)

    # Enrich planets with Avastha and Ishta/Kashta
    for name in planets_for_rel:
        if name in ("Rahu", "Ketu"): continue
        # Get Uccha and Chesta from shadbala_full
        s_data = shadbala_full.get(name, {})
        uccha = s_data.get("uccha", 30)
        chesta = s_data.get("chesta", 30)
        ik_phala = ishta_kashta_phala(uccha, chesta)
        planets[name]["ishta_kashta"] = ik_phala
        
        avasthas = get_graha_avastha(name, planets[name]["abs_pos"], planets[name]["house"], planets[name]["retrograde"], planets[name]["dignity"])
        planets[name]["avasthas"] = avasthas

    # 5. Doshas
    detected_doshas = check_doshas(planet_houses_map, house_lords_map, SIGN_IDX[lagna_sign])

    # Build the assembled profile
    # ── Step 11: Real Astrologer Synthesis ─────────────────────────────────
    from core.bhrigu_nadi import BhriguNadiEngine
    from core.jaimini_padas import JaiminiPadaEngine
    from core.tajika_engine import TajikaEngine
    from core.karmic_engine import KarmicNarrativeEngine
    from core.yogini_engine import get_yogini_dasha
    
    bhrigu = BhriguNadiEngine(subject, planets, SIGN_IDX[lagna_sign])
    pada_engine = JaiminiPadaEngine()
    tajika_engine = TajikaEngine(subject)
    karmic_engine = KarmicNarrativeEngine(planets)
    yogini_sequence = get_yogini_dasha(planets["Moon"]["abs_pos"], birth_dt)
    
    # Preserve lived experience if profile already exists
    user_id = _slugify(birth_info["name"])
    lived_experience = {}
    old_p_path = _profile_path(user_id)
    if old_p_path.exists():
        try:
            with open(old_p_path, "r", encoding="utf-8") as f:
                old_p = json.load(f)
                lived_experience = old_p.get("lived_experience", {})
        except: pass

    profile = {
        "meta": {
            "user_id": user_id,
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
                "lat": float(getattr(subject, "lat", birth_info.get("lat", 0)) or 0),
                "lon": float(getattr(subject, "lng", birth_info.get("lon", 0)) or 0),
            },
            "generated_at": datetime.now().isoformat(),
            "rectification": birth_info.get("rectification", {
                "confidence_label": "rectified" if birth_info.get("rectified") else "unverified",
            }),
        },
        "lived_experience": lived_experience,
        "lagna": {
            "sign": lagna_sign,
            "sign_idx": SIGN_IDX[lagna_sign],
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
        "divisional_charts": divisional_charts,
        "houses": houses,
        "yogas": yogas,
        "aspects": structured_aspects,
        "dasha": {
            "summary": dasha_summary,
            "current_md": dasha_info.get("current_mahadasha", {}).get("lord", "?"),
            "current_ad": dasha_info.get("current_antardasha", {}).get("lord", "?"),
            "current_pd": dasha_info.get("current_pratyantardasha", {}).get("lord", "?"),
            "md_end": dasha_info.get("current_mahadasha", {}).get("end") if dasha_info.get("current_mahadasha") else "?",
            "ad_end": dasha_info.get("current_antardasha", {}).get("end") if dasha_info.get("current_antardasha") else "?",
            "pd_end": dasha_info.get("current_pratyantardasha", {}).get("end") if dasha_info.get("current_pratyantardasha") else "?",
            "full_timeline": dasha_info.get("full_timeline", [])
        },
        "chara_dasha": chara_dasha_info,
        "yogini_dasha": yogini_sequence,
        "panchanga": panchanga,
        "bhava_chalit": bhava_chalit,
        "arudhas": arudhas,
        "relationships": relationships,
        "doshas": detected_doshas,
        "ashtakavarga": {
            "sarvashtakavarga": sav,
            "sarvashtakavarga_by_sign": av_data["sarvashtakavarga_by_sign"],
            "interpretation": sav_interpretation,
        },
        "shadbala": shadbala,
        "shadbala_full": shadbala_full,
        "bhava_bala": bhava_bala,
        "karakas": {
            "chara": chara_karakas,
            "sthira": sthira_karakas
        },
        "remedies": remedies,
        "bhrigu_nadi": bhrigu.get_full_report(),
        "micro_timing": pada_engine.get_current_pada_snapshot(),
        "tajika": tajika_engine.get_varshaphal(datetime.now().year),
        "karmic_story": karmic_engine.get_soul_story()
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
    birth_save = {
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
    }
    if birth_info.get("rectification"):
        birth_save["rectification"] = birth_info["rectification"]
        birth_save["rectified"] = birth_info.get("rectified", True)

    with open(_birth_path(user_id), "w", encoding="utf-8") as f:
        yaml.dump(birth_save, f, default_flow_style=False)

    # Compute the profile
    profile = _compute_profile_from_kerykeion(birth_info)

    # Save profile JSON
    with open(_profile_path(user_id), "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False, default=str)

    print(f"  [OK] Profile created: {user_id} -- saved to {_profile_path(user_id)}")
    return user_id


def refresh_live_dasha(profile: dict) -> dict:
    """Recompute Vimshottari MD/AD/PD from current date (never serve stale dasha from JSON)."""
    birth = profile["meta"]["birth"]
    birth_dt = datetime(
        int(birth["year"]), int(birth["month"]), int(birth["day"]),
        int(birth["hour"]), int(birth["minute"]),
        int(birth.get("second", 0)),
    )
    moon_lon = profile["planets"]["Moon"]["abs_pos"]
    dasha_info = calculate_vimshottari_dasha(birth_dt, moon_lon)
    if dasha_info.get("error"):
        return profile
    md = dasha_info["current_mahadasha"]
    ad = dasha_info["current_antardasha"]
    pd = dasha_info["current_pratyantardasha"]
    profile["dasha"] = {
        "summary": dasha_info.get("summary", ""),
        "current_md": md.get("lord", "?"),
        "current_ad": ad.get("lord", "?"),
        "current_pd": pd.get("lord", "?"),
        "md_end": md.get("end"),
        "ad_end": ad.get("end"),
        "pd_end": pd.get("end"),
        "md_end_display": md.get("end_inclusive"),
        "ad_end_display": ad.get("end_inclusive"),
        "pd_end_display": pd.get("end_inclusive"),
        "md_start": md.get("start"),
        "ad_start": ad.get("start"),
        "pd_start": pd.get("start"),
        "full_timeline": dasha_info.get("full_timeline", []),
        "pratyantardasha_timeline": dasha_info.get("pratyantardasha_timeline", []),
        "computed_at": datetime.now().isoformat(),
    }
    return profile


def load_user_profile(user_id: str) -> dict:
    """Loads profile.json for the given user_id. Raises FileNotFoundError if missing."""
    p = _profile_path(user_id)
    if not p.exists():
        raise FileNotFoundError(f"No profile found for user '{user_id}'. Create one first.")
    
    with open(p, "r", encoding="utf-8") as f:
        profile = json.load(f)
        
    # AUTO-UPGRADE: Re-compute if divisional charts or other new layers are missing
    if "divisional_charts" not in profile or "panchanga" not in profile:
        print(f"  [AUTO-UPGRADE] Profile {user_id} missing new data layers. Re-computing...")
        bpath = _birth_path(user_id)
        if bpath.exists():
            with open(bpath, 'r') as bf:
                birth_info = yaml.safe_load(bf)
                new_profile = _compute_profile_from_kerykeion(birth_info)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(new_profile, f, indent=2, ensure_ascii=False, default=str)
                return refresh_live_dasha(new_profile)

    return refresh_live_dasha(profile)


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


def update_lived_experience(user_id: str, data: dict) -> None:
    """
    Updates the qualitative user context in the profile.
    data can contain: profession, struggles, goals, life_events, emotional_tone
    """
    p_path = _profile_path(user_id)
    if not p_path.exists():
        return
    
    with open(p_path, "r", encoding="utf-8") as f:
        p = json.load(f)
        
    if "lived_experience" not in p:
        p["lived_experience"] = {}
        
    # Deep update or merge
    for key, val in data.items():
        if isinstance(val, list):
            existing = p["lived_experience"].get(key)
            if not isinstance(existing, list):
                p["lived_experience"][key] = [existing] if existing else []
            p["lived_experience"][key].extend(val)
        elif isinstance(val, dict):
            existing = p["lived_experience"].get(key)
            if not isinstance(existing, dict):
                p["lived_experience"][key] = {}
            p["lived_experience"][key].update(val)
        else:
            p["lived_experience"][key] = val
            
    with open(p_path, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2, ensure_ascii=False, default=str)


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
    sav = profile["ashtakavarga"]["sarvashtakavarga"]
    shadbala = profile["shadbala"]
    remedies = profile.get("remedies", [])

    birth = meta["birth"]
    lived = profile.get("lived_experience", {})
    lines = [
        f"╔══════════════════════════════════════════════════════════════════════════════╗",
        f"║  USER: {meta['name']:40}                        ║",
        f"║  Born: {birth['year']}-{birth['month']:02d}-{birth['day']:02d} {birth['hour']:02d}:{birth['minute']:02d} | {birth['city']}, {birth['nation']}    ║",
        f"╚══════════════════════════════════════════════════════════════════════════════╝",
        "",
        "━━━ LIVED EXPERIENCE (Qualitative Context) ━━━",
        f"  Current Work/Projects: {lived.get('profession', 'Not shared yet')}",
        f"  Active Struggles:      {lived.get('struggles', 'Not shared yet')}",
        f"  Goals/Ambitions:      {lived.get('goals', 'Not shared yet')}",
        f"  Significant Events:    {lived.get('life_events', 'Not shared yet')}",
        f"  Emotional Signature:   {lived.get('emotional_tone', 'Not shared yet')}",
        "",
        f"LAGNA: {lagna['sign']} {lagna['degree']:.1f}° | Nakshatra: {lagna['nakshatra']} Pada {lagna['pada']}",
        f"RASHI: {rashi['sign']} | Moon Nakshatra: {rashi['nakshatra']}",
        f"LAGNA LORD: {lagna['lord']} in H{lagna['lord_house']}",
        "",
        "━━━ PLANETARY POSITIONS (Layer 1) ━━━",
    ]

    for name, pd in planets.items():
        if name == "ASC": continue
        retro = " ®" if pd.get("retrograde") else ""
        varg = " ★VARG" if pd.get("vargottama") else ""
        d60 = f" [D60: {pd.get('d60_devata', '?')}]"
        conv = pd.get("convergence", {})
        conv_str = f" | Convergence: {conv.get('score', '')} -> {conv.get('narrative', '')}" if conv else ""
        lines.append(
            f"  {name:10} H{pd['house']:<2} {pd['sign']:14} {pd['nakshatra']:22} Pada {pd['pada']} | "
            f"Dignity: {pd['dignity']:12} | Nak Lord: {pd['nakshatra_lord']}{retro}{varg}{d60}{conv_str}"
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
              
    chara = profile.get("chara_dasha", {})
    if chara and chara.get("current_md"):
        cmd = chara["current_md"]
        lines += ["", "━━━ JAIMINI CHARA DASHA (Dual-Clock Layer) ━━━",
                  f"  Current Mahadasha: {cmd['sign']} ({cmd['years']} years) | {_fmt_dt(cmd['start'])} to {_fmt_dt(cmd['end'])}"]

    lines += ["", "━━━ DIVISIONAL CHARTS (Layer 6) ━━━"]
    DIV_NAMES = {
        "1": "D1 Rashi", "2": "D2 Hora", "3": "D3 Drekkana", "4": "D4 Chaturthamsa", "7": "D7 Saptamsa",
        "9": "D9 Navamsa", "10": "D10 Dasamsa", "12": "D12 Dwadasamsa", "16": "D16 Shodasamsa",
        "20": "D20 Vimsamsa", "24": "D24 Chaturvimsamsa", "27": "D27 Sapta-vimshamsa",
        "30": "D30 Trimsamsa", "40": "D40 Khavedamsa", "45": "D45 Akshavedamsa", "60": "D60 Shashtyamsa"
    }
    
    div_charts = profile.get("divisional_charts", {})
    for d_code, d_name in DIV_NAMES.items():
        if d_code in div_charts:
            lines.append(f"\n  [{d_name}]")
            d_data = div_charts[d_code]
            # Order Lagna first
            p_names = ['ASC', 'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
            for p_name in p_names:
                if p_name in d_data:
                    pos = d_data[p_name]
                    lines.append(f"    {p_name:8} : {pos['sign']:14} (House {pos['house']})")

    lines += ["", "━━━ SHADBALA — STRENGTH SCORES (Layer 9) ━━━"]
    for name, score in shadbala.items():
        bar = "[***] STRONG" if score >= 7 else ("[**]  GOOD" if score >= 5 else ("[*]   MOD" if score >= 3 else "[ ]   WEAK"))
        lines.append(f"  {name:10} {score:4.1f}/10  {bar}")

    lines += ["", "━━━ ASHTAKAVARGA SAV BY HOUSE (Layer 10) ━━━",
              "  H:   " + "  ".join(f"{h:2}" for h in range(1, 13)),
              "  SAV: " + "  ".join(f"{sav.get(h, sav.get(str(h), 0)):2}" for h in range(1, 13)),
              "  Key: ≥30=Favourable | 25-29=Neutral | <25=Challenging",
              f"  {profile['ashtakavarga']['interpretation']}"]

    lines += ["", "━━━ RECOMMENDED REMEDIES (Based on Weak/Afflicted Planets) ━━━"]
    for rem in remedies:
        lines.append(f"  ★ For {rem['planet']} ({rem['reason']}):")
        lines.append(f"      Mantra:  {rem['mantra']}")
        lines.append(f"      Gem:     {rem['gemstone']}")
        lines.append(f"      Charity: {rem['charity']}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Migration helper — wrap Demo User's hardcoded profile into JSON format
# ─────────────────────────────────────────────────────────────────────────────

def migrate_demo_from_yaml():
    """
    Seeds the demo profile from the existing config/birth_data.yaml
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
    print("Migrating Demo profile from yaml...")
    uid = migrate_demo_from_yaml()
    print(f"Done. user_id = {uid}")
    p = load_user_profile(uid)
    print(profile_to_context_text(p)[:1000])
