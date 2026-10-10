"""
core/bhrigu_nadi.py
Bhrigu Nadi Engine — real Jupiter transit windows (no duplicate cards).
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from core.astro_engine import SIGNS, get_sidereal_sign_idx
from core.user_profile_engine import SIGN_IDX


class BhriguNadiEngine:
    def __init__(self, natal_chart_model, planets_data, lagna_sign_idx):
        self.m = natal_chart_model
        self.planets = planets_data
        self.lagna_idx = lagna_sign_idx
        self.house_lords = self._identify_house_lords()

    def _identify_house_lords(self):
        SIGN_LORDS_NAMES = [
            "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
            "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
        ]
        lords = {}
        for h in range(1, 13):
            sign_idx = (self.lagna_idx + h - 1) % 12
            lords[h] = SIGN_LORDS_NAMES[sign_idx]
        return lords

    def _jupiter_house_from(self, ref_idx: int, check_date: datetime) -> int:
        return (get_sidereal_sign_idx(check_date, "Jupiter") - ref_idx) % 12 + 1

    def predict_marriage_window(self):
        """
        Jupiter transiting 7th from Lagna OR 7th from Moon — one card per distinct window.
        """
        moon_sign = self.planets.get("Moon", {}).get("sign", SIGNS[self.lagna_idx])
        moon_idx = SIGN_IDX[moon_sign]
        cursor = datetime.now().replace(day=1)
        end_scan = cursor + relativedelta(years=15)

        windows = []
        was_in_7th = {"Lagna": False, "Moon": False}
        while cursor <= end_scan and len(windows) < 3:
            for ref_name, ref_idx in (("Lagna", self.lagna_idx), ("Moon", moon_idx)):
                in_7th = self._jupiter_house_from(ref_idx, cursor) == 7
                if in_7th and not was_in_7th[ref_name]:
                    windows.append({
                        "event": "Marriage/Significant Partnership",
                        "window": f"{cursor.strftime('%b %Y')} – {(cursor + relativedelta(months=12)).strftime('%b %Y')}",
                        "indicator": f"Jupiter transiting 7th from {ref_name} ({SIGNS[(ref_idx + 6) % 12]})",
                        "confidence": "High" if ref_name == "Lagna" else "Medium",
                    })
                was_in_7th[ref_name] = in_7th
            cursor += relativedelta(months=1)

        if not windows:
            windows.append({
                "event": "Marriage/Significant Partnership",
                "window": "Beyond 15-year scan",
                "indicator": "Jupiter does not reach the 7th from Lagna or Moon within the scan",
                "confidence": "Low",
            })
        return windows[:3]

    def predict_career_peaks(self):
        tenth_sign = SIGNS[(self.lagna_idx + 9) % 12]
        now = datetime.now().replace(day=1)
        jup_h = self._jupiter_house_from(self.lagna_idx, now)

        cursor, end_scan, start = now, now + relativedelta(years=13), None
        while cursor <= end_scan:
            in_10th = self._jupiter_house_from(self.lagna_idx, cursor) == 10
            if in_10th and start is None:
                start = cursor
            elif not in_10th and start is not None:
                break
            cursor += relativedelta(months=1)
        window = (
            f"{start.strftime('%b %Y')} – {cursor.strftime('%b %Y')}" if start
            else "Beyond 13-year scan"
        )
        return [{
            "event": "Career Consolidation / Authority Rise",
            "window": window,
            "reason": (
                f"Jupiter transit of the 10th ({tenth_sign}) from {SIGNS[self.lagna_idx]} Lagna; "
                f"Jupiter is in H{jup_h} now."
            ),
        }]

    def get_full_report(self):
        return {
            "marriage": self.predict_marriage_window(),
            "career": self.predict_career_peaks(),
        }


def format_bhrigu_report(report):
    lines = ["BHRIGU NADI TIMELINE (Significant Life Windows):"]
    for item in report.get("career", []):
        lines.append(f"  ★ {item['event']}: {item['window']} → {item['reason']}")
    for item in report.get("marriage", []):
        lines.append(
            f"  ★ {item['event']}: {item.get('window', '?')} "
            f"→ {item['indicator']}"
        )
    return "\n".join(lines)
