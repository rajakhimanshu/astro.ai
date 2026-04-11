"""
core/kundali_profile.py
────────────────────────────────────────────────────
Complete Kundali (Birth Chart) Profile — Himanshu Rajak
Source: VedicReport.pdf (AstroSage), cross-verified with kerykeion engine
Born: 22 Aug 2006 | 9:37:29 AM IST | Jabalpur, MP, India
Ayanamsha: Lahiri (Sidereal) | House System: Whole Sign
Lagna: Virgo 26°20'04" | Rashi: Cancer | Nakshatra: Ashlesha Pada 1
────────────────────────────────────────────────────
"""

# ─── COMPLETE STATIC NATAL PROFILE ───────────────────────────────────────────

KUNDALI_PROFILE = {
    "name": "Himanshu Rajak",
    "birth": {
        "date": "22 August 2006",
        "weekday": "Tuesday",
        "time": "9:37:29 AM IST",
        "place": "Jabalpur, Madhya Pradesh, India",
        "latitude": "23°10'N",
        "longitude": "79°57'E",
        "timezone": "IST (UTC+5:30)",
        "ayanamsha": "Lahiri — 23°56'57\"",
        "tithi": "Chaturdashi, Krishna Paksha",
        "yoga": "Variyan",
        "karan": "Sakuni",
    },

    # ── Lagna & Rashi ────────────────────────────────────────────────────────
    "lagna": {
        "sign": "Virgo",
        "degree": "26°20'04\"",
        "nakshatra": "Chitra",
        "pada": 1,
        "lord": "Mercury",
        "element": "Earth",
        "nature": "Mutable / Dual",
        "quality": "Analytical, service-oriented, detail-focused, discriminating",
    },
    "rashi": {
        "sign": "Cancer",
        "lord": "Moon",
        "nakshatra": "Ashlesha",
        "pada": 1,
        "nakshatra_lord": "Mercury",
    },

    # ── Planetary Positions (Whole Sign Houses, Virgo Lagna) ─────────────────
    # House mapping: 1H=Virgo, 2H=Libra, 3H=Scorpio, 4H=Sagittarius,
    #                5H=Capricorn, 6H=Aquarius, 7H=Pisces, 8H=Aries,
    #                9H=Taurus, 10H=Gemini, 11H=Cancer, 12H=Leo
    "planets": {
        "ASC": {
            "sign": "Virgo", "house": 1, "degree": "26°20'04\"",
            "nakshatra": "Chitra", "pada": 1, "lord": "Mars",
            "retrograde": False,
        },
        "Sun": {
            "sign": "Leo", "house": 12, "degree": "5°00'13\"",
            "nakshatra": "Magha", "pada": 2, "nakshatra_lord": "Ketu",
            "retrograde": False,
            "dignity": "Own sign (Leo) — powerful despite 12H placement",
            "rules_houses": [12],  # Leo = 12H for Virgo lagna (no, wait Sun rules Leo which is 12H)
            "analysis": (
                "Sun in Leo (own sign) in 12th house: The soul burns bright but in hidden domains. "
                "Spiritual authority, foreign connections, research intensity. Sun in Magha (Ketu-ruled) deepens "
                "ancestral pride and karmic authority. 12H Sun = strong moksha indicator. Father may be spiritually-inclined "
                "or distant. Hidden leadership. Energy directed toward isolation, meditation, foreign lands, hospitals. "
                "Sun's 7th aspect from 12H falls on 6H — health discipline and victory over enemies."
            ),
        },
        "Moon": {
            "sign": "Cancer", "house": 11, "degree": "17°00'23\"",
            "nakshatra": "Ashlesha", "pada": 1, "nakshatra_lord": "Mercury",
            "retrograde": False,
            "dignity": "Own sign (Cancer) in 11H — maximum strength for gains",
            "rules_houses": [11],  # Cancer = 11H
            "analysis": (
                "Moon in Cancer (own sign, exaltation-adjacent) in 11th house: This is the most powerful placement "
                "in the chart for material gains, social success, and emotional fulfillment. Moon in Ashlesha (serpent nakshatra) "
                "gives hypnotic intelligence, strategic mind, and deep psychological insight. 11H Moon in own sign = "
                "desires will be fulfilled, income from mass appeal, strong mother relationship, influential elder siblings. "
                "The emotional life is tied to achievement and social validation."
            ),
        },
        "Mars": {
            "sign": "Leo", "house": 12, "degree": "25°10'11\"",
            "nakshatra": "Purva Phalguni", "pada": 4, "nakshatra_lord": "Venus",
            "retrograde": False,
            "dignity": "Friendly sign, 12th house placement",
            "rules_houses": [3, 8],  # Scorpio=3H, Aries=8H for Virgo lagna
            "analysis": (
                "Mars (lord of 3H-skills and 8H-transformation) in Leo-12H: Courage and drive are applied in hidden, "
                "foreign, or research-oriented domains. Purva Phalguni nakshatra (Venus-ruled) brings creative flair and "
                "sensual energy. Mars in 12H can represent hidden enemies or expenses, but also drives foreign work, "
                "research, and spiritual practices. As 8H lord in 12H, this creates Viparita Raja Yoga — sudden, "
                "unexpected rise through apparent losses. Mars aspects 3H (courage, siblings), 6H (health/enemies), 7H (partnerships)."
            ),
        },
        "Mercury": {
            "sign": "Cancer", "house": 11, "degree": "24°51'47\"",
            "nakshatra": "Ashlesha", "pada": 3, "nakshatra_lord": "Mercury",
            "retrograde": False,
            "dignity": "Neutral in Cancer; Lagna lord in 11H = excellent",
            "rules_houses": [1, 10],  # Virgo=1H, Gemini=10H for Virgo lagna
            "analysis": (
                "Mercury (Lagna lord AND 10th house lord) in Cancer-11H: The most career-defining placement. "
                "Mercury rules both SELF (1H-Virgo) and CAREER (10H-Gemini), and is placed in the GAINS house (11H). "
                "This means: income comes through intellectual work, technology, communication, writing, and networking. "
                "Career (Gemini-10H) is connected to gains (Cancer-11H) — income IS the career. Ashlesha pada 3 Mercury "
                "gives penetrating analytical intelligence and persuasive communication. The mind is suited for "
                "technology, AI, business strategy, writing, media. Mercury in Ashlesha = strategic, cunning intelligence."
            ),
        },
        "Jupiter": {
            "sign": "Libra", "house": 2, "degree": "18°09'03\"",
            "nakshatra": "Swati", "pada": 4, "nakshatra_lord": "Rahu",
            "retrograde": False,
            "dignity": "Neutral in Libra; 2H placement good for wealth",
            "rules_houses": [4, 7],  # Sagittarius=4H, Pisces=7H for Virgo lagna
            "analysis": (
                "Jupiter (lord of 4H-home/education and 7H-partnerships) in Libra-2H: Wisdom and philosophy "
                "expressed through speech and wealth-building. Jupiter in Swati (Rahu-ruled) gives global ambitions, "
                "entrepreneurial thinking, and mastery of balance/justice. 7H lord in 2H creates Dhana yoga from "
                "partnerships. 4H lord in 2H = wealthy home life, education contributes to wealth. Jupiter aspects "
                "6H (victory over competition through wisdom), 8H (deep research, spiritual inheritance), and 10H "
                "(career elevated by Jupiter's wisdom — Hamsa yoga influence)."
            ),
        },
        "Venus": {
            "sign": "Cancer", "house": 11, "degree": "17°28'29\"",
            "nakshatra": "Ashlesha", "pada": 1, "nakshatra_lord": "Mercury",
            "retrograde": False,
            "dignity": "Neutral in Cancer; exceptional placement as 2H+9H lord in 11H",
            "rules_houses": [2, 9],  # Libra=2H, Taurus=9H for Virgo lagna
            "analysis": (
                "Venus (lord of 2H-wealth AND 9H-fortune/dharma) in Cancer-11H: This is the primary Dhana Yoga "
                "of the chart. Venus rules both the wealth house AND the luck/fortune house, and is placed in the "
                "gains house. This promises significant wealth accumulation through creative, aesthetic, social, "
                "or entertainment work. Venus in Ashlesha pada 1 with Moon (own sign) in same house = magnetic "
                "charm, excellent relationships, income through beauty/luxury/social connections. Venus Mahadasha "
                "(2030-2050) will be a period of extraordinary prosperity. Conjunct Moon and Saturn in 11H."
            ),
        },
        "Saturn": {
            "sign": "Cancer", "house": 11, "degree": "22°45'31\"",
            "nakshatra": "Ashlesha", "pada": 2, "nakshatra_lord": "Mercury",
            "retrograde": False,
            "dignity": "Debilitated (neecha) in Cancer; 11H mitigates significantly",
            "rules_houses": [5, 6],  # Capricorn=5H, Aquarius=6H for Virgo lagna
            "analysis": (
                "Saturn (neecha/debilitated in Cancer) in 11H: Saturn's debilitation is mitigated by: (1) being in "
                "11H (upachaya — Saturn loves upachaya houses), (2) Moon in same sign in own sign (neecha bhanga), "
                "(3) multiple planets in same house (strength through company). As 5H lord: creativity and romance "
                "come with delays and discipline. As 6H lord in 11H: income through service, disciplined competition wins. "
                "Gains come through sustained hard work, not shortcuts. Social network built slowly but becomes "
                "powerful. Full neecha bhanga applies due to Moon in own sign in same house."
            ),
        },
        "Rahu": {
            "sign": "Pisces", "house": 7, "degree": "2°41'41\"",
            "nakshatra": "Purva Bhadrapada", "pada": 4, "nakshatra_lord": "Jupiter",
            "retrograde": True,
            "dignity": "Amplifies 7th house themes (partnerships, foreign, marriage)",
            "analysis": (
                "Rahu in Pisces-7H (Retrograde): Intense karmic pull toward partnerships, marriage, and foreign "
                "connections. Rahu in Pisces seeks transcendence through relationships — drawn to spiritual, "
                "foreign, or unconventional partners. Business partnerships may be with people from very different "
                "backgrounds. Strong desire for international collaboration. Rahu in Purva Bhadrapada (Jupiter-ruled) "
                "gives visionary thinking in partnerships. The 7H Rahu's obsessive energy means relationships can "
                "become consuming — caution needed in commitment timing. Currently activated in Ketu MD (Ketu in 1H, "
                "Rahu in 7H = nodal axis on 1H-7H = self vs. other dynamic front and center)."
            ),
        },
        "Ketu": {
            "sign": "Virgo", "house": 1, "degree": "2°41'41\"",
            "nakshatra": "Uttara Phalguni", "pada": 2, "nakshatra_lord": "Sun",
            "retrograde": True,
            "dignity": "In Lagna — past-life wisdom, spiritual detachment, analytical insight",
            "analysis": (
                "Ketu in Virgo-1H (Retrograde, Lagna): Past-life analytical mastery is embedded in the personality. "
                "Natural inclination toward perfection, spiritual detachment, and discrimination. The self can feel "
                "undefined or disconnected from ego — a highly spiritual signature. Uttara Phalguni (Sun-ruled) "
                "gives inherent dignity and leadership despite Ketu's detachment quality. During Ketu Mahadasha "
                "(2023-2030), the 1H Ketu IS being activated — this is a profoundly personal period of identity "
                "transformation, spiritual awakening, and detachment from worldly pursuits. The body/health requires "
                "attention during this period. Ketu in Lagna gives flashes of insight, intuitive intelligence, "
                "and a non-mainstream personality."
            ),
        },
    },

    # ── House-by-House Analysis (Virgo Lagna, Whole Sign) ────────────────────
    "houses": {
        1:  {"sign": "Virgo",       "lord": "Mercury", "occupants": ["Ketu"],
             "quality": "Personality, body, self-image, overall life direction",
             "summary": "Virgo lagna: Analytical, service-oriented, discerning, perfectionist. Ketu here adds past-life wisdom and spiritual detachment. Mercury as lagna lord in 11H makes the intellect the primary tool for success."},
        2:  {"sign": "Libra",       "lord": "Venus",   "occupants": ["Jupiter"],
             "quality": "Wealth, speech, family, food, accumulated resources",
             "summary": "Jupiter in Libra-2H: Eloquent, philosophical speech. Wealth through balance/judgment. 7H lord (Jupiter) in 2H = wealth through partnerships. Venus (2H lord) in 11H = wealth through social gains. 2H has 43 SAV points — HIGHEST in chart. Wealth house is very strong."},
        3:  {"sign": "Scorpio",     "lord": "Mars",    "occupants": [],
             "quality": "Courage, siblings, communication, short travel, skills, media",
             "summary": "Empty 3H Scorpio. Mars (3H lord) in 12H — courage applied in hidden/foreign domains. Investigative and research communication style. Skills are developed in private, then deployed powerfully."},
        4:  {"sign": "Sagittarius", "lord": "Jupiter", "occupants": [],
             "quality": "Home, mother, comforts, vehicles, property, higher education",
             "summary": "Empty 4H Sagittarius. Jupiter (4H lord) in 2H — home life is philosophical and wealth-generating. Higher education strongly supported. Mother is wise/generous. Jupiter aspects 4H from 2H (by 3rd aspect in Jyotish? No — Jupiter's special aspects are 5th, 7th, 9th from its position. From 2H: aspects 6H, 8H, 10H). Property timing linked to Jupiter transits."},
        5:  {"sign": "Capricorn",   "lord": "Saturn",  "occupants": [],
             "quality": "Children, intelligence, creativity, romance, past deeds, speculation",
             "summary": "Empty 5H Capricorn. Saturn (5H lord) debilitated in 11H — creativity comes through discipline and hard work. Romance may face delays (especially in Saturn AD). Intelligence is structured and practical. Speculation requires caution."},
        6:  {"sign": "Aquarius",    "lord": "Saturn",  "occupants": [],
             "quality": "Enemies, debt, disease, service, competition, daily work",
             "summary": "Empty 6H Aquarius. Saturn (6H lord) in 11H — income from service work. Victory over enemies through disciplined networking. Health needs consistent attention. Saturn's 34 SAV in 6H = decent strength to handle challenges."},
        7:  {"sign": "Pisces",      "lord": "Jupiter", "occupants": ["Rahu"],
             "quality": "Marriage, business partners, foreign connections, legal",
             "summary": "Rahu in Pisces-7H — karmic/unconventional/foreign partnerships. Jupiter (7H lord) in 2H = partnerships bring wealth. 7H has 22 SAV points — CAUTION in partnerships. Take time before committing. Rahu here = powerful but potentially destabilizing relationships."},
        8:  {"sign": "Aries",       "lord": "Mars",    "occupants": [],
             "quality": "Sudden change, hidden wealth, occult, in-laws, longevity, crisis",
             "summary": "Empty 8H Aries. Mars (8H lord) in 12H — potential Viparita Raja Yoga. Interest in occult/research. Sudden events can bring unforeseen gains (VRY). Longevity supported by Virgo lagna + strong Moon."},
        9:  {"sign": "Taurus",      "lord": "Venus",   "occupants": [],
             "quality": "Fortune, dharma, father, philosophy, higher wisdom, foreign travel",
             "summary": "Empty 9H Taurus. Venus (9H lord) in 11H = fortune comes through income/gains/social network. Father may be artistic/wealthy. Foreign travel strongly supported. Higher education abroad possible. Venus as 9H lord in 11H = Lakshmi Yoga aspect."},
        10: {"sign": "Gemini",      "lord": "Mercury", "occupants": [],
             "quality": "Career, public image, status, authority, father, government",
             "summary": "Empty 10H Gemini. Mercury (10H lord AND lagna lord) in 11H — career success comes through intellectual networking and communication. Career in technology, writing, AI, media, finance. 10H has ONLY 18 SAV points (weakest in chart) — career requires extra deliberate effort. Victory comes but not easily."},
        11: {"sign": "Cancer",      "lord": "Moon",    "occupants": ["Moon", "Mercury", "Venus", "Saturn"],
             "quality": "Income, gains, elder siblings, social network, fulfillment of desires",
             "summary": "POWERHOUSE 11H with 4 planets. Moon (own sign, very strong), Mercury (lagna+career lord), Venus (wealth+fortune lord), Saturn (gains through service). This is the dominant house of the chart. Income potential is extraordinary. The life path revolves around gains through intellectual/social/creative work. All major desires fulfilled eventually."},
        12: {"sign": "Leo",         "lord": "Sun",     "occupants": ["Sun", "Mars"],
             "quality": "Foreign lands, spirituality, losses, isolation, moksha, expenses",
             "summary": "Sun (own sign, strong) and Mars (VRY potential) in Leo-12H. Foreign connections are strong. Spiritual inclinations very high. Income from foreign sources possible. Hidden work and research. Expenses can be high but also foreign earnings compensate. Strong moksha indicator in the chart."},
    },

    # ── Ashtakvarga ─────────────────────────────────────────────────────────
    "ashtakvarga": {
        "sarvashtakavarga": {
            1: 26, 2: 43, 3: 30, 4: 25, 5: 24,
            6: 34, 7: 22, 8: 29, 9: 29, 10: 18, 11: 28, 12: 29
        },
        "total": 337,
        "interpretation": (
            "2H (Libra) = 43 points — STRONGEST. Wealth and speech promise is highest in chart. "
            "6H (Aquarius) = 34 points — Good strength to handle enemies/competition. "
            "10H (Gemini) = 18 points — WEAKEST. Career house needs maximum effort. "
            "7H (Pisces) = 22 points — Caution with partnerships/marriage. "
            "11H (Cancer) = 28 points — Average, but 4-planet stellium compensates. "
            "Overall average SAV = 28. Houses above average: 2, 3, 6, 8, 9, 12."
        ),
    },

    # ── Vimshottari Dasha Timeline ───────────────────────────────────────────
    "dasha": {
        "completed": [
            {"md": "Mercury", "period": "22 Aug 2006 – 17 Mar 2023", "years": 16,
             "note": "Mercury MD: formative education years, analytical development, networked early life."},
        ],
        "current_md": {
            "lord": "Ketu",
            "period": "17 Mar 2023 – 17 Mar 2030",
            "years": 7,
            "ketu_position": "1st House (Virgo) — activates SELF, spiritual identity",
            "interpretation": (
                "Ketu Mahadasha (2023–2030): A period of profound internal transformation, spiritual awakening, "
                "and detachment from conventional success. Ketu in 1H Virgo means the SELF is being purified. "
                "Past-life patterns surface for resolution. This is NOT a material-gains period generally, but it "
                "builds the foundation for Venus MD (2030–2050), which will be outrageously prosperous. "
                "During Ketu MD: unconventional paths, spiritual development, research, foreign connections, "
                "clearing karmic debts. Early years may feel directionless but late Ketu MD (2028–2030) improves."
            ),
            "antardashas": [
                {"ad": "Ketu",    "period": "17 Mar 2023 – 14 Aug 2023",   "note": "Identity shock, karmic clearing"},
                {"ad": "Venus",   "period": "14 Aug 2023 – 14 Oct 2024",   "note": "Material comforts, relationships, creative work"},
                {"ad": "Sun",     "period": "14 Oct 2024 – 20 Feb 2025",   "note": "Authority, father, hidden power"},
                {"ad": "Moon",    "period": "20 Feb 2025 – 20 Sep 2025",   "note": "Emotional clarity, memory, family, gains"},
                {"ad": "Mars",    "period": "20 Sep 2025 – 17 Feb 2026",   "note": "Courage, hidden action, foreign drive"},
                {"ad": "Rahu",    "period": "17 Feb 2026 –  5 Mar 2027",   "note": "★ CURRENT: Karmic partnerships, foreign amplification, nodal axis activated"},
                {"ad": "Jupiter", "period": " 5 Mar 2027 – 11 Feb 2028",   "note": "Wisdom, wealth through knowledge, education gains"},
                {"ad": "Saturn",  "period": "11 Feb 2028 – 20 Mar 2029",   "note": "Hard-won discipline, service income, delayed but real gains"},
                {"ad": "Mercury", "period": "20 Mar 2029 – 17 Mar 2030",   "note": "Career clarity, tech/communication surge before Venus MD"},
            ],
            "current_ad": "Rahu",
            "current_ad_period": "17 Feb 2026 – 5 Mar 2027",
            "current_ad_interpretation": (
                "Ketu MD – Rahu AD (Feb 2026 – Mar 2027): The nodal axis dominates. "
                "Ketu in 1H activates self/identity; Rahu in 7H activates partnerships/foreign. "
                "This is a karmic period for RELATIONSHIPS and BUSINESS PARTNERSHIPS. "
                "Foreign connections, unconventional opportunities, amplified social exposure. "
                "Rahu's obsessive energy pushes toward partnership/collaboration ventures. "
                "Caution: Rahu AD in Ketu MD can bring confusion about direction — maintain spiritual grounding. "
                "Positive: Technology, foreign collaborations, digital platforms can grow significantly. "
                "Watch 7H matters (partnerships, potential romantic interest) — karmic and intense."
            ),
        },
        "upcoming_mds": [
            {"md": "Venus", "period": "17 Mar 2030 – 17 Mar 2050", "years": 20,
             "note": "Venus rules 2H (wealth) AND 9H (fortune), placed in 11H (gains) in own-sign-company Cancer. "
                     "This is the GOLDEN ERA. 20 years of Venus MD will likely bring peak wealth, creative success, "
                     "marriage, luxury, and fulfillment. Venus is the most powerful planet for Virgo lagna."},
        ],
    },

    # ── Key Yogas ────────────────────────────────────────────────────────────
    "yogas": [
        {
            "name": "Dhana Yoga (Primary)",
            "planets": "Venus in 11H (lord of 2H wealth + 9H fortune)",
            "active_in": "Venus Mahadasha (2030–2050) — peak activation",
            "effect": "Significant wealth accumulation through creative, social, and fortune-aligned work. "
                      "Venus as dual-lord of artha and dharma houses in gains house is classic wealth yoga.",
        },
        {
            "name": "Dhana Yoga (Secondary)",
            "planets": "Jupiter in 2H (lord of 7H partnerships)",
            "active_in": "Jupiter periods (Ketu-Jupiter AD: Mar 2027 – Feb 2028)",
            "effect": "Wealth through partnerships and wise associations. Jupiter expands the 2H (wealth house) directly.",
        },
        {
            "name": "Mercury Yoga (Career-Gains Link)",
            "planets": "Mercury in 11H (lord of 1H lagna + 10H career)",
            "active_in": "All Mercury periods; perpetual background yoga",
            "effect": "Career house lord (10H) and lagna lord in gains house (11H) — income IS the career. "
                      "Intellectual and communication-based income is the primary life path.",
        },
        {
            "name": "Viparita Raja Yoga (Hidden)",
            "planets": "Mars (8H lord) in 12H",
            "active_in": "Mars periods, Saturn periods, foreign/crisis events",
            "effect": "Lord of dusthana (8H) in another dusthana (12H) = VRY. "
                      "Sudden, unexpected rise through apparent losses or crises. Hidden enemies become allies.",
        },
        {
            "name": "Neecha Bhanga Raja Yoga",
            "planets": "Saturn (debilitated in Cancer) + Moon (own sign in Cancer)",
            "active_in": "Saturn periods, especially Venus-Saturn AD",
            "effect": "Saturn's debilitation is cancelled by Moon's strength in same sign. "
                      "The cancellation creates Raja Yoga quality — rise from difficult beginnings.",
        },
        {
            "name": "Gajakesari Yoga",
            "planets": "Moon (11H-Cancer) and Jupiter (2H-Libra) — Moon and Jupiter in kendra from each other",
            "active_in": "Jupiter periods",
            "effect": "Moon and Jupiter form Gajakesari (11H to 2H = 4th house = kendra from each other). "
                      "Brings wisdom, recognition, wealth, and stability. Classic benefic yoga.",
        },
    ],

    # ── Lucky & Remedial Elements ─────────────────────────────────────────────
    "favorable": {
        "numbers": [7, 1, 2, 3, 9],
        "days": ["Sunday", "Tuesday"],
        "metal": "Silver",
        "stone": "Pearl (Moon, confirmed by chart)",
        "colors": ["Green", "White", "Gold"],
        "good_planets": ["Sun", "Mercury", "Mars"],
        "caution_planets": ["Jupiter (functional malefic as lord of 4/7H for Virgo lagna)"],
    },
    "remedies": [
        "Worship Mercury (Budha) — lord of lagna and career. Recite Budha Beej Mantra (Om Bram Brim Braum Sah Budhaya Namah) on Wednesdays.",
        "Wear Pearl — Moon is 11H lord in own sign, a primary strength. Pearl energizes the powerful 11H stellium.",
        "Ketu MD remedy: Worship Ganesha and practice Ketu-Rahu balance. Avoid ego battles; embrace humility.",
        "Saturn neecha remedy: Offer water to the Sun daily. Light mustard oil lamp on Saturdays. Recite Shani mantra.",
        "For career (weak 10H): Wear Panna (Emerald) if budget allows — it strengthens Mercury, lord of both lagna and 10H.",
        "For Rahu-7H caution in partnerships: Do not rush into business or romantic partnerships. Seek Jupiter guidance (mentors/elders).",
    ],
}


