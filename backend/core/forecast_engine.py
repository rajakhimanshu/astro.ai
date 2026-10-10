"""
core/forecast_engine.py — Horizon forecasts a practicing Jyotishi would deliver.

Horizons:
  life  — natal promise (yogas, vargas, karakas, current MD thesis)
  today — daily quality (PD + Tarabala/Chandrabala + kakshya + Moon house)
  30d   — week buckets + muhurta windows + PD shifts
  1y    — month grid + AD boundaries + Jupiter/Saturn + convergence
  5y    — phase map (MD/AD + Chara + slow ingresses) — no day precision

Deterministic engines score first; LLM only narrates these tables.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.astro_engine import calculate_vimshottari_dasha, get_sky_on_date, SIGNS
from core.user_profile_engine import load_user_profile, get_active_profile, SIGN_IDX
from core.transit_engine import abs_pos_to_house

VALID_HORIZONS = ("life", "today", "30d", "1y", "5y")

TOPIC_LABELS = {
    "career": "Career & Profession",
    "wealth": "Wealth & Finance",
    "marriage": "Marriage & Partnership",
    "health": "Health & Vitality",
    "education": "Education & Wisdom",
    "spiritual": "Spiritual Path",
}


def generate_12_month_forecast(user_id: Optional[str] = None) -> str:
    """Legacy text month-grid (kept for agent backward compatibility)."""
    data = generate_horizon_forecast(user_id, horizon="1y")
    return format_horizon_forecast(data.get("horizons", {}).get("1y", data))


def generate_horizon_forecast(
    user_id: Optional[str] = None,
    horizon: str = "all",
) -> Dict[str, Any]:
    """
    Build structured forecast for one horizon or all.
    horizon: life | today | 30d | 1y | 5y | all
    """
    try:
        profile = load_user_profile(user_id) if user_id else get_active_profile()
    except Exception as e:
        return {"status": "error", "error": str(e)}

    meta = profile.get("meta", {})
    name = meta.get("name", "Native")
    now = datetime.now()
    requested = horizon.lower().strip()
    targets = list(VALID_HORIZONS) if requested in ("all", "") else [requested]
    for h in targets:
        if h not in VALID_HORIZONS:
            return {"status": "error", "error": f"Unknown horizon '{h}'. Use: {', '.join(VALID_HORIZONS)}"}

    builders = {
        "life": _build_life,
        "today": _build_today,
        "30d": _build_30d,
        "1y": _build_1y,
        "5y": _build_5y,
    }

    horizons: Dict[str, Any] = {}
    for h in targets:
        try:
            horizons[h] = builders[h](profile, now)
        except Exception as e:
            horizons[h] = {
                "horizon": h,
                "error": str(e),
                "summary": f"Could not compute {h} forecast: {e}",
            }

    return {
        "status": "success",
        "user_id": user_id or meta.get("user_id"),
        "name": name,
        "as_of": now.isoformat(timespec="seconds"),
        "disclaimer": (
            "Scored from Vimshottari, gochara, Ashtakavarga, yogas, and convergence. "
            "Precision is gated — day-level claims only when signals agree."
        ),
        "horizons": horizons,
    }


def format_horizon_forecast(block: Dict[str, Any]) -> str:
    """Compact text for LLM context / reports."""
    if not block:
        return ""
    if block.get("error"):
        return f"[Forecast Error: {block['error']}]"

    h = block.get("horizon", "?")
    lines = [
        f"{'=' * 70}",
        f"FORECAST — {str(h).upper()} | Confidence {block.get('confidence', '?')}/100",
        f"Precision: {block.get('precision', 'themes')}",
        f"{'=' * 70}",
        block.get("summary", ""),
        "",
    ]

    if block.get("timing_rule"):
        lines.append(f"TIMING RULE: {block['timing_rule']}")
        lines.append("")

    for theme in block.get("themes", [])[:8]:
        lines.append(f"• {theme}")

    for key, title in (
        ("life_areas", "LIFE AREAS"),
        ("daily", "TODAY DETAIL"),
        ("weeks", "30-DAY WEEKS"),
        ("months", "12-MONTH GRID"),
        ("phases", "5-YEAR PHASES"),
        ("windows", "AUSPICIOUS WINDOWS"),
        ("signals", "KEY SIGNALS"),
    ):
        items = block.get(key)
        if not items:
            continue
        lines.append("")
        lines.append(title)
        if isinstance(items, dict):
            for k, v in items.items():
                if isinstance(v, dict):
                    lines.append(f"  {k}: {v.get('summary', v.get('verdict', str(v)[:120]))}")
                else:
                    lines.append(f"  {k}: {v}")
        elif isinstance(items, list):
            for item in items[:14]:
                if isinstance(item, dict):
                    label = item.get("label") or item.get("period") or item.get("month") or item.get("date") or ""
                    body = item.get("summary") or item.get("signal") or item.get("quality") or ""
                    conf = item.get("confidence")
                    conf_s = f" [{conf}]" if conf is not None else ""
                    lines.append(f"  {label}{conf_s}: {body}")
                else:
                    lines.append(f"  {item}")

    return "\n".join(lines).strip()


def format_all_horizons_for_agent(forecast: Dict[str, Any]) -> str:
    if forecast.get("status") != "success":
        return f"[Forecast Error: {forecast.get('error', 'unknown')}]"
    parts = [f"MASTER HORIZON FORECAST FOR {forecast.get('name', '').upper()}"]
    for h in VALID_HORIZONS:
        block = forecast.get("horizons", {}).get(h)
        if block:
            parts.append(format_horizon_forecast(block))
    return "\n\n".join(parts)


# ── helpers ───────────────────────────────────────────────────────────────────

def _birth_dt(profile: dict) -> datetime:
    b = profile["meta"]["birth"]
    return datetime(b["year"], b["month"], b["day"], b["hour"], b["minute"])


def _dasha_at(profile: dict, target: datetime) -> dict:
    return calculate_vimshottari_dasha(
        _birth_dt(profile),
        profile["planets"]["Moon"]["abs_pos"],
        target_dt=target,
    )


def _sav(profile: dict, house: int) -> int:
    sav = profile.get("ashtakavarga", {}).get("sarvashtakavarga", {})
    return int(sav.get(house, sav.get(str(house), 25)))


def _sky_houses(profile: dict, dt: datetime) -> Dict[str, int]:
    birth = profile["meta"]["birth"]
    lagna_idx = SIGN_IDX.get(profile["lagna"]["sign"], 0)
    sky = get_sky_on_date(
        dt.year, dt.month, dt.day, 12, 0,
        birth.get("city", "Delhi"), birth.get("nation", "IN"),
    )
    m = sky.model()
    return {
        "Sun": abs_pos_to_house(m.sun.abs_pos, lagna_idx),
        "Moon": abs_pos_to_house(m.moon.abs_pos, lagna_idx),
        "Mars": abs_pos_to_house(m.mars.abs_pos, lagna_idx),
        "Mercury": abs_pos_to_house(m.mercury.abs_pos, lagna_idx),
        "Jupiter": abs_pos_to_house(m.jupiter.abs_pos, lagna_idx),
        "Venus": abs_pos_to_house(m.venus.abs_pos, lagna_idx),
        "Saturn": abs_pos_to_house(m.saturn.abs_pos, lagna_idx),
        "Rahu": abs_pos_to_house(m.true_north_lunar_node.abs_pos, lagna_idx),
        "Ketu": abs_pos_to_house(m.true_south_lunar_node.abs_pos, lagna_idx),
        "_jupiter_sign": m.jupiter.sign,
        "_saturn_sign": m.saturn.sign,
        "_moon_sign": m.moon.sign,
    }


def _confidence_from_convergence(conv: dict) -> int:
    return int(conv.get("confidence", 40))


def _precision_for(horizon: str, conv: dict) -> str:
    if horizon == "life":
        return "natal_themes"
    if horizon == "5y":
        return "year_phases"
    if horizon == "1y":
        return "month_themes" if conv.get("can_predict_timing") else "quarter_themes"
    if horizon == "30d":
        return "week_windows" if conv.get("can_predict_timing") else "period_themes"
    if horizon == "today":
        return "daily_quality" if conv.get("can_predict_timing") else "daily_themes_only"
    return "themes"


def _score_day_quality(gochara: dict, houses: dict, dasha: dict, profile: dict) -> Dict[str, Any]:
    score = int(gochara.get("overall_score", 0))
    flags: List[str] = []

    moon_h = houses.get("Moon", 1)
    if moon_h in (1, 3, 6, 7, 10, 11):
        score += 2
        flags.append(f"Moon favourably placed in H{moon_h}")
    elif moon_h in (8, 12):
        score -= 2
        flags.append(f"Moon in sensitive H{moon_h}")

    jup_h = houses.get("Jupiter", 1)
    jup_sav = _sav(profile, jup_h)
    if jup_h in (1, 5, 9, 10, 11) and jup_sav >= 28:
        score += 2
        flags.append(f"Jupiter supports from H{jup_h} (SAV {jup_sav})")

    sat_h = houses.get("Saturn", 1)
    if sat_h in (6, 8, 12) and _sav(profile, sat_h) < 25:
        score -= 2
        flags.append(f"Saturn pressure in H{sat_h}")

    if "error" not in dasha:
        pd = dasha.get("current_pratyantardasha", {}).get("lord", "")
        if pd:
            flags.append(f"Active PD: {pd}")

    if score >= 6:
        quality = "AUSPICIOUS"
    elif score >= 2:
        quality = "SUPPORTIVE"
    elif score >= -1:
        quality = "MIXED"
    else:
        quality = "CAUTION"

    return {"score": score, "quality": quality, "flags": flags}


def _life_area_snapshot(profile: dict, topic: str) -> dict:
    from core.convergence_scorer import score_convergence
    conv = score_convergence(profile, topic=topic)
    yogas = [
        y.get("name", "")
        for y in profile.get("yogas", [])
        if y.get("name")
    ][:4]
    return {
        "topic": topic,
        "label": TOPIC_LABELS.get(topic, topic),
        "confidence": conv["confidence"],
        "can_time": conv["can_predict_timing"],
        "summary": conv["timing_rule"],
        "signals": [
            f"{s['signal']}: {s['detail'][:100]}"
            for s in conv["signals"] if s.get("active")
        ][:4],
        "yogas_hint": yogas,
        "verdict": (
            "Strong natal promise"
            if conv["confidence"] >= 55
            else ("Mixed natal promise" if conv["confidence"] >= 35 else "Needs remedies / patience")
        ),
    }


# ── horizon builders ──────────────────────────────────────────────────────────

def _build_life(profile: dict, now: datetime) -> dict:
    from core.convergence_scorer import score_convergence

    dasha = _dasha_at(profile, now)
    md = dasha.get("current_mahadasha", {}).get("lord", "?") if "error" not in dasha else "?"
    ad = dasha.get("current_antardasha", {}).get("lord", "?") if "error" not in dasha else "?"

    areas = {
        t: _life_area_snapshot(profile, t)
        for t in ("career", "wealth", "marriage", "health", "spiritual")
    }

    yogas = [
        {"name": y.get("name"), "effect": y.get("effect", y.get("description", ""))[:160]}
        for y in profile.get("yogas", [])[:8]
    ]

    d9 = profile.get("divisional_charts", {}).get("9", {})
    d10 = profile.get("divisional_charts", {}).get("10", {})
    conv = score_convergence(profile, topic="general")

    karakas = profile.get("karakas", {}) or profile.get("chara_karakas", {})
    themes = [
        f"Current life chapter: {md} Mahadasha / {ad} Antardasha",
        f"Lagna {profile['lagna']['sign']} | Moon {profile['planets']['Moon']['sign']} "
        f"({profile['planets']['Moon'].get('nakshatra', '')})",
    ]
    if yogas:
        themes.append("Key yogas: " + ", ".join(y["name"] for y in yogas[:4] if y.get("name")))

    strong = [a["label"] for a in areas.values() if a["confidence"] >= 55]
    weak = [a["label"] for a in areas.values() if a["confidence"] < 35]
    if strong:
        themes.append("Strong natal support: " + ", ".join(strong))
    if weak:
        themes.append("Areas needing care: " + ", ".join(weak))

    return {
        "horizon": "life",
        "title": "Life Overview (Natal Promise)",
        "confidence": _confidence_from_convergence(conv),
        "precision": _precision_for("life", conv),
        "timing_rule": "LIFE_THESIS: Speak natal promise and current MD chapter — not transit dates.",
        "summary": (
            f"Your chart's core thesis under {md}/{ad}. "
            "This is what the kundali promises — timing comes from dasha + gochara separately."
        ),
        "themes": themes,
        "life_areas": areas,
        "yogas": yogas,
        "current_dasha": {"md": md, "ad": ad, "summary": dasha.get("summary", "")},
        "varga_notes": {
            "D9_navamsa": f"{len(d9)} planets mapped" if d9 else "D9 not loaded",
            "D10_dasamsa": f"{len(d10)} planets mapped" if d10 else "D10 not loaded",
        },
        "karakas": karakas if isinstance(karakas, dict) else {},
        "signals": [
            {"label": s["signal"], "summary": s["detail"], "active": s["active"]}
            for s in conv["signals"]
        ],
    }


def _build_today(profile: dict, now: datetime) -> dict:
    from core.convergence_scorer import score_convergence
    from core.gochara_bala_engine import analyze_gochara_bala
    from core.kakshya_engine import analyze_transit_kakshyas

    dasha = _dasha_at(profile, now)
    gochara = analyze_gochara_bala(profile, target_dt=now)
    try:
        kakshya = analyze_transit_kakshyas(profile, target_dt=now)
    except Exception as e:
        kakshya = {"error": str(e), "results": []}

    houses = _sky_houses(profile, now)
    day = _score_day_quality(gochara, houses, dasha, profile)
    conv = score_convergence(profile, topic="forecast", target_dt=now)

    md = dasha.get("current_mahadasha", {}).get("lord", "?") if "error" not in dasha else "?"
    ad = dasha.get("current_antardasha", {}).get("lord", "?") if "error" not in dasha else "?"
    pd = dasha.get("current_pratyantardasha", {}).get("lord", "?") if "error" not in dasha else "?"

    kakshya_hits = []
    for r in (kakshya.get("transits") or kakshya.get("results") or kakshya.get("planets") or [])[:5]:
        if isinstance(r, dict):
            kakshya_hits.append(
                f"{r.get('planet', '?')}: {r.get('verdict', r.get('quality', ''))[:90]}"
            )

    themes = [
        f"Day quality: {day['quality']} (score {day['score']})",
        f"Dasha clock: {md} MD / {ad} AD / {pd} PD",
        f"Moon in natal H{houses.get('Moon')} ({houses.get('_moon_sign', '')})",
        f"Jupiter H{houses.get('Jupiter')} | Saturn H{houses.get('Saturn')} | Rahu H{houses.get('Rahu')}",
        gochara.get("recommendation", ""),
    ] + day["flags"][:3]

    return {
        "horizon": "today",
        "title": f"Today — {now.strftime('%A, %d %b %Y')}",
        "confidence": min(100, (_confidence_from_convergence(conv) + max(0, day["score"] * 3)) // 1),
        "precision": _precision_for("today", conv),
        "timing_rule": conv.get("timing_rule"),
        "summary": (
            f"Today is {day['quality'].lower()}. "
            f"Operate under {pd} Pratyantardasha with Moon activating house {houses.get('Moon')}."
        ),
        "themes": [t for t in themes if t],
        "daily": {
            "quality": day["quality"],
            "score": day["score"],
            "dasha": f"{md}/{ad}/{pd}",
            "moon_house": houses.get("Moon"),
            "jupiter_house": houses.get("Jupiter"),
            "saturn_house": houses.get("Saturn"),
            "gochara_recommendation": gochara.get("recommendation"),
            "kakshya": kakshya_hits,
            "do": _today_do(day["quality"]),
            "avoid": _today_avoid(day["quality"]),
        },
        "signals": day["flags"],
    }


def _today_do(quality: str) -> List[str]:
    if quality == "AUSPICIOUS":
        return ["Important conversations", "Payments / proposals", "Spiritual practice"]
    if quality == "SUPPORTIVE":
        return ["Steady work", "Networking", "Health routines"]
    if quality == "MIXED":
        return ["Finish pending tasks", "Review plans", "Quiet focus work"]
    return ["Rest and review", "Remedial mantra / charity", "Avoid forcing outcomes"]


def _today_avoid(quality: str) -> List[str]:
    if quality in ("AUSPICIOUS", "SUPPORTIVE"):
        return ["Unnecessary conflict", "Over-promising"]
    return ["New partnerships", "Large financial risk", "Confrontations"]


def _build_30d(profile: dict, now: datetime) -> dict:
    from core.convergence_scorer import score_convergence
    from core.gochara_bala_engine import analyze_gochara_bala
    from core.muhurta_engine import calculate_muhurta_score
    import swisseph as swe

    conv = score_convergence(profile, topic="forecast", target_dt=now)
    birth = profile["meta"]["birth"]
    natal_chart = {
        "lat": birth.get("lat", 28.6),
        "lon": birth.get("lon", 77.2),
        "moon_abs": profile["planets"]["Moon"]["abs_pos"],
    }

    weeks: List[dict] = []
    windows: List[dict] = []
    prev_pd = None

    for week in range(4):
        start = now + timedelta(days=week * 7)
        mid = start + timedelta(days=3)
        dasha = _dasha_at(profile, mid)
        gochara = analyze_gochara_bala(profile, target_dt=mid)
        houses = _sky_houses(profile, mid)
        day = _score_day_quality(gochara, houses, dasha, profile)
        pd = dasha.get("current_pratyantardasha", {}).get("lord", "?") if "error" not in dasha else "?"
        md = dasha.get("current_mahadasha", {}).get("lord", "?") if "error" not in dasha else "?"
        ad = dasha.get("current_antardasha", {}).get("lord", "?") if "error" not in dasha else "?"

        pd_note = ""
        if prev_pd and pd != prev_pd:
            pd_note = f"PD shifts to {pd}"
        prev_pd = pd

        end = start + timedelta(days=6)
        weeks.append({
            "label": f"Week {week + 1} ({start.strftime('%d %b')}–{end.strftime('%d %b')})",
            "period": f"{start.date()} → {end.date()}",
            "quality": day["quality"],
            "confidence": max(20, min(90, 50 + day["score"] * 4)),
            "summary": (
                f"{day['quality']} — {md}/{ad}/{pd}. "
                f"Moon H{houses.get('Moon')}, Ju H{houses.get('Jupiter')}, Sa H{houses.get('Saturn')}."
                + (f" {pd_note}." if pd_note else "")
            ),
            "dasha": f"{md}/{ad}/{pd}",
        })

    # Daily muhurta scan for best/worst windows
    best_days: List[dict] = []
    for d in range(0, 30):
        dt = now + timedelta(days=d)
        try:
            jd = swe.julday(dt.year, dt.month, dt.day, 12.0)
            m = calculate_muhurta_score(jd, natal_chart, purpose="general")
            if m["score"] >= 4:
                best_days.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "label": dt.strftime("%a %d %b"),
                    "quality": m["quality"],
                    "score": m["score"],
                    "summary": ", ".join(m["flags"][:3]),
                })
        except Exception:
            continue
    best_days.sort(key=lambda x: -x["score"])
    windows = best_days[:8]

    qualities = [w["quality"] for w in weeks]
    overall = (
        "Generally supportive month"
        if qualities.count("AUSPICIOUS") + qualities.count("SUPPORTIVE") >= 2
        else "Mixed month — pick windows carefully"
    )

    return {
        "horizon": "30d",
        "title": "Next 30 Days",
        "confidence": _confidence_from_convergence(conv),
        "precision": _precision_for("30d", conv),
        "timing_rule": conv.get("timing_rule"),
        "summary": overall + ". Use auspicious windows for launches; caution weeks for planning only.",
        "themes": [
            weeks[0]["summary"] if weeks else "Scan unavailable",
            f"{len(windows)} strong muhurta days in the next month",
        ],
        "weeks": weeks,
        "windows": windows,
        "best_day": windows[0] if windows else None,
        "signals": [f"{w['label']}: {w['quality']}" for w in weeks],
    }


def _build_1y(profile: dict, now: datetime) -> dict:
    from core.convergence_scorer import score_convergence

    conv = score_convergence(profile, topic="forecast", target_dt=now)
    months: List[dict] = []
    birth = profile["meta"]["birth"]
    city = birth.get("city", "Delhi")
    nation = birth.get("nation", "IN")
    lagna_idx = SIGN_IDX.get(profile["lagna"]["sign"], 0)

    prev_ad = None
    ad_changes: List[str] = []

    for i in range(12):
        target = now + timedelta(days=30 * i + 15)
        month_str = target.strftime("%B %Y")
        dasha = _dasha_at(profile, target)
        if "error" in dasha:
            months.append({"month": month_str, "label": month_str, "summary": "Dasha unavailable", "confidence": 0})
            continue

        md = dasha["current_mahadasha"]["lord"]
        ad = dasha["current_antardasha"]["lord"]
        pd = dasha["current_pratyantardasha"]["lord"]

        if prev_ad and ad != prev_ad:
            ad_changes.append(f"{month_str}: AD → {ad}")
        prev_ad = ad

        try:
            sky = get_sky_on_date(target.year, target.month, target.day, 12, 0, city, nation)
            m = sky.model()
            jup_h = abs_pos_to_house(m.jupiter.abs_pos, lagna_idx)
            sat_h = abs_pos_to_house(m.saturn.abs_pos, lagna_idx)
            rah_h = abs_pos_to_house(m.true_north_lunar_node.abs_pos, lagna_idx)
            sun_h = abs_pos_to_house(m.sun.abs_pos, lagna_idx)
            jup_sav = _sav(profile, jup_h)
            sat_sav = _sav(profile, sat_h)

            signals = []
            score = 40
            if jup_h in (1, 5, 9, 10, 11) and jup_sav >= 28:
                signals.append("Jupiter growth")
                score += 15
            if sat_h in (6, 8, 12) and sat_sav < 25:
                signals.append("Saturn tests")
                score -= 12
            if sun_h in (10, 11):
                signals.append("Career/solar focus")
                score += 8
            if sat_h in (3, 6, 11):
                signals.append("Saturn constructive")
                score += 6

            quality = "SUPPORTIVE" if score >= 50 else ("MIXED" if score >= 35 else "CAUTION")
            months.append({
                "month": month_str,
                "label": month_str,
                "dasha": f"{md}/{ad}/{pd}",
                "quality": quality,
                "confidence": max(15, min(90, score)),
                "summary": (
                    f"{quality} — {md}/{ad}/{pd}. "
                    f"Ju H{jup_h}(SAV{jup_sav}) Sa H{sat_h}(SAV{sat_sav}) Ra H{rah_h}. "
                    + ("; ".join(signals) if signals else "Steady period")
                ),
                "transits": {
                    "jupiter_house": jup_h,
                    "saturn_house": sat_h,
                    "rahu_house": rah_h,
                    "sun_house": sun_h,
                },
                "signal": "; ".join(signals) if signals else "Steady",
            })
        except Exception as e:
            months.append({
                "month": month_str,
                "label": month_str,
                "summary": f"Transit unavailable: {e}",
                "confidence": 0,
            })

    # Tajika / Varshaphal hint
    tajika_note = ""
    try:
        age = now.year - birth["year"]
        if (now.month, now.day) < (birth["month"], birth["day"]):
            age -= 1
        muntha_idx = (SIGN_IDX.get(profile["lagna"]["sign"], 0) + age) % 12
        tajika_note = f"Muntha in {SIGNS[muntha_idx]} (age {age}) — annual karmic focus sign."
    except Exception:
        tajika_note = ""

    supportive = sum(1 for m in months if m.get("quality") == "SUPPORTIVE")
    return {
        "horizon": "1y",
        "title": "Next 12 Months",
        "confidence": _confidence_from_convergence(conv),
        "precision": _precision_for("1y", conv),
        "timing_rule": conv.get("timing_rule"),
        "summary": (
            f"{supportive}/12 months lean supportive. "
            + (f"AD shifts: {', '.join(ad_changes[:3])}. " if ad_changes else "")
            + tajika_note
        ),
        "themes": [
            months[0]["summary"] if months else "",
            tajika_note,
            f"Antardasha changes: {len(ad_changes)}",
        ],
        "months": months,
        "ad_changes": ad_changes,
        "signals": [m["summary"] for m in months if m.get("quality") in ("SUPPORTIVE", "CAUTION")][:6],
    }


def _build_5y(profile: dict, now: datetime) -> dict:
    from core.convergence_scorer import score_convergence

    conv = score_convergence(profile, topic="forecast", target_dt=now)
    phases: List[dict] = []
    birth = profile["meta"]["birth"]
    city = birth.get("city", "Delhi")
    nation = birth.get("nation", "IN")
    lagna_idx = SIGN_IDX.get(profile["lagna"]["sign"], 0)

    chara = profile.get("chara_dasha", {})
    chara_md = (chara.get("current_md") or {}).get("sign", "")

    prev_jup_sign = None
    prev_sat_sign = None

    for year_offset in range(5):
        # Mid-year sample
        target = datetime(now.year + year_offset, 7, 1, 12, 0)
        if year_offset == 0:
            target = now + timedelta(days=180)

        dasha = _dasha_at(profile, target)
        md = dasha.get("current_mahadasha", {}).get("lord", "?") if "error" not in dasha else "?"
        ad = dasha.get("current_antardasha", {}).get("lord", "?") if "error" not in dasha else "?"
        md_end = dasha.get("current_mahadasha", {}).get("end", "") if "error" not in dasha else ""

        ingress_notes = []
        try:
            sky = get_sky_on_date(target.year, target.month, target.day, 12, 0, city, nation)
            m = sky.model()
            jup_sign = m.jupiter.sign
            sat_sign = m.saturn.sign
            jup_h = abs_pos_to_house(m.jupiter.abs_pos, lagna_idx)
            sat_h = abs_pos_to_house(m.saturn.abs_pos, lagna_idx)

            if prev_jup_sign and jup_sign != prev_jup_sign:
                ingress_notes.append(f"Jupiter enters {jup_sign}")
            if prev_sat_sign and sat_sign != prev_sat_sign:
                ingress_notes.append(f"Saturn enters {sat_sign}")
            prev_jup_sign = jup_sign
            prev_sat_sign = sat_sign

            score = 45
            themes = []
            if jup_h in (1, 5, 9, 10, 11):
                themes.append(f"Jupiter in H{jup_h} supports expansion")
                score += 12
            if sat_h in (6, 8, 12):
                themes.append(f"Saturn in H{sat_h} demands discipline")
                score -= 8
            elif sat_h in (3, 6, 11):
                themes.append(f"Saturn in H{sat_h} can yield results with effort")
                score += 6

            quality = "GROWTH" if score >= 55 else ("BUILD" if score >= 40 else "TEST")
            year_label = str(now.year + year_offset)
            phases.append({
                "label": year_label,
                "period": year_label,
                "quality": quality,
                "confidence": max(25, min(85, score)),
                "dasha": f"{md}/{ad}",
                "summary": (
                    f"{quality} year under {md} MD / {ad} AD. "
                    f"Ju {jup_sign} H{jup_h}, Sa {sat_sign} H{sat_h}. "
                    + (" ".join(themes) if themes else "")
                    + ((" | " + "; ".join(ingress_notes)) if ingress_notes else "")
                ),
                "md_end": str(md_end)[:10] if md_end else "",
                "signal": "; ".join(ingress_notes + themes[:2]) or f"{md}/{ad} chapter",
            })
        except Exception as e:
            phases.append({
                "label": str(now.year + year_offset),
                "period": str(now.year + year_offset),
                "summary": f"Phase unavailable: {e}",
                "confidence": 0,
            })

    return {
        "horizon": "5y",
        "title": "Next 5 Years (Phase Map)",
        "confidence": _confidence_from_convergence(conv),
        "precision": _precision_for("5y", conv),
        "timing_rule": (
            "PHASE_MAP_ONLY: Speak in years and dasha chapters. "
            "Never invent month-level dates for a 5-year view."
        ),
        "summary": (
            f"Five-year arc shaped by Vimshottari MD/AD"
            + (f" and Chara MD in {chara_md}" if chara_md else "")
            + ". Use year phases for direction; zoom to 1y/30d for timing."
        ),
        "themes": [p["summary"] for p in phases[:3]],
        "phases": phases,
        "chara_dasha_hint": chara_md,
        "signals": [p.get("signal", "") for p in phases if p.get("signal")],
    }
