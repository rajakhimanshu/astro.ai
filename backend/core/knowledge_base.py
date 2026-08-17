"""
core/knowledge_base.py
────────────────────────────────────────
RAG Knowledge Base for Astro.AI.
Indexes classical Jyotish texts and provides semantic search.

FIX: Graceful degradation when Ollama is unavailable (Groq-only mode).
embed_text() returns None instead of crashing. search_knowledge() returns []
gracefully so the rest of the pipeline continues normally.
"""

import chromadb
import os
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
os.makedirs(DATA_DIR, exist_ok=True)

# Separate ChromaDB collection for astrology knowledge
chroma_client = chromadb.PersistentClient(path=str(DATA_DIR / "chroma_db"))
knowledge_collection = chroma_client.get_or_create_collection('astro_knowledge')


def embed_text(text: str):
    """
    Convert text to embedding using Ollama nomic-embed-text.
    Returns None gracefully if Ollama is unavailable (e.g., Groq-only mode).
    """
    try:
        import ollama
        response = ollama.embeddings(model='nomic-embed-text', prompt=text)
        return response.get('embedding') or response.get('embeddings')
    except Exception as e:
        print(f"  [KB-EMBED] Ollama unavailable: {e} — skipping embedding")
        return None


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Chunks text into overlapping parts for better RAG retrieval."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks


def source_is_indexed(source_label: str) -> bool:
    """True if ChromaDB already has chunks for this source."""
    try:
        if knowledge_collection.count() == 0:
            return False
        existing = knowledge_collection.get(where={"source": source_label}, limit=1)
        return bool(existing and existing.get("ids"))
    except Exception:
        return False


def upsert_knowledge_chunks(
    source_label: str,
    chunks: list,
    metadata: dict = None,
    force: bool = False,
) -> int:
    """
    Embed and upsert text chunks into astro_knowledge collection.
    Returns number of chunks stored.
    """
    if force:
        try:
            existing = knowledge_collection.get(where={"source": source_label})
            if existing.get("ids"):
                knowledge_collection.delete(ids=existing["ids"])
        except Exception:
            pass
    elif source_is_indexed(source_label):
        return 0

    meta_base = dict(metadata or {})
    meta_base["source"] = source_label
    stored = 0
    batch_ids, batch_embs, batch_docs, batch_meta = [], [], [], []

    for i, chunk in enumerate(chunks):
        if not chunk or len(chunk.strip()) < 40:
            continue
        emb = embed_text(chunk)
        if emb is None:
            print(f"  [KB] Skip chunk {i} — embedding unavailable")
            continue
        meta = {**meta_base, "chunk": i}
        batch_ids.append(f"kb_{source_label}_{i}")
        batch_embs.append(emb)
        batch_docs.append(chunk)
        batch_meta.append(meta)

        if len(batch_ids) >= 50:
            knowledge_collection.upsert(
                ids=batch_ids, embeddings=batch_embs,
                documents=batch_docs, metadatas=batch_meta,
            )
            stored += len(batch_ids)
            batch_ids, batch_embs, batch_docs, batch_meta = [], [], [], []

    if batch_ids:
        knowledge_collection.upsert(
            ids=batch_ids, embeddings=batch_embs,
            documents=batch_docs, metadatas=batch_meta,
        )
        stored += len(batch_ids)

    return stored


def add_knowledge_chunk(text: str, source: str, metadata: dict = None) -> bool:
    """Add a single knowledge chunk (used by legacy scripts)."""
    n = upsert_knowledge_chunks(source_label=source, chunks=[text], metadata=metadata, force=False)
    return n > 0


def get_knowledge_stats() -> dict:
    """Summary of indexed knowledge base."""
    try:
        total = knowledge_collection.count()
        if total == 0:
            return {"total_chunks": 0, "sources": {}, "youtube_videos": 0}

        sample = knowledge_collection.get(limit=min(total, 5000), include=["metadatas"])
        sources = {}
        youtube = 0
        for m in sample.get("metadatas") or []:
            src = m.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
            if m.get("type") == "youtube" or str(src).startswith("youtube_"):
                youtube += 1
        return {
            "total_chunks": total,
            "sources": sources,
            "youtube_videos": len([s for s in sources if s.startswith("youtube_")]),
            "source_count": len(sources),
        }
    except Exception as e:
        return {"total_chunks": 0, "error": str(e)}


def index_all_knowledge():
    """
    Index all .txt files in the knowledge/ directory into ChromaDB.
    Requires Ollama to be running (nomic-embed-text model).
    """
    global knowledge_collection

    try:
        chroma_client.delete_collection('astro_knowledge')
    except Exception:
        pass
    knowledge_collection = chroma_client.create_collection('astro_knowledge')

    print(f"-> Starting indexing from '{KNOWLEDGE_DIR}'...")

    total_chunks = 0
    if not KNOWLEDGE_DIR.exists():
        print(f"   [ERROR] Knowledge directory not found: {KNOWLEDGE_DIR}")
        return

    for filename in os.listdir(KNOWLEDGE_DIR):
        if not filename.endswith('.txt'):
            continue

        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        print(f"   Processing {filename}...")

        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

            if len(text) < 5000:
                chunks = [c.strip() for c in text.split('\n\n') if len(c.strip()) > 10]
            else:
                chunks = chunk_text(text)

            all_ids = []
            all_embeddings = []
            all_docs = []
            all_metas = []

            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                emb = embed_text(chunk)
                if emb is None:
                    print(f"   [SKIP] Embedding failed for chunk {i} of {filename}")
                    continue

                all_ids.append(f"kb_{filename}_{i}_{datetime.datetime.now().timestamp()}")
                all_embeddings.append(emb)
                all_docs.append(chunk)
                all_metas.append({'source': filename, 'chunk': i})

                if len(all_ids) >= 100:
                    knowledge_collection.add(
                        ids=all_ids,
                        embeddings=all_embeddings,
                        documents=all_docs,
                        metadatas=all_metas
                    )
                    total_chunks += len(all_ids)
                    all_ids, all_embeddings, all_docs, all_metas = [], [], [], []

            if all_ids:
                knowledge_collection.add(
                    ids=all_ids,
                    embeddings=all_embeddings,
                    documents=all_docs,
                    metadatas=all_metas
                )
                total_chunks += len(all_ids)

    print(f"✅ Indexed {total_chunks} knowledge chunks into 'astro_knowledge' collection.")


def search_knowledge(query: str, n_results: int = 4) -> list:
    """
    Semantic search over the astrology knowledge base.
    Returns empty list gracefully if Ollama is unavailable or collection is empty.
    """
    try:
        query_embedding = embed_text(query)
        if query_embedding is None:
            return []

        # Check if collection has any data
        count = knowledge_collection.count()
        if count == 0:
            return []

        # Don't request more results than we have
        actual_n = min(n_results, count)
        results = knowledge_collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_n
        )
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        print(f"  [KB-SEARCH] Search failed gracefully: {e}")
        return []


if __name__ == '__main__':
    index_all_knowledge()
