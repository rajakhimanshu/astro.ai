"""
core/remedial_engine.py
────────────────────────────────────────────────────
Multi-Layered Remedial Engine
Generates Spiritual, Behavioral, and Material prescriptions.
────────────────────────────────────────────────────
"""

class RemedialEngine:
    def __init__(self, user_profile):
        # User profile should have a 'spiritual_level' key
        self.level = user_profile.get("spiritual_level", "Beginner")

    def get_prescriptions(self, problematic_planets):
        """
        problematic_planets: list of planet names that are weak or afflicted.
        """
        results = []
        for p in problematic_planets:
            results.append({
                "planet": p,
                "spiritual": self._get_spiritual(p),
                "behavioral": self._get_behavioral(p),
                "material": self._get_material(p)
            })
        return results

    def _get_spiritual(self, p):
        M = {
            "Saturn": {
                "Beginner": "Chant 'Om Sham Shanicharaya Namah' 108 times on Saturdays.",
                "Advanced": "Sadhana of Lord Bhairava or rigorous fasting on Saturdays."
            },
            "Moon": {
                "Beginner": "Chant 'Om Som Somaya Namah' and offer water to the Moon.",
                "Advanced": "Meditation on the Tithis and Lunar phases; Chandra Yantra upasana."
            },
            "Sun": {
                "Beginner": "Surya Namaskar at sunrise; chant 'Om Ghrini Suryaya Namah'.",
                "Advanced": "Aditya Hridaya Stotra daily with focus on inner light."
            }
        }
        # Fallback to Beginner if Adv not found
        return M.get(p, {}).get(self.level, M.get(p, {}).get("Beginner", "Standard deity worship."))

    def _get_behavioral(self, p):
        M = {
            "Saturn": "Build rigid daily structures. Commit to finishing one project before starting next. Respect elders.",
            "Moon": "Maintain an emotional journal. Practice mindfulness in reactions. Stay near water bodies.",
            "Sun": "Step into leadership. Accept public recognition. Cultivate a confident posture.",
            "Mercury": "Practice simple, non-technical explanation of ideas. Commit to silence for 1 hour daily."
        }
        return M.get(p, "Align your daily habits with the discipline of this planet.")

    def _get_material(self, p):
        M = {
            "Saturn": "Donate black sesame or iron tools on Saturdays.",
            "Moon": "Donate rice or white cloth on Mondays.",
            "Sun": "Donate wheat or copper items on Sundays.",
            "Mercury": "Donate green vegetables or books on Wednesdays."
        }
        return M.get(p, "Perform charity related to the planet's color or metal.")

def format_remedial_report(prescriptions):
    lines = ["REMEDIAL PRESCRIPTIONS (Evolutionary Alignment):"]
    for p in prescriptions:
        lines.append(f"\n  [FOR {p['planet'].upper()}]:")
        lines.append(f"    - Spiritual: {p['spiritual']}")
        lines.append(f"    - Behavioral: {p['behavioral']}")
        lines.append(f"    - Material/Charity: {p['material']}")
    return "\n".join(lines)
