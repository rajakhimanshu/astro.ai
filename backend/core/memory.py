"""
core/memory.py
────────────────────────────────────────────────────────────────
Life Event Memory System — Per-User, ML-Enabled.

FIXES:
  1. add_event() now accepts user_id and uses per-user birth data/natal chart.
  2. get_all_events() added for the UI to display logged events.
  3. Per-user SQLite DB paths (data/users/<user_id>/events.db).
  4. Graceful fallback when Ollama embeddings are unavailable.
────────────────────────────────────────────────────────────────
"""

import sqlite3
import chromadb
import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
USERS_DIR = DATA_DIR / "users"
os.makedirs(DATA_DIR, exist_ok=True)

# Global ChromaDB client — shared collection with user-specific metadata
chroma_client = chromadb.PersistentClient(path=str(DATA_DIR / "chroma_db"))
collection = chroma_client.get_or_create_collection('life_events')


# ─────────────────────────────────────────────────────────────────────────────
# DB Setup (per-user)
# ─────────────────────────────────────────────────────────────────────────────

def _get_user_db_path(user_id: str = None) -> Path:
    """Returns per-user DB path if user_id provided, else global fallback."""
    if user_id:
        udir = USERS_DIR / user_id
        udir.mkdir(parents=True, exist_ok=True)
        return udir / "events.db"
    return DATA_DIR / "life_events.db"


def init_database(user_id: str = None):
    """Initialize the SQLite events database for a user."""
    db_path = _get_user_db_path(user_id)
    conn = sqlite3.connect(str(db_path))
    conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            date TEXT,
            title TEXT,
            description TEXT,
            domain TEXT,
            emotion_score INTEGER,
            outcome TEXT,
            planet_snapshot TEXT,
            dasha TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()
    return str(db_path)


def _get_conn(user_id: str = None):
    """Get a SQLite connection for the appropriate user DB."""
    db_path = _get_user_db_path(user_id)
    init_database(user_id)
    return sqlite3.connect(str(db_path))


# ─────────────────────────────────────────────────────────────────────────────
# Embedding (Ollama optional)
# ─────────────────────────────────────────────────────────────────────────────

def embed_text(text: str):
    """
    Convert text to embedding using Ollama nomic-embed-text.
    Returns None if Ollama is unavailable (Groq-only mode) — never crashes.
    """
    try:
        import ollama
        response = ollama.embeddings(model='nomic-embed-text', prompt=text)
        return response.get('embedding') or response.get('embeddings')
    except Exception as e:
        print(f"  [EMBEDDING] Ollama unavailable: {e} — skipping semantic indexing")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Event Logging
# ─────────────────────────────────────────────────────────────────────────────

