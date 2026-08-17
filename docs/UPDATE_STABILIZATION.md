# Jyotish-AI System Update & Stabilization

## Critical System Issues Resolved

### Backend Engine & Logic
*   **`.env` Parsing Failure:** The `GROQ_API_KEY` was accidentally concatenated with `GEONAMES_PASSWORD` on a single line (`...H9hGROQ_API_KEY=gsk_...`), rendering the API key invisible to the python environment and gracefully but silently falling back to Ollama. **Fixed.**
*   **Dynamic Data Context Integration (`agent.py`):** The agent context builder was silently bypassing dynamically calculated user profiles in favor of a hardcoded `birth_data.yaml`. This caused static outputs regardless of which user was actually loaded. The system now parses strength, yogas, dasha bounds, and 12-layer data natively through the `profile.json`.
*   **`shadbala_engine.py` Refactoring:** Previous values were strictly hardcoded to a single user baseline (User's data points). Re-engineered the file to compute `shadbala_rupas` dynamically per user, evaluating *Uccha Bala* (exaltation deviation), *Kendradi Bala*, *Naisargika*, and *Chesta Bala* in virupas accurately. Every user receives a bespoke result.
*   **Sign-Name Mismatch Crash:** `ashtakavarga.py` used truncated 3-character keys (e.g. "Ari", "Tau") leading to a fatal KeyErrors as Kerykeion v4 objects return fullname values ("Aries") for planetary coordinates. **Fixed by providing generalized lookup maps for any version.**
*   **Dasha Engine Error:** Removed the outdated references to `natal` inside the Dasha block of `agent.py`, converting it to query directly against profile `birth_dt`, completely restoring live Vimshottari calculations.
*   **Kerykeion GeoAuth Integration:** `forecast_engine.py` failed to bind to a geonames auth, running in blind-tropical fallback mode without it. Updated the engine to properly pass the `.env` `GEONAMES_USERNAME` with strict Sidereal/Lahiri parameters. 

### Frontend UI & Architecture
*   **Next.js Critical Vulnerability Update:** Pinned Next.js to Version 15.3.1 to patch a publicly tracked zero-day framework issue (CVE-2025-66478).
*   **Lucide-React Artifact Fixed:** Pinned the non-existent `^1.8.0` request for `lucide-react` back to `^0.469.0` so tests/rendering successfully passes.
*   **Flex-box Parity Broken:** The DOM failed to extend fully into the screen due to missing `html, body { height: 100%; width: 100% }` sizing statements.
*   **Paper Texture Hover Blocking:** `globals.css` assigned an absolute pseudo-element rendering over top of interactive layout buttons, suppressing pointer-events. Modified `z-index` to `-1` to resolve UI clicks correctly across the site.
*   **Class Collisions:** `layout.tsx` was aggressively targeting `className="dark" text-white`, stripping away the newly-introduced custom HSL ink palettes designed for the professional cream/ivory styling update. Cleaned layout nodes to utilize `<body className="h-full">`.

### Module Resiliency 
*   **ChromaDB Exception Halts:** Memory embedding searches against `nomic-embed-text` now soft-fail when the local `.ollama` runtime is inactive, allowing searches to continue functionally instead of throwing unrecoverable 500 exceptions down the stack flow.

**Status:** The system is live with frontend and backend processes successfully spun-up. All endpoints have stable logic paths. The Agent successfully aggregates 12 contextual layers and falls back organically to Groq correctly.
