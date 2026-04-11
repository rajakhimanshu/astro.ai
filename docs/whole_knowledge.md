# Astro.AI — Astrology Knowledge Base & Engine Audit 🌌

This document provides a complete audit of the astrological logic, classical texts, and planetary engines that power the **Jyotish AI** oracle. It synthesizes insights from multiple centuries of Vedic tradition combined with high-precision modern computational astrology.

---

## 📚 1. Classical Knowledge Base (ChromaDB Vector Store)
Jyotish AI uses Retrieval-Augmented Generation (RAG) to instantly search and synthesize thousands of pages of classical Vedic texts whenever you ask a question.

Currently Indexed Sources:
1. **Brihat Parāśara Horā Śhāstra** (Translated by R. Santhanam) — The fundamental foundation of Vedic Astrology.
2. **Encyclopedia of Vedic Astrology: Yogas** (Shanker Adawal) — Deep references for planetary combinations.
3. **Phaladeepika** (Mantreswara) — Advanced rules on transits, dashas, and yogas.
4. **Astrology of the Seers** (Dr. David Frawley) — Modern psychological & Ayurvedic perspectives on Jyotish.
5. **How to Judge a Horoscope** (B.V. Raman) — Practical case studies for interpreting houses.
6. **Brihat Jataka** (Varahamihira) — Classical predictive texts on planetary results.
7. **Uttara Kalamritam** — Specific and advanced predictive techniques.
8. **VedicReport.pdf** — Your embedded personal Kundali interpretations.

*The AI retrieves exact paragraphs from these texts before constructing its conversational answers.*

---

## ⚙️ 2. The 12-Layer Computational Engine (Python Backend)
Unlike standard generative AI, Jyotish AI doesn't "hallucinate" math. It calculates exact planet degrees using the **Swiss Ephemeris** (via Kerykeion) on the **Ayanamsha Lahiri (Sidereal)** system.

### Calculated Layers:
- **L1: D1 Natal Chart**: Calculates precise house placements, degrees, and dignities (Exalted, Debilitated, Moolatrikona, Own Sign).
- **L2: Drishti (Aspects)**: Calculates traditional 7th house aspects, plus special aspects for Mars (4th, 8th), Jupiter (5th, 9th), and Saturn (3rd, 10th).
- **L3: House Lordships**: Maps where the lord of each house is placed to determine the focus of life areas.
- **L4: Yogas (Planetary Combinations)**: Auto-detects Dhana Yogas (wealth), Raja Yogas (power), Viparita Raja Yogas, Neecha Bhanga, and Gajakesari Yogas.
- **L5: Nakshatras & Padas**: Maps precise lunar mansions and sub-lords (down to the pada/quarter).
- **L6: Vimshottari Dasha**: Computes exact Mahadasha (MD), Antardasha (AD), and Pratyantardasha (PD) timing cycles scaled to your birth moon.
- **L7: Live Transits (Gochara)**: Projects the current sky mapped automatically to your natal rising sign.
- **L8: Divisional Charts (Vargas)**: Computes the **D9 Navamsa** (marriage, undercurrent of the soul) and **D10 Dashamsa** (career prestige).
- **L9: Shadbala (6-Fold Strength)**: Computes a mathematical score (/10) representing the true kinetic strength of a planet.
- **L10: Ashtakavarga**: Computes SAV (Sarvashtakavarga) scores per house to determine if a transit will be fruitful (scores >28) or challenging.
- **L11: Panchanga**: Evaluates the live Hindu calendar (Tithi, Vara, Karana, Yoga).
- **L12: Prashna**: Horary astrology reference for the moment the user asks a question.

---

## 🚨 3. Dynamic Alerts & Remedies Framework
Added natively into the AI's core orchestrator, these are event triggers the AI continuously evaluates in the background:

- **Tight Transit Alert System:** If transiting Saturn, Jupiter, Rahu, or Ketu conjoins or strictly aspects the natal Lagna, Moon, or Sun within a **3.0° Orb**, the AI triggers a high-priority structural alert.
- **Dynamic Remedies Library:** Evaluates planet weakness. If a planet's Shadbala score drops below **5.0/10**, or if Rahu/Ketu inhabit sensitive houses (1, 6, 8, 12), the engine injects:
  - **Specific Mantras** (e.g. *Om Pram Preem Proum Sah Shanaishcharaya Namah*)
  - **Gemstone Suggestions**
  - **Targeted Charities/Donations**

---

## 🔮 4. Prompt Engineering & Persona
The AI operates under strict personality directives:
- **Tone:** A wise, highly skilled human astrologer writing in flowing, conversational paragraphs.
- **Style Constraints:** Banned from using robotic 12-section breakdowns or bulletized list dumps.
- **Dynamic Modulation:** The AI subtly shifts its tone based on the user's Lagna and dominant planet (e.g., firmer tone for strong Mars, more empathetic tone for strong Moon).
