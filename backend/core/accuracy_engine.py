"""
core/accuracy_engine.py
────────────────────────────────────────────────────────────────────────
Accuracy dashboard — hit rate, calibration, learning summary.
────────────────────────────────────────────────────────────────────────
"""

from core.prediction_ledger import get_all_predictions
from core.memory import analyze_planetary_empirical_performance, get_all_events


def compute_accuracy_report(user_id: str) -> dict:
    preds = get_all_predictions(user_id)
    verified = [p for p in preds if p["status"] in ("hit", "miss")]
    pending = [p for p in preds if p["status"] == "pending"]
    hits = [p for p in verified if p["status"] == "hit"]
    misses = [p for p in verified if p["status"] == "miss"]

    hit_rate = round(len(hits) / len(verified) * 100, 1) if verified else None

    by_topic = {}
    for p in verified:
        t = p.get("topic", "general")
        by_topic.setdefault(t, {"hit": 0, "miss": 0})
        by_topic[t][p["status"]] += 1

    topic_rates = {}
    for t, counts in by_topic.items():
        total = counts["hit"] + counts["miss"]
        topic_rates[t] = round(counts["hit"] / total * 100, 1) if total else 0

    empirical = analyze_planetary_empirical_performance(user_id)
    events = get_all_events(user_id)

    high_conf_hits = sum(
        1 for p in hits if (p.get("confidence") or 0) >= 60
    )
    high_conf_total = sum(
        1 for p in verified if (p.get("confidence") or 0) >= 60
    )
    high_conf_rate = (
        round(high_conf_hits / high_conf_total * 100, 1) if high_conf_total else None
    )

    return {
        "total_predictions": len(preds),
        "verified_count": len(verified),
        "pending_count": len(pending),
        "hit_count": len(hits),
        "miss_count": len(misses),
        "hit_rate_pct": hit_rate,
        "high_confidence_hit_rate_pct": high_conf_rate,
        "by_topic": topic_rates,
        "life_events_logged": len(events),
        "empirical_planets_tracked": len(empirical),
        "learning_active": len(events) >= 3 or len(verified) >= 1,
        "grade": _grade(hit_rate, len(verified)),
        "recommendation": _recommendation(hit_rate, len(verified), len(pending)),
    }


def _grade(hit_rate, verified_count):
    if verified_count < 3:
        return "CALIBRATING — log outcomes to build accuracy score"
    if hit_rate is None:
        return "UNKNOWN"
    if hit_rate >= 70:
        return "A — Exceeding average astrologer theme accuracy"
    if hit_rate >= 55:
        return "B — Matching good astrologer on themes"
    if hit_rate >= 40:
        return "C — Needs more data / rectification"
    return "D — Review birth time and convergence rules"


def _recommendation(hit_rate, verified, pending):
    if verified < 5:
        return "Verify at least 5 predictions (hit/miss) to unlock real accuracy scoring."
    if pending > 0:
        return f"You have {pending} pending predictions — confirm yes/no to train the system."
    if hit_rate and hit_rate < 50:
        return "Run birth-time rectification and log more life events to improve calibration."
    return "System is learning from your chart. Keep verifying predictions after each reading."


def format_accuracy_report(user_id: str) -> str:
    r = compute_accuracy_report(user_id)
    lines = [
        "=" * 70,
        "ACCURACY DASHBOARD — Prediction vs Outcome",
        "=" * 70,
        f"Grade: {r['grade']}",
        f"Predictions: {r['total_predictions']} total | {r['verified_count']} verified | {r['pending_count']} pending",
    ]
    if r["hit_rate_pct"] is not None:
        lines.append(f"Hit rate: {r['hit_rate_pct']}% ({r['hit_count']} hits / {r['miss_count']} misses)")
    if r["high_confidence_hit_rate_pct"] is not None:
        lines.append(f"High-confidence (60+) hit rate: {r['high_confidence_hit_rate_pct']}%")
    if r["by_topic"]:
        lines.append("By topic:")
        for t, rate in r["by_topic"].items():
            lines.append(f"  {t}: {rate}% hit rate")
    lines.append(f"Life events: {r['life_events_logged']} | Empirical planets: {r['empirical_planets_tracked']}")
    lines.append(f"Learning active: {'YES' if r['learning_active'] else 'NO — log events and verify predictions'}")
    lines.append(f"Next step: {r['recommendation']}")
    lines.append("=" * 70)
    return "\n".join(lines)
