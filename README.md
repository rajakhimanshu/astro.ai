# Astro.AI

Astro.AI is an advanced, high-precision Vedic astrology oracle. Built with a robust backend architecture and a modern web interface, Astro.AI provides deep, multi-layered astrological insights. It synthesizes natal charts, planetary transits, dasha cycles, and historical life events to deliver personalized, data-driven analysis.

## Features

- **12-Layer Astrological Context**: Integrates Natal, Aspects, Lordships, Yogas, Nakshatras, Dasha, Transits, Divisional Charts, and more.
- **RAG Pipeline**: Analyzes classic astrological texts combined with personal history.
- **Live Transit Analysis**: Real-time celestial updates and their implications.
- **Microservice Architecture**: Python/FastAPI backend with a dedicated, responsive Next.js frontend.
- **Multi-user Support**: Manage multiple user profiles dynamically to receive tailored horoscopes.

## Project Structure

- `/backend` - The core AI, astronomical calculation engine, and FastAPI server.
- `/frontend` - The user-facing Next.js dashboard providing rich visualization and interactive Q&A.
- `/docs` - System architecture, knowledge bases, and project status details.

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+

### Backend Setup
1. Navigate to the `backend` directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API:
   ```bash
   python main.py
   ```
   The backend will be available at `http://0.0.0.0:8000`.

### Frontend Setup
1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:3000`.

## License

This project is proprietary.
