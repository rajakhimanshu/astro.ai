# Astro.AI: Engineering Depth & Architecture

Astro.AI is engineered to be a state-of-the-art Vedic astrology intelligence system. Rather than providing generic template-based horoscopes, the system dynamically calculates a profound 12-layer astrological context using high-precision ephemeris data and feeds it into an advanced Retrieval-Augmented Generation (RAG) pipeline for deeply personalized insights.

## Core Architecture

The architecture is divided into a specialized Python backend dedicated to heavy astronomical computations and an interactive Next.js frontend tailored for dynamic, conversational user experiences.

### 1. The Astronomical Calculation Engine (Python / FastAPI)

The backend is built around `kerykeion` and the Swiss Ephemeris. This ensures that calculations for planetary degrees, nakshatras, and divisional charts (Vargas) are accurate down to the minute. 

**Key Components:**
- **Profile Generation (`user_profile_engine.py`)**: Computes everything from the ascendant degree to the deep Ashtakavarga and Shadbala scores. It compiles a comprehensive `profile.json` per user that acts as the source of truth for the AI.
- **Divisional Charts (Vargas)**: Not just D1 (Rashi) and D9 (Navamsa), but computations extending to D10 (Dashamsa) and up to D60 (Shashtyamsa) proxy estimations.
- **Vimshottari Dasha Engine**: Accurately tracks planetary time periods, calculating Mahadasha, Antardasha, and Pratyantardasha based on the Moon's exact natal degree.
- **Yoga Detection Engine**: Scans the chart for hundreds of planetary combinations (e.g., Gajakesari Yoga, Dhana Yogas, Viparita Raja Yogas) and appends their specific effects to the prompt context.
- **Remedial Engine**: Analyzes Shadbala strength to identify weak planets and dynamically generates personalized remedies (mantras, gemstones, behavioral shifts).

### 2. Multi-Layer Context Pipeline (RAG)

To provide human-like astrological counseling, the system utilizes a 12-Layer context building approach. When a user asks a question, the LLM receives:

1. **Static Natal Profile**: Lagna, Rashi, and exact degrees.
2. **Dynamic Planetary Dignities**: Exaltation, debilitation, retrograde status.
3. **House Analysis**: Occupants, lords, and aspects.
4. **Ashtakavarga Strength**: House-by-house point accumulation (SAV).
5. **Dasha Timeline**: Current active planetary periods and their intersecting themes.
6. **Live Transits**: Current ephemeris compared against natal positions.
7. **Classical Texts (RAG)**: Integration of Parashara, Jaimini, and other classical knowledge parsed via a vector database.
8. **Karmic & Spiritual Layer**: Analysis of the nodal axis (Rahu/Ketu).

This immense text context is parsed and structured so the LLM acts as an expert astrologer synthesizing complex overlapping rules, rather than a generic text generator.

### 3. The Conversational Frontend (Next.js)

The frontend is built using Next.js to provide a rich, interactive dashboard.
- **Micro-Animations & Glassmorphism**: For a premium, spiritual, yet highly modern aesthetic.
- **Dynamic Routing**: Easy switching between chart visualization, dasha timelines, and the chat interface.
- **Real-Time Streaming**: Utilizing server-sent events or WebSocket for streaming AI responses token-by-token.

## Data Storage & Privacy

User data is stored locally in `data/users/<user_id>/`. The system uses `birth_data.yaml` as the intake point and generates a full `profile.json`.

**Important setup requirement for Geonames:**
The system uses Geonames for translating city strings (like "New York") into exact latitude/longitude coordinates required for house calculation. Users must set `GEONAMES_USERNAME` in their `.env` file to their own registered Geonames account.

## Future Engineering Goals
- **Full Vector DB Implementation**: For expanding the RAG capabilities across thousands of case studies.
- **Local LLM Support**: Running entirely offline via Ollama for maximum privacy.
- **Temporal Event Memory**: A database to track life events (marriage, job changes) to continually rectify the birth time automatically based on AI analysis.
