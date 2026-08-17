"""
core/ashtakavarga.py
────────────────────────────────────────────────────────────────
Pure mathematical Ashtakavarga engine.
Computes Bhinnashtakavarga (BAV) and Sarvashtakavarga (SAV)
per standard BPHS / Parashara bindu tables.

FIX: House mapping was wrong — was mapping by sign index, now
correctly maps H1 = Lagna sign, H2 = next sign, etc.
The BAV is computed per SIGN (0-11), then mapped to HOUSES
relative to the Lagna sign index.
────────────────────────────────────────────────────────────────
"""
try:
    from core.astro_engine import SIGNS
except ImportError:
    from backend.core.astro_engine import SIGNS

# ── BPHS Parashara Bindu Tables ───────────────────────────────────────────────
# For each planet (target), each contributor (source) donates a bindu
# to signs that are at these distances (1-based) from the source planet.
AV_TABLES = {
    "sun": {
        "sun":     [1, 2, 4, 7, 8, 9, 10, 11],
        "moon":    [3, 6, 10, 11],
        "mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "mercury": [3, 5, 6, 9, 10, 11, 12],
        "jupiter": [5, 6, 9, 11],
        "venus":   [6, 7, 12],
        "saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "lagna":   [3, 4, 6, 10, 11, 12],
    },
    "moon": {
        "sun":     [3, 6, 7, 8, 10, 11],
        "moon":    [1, 3, 6, 7, 10, 11],
        "mars":    [2, 3, 5, 6, 9, 10, 11],
        "mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "jupiter": [1, 4, 7, 8, 10, 11, 12],
        "venus":   [3, 4, 5, 7, 9, 10, 11],
        "saturn":  [3, 5, 6, 11],
        "lagna":   [3, 6, 10, 11],
    },
    "mars": {
        "sun":     [3, 5, 6, 10, 11],
        "moon":    [3, 6, 11],
        "mars":    [1, 2, 4, 7, 8, 10, 11],
        "mercury": [3, 5, 6, 11],
        "jupiter": [6, 10, 11, 12],
        "venus":   [6, 8, 11, 12],
        "saturn":  [1, 4, 7, 8, 9, 10, 11],
        "lagna":   [1, 3, 6, 10, 11],
    },
    "mercury": {
        "sun":     [5, 6, 9, 11, 12],
        "moon":    [2, 4, 6, 8, 10, 11],
        "mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "jupiter": [6, 8, 11, 12],
        "venus":   [1, 2, 3, 4, 5, 8, 9, 11],
        "saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "lagna":   [1, 2, 4, 6, 8, 10, 11],
    },
    "jupiter": {
        "sun":     [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "moon":    [2, 5, 7, 9, 11],
        "mars":    [1, 2, 4, 7, 8, 10, 11],
        "mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "venus":   [2, 5, 6, 9, 10, 11],
        "saturn":  [3, 5, 6, 12],
        "lagna":   [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "venus": {
        "sun":     [8, 11, 12],
        "moon":    [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "mars":    [3, 5, 6, 9, 11, 12],
        "mercury": [3, 5, 6, 9, 11],
        "jupiter": [5, 8, 9, 10, 11],
        "venus":   [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "saturn":  [3, 4, 5, 8, 9, 10, 11],
        "lagna":   [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "saturn": {
        "sun":     [1, 2, 4, 7, 8, 10, 11],
        "moon":    [3, 6, 11],
        "mars":    [3, 5, 6, 10, 11, 12],
        "mercury": [6, 8, 9, 10, 11, 12],
        "jupiter": [5, 6, 11, 12],
        "venus":   [6, 11, 12],
        "saturn":  [3, 5, 6, 11],
        "lagna":   [1, 3, 4, 6, 10, 11],
    },
}

SIGN_MAP = {
    "Ari": 0, "Tau": 1, "Gem": 2, "Can": 3, "Leo": 4, "Vir": 5,
    "Lib": 6, "Sco": 7, "Sag": 8, "Cap": 9, "Aqu": 10, "Pis": 11,
    "Aries": 0, "Taurus": 1, "Gemini": 2, "Cancer": 3, "Leo": 4, "Virgo": 5,
    "Libra": 6, "Scorpio": 7, "Sagittarius": 8, "Capricorn": 9,
    "Aquarius": 10, "Pisces": 11,
}


def calculate_ashtakavarga(subject) -> dict:
    """
    Computes Bhinnashtakavarga (BAV) and Sarvashtakavarga (SAV).

    KEY FIX: BAV is stored by SIGN index (0-11, Aries=0).
    House values are then mapped as: H1 = Lagna sign, H2 = next sign, etc.
    This means bav[planet][sign_idx] = bindus for that sign.
    House H = bav[planet][(lagna_sign_idx + H - 1) % 12]
    """
    m = subject.model()

    # ── Collect natal sign indices ────────────────────────────────────────────
    positions = {}
    for p_key in ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']:
        sign_str = getattr(m, p_key).sign
        positions[p_key] = SIGN_MAP.get(sign_str, 0)

    lagna_idx = SIGN_MAP.get(m.ascendant.sign, 0)
    positions['lagna'] = lagna_idx

    # ── Step 1: Bhinnashtakavarga (BAV) per SIGN ─────────────────────────────
    # For each target planet, for each of the 12 signs:
    # check each contributor's position, compute distance, award bindu if in table.
    bav_by_sign = {p: [0] * 12 for p in AV_TABLES.keys()}

    for target_p, contributors in AV_TABLES.items():
        for sign_idx in range(12):              # sign_idx = candidate sign (0=Aries)
            total = 0
            for source_p, houses in contributors.items():
                source_sign = positions[source_p]
                # Distance from source planet to candidate sign (1-based, forward count)
                dist = (sign_idx - source_sign + 12) % 12 + 1
                if dist in houses:
                    total += 1
            bav_by_sign[target_p][sign_idx] = total

    # ── Step 2: Sarvashtakavarga (SAV) per SIGN ───────────────────────────────
    sav_by_sign = [
        sum(bav_by_sign[p][s] for p in AV_TABLES)
        for s in range(12)
    ]

    # ── Step 3: Map output ─────────────────────────────────────────────────────
    # IMPORTANT: Standard Parashara/Jagannath Hora outputs Ashtakavarga
    # numbered by SIGN (Aries=H1, Taurus=H2 ... Pisces=H12), NOT by Lagna house.
    # The read.txt reference values confirm: H1=Aries sign, H2=Taurus, etc.
    house_sav = {h: sav_by_sign[h - 1] for h in range(1, 13)}
    
    grand_total = sum(house_sav.values()) # Calculate sum before adding redundant keys
    
    # Add house_1 style keys for compatibility
    for h in range(1, 13):
        house_sav[f"house_{h}"] = sav_by_sign[h - 1]

    # Per-planet house bindus (same: sign-based, Aries=H1)
    bav_by_house = {}
    for planet, sign_arr in bav_by_sign.items():
        bav_by_house[planet] = {h: sign_arr[h - 1] for h in range(1, 13)}
        # Add house_1 style keys for compatibility
        for h in range(1, 13):
            bav_by_house[planet][f"house_{h}"] = sign_arr[h - 1]

    # Lagna-based house values (for transit & house analysis)
    lagna_house_sav = {}
    for h in range(1, 13):
        s_idx = (lagna_idx + h - 1) % 12
        lagna_house_sav[h] = sav_by_sign[s_idx]

    return {
        "sarvashtakavarga": house_sav,           # by sign (Aries=H1) — matches reference
        "sarvashtakavarga_lagna": lagna_house_sav, # by lagna house (H1=Lagna)
        "bhinnashtakavarga_by_house": bav_by_house, # by sign (Aries=H1)
        "bhinnashtakavarga": bav_by_sign,          # raw by sign index 0-11
        "lagna_idx": lagna_idx,
        "grand_total": grand_total,
    }


def format_ashtakavarga_for_ai(av_data: dict) -> str:
    """
    Formats Ashtakavarga summary for AI context injection.
    Includes both SAV totals and per-planet BAV for key houses.
    """
    sav = av_data["sarvashtakavarga"]
    bav = av_data.get("bhinnashtakavarga_by_house", {})
    grand = av_data.get("grand_total", sum(sav.values()))

    lines = [f"ASHTAKAVARGA (Grand Total: {grand}/337 ideal):"]

    # SAV line
    sav_parts = []
    for h in range(1, 13):
        pts = sav[h]
        if pts >= 30:
            qual = "Strong"
        elif pts >= 25:
            qual = "Moderate"
        else:
            qual = "Weak"
        sav_parts.append(f"H{h}:{pts}({qual})")
    lines.append("SAV: " + " | ".join(sav_parts))

    # Per-planet BAV for each house
    planet_order = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
    planet_labels = {"sun": "Sun", "moon": "Moon", "mars": "Mars",
                     "mercury": "Merc", "jupiter": "Jup", "venus": "Ven", "saturn": "Sat"}

    for planet in planet_order:
        if planet in bav:
            row = bav[planet]
            label = planet_labels[planet]
            row_str = " ".join(f"H{h}:{row[h]}" for h in range(1, 13))
            planet_total = sum(row[h] for h in range(1, 13))
            lines.append(f"{label}({planet_total}): {row_str}")

    return "\n".join(lines)
