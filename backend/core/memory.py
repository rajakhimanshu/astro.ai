import sqlite3
import chromadb
import ollama
import json
import os
from datetime import datetime
from core.astro_engine import (
    get_sky_on_date, 
    calculate_vimshottari_dasha, 
    load_birth_data, 
    get_planet_snapshot_dict
)

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# Setup ChromaDB (stores in your data/ folder)
chroma_client = chromadb.PersistentClient(path='data/chroma_db')
collection = chroma_client.get_or_create_collection('life_events')

# Setup SQLite database
def init_database():
    conn = sqlite3.connect('data/life_events.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    return conn

# Convert text to embedding vector using nomic model
def embed_text(text):
    response = ollama.embeddings(model='nomic-embed-text', prompt=text)
    return response['embedding']

# Add a life event to both databases
def add_event(date, title, description, domain,
              emotion_score=0, outcome=''):
    # 1. Parse the event date
    dt = datetime.strptime(date, '%Y-%m-%d')

    # 2. Get birth data for dasha calculation
    bd = load_birth_data()
    birth_dt = datetime(bd['year'], bd['month'], bd['day'], bd['hour'], bd['minute'])
    
    # We need the Moon's longitude at BIRTH to calculate any dasha in life
    # Let's get the natal chart once
    from core.astro_engine import get_natal_chart
    natal_chart = get_natal_chart()
    moon_lon_at_birth = natal_chart.model().moon.abs_pos

    # 3. Calculate dasha for the EVENT date
    dasha_info = calculate_vimshottari_dasha(birth_dt, moon_lon_at_birth, target_dt=dt)
    if "error" in dasha_info:
        dasha_str = f"Dasha data unavailable for this date: {dasha_info['error']}"
        # Provide a dummy snapshot if dasha fails
        snapshot_dict = {"error": dasha_info['error']}
    else:
        dasha_str = dasha_info['summary']
        # 4. Get planetary snapshot for the EVENT date
        sky = get_sky_on_date(dt.year, dt.month, dt.day)
        snapshot_dict = get_planet_snapshot_dict(sky, dasha_info)

    planet_snapshot_json = json.dumps(snapshot_dict)

    # 5. Save to SQLite
    conn = init_database()
    conn.execute(
        'INSERT INTO events VALUES (NULL,?,?,?,?,?,?,?,?,?)',
        (date, title, description, domain,
         emotion_score, outcome, planet_snapshot_json, dasha_str, datetime.now().isoformat())
    )
    conn.commit()
    event_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()

    # 6. Save to ChromaDB for semantic search
    full_text = f'{title}. {description}. Outcome: {outcome}'
    embedding = embed_text(full_text)
    collection.add(
        ids=[str(event_id)],
        embeddings=[embedding],
        documents=[full_text],
        metadatas=[{
            'date': date, 
            'domain': domain,
            'emotion': emotion_score, 
            'planets': planet_snapshot_json,
            'dasha': dasha_str
        }]
    )
    print(f'Event saved: {title} (Dasha: {dasha_str})')
    return event_id

# Search life events by meaning
def search_events(query, n_results=5):
    query_embedding = embed_text(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results

# Get all events in a date range
def get_events_in_range(start_date, end_date):
    conn = init_database()
    events = conn.execute(
        'SELECT * FROM events WHERE date BETWEEN ? AND ? ORDER BY date',
        (start_date, end_date)
    ).fetchall()
    conn.close()
    return events