def add_event(
    date: str,
    title: str,
    description: str,
    domain: str,
    emotion_score: int = 0,
    outcome: str = '',
    user_id: str = None
) -> int:
    """
    Add a life event to the user's SQLite DB and ChromaDB (if embeddings available).
    
    Args:
        date: ISO date string (YYYY-MM-DD)
        title: Short title of the event
        description: Detailed description
        domain: Category (career, health, relationship, finance, spiritual, general)
        emotion_score: -5 (very bad) to +5 (very good)
        outcome: What happened as a result
        user_id: The user this event belongs to
    """
    from pathlib import Path
    
    dt = datetime.strptime(date, '%Y-%m-%d')

    # ── Get user-specific birth data and natal chart ──────────────────────────
    dasha_str = "Dasha data unavailable"
    snapshot_dict = {}

    try:
        if user_id:
            # Load from per-user profile
            from core.user_profile_engine import load_user_profile
            from core.astro_engine import get_sky_on_date, get_planet_snapshot_dict, calculate_vimshottari_dasha

            profile = load_user_profile(user_id)
            birth = profile['meta']['birth']
            birth_dt = datetime(birth['year'], birth['month'], birth['day'],
                                birth['hour'], birth['minute'])
            moon_lon = profile['planets']['Moon']['abs_pos']

            dasha_info = calculate_vimshottari_dasha(birth_dt, moon_lon, target_dt=dt)
            if "error" not in dasha_info:
                dasha_str = dasha_info['summary']
                sky = get_sky_on_date(
                    dt.year, dt.month, dt.day, 12, 0,
                    birth.get("city", "Delhi"), birth.get("nation", "IN"),
                )
                snapshot_dict = get_planet_snapshot_dict(sky, dasha_info)
        else:
            # Fallback: use default birth data
            from core.astro_engine import (
                load_birth_data, get_natal_chart,
                get_sky_on_date, get_planet_snapshot_dict, calculate_vimshottari_dasha
            )
            bd = load_birth_data()
            birth_dt = datetime(bd['year'], bd['month'], bd['day'], bd['hour'], bd['minute'])
            natal_chart = get_natal_chart()
            moon_lon = natal_chart.model().moon.abs_pos
            dasha_info = calculate_vimshottari_dasha(birth_dt, moon_lon, target_dt=dt)
            if "error" not in dasha_info:
                dasha_str = dasha_info['summary']
                sky = get_sky_on_date(dt.year, dt.month, dt.day)
                snapshot_dict = get_planet_snapshot_dict(sky, dasha_info)
    except Exception as e:
        print(f"  [EVENT] Dasha/snapshot computation failed: {e}")

    planet_snapshot_json = json.dumps(snapshot_dict)

    # ── Save to SQLite ────────────────────────────────────────────────────────
    conn = _get_conn(user_id)
    conn.execute(
        'INSERT INTO events VALUES (NULL,?,?,?,?,?,?,?,?,?,?)',
        (user_id or "global", date, title, description, domain,
         emotion_score, outcome, planet_snapshot_json, dasha_str,
         datetime.now().isoformat())
    )
    conn.commit()
    event_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()

    # Auto-suggest rectification after 3+ events (non-blocking)
    if user_id:
        try:
            total = len(get_all_events(user_id))
            if total >= 3 and total % 3 == 0:
                from core.rectification_engine import rectify_user_profile
                rectify_user_profile(user_id, window_minutes=30)
        except Exception as e:
            print(f"  [RECTIFY] Auto-rectification skipped: {e}")

    # ── Semantic index via ChromaDB ───────────────────────────────────────────
    embed_text_content = f'{title}. {description}. Domain: {domain}. Outcome: {outcome}'
    embedding = embed_text(embed_text_content)
    if embedding is not None:
        try:
            chroma_id = f"evt_{user_id or 'global'}_{event_id}"
            collection.add(
                ids=[chroma_id],
                embeddings=[embedding],
                documents=[embed_text_content],
                metadatas=[{
                    'user_id': user_id or 'global',
                    'date': date,
                    'domain': domain,
                    'emotion': emotion_score,
                    'planets': planet_snapshot_json,
                    'dasha': dasha_str
                }]
            )
        except Exception as e:
            print(f"  [CHROMADB] Index failed: {e}")

    print(f"  [EVENT] Saved: '{title}' | Domain: {domain} | Emotion: {emotion_score} | Dasha: {dasha_str[:60]}...")
    return event_id


# ─────────────────────────────────────────────────────────────────────────────
# Event Retrieval
# ─────────────────────────────────────────────────────────────────────────────

def get_all_events(user_id: str = None) -> list:
    """
    Retrieve all events for a user, sorted newest first.
    Returns a list of dicts for the UI.
    """
    try:
        conn = _get_conn(user_id)
        rows = conn.execute(
            'SELECT id, date, title, description, domain, emotion_score, outcome, dasha, created_at '
            'FROM events ORDER BY date DESC'
        ).fetchall()
        conn.close()
        return [
            {
                "id": r[0], "date": r[1], "title": r[2], "description": r[3],
                "domain": r[4], "emotion_score": r[5], "outcome": r[6],
                "dasha": r[7], "created_at": r[8]
            }
            for r in rows
        ]
    except Exception as e:
        print(f"  [EVENT] get_all_events failed: {e}")
        return []


def search_events(query: str, n_results: int = 5, user_id: str = None) -> dict:
    """
    Semantic search over life events.
    Filters by user_id if provided.
    Returns empty result structure (not an exception) if embeddings unavailable.
    """
    empty = {'documents': [[]], 'metadatas': [[]]}
    try:
        embedding = embed_text(query)
        if embedding is None:
            # Fallback to SQLite keyword search
            return _keyword_search_events(query, n_results, user_id)

        where_filter = {"user_id": user_id} if user_id else None
        count = collection.count()
        if count == 0:
            return empty

        actual_n = min(n_results, count)
        if where_filter:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=actual_n,
                where=where_filter
            )
        else:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=actual_n
            )
        return results
    except Exception as e:
        print(f"  [MEMORY] Semantic search failed: {e}")
        return _keyword_search_events(query, n_results, user_id)


