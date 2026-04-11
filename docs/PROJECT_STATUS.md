# Astro.AI - Project Status Report

## 1. System Overview
Astro.AI is a personalized Vedic Astrology intelligence that combines real-time planetary calculations, a long-term memory of life events, and a technical knowledge base to provide non-generic, data-driven insights.

## 2. Core Components Built
- **Astro Engine (`core/astro_engine.py`):** Uses `kerykeion` and `swisseph` for high-precision Sidereal (Lahiri) calculations. It supports the Whole Sign House system and provides detailed reports on natal positions and current transits.
- **Memory System (`core/memory.py`):** A dual-database setup. 
    - **SQLite:** Stores structured life event data (dates, domains, descriptions).
    - **ChromaDB (Vector DB):** Stores semantic embeddings of life events for "meaning-based" retrieval using the `nomic-embed-text` model.
- **Knowledge Base (`core/knowledge_base.py`):** A Vector database containing technical astrological rules, planet meanings, and house interpretations.
- **The Agent (`core/agent.py`):** The orchestrator. It uses `Ollama` (Mistral 7B) to synthesize birth data, transits, relevant past life events, and technical knowledge into a final response.
- **Web UI (`ui/app.py` & `main.py`):** A Gradio-based interface with tabs for Chatting and adding Life Events.

## 3. Current Data & Knowledge
- **User Data:** Loaded from `config/birth_data.yaml`.
- **Life History:** Populated from `data/my_story.txt` and manual entries in the UI.
- **Astrology Knowledge:** 
    - Initial text files in `/knowledge/` (Nakshatras, Dashas, Planet Meanings, etc.).
    - Reference PDF: *Brihat Parāśara Horā Śhāstra*.

## 4. Pending Knowledge Expansion
- **Source:** New "study data" folder and various PDFs.
- **Challenges:** 
    - Hindi language support.
    - Scanned/Image-based PDFs (requires OCR).
    - Complex text extraction from technical manuals.
