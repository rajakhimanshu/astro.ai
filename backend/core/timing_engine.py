"""
core/timing_engine.py
────────────────────────────────────────────────────────────────────────
Topic-specific future timing scanner.

Walks the Vimshottari MD/AD/PD timeline month by month over a horizon and
scores every month for one life topic by combining:
  • Dasha-lord significance for the topic — house ownership, placement,
    graha drishti, conjunction with the topic lord, nakshatra (star) lord,
    karaka role and placement in the topic's divisional chart
  • MD ↔ AD lord mutual position (6/8 and 2/12 penalties)
  • Jupiter + Saturn double transit over the topic house or its lord,
    from Lagna and from the Moon
  • Sarvashtakavarga support for the transited signs
Consecutive strong months are merged into ranked windows so the LLM only
narrates timing the engine actually found.
────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from dateutil.relativedelta import relativedelta

from core.astro_engine import calculate_vimshottari_dasha, get_sidereal_sign_idx, SIGNS
from core.convergence_scorer import TOPIC_MAP, detect_topic, _natal_promise
from core.user_profile_engine import SIGN_IDX, SIGN_LORDS

PRIMARY_HOUSE = {
    "career": 10, "wealth": 11, "marriage": 7, "health": 1, "education": 4,
    "children": 5, "spiritual": 9, "forecast": 10, "general": 1,
}

# Whole-sign graha drishti, counted inclusively from the planet's own sign.
ASPECTS = {
    "Mars": (4, 7, 8), "Jupiter": (5, 7, 9), "Saturn": (3, 7, 10),
    "Rahu": (5, 7, 9), "Ketu": (5, 7, 9),
}
STRONG_VARGA_HOUSES = {1, 4, 5, 7, 9, 10}
# Raw significance points a fully wired dasha lord realistically reaches (mapped to 10).
SIGNIFICANCE_FULL_SCALE = 7.0
ACTIVE_MONTH_SCORE = 6.0


def _aspected_houses(planet: str, house: int) -> set:
    return {(house - 1 + off - 1) % 12 + 1 for off in ASPECTS.get(planet, (7,))}


def _influences(planet: str, from_sign: int, target_sign: int) -> bool:
    """True if a planet in from_sign occupies or aspects target_sign."""
    count = (target_sign - from_sign) % 12 + 1
    return count == 1 or count in ASPECTS.get(planet, (7,))


def _owned_houses(profile: dict, planet: str) -> List[int]:
    return [int(h) for h, info in profile.get("houses", {}).items() if info.get("lord") == planet]


def _sav(profile: dict, house: int) -> int:
    sav = profile.get("ashtakavarga", {}).get("sarvashtakavarga", {})
    return int(sav.get(str(house), sav.get(house, 28)))


def _planet_significance(
    profile: dict, planet: str, topic: str, cfg: dict, primary: int, depth: int = 0
) -> Tuple[float, List[str]]:
    """How strongly a dasha lord is wired to the topic (0-10) plus the reasons."""
    planets = profile.get("planets", {})
    pdata = planets.get(planet) or {}
    house = pdata.get("house")
    topic_houses = set(cfg["houses"])
    owned = _owned_houses(profile, planet)
    primary_lord = profile.get("houses", {}).get(str(primary), {}).get("lord")

    score, reasons = 0.0, []
    if primary in owned:
        score += 3
        reasons.append(f"rules H{primary}")
    other_owned = sorted(h for h in owned if h in topic_houses and h != primary)
    if other_owned:
        score += 1.5
        reasons.append("rules " + "/".join(f"H{h}" for h in other_owned))

    if house == primary:
        score += 3
        reasons.append(f"sits in H{primary}")
    elif house in topic_houses:
        score += 2
        reasons.append(f"sits in H{house}")

    if house and house != primary and primary in _aspected_houses(planet, house):
        score += 1.5
        reasons.append(f"aspects H{primary}")

    if primary_lord and planet != primary_lord and planets.get(primary_lord, {}).get("house") == house:
        score += 1
        reasons.append(f"conjoins H{primary} lord {primary_lord}")

    star_lord = pdata.get("nakshatra_lord")
    if star_lord and star_lord != planet:
        sl_house = planets.get(star_lord, {}).get("house")
        if sl_house in topic_houses or set(_owned_houses(profile, star_lord)) & topic_houses:
            score += 1.5
            reasons.append(f"star-lord {star_lord} links topic houses")

    if planet in cfg["karakas"]:
        score += 1
        reasons.append("natural karaka")

    varga_key = cfg.get("varga_key")
    varga = profile.get("divisional_charts", {}).get(varga_key, {}).get(planet)
    if varga and varga.get("house") in STRONG_VARGA_HOUSES:
        score += 1
        reasons.append(f"strong in D{varga_key} (H{varga['house']})")

    if planet in ("Rahu", "Ketu") and depth == 0:
        dispositor = SIGN_LORDS.get(pdata.get("sign", ""))
        if dispositor:
            d_score, _ = _planet_significance(profile, dispositor, topic, cfg, primary, depth=1)
            d_raw = d_score * SIGNIFICANCE_FULL_SCALE / 10
            if d_raw >= 3:
                score += d_raw * 0.5
                reasons.append(f"carries dispositor {dispositor}")

    if topic != "health" and house in (6, 8, 12) and house not in topic_houses:
        score -= 1
        reasons.append(f"obstructed from H{house}")

    return max(0.0, min(10.0, score * 10 / SIGNIFICANCE_FULL_SCALE)), reasons


def _lord_relationship(profile: dict, md: str, ad: str) -> Tuple[float, Optional[str]]:
    planets = profile.get("planets", {})
    h_md, h_ad = planets.get(md, {}).get("house"), planets.get(ad, {}).get("house")
    if not h_md or not h_ad or md == ad:
        return 0.0, None
    count = (h_ad - h_md) % 12 + 1
    if count in (6, 8):
        return -1.0, f"{md}/{ad} in 6-8 from each other (friction)"
    if count in (2, 12):
        return -0.5, f"{md}/{ad} in 2-12 from each other"
    if count in (1, 4, 5, 7, 9, 10):
        return 0.5, f"{md}/{ad} mutually supportive"
    return 0.0, None


def _flatten_pratyantardashas(profile: dict) -> List[dict]:
    birth = profile["meta"]["birth"]
    birth_dt = datetime(
        int(birth["year"]), int(birth["month"]), int(birth["day"]),
        int(birth["hour"]), int(birth["minute"]),
    )
    dasha = calculate_vimshottari_dasha(birth_dt, profile["planets"]["Moon"]["abs_pos"])
    periods = []
    for md in dasha.get("full_timeline", []):
        for ad in md.get("antardashas", []):
            for pd in ad.get("pratyantardashas", []):
                periods.append({
                    "start": datetime.fromisoformat(pd["start"]),
                    "end": datetime.fromisoformat(pd["end"]),
                    "md": md["lord"], "ad": ad["lord"], "pd": pd["lord"],
                })
    return periods


def _period_at(periods: List[dict], when: datetime) -> Optional[dict]:
    for p in periods:
        if p["start"] <= when < p["end"]:
            return p
    return None


def _transit_score(profile: dict, when: datetime, primary: int) -> Tuple[float, List[str], bool]:
    """Jupiter/Saturn double-transit score (0-10), notes, and whether a double transit is live."""
    planets = profile.get("planets", {})
    lagna_idx = SIGN_IDX[profile["lagna"]["sign"]]
    moon_idx = SIGN_IDX[planets["Moon"]["sign"]]
    primary_lord = profile.get("houses", {}).get(str(primary), {}).get("lord")
    lord_sign = planets.get(primary_lord, {}).get("sign")

    lagna_targets = {(lagna_idx + primary - 1) % 12}
    if lord_sign:
        lagna_targets.add(SIGN_IDX[lord_sign])
    moon_target = (moon_idx + primary - 1) % 12

    jup = get_sidereal_sign_idx(when, "Jupiter")
    sat = get_sidereal_sign_idx(when, "Saturn")
    jup_hit = any(_influences("Jupiter", jup, t) for t in lagna_targets)
    sat_hit = any(_influences("Saturn", sat, t) for t in lagna_targets)

    raw, notes = 0.0, []
    double = jup_hit and sat_hit
    if double:
        raw += 4
        notes.append(f"Jupiter+Saturn double transit on H{primary}/its lord")
    elif jup_hit:
        raw += 1.5
        notes.append(f"Jupiter activates H{primary}/its lord")
    elif sat_hit:
        raw += 1
        notes.append(f"Saturn activates H{primary}/its lord")

    if _influences("Jupiter", jup, moon_target) and _influences("Saturn", sat, moon_target):
        raw += 1.5
        notes.append(f"double transit also from Moon (H{primary} from Moon)")

    jup_house = (jup - lagna_idx) % 12 + 1
    sat_house = (sat - lagna_idx) % 12 + 1
    if _sav(profile, jup_house) >= 28:
        raw += 1
        notes.append(f"Jupiter in strong SAV sign (H{jup_house}, {_sav(profile, jup_house)})")
    if sat_house == primary and _sav(profile, primary) < 25:
        raw -= 1
        notes.append(f"Saturn presses a weak H{primary} (SAV {_sav(profile, primary)})")

    return max(0.0, min(10.0, raw * 10 / 6.5)), notes, double


def scan_timing_windows(
    profile: dict,
    topic: str = "general",
    question: str = "",
    years: int = 3,
    start: Optional[datetime] = None,
) -> Dict:
    """Month-by-month scan for one topic; returns ranked windows and the monthly table."""
    if topic == "general" and question:
        topic = detect_topic(question)
    if topic == "general":
        topic = "forecast"
    cfg = TOPIC_MAP.get(topic, TOPIC_MAP["forecast"])
    primary = PRIMARY_HOUSE.get(topic, 1)
    promise = _natal_promise(profile, cfg)
    periods = _flatten_pratyantardashas(profile)

    sig_cache: Dict[str, Tuple[float, List[str]]] = {}

    def sig(planet: str) -> Tuple[float, List[str]]:
        if planet not in sig_cache:
            sig_cache[planet] = _planet_significance(profile, planet, topic, cfg, primary)
        return sig_cache[planet]

    first = (start or datetime.now()).replace(day=15, hour=12, minute=0, second=0, microsecond=0)
    months = []
    for i in range(max(1, years) * 12):
        when = first + relativedelta(months=i)
        period = _period_at(periods, when)
        if not period:
            continue
        md_s, _ = sig(period["md"])
        ad_s, _ = sig(period["ad"])
        pd_s, _ = sig(period["pd"])
        rel, rel_note = _lord_relationship(profile, period["md"], period["ad"])
        dasha_score = max(0.0, min(10.0, 0.35 * md_s + 0.45 * ad_s + 0.20 * pd_s + rel))
        transit, t_notes, double = _transit_score(profile, when, primary)
        score = 0.6 * dasha_score + 0.4 * transit
        if not promise["active"]:
            score *= 0.85
        months.append({
            "month": when.strftime("%Y-%m"),
            "label": when.strftime("%b %Y"),
            "dasha": f"{period['md']}/{period['ad']}/{period['pd']}",
            "md": period["md"], "ad": period["ad"], "pd": period["pd"],
            "dasha_score": round(dasha_score, 1),
            "transit_score": round(transit, 1),
            "score": round(score, 1),
            "double_transit": double,
            "notes": ([rel_note] if rel_note else []) + t_notes,
            "active": score >= ACTIVE_MONTH_SCORE and dasha_score >= 5 and transit > 0,
        })

    windows = []
    run: List[dict] = []
    for m in months + [{"active": False}]:
        if m.get("active"):
            run.append(m)
            continue
        if run:
            windows.append(_build_window(run, sig, promise["active"], profile))
            run = []
    windows.sort(key=lambda w: (w["peak"], w["mean"]), reverse=True)

    return {
        "topic": topic,
        "label": cfg["label"],
        "primary_house": primary,
        "horizon_years": years,
        "natal_promise": {"active": promise["active"], "detail": promise["detail"]},
        "birth_time_confidence": profile.get("meta", {}).get("rectification", {}).get("confidence_label", "unverified"),
        "windows": windows[:5],
        "best_months": sorted(months, key=lambda m: m["score"], reverse=True)[:3],
        "months": months,
    }


def _build_window(run: List[dict], sig, promise_active: bool, profile: dict) -> Dict:
    peak_month = max(run, key=lambda m: m["score"])
    peak = peak_month["score"]
    mean = sum(m["score"] for m in run) / len(run)
    has_double = any(m["double_transit"] for m in run)

    if peak >= 7.5 and has_double and promise_active:
        confidence = "HIGH"
    elif peak >= 6.5:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    if profile.get("meta", {}).get("rectification", {}).get("confidence_label") == "low":
        confidence = {"HIGH": "MEDIUM", "MEDIUM": "LOW"}.get(confidence, "LOW")

    reasons = []
    for role in ("ad", "md", "pd"):
        lord = peak_month[role]
        _, why = sig(lord)
        if why:
            reasons.append(f"{role.upper()} {lord}: {', '.join(why[:3])}")
    reasons.extend(peak_month["notes"][:2])

    return {
        "start": run[0]["month"],
        "end": run[-1]["month"],
        "label": run[0]["label"] if len(run) == 1 else f"{run[0]['label']} – {run[-1]['label']}",
        "months": len(run),
        "peak": peak,
        "peak_month": peak_month["label"],
        "mean": round(mean, 1),
        "confidence": confidence,
        "dasha": peak_month["dasha"],
        "double_transit": has_double,
        "reasons": reasons,
    }


def format_timing_windows(result: Dict) -> str:
    lines = [
        "═══════════════════════════════════════════════════════════════",
        f"TIMING WINDOWS — {result['label'].upper()} (next {result['horizon_years']} years)",
        "Month-by-month scan: dasha-lord links to the topic × Jupiter/Saturn double transit",
        "═══════════════════════════════════════════════════════════════",
        f"Primary house: H{result['primary_house']} | Natal promise: "
        f"{'STRONG' if result['natal_promise']['active'] else 'WEAK'} — {result['natal_promise']['detail'][:220]}",
        f"Birth time confidence: {result['birth_time_confidence']}",
    ]
    windows = result.get("windows") or []
    if windows:
        for i, w in enumerate(windows, 1):
            lines.append(
                f"{i}. {w['label']} | {w['confidence']} | peak {w['peak']} ({w['peak_month']}) | {w['dasha']}"
            )
            for r in w["reasons"][:4]:
                lines.append(f"     · {r}")
    else:
        best = ", ".join(f"{m['label']} ({m['score']})" for m in result.get("best_months", []))
        lines.append("No month crosses the activation threshold in this horizon.")
        if best:
            lines.append(f"Least-resistance months (low confidence): {best}")
    lines += [
        "",
        "RULE: Take timing ONLY from these windows. Quote month ranges, never a single date. "
        "Name the dasha lords and the transit that open each window. If the natal promise is WEAK "
        "or no window exists, say so plainly instead of inventing dates.",
    ]
    return "\n".join(lines)