# ─── TEXT FORMATTER FOR AI CONTEXT ──────────────────────────────────────────

def get_full_kundali_text() -> str:
    """
    Returns the complete kundali as a structured, AI-readable text block.
    This is the 'ground truth' of the chart injected into every AI query.
    """
    p = KUNDALI_PROFILE
    lines = [
        "╔══════════════════════════════════════════════════════════════════════════════╗",
        "║           COMPLETE NATAL CHART — HIMANSHU RAJAK (GROUND TRUTH)             ║",
        "╚══════════════════════════════════════════════════════════════════════════════╝",
        f"Born: {p['birth']['date']}  |  Time: {p['birth']['time']}  |  {p['birth']['place']}",
        f"Ayanamsha: {p['birth']['ayanamsha']}  |  Day: {p['birth']['weekday']}  |  Tithi: {p['birth']['tithi']}",
        "",
        "┌─ LAGNA & RASHI ─────────────────────────────────────────────────────────────┐",
        f"  Lagna (Ascendant): Virgo 26°20' | Chitra Nakshatra, Pada 1 | Lord: Mercury",
        f"  Rashi (Moon Sign): Cancer       | Ashlesha Nakshatra, Pada 1 | Lord: Mercury",
        "",
        "┌─ PLANETARY POSITIONS (Sidereal / Lahiri / Whole Sign Houses) ──────────────┐",
        f"{'Planet':<12} {'Sign':<14} {'House':<7} {'Degree':<14} {'Nakshatra':<18} {'Pada':<5} {'Retro':<5}",
        "─"*80,
    ]

    for name, pd_ in p['planets'].items():
        retro = "YES" if pd_['retrograde'] else "No"
        lines.append(
            f"  {name:<10} {pd_['sign']:<14} {pd_['house']:<7} {pd_['degree']:<14} {pd_['nakshatra']:<18} {pd_['pada']:<5} {retro:<5}"
        )

    lines.extend([
        "",
        "┌─ HOUSE LORDS & OCCUPANTS ──────────────────────────────────────────────────┐",
        f"  {'House':<7} {'Sign':<14} {'Lord':<10} {'Occupants':<30} Summary",
        "─"*100,
    ])
    for h, hd in p['houses'].items():
        occupants = ', '.join(hd['occupants']) if hd['occupants'] else '(empty)'
        lines.append(f"  {h:<7} {hd['sign']:<14} {hd['lord']:<10} {occupants:<30} {hd['summary'][:80]}...")

    lines.extend([
        "",
        "┌─ PLANET-BY-PLANET INTERPRETATIONS ─────────────────────────────────────────┐",
    ])
    for name, pd_ in p['planets'].items():
        if name == "ASC":
            continue
        lines.append(f"\n  [{name} in {pd_['sign']} — House {pd_['house']} — {pd_['nakshatra']} Pada {pd_['pada']}]")
        lines.append(f"  Dignity: {pd_['dignity']}")
        lines.append(f"  Rules: Houses {pd_.get('rules_houses', ['?'])}")
        lines.append(f"  Analysis: {pd_['analysis']}")

    lines.extend([
        "",
        "┌─ ASHTAKVARGA (Sarvashtakavarga by House) ──────────────────────────────────┐",
        "  House:  1   2   3   4   5   6   7   8   9  10  11  12",
        "  SAV:  " + "  ".join(f"{p['ashtakvarga']['sarvashtakavarga'][h]:2}" for h in range(1,13)),
        f"  Avg=~28. Max=2H(43), Min=10H(18).",
        f"  Interpretation: {p['ashtakvarga']['interpretation']}",
        "",
        "┌─ KEY YOGAS ─────────────────────────────────────────────────────────────────┐",
    ])
    for yoga in p['yogas']:
        lines.append(f"  ● {yoga['name']}")
        lines.append(f"    Planets: {yoga['planets']}")
        lines.append(f"    Effect:  {yoga['effect']}")
        lines.append(f"    Active in: {yoga['active_in']}")
        lines.append("")

    lines.extend([
        "┌─ CURRENT DASHA (Time Lords) ────────────────────────────────────────────────┐",
        f"  Mahadasha: KETU ({p['dasha']['current_md']['period']})",
        f"  Ketu is in: {p['dasha']['current_md']['ketu_position']}",
        f"  MD Interpretation: {p['dasha']['current_md']['interpretation']}",
        "",
        f"  ★ CURRENT Antardasha: RAHU ({p['dasha']['current_md']['current_ad_period']})",
        f"  AD Interpretation: {p['dasha']['current_md']['current_ad_interpretation']}",
        "",
        "  Upcoming Antardasha schedule:",
    ])
    for ad in p['dasha']['current_md']['antardashas']:
        marker = " ← CURRENT" if ad['ad'] == 'Rahu' else ""
        lines.append(f"    • Ketu–{ad['ad']:8} | {ad['period']}  | {ad['note']}{marker}")

    lines.extend([
        "",
        "  VENUS MAHADASHA begins:" ,
        f"    {p['dasha']['upcoming_mds'][0]['period']} — {p['dasha']['upcoming_mds'][0]['note']}",
        "",
        "┌─ REMEDIES & FAVORABLE ELEMENTS ─────────────────────────────────────────────┐",
    ])
    for rem in p['remedies']:
        lines.append(f"  • {rem}")

    return "\n".join(lines)


def get_current_dasha_summary() -> dict:
    """Returns a structured dict of the current dasha state."""
    return {
        "mahadasha": "Ketu",
        "antardasha": "Rahu",
        "pratyantardasha": "Varies",
        "md_period": "17 Mar 2023 – 17 Mar 2030",
        "ad_period": "17 Feb 2026 – 5 Mar 2027",
        "md_interpretation": KUNDALI_PROFILE['dasha']['current_md']['interpretation'],
        "ad_interpretation": KUNDALI_PROFILE['dasha']['current_md']['current_ad_interpretation'],
        "next_ad": "Jupiter (5 Mar 2027 – 11 Feb 2028)",
        "golden_era": "Venus Mahadasha begins 17 Mar 2030",
    }
