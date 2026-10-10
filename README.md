# Astro.AI

Astro.AI is an advanced, high-precision Vedic astrology oracle. Built with a robust backend architecture and a modern web interface, Astro.AI provides deep, multi-layered astrological insights. It synthesizes natal charts, planetary transits, dasha cycles, and historical life events to deliver personalized, data-driven analysis.

## Features

- **12-Layer Astrological Context**: Integrates Natal, Aspects, Lordships, Yogas, Nakshatras, Dasha, Transits, Divisional Charts, and more.
- **RAG Pipeline**: Analyzes classic astrological texts combined with personal history.
- **Live Transit Analysis**: Real-time celestial updates and their implications.
- **Timing Engine**: Month-by-month dasha × double-transit scan that produces ranked prediction windows per life topic.
- **Microservice Architecture**: Python/FastAPI backend with a dedicated, responsive Next.js frontend.
- **Multi-user Support**: Manage multiple user profiles dynamically to receive tailored horoscopes.

## Project Structure

- `/backend` - The core AI, astronomical calculation engine, and FastAPI server.
- `/frontend` - The user-facing Next.js dashboard providing rich visualization and interactive Q&A.
- `/docs` - System architecture, knowledge bases, and project status details.
- `ENG_DEPTH.md` - Comprehensive engineering and architectural overview of the system.

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- An LLM: a free [Groq API key](https://console.groq.com/keys) **or** [Ollama](https://ollama.com) running locally (`ollama pull mistral`)

### Run it
```bash
git clone https://github.com/rajakhimanshu/astro.ai.git
cd astro.ai
```

Windows (PowerShell):
```powershell
./start.ps1
```

macOS / Linux:
```bash
chmod +x start.sh && ./start.sh
```

The first run creates a Python virtual environment, installs all dependencies, and copies `.env.example` to `.env`. Put your `GROQ_API_KEY` in `.env` (or set `LLM_MODE=ollama`), then open **http://localhost:3000**, click **New Enrollment**, and enter your name, birth date, 24-hour birth time and birth city. Your chart is computed instantly and the consultation starts.

Your profile, life events and chat memory are stored only on your machine in `backend/data/` (git-ignored). No GeoNames account is needed; set `GEONAMES_USERNAME` in `.env` only if you hit city-lookup rate limits.

### Manual setup (optional)
```bash
# Backend — http://127.0.0.1:8001
cd backend
pip install -r requirements.txt
python main.py

# Frontend — http://localhost:3000 (in a second terminal)
cd frontend
npm install
npm run dev
```
Set `BACKEND_URL` before `npm run dev` if the backend runs somewhere other than `http://127.0.0.1:8001`.

## Timing Engine

Timing questions ("when will I get promoted / married?") are answered from a deterministic month-by-month scan, not by the LLM guessing. For the next three years the engine scores every month for the topic by combining:

- **Dasha-lord significance** — how each running MD/AD/PD lord is wired to the topic: house ownership, placement, graha drishti, conjunction with the topic lord, nakshatra (star) lord, karaka role, and placement in the topic's divisional chart
- **MD ↔ AD relationship** — 6/8 and 2/12 friction between the period lords
- **Double transit** — Jupiter and Saturn both influencing the topic house or its lord, from Lagna and from the Moon
- **Ashtakavarga** support for the transited signs

Strong consecutive months merge into ranked windows (HIGH / MEDIUM / LOW) with the reasons attached. The LLM may only quote these windows; when the chart shows no clear trigger, it says so instead of inventing dates. Query it directly with `GET /api/users/{id}/timing?topic=career&years=3`.

See `ENG_DEPTH.md` and `docs/ACCURACY_STACK.md` for details on the prediction-learning pipeline.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