def _keyword_search_events(query: str, n_results: int = 5, user_id: str = None) -> dict:
    """Fallback keyword-based search when embeddings are unavailable."""
    try:
        conn = _get_conn(user_id)
        keywords = query.lower().split()
        conditions = ' OR '.join(['lower(title) LIKE ? OR lower(description) LIKE ?' for _ in keywords])
        params = []
        for kw in keywords:
            params.extend([f'%{kw}%', f'%{kw}%'])
        
        rows = conn.execute(
            f'SELECT title, description, domain, dasha, date FROM events WHERE {conditions} LIMIT ?',
            params + [n_results]
        ).fetchall()
        conn.close()
        
        docs = [f"{r[0]}. {r[1]}. Domain: {r[2]}. Dasha: {r[3]}. Date: {r[4]}" for r in rows]
        return {'documents': [docs], 'metadatas': [[]]}
    except Exception:
        return {'documents': [[]], 'metadatas': [[]]}


# ─────────────────────────────────────────────────────────────────────────────
# ML Empirical Feedback Engine
# ─────────────────────────────────────────────────────────────────────────────

def analyze_planetary_empirical_performance(user_id: str = None) -> dict:
    """
    Event Correction Engine (Empirical ML Feedback):
    Analyzes all past logged events to calculate a real-world 'functional benefic/malefic'
    score for each planet, based on the emotion_score when that planet was active in Dasha.
    
    This is what makes the system learn from lived experience.
    """
    try:
        conn = _get_conn(user_id)
        events = conn.execute('SELECT emotion_score, dasha FROM events').fetchall()
        conn.close()
    except Exception:
        return {}

    planet_scores = {p: {"score": 0, "count": 0} for p in [
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
    ]}

    for emotion, dasha_str in events:
        if not dasha_str:
            continue
        for p in planet_scores.keys():
            if p in dasha_str:
                planet_scores[p]["score"] += emotion
                planet_scores[p]["count"] += 1

    # Prediction ledger learning (verified hits/misses)
    try:
        if user_id:
            from core.prediction_ledger import _init_predictions_table
            _init_predictions_table(user_id)
            conn = _get_conn(user_id)
            pred_rows = conn.execute(
                "SELECT convergence_json, status, outcome_score FROM predictions WHERE status IN ('hit','miss')"
            ).fetchall()
            conn.close()
            for conv_json, status, oscore in pred_rows:
                if not conv_json:
                    continue
                conv = json.loads(conv_json)
                weight = 1 if status == "hit" else -1
                for sig in conv.get("signals", []):
                    detail = sig.get("detail", "")
                    for p in planet_scores:
                        if p in detail and sig.get("active"):
                            planet_scores[p]["score"] += weight * max(1, abs(oscore or 2))
                            planet_scores[p]["count"] += 1
    except Exception:
        pass

    results = {}
    for p, data in planet_scores.items():
        if data["count"] > 0:
            avg_score = data["score"] / data["count"]
            if avg_score > 2:
                status = "Highly Productive (Empirically)"
            elif avg_score > 0:
                status = "Productive (Empirically)"
            elif avg_score == 0:
                status = "Neutral (Empirically)"
            elif avg_score > -2:
                status = "Challenging (Empirically)"
            else:
                status = "Highly Challenging (Empirically)"

            results[p] = {
                "avg_emotion": round(avg_score, 2),
                "event_count": data["count"],
                "empirical_status": status,
                "interpretation": (
                    f"Based on {data['count']} logged events + verified predictions, {p} periods have been "
                    f"{status.lower()} for you personally (avg score: {avg_score:+.1f})."
                )
            }

    return results


def get_events_in_range(start_date: str, end_date: str, user_id: str = None) -> list:
    """Get events within a date range."""
    try:
        conn = _get_conn(user_id)
        events = conn.execute(
            'SELECT * FROM events WHERE date BETWEEN ? AND ? ORDER BY date',
            (start_date, end_date)
        ).fetchall()
        conn.close()
        return events
    except Exception:
        return []
