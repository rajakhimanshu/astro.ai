# 🕉️ Astro.AI: System Architecture & Intelligence Logic

**Date:** March 31, 2026  
**Target Audience:** AI Engineers, Data Scientists, Vedic Astrology Experts  

---

## 1. Executive Summary
Astro.AI is a sophisticated **Context-Aware Retrieval-Augmented Generation (RAG)** system. Unlike generic LLMs, it anchors AI reasoning in three distinct data layers:
- **Astronomical Layer:** Real-time planetary positions via Swiss Ephemeris.
- **Semantic Memory Layer:** A vector-embedded "Life Story" database (SQLite + ChromaDB).
- **Domain-Specific Knowledge Layer:** 18,000+ chunks of classical Jyotish texts (BPHS, etc.).

The system's goal is to move from "Static Interpretation" to **"Predictive Pattern Matching."**

---

## 2. Technical Architecture & Directory Structure
```text
W:\The Office\Currently Working\Ai Astrologer\jyotish-ai\
├───core\               
│   ├───agent.py            # AI Orchestrator: Context synthesis & LLM Interface
│   ├───astro_engine.py     # Deterministic Layer: High-precision calculations
│   ├───knowledge_base.py   # RAG Engine: ChromaDB vector search (18k chunks)
│   ├───memory.py           # User Layer: Hybrid SQL/Vector life story storage
│   └───pattern_engine.py   # Heuristic Engine: Similarity scoring for transits
├───data\               
│   ├───chroma_db\          # Vector Storage: nomic-embed-text embeddings
│   └───life_events.db      # Relational Storage: Linked to planetary snapshots
├───knowledge\          # Raw Data: BPHS, Nakshatras, etc.
└───main.py             # Entry Point: Gradio UI + Loop
```

---

## 3. The Intelligence Logic: "Triple-Alignment RAG"

When a user asks a question (e.g., *"When will I succeed in trading?"*), the system executes a **Triple-Alignment** pipeline:

### A. Semantic Retrieval (The "What")
The query is embedded using the `nomic-embed-text` model. The system pulls the **top 10-15 most relevant chunks** from the 18,000-chunk knowledge base and the **top 10 relevant life events**.
- **Metric:** Cosine Similarity.
- **Context:** This provides the "Classical Rules" for the specific topic (e.g., Dhana Yogas for Trading).

### B. Planetary Signature Matching (The "When")
The `pattern_engine.py` calculates a **"Signature Similarity Score"** between the current sky and the user's recorded past.
- **Scoring Logic:**
  - `Mahadasha Match`: +25 pts
  - `Saturn/Jupiter House Alignment (±1 House)`: +20 pts each
  - `Rahu/Ketu Axis Identity`: +15 pts
- **Result:** This identifies if the user's current query aligns with a period where they've already had success/failure.

### C. Synthetic Reasoning (The AI Persona)
The context is passed to **Mistral 7B (via Ollama)** with a "Master Astrologer" system prompt. The AI is instructed to:
1.  **Synthesize:** Cross-reference the [Classical Rules] with the [Life Events].
2.  **Verify:** Check if current transits echo past successful patterns.
3.  **Predict:** Generate a non-generic, data-driven timeline.

---

## 4. Code Logic: The Similarity Scorer
```python
def calculate_similarity_score(sig1, sig2):
    """Compares the current 'Planetary Signature' to stored past events."""
    score = 0
    # MD (Mahadasha) weighting
    if sig1["mahadasha"] == sig2["mahadasha"]:
        score += 25
        
    # Saturn (Karma/Career) weighting
    s1, s2 = sig1["saturn_house"], sig2["saturn_house"]
    if abs(s1 - s2) == 0:
        score += 20
    elif abs(s1 - s2) in [1, 11]: # Adjacent houses
        score += 10
    
    return score # Scale 0-100
```

---

## 5. Challenges for AI Experts (The Roadmap)
1.  **Multi-Dimensional Embeddings:** Currently, we embed only text. We need to embed **Planetary Snapshots** as vectors to allow the AI to find "Astrological Similarity" via pure math rather than manual scoring.
2.  **Long-Term Memory Fragmentation:** As the user story grows, how do we prioritize the *most impactful* memories over the most *recent* ones?
3.  **Varga (Divisional) Analysis:** Implementing higher-order RAG that looks at D9 (Navamsha) or D10 (Dashamsha) charts for career-specific queries.

---

## 6. System Requirements
- **Local LLM:** Ollama (Mistral 7B)
- **Vector DB:** ChromaDB (Persistent)
- **Astronomical Library:** Kerykeion (Swiss Ephemeris Wrapper)
- **Interface:** Gradio (Python-based UI)
