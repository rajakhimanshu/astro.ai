"""
scripts/ingest_all_pdfs.py
────────────────────────────────────────────────────
Unified PDF → ChromaDB Knowledge Base Ingestion Script

Processes ALL sources in order:
  1. raw_pdfs/   — 10 classical Vedic astrology texts (BPHS, Encyclopedia, Phaladeepika, etc.)
  2. VedicReport.pdf — Himanshu's personal Kundali report from AstroSage
  3. knowledge/  — Any .txt files already extracted

Run this once (or whenever you add new PDFs).
Already-indexed sources are skipped automatically (use --force to re-index).
────────────────────────────────────────────────────
Usage:
    python scripts/ingest_all_pdfs.py
    python scripts/ingest_all_pdfs.py --force   (re-index everything)
    python scripts/ingest_all_pdfs.py --status  (show current index stats)
"""

import os
import sys
import time
import argparse

# Force UTF-8 on Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── PDF engine ───────────────────────────────────────────────────────────────
try:
    import fitz  # PyMuPDF
except ImportError:
    print("[ERROR] PyMuPDF not found. Install it: pip install pymupdf")
    sys.exit(1)

# ── Vector DB ────────────────────────────────────────────────────────────────
import chromadb
import ollama

# ── Config ───────────────────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
chroma_client = chromadb.PersistentClient(path="data/chroma_db")
COLLECTION = chroma_client.get_or_create_collection("astro_knowledge")

CHUNK_SIZE  = 900    # characters per chunk
OVERLAP     = 150    # overlap between chunks
MIN_CHUNK   = 60     # skip chunks shorter than this

# Sources in priority order — personal report first for quick identification
SOURCES = [
    # (path, label, is_personal_chart)
    ("VedicReport.pdf",                       "VedicReport_Personal_Kundali",   True ),
    ("raw_pdfs/Brihat Parāśara Horā Śhāstra By R. Santhanam.pdf",
                                              "BPHS_Santhanam",                  False),
    ("raw_pdfs/Encyclopedia of Vedic Astrology, Yogas Shanker Adawal.pdf",
                                              "Encyclopedia_Yogas_Adawal",       False),
    ("raw_pdfs/Astrology of the Seers_ A Guide to Vedic_Hindu Astrology ( PDFDrive ).pdf",
                                              "Astrology_of_Seers",              False),
    ("raw_pdfs/How to Judge a Horoscope - R. Santhanam.pdf",
                                              "How_To_Judge_Horoscope",          False),
    ("raw_pdfs/Mantreswara_s__Phaladeeplka_.pdf",
                                              "Phaladeepika_Mantreswara",        False),
    ("raw_pdfs/Uttara Kalamritam.pdf",        "Uttara_Kalamritam",               False),
    ("raw_pdfs/vedic_astro_textbook.pdf",     "Vedic_Astro_Textbook",            False),
    ("raw_pdfs/Brihat Jataka by Varahamihira — another classical text, covers planetary combinations deeply..txt",
                                              "Brihat_Jataka_Varahamihira",      False),
    ("raw_pdfs/6945.pdf",                    "Classical_Text_6945",              False),
    ("raw_pdfs/7888.pdf",                    "Classical_Text_7888",              False),
]

# Also auto-discover any .txt files in knowledge/
KNOWLEDGE_DIR = "knowledge"


# ─────────────────────────────────────────────────────────────────────────────
# Text Extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_text(file_path: str) -> str:
    """Extract text from PDF or TXT file."""
    if file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    doc = fitz.open(file_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append(f"\n[Page {i+1}]\n{text}")
    doc.close()
    return "\n".join(pages)


# ─────────────────────────────────────────────────────────────────────────────
# Smart Chunker
# ─────────────────────────────────────────────────────────────────────────────

def smart_chunk(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """
    Paragraph-aware chunker with overlap.
    Tries to break at paragraph boundaries first, then falls back to character splits.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks      = []
    current     = ""

    for para in paragraphs:
        # If a single paragraph is huge, force-split it
        if len(para) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(para), chunk_size - overlap):
                sub = para[i : i + chunk_size]
                if len(sub) >= MIN_CHUNK:
                    chunks.append(sub)
            continue

        if len(current) + len(para) + 2 <= chunk_size:
            current = (current + "\n\n" + para).lstrip()
        else:
            if current:
                chunks.append(current)
            # Carry overlapping tail into next chunk
            tail    = current[-overlap:] if len(current) > overlap else current
            current = (tail + "\n\n" + para).lstrip()

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) >= MIN_CHUNK]


# ─────────────────────────────────────────────────────────────────────────────
# Embedding with Retry
# ─────────────────────────────────────────────────────────────────────────────

def embed(text: str, retries: int = 3) -> list[float]:
    for attempt in range(retries):
        try:
            resp = ollama.embeddings(model="nomic-embed-text", prompt=text)
            return resp["embedding"]
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"      Embedding retry {attempt+1}/{retries}: {e}")
            time.sleep(2)
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Already-Indexed Check
# ─────────────────────────────────────────────────────────────────────────────

def get_indexed_sources() -> set:
    """Returns a set of source labels already present in ChromaDB."""
    try:
        existing = COLLECTION.get(include=["metadatas"])
        return {m["source"] for m in existing["metadatas"] if m.get("source")}
    except Exception:
        return set()


# ─────────────────────────────────────────────────────────────────────────────
# Process One File
# ─────────────────────────────────────────────────────────────────────────────

def process_file(file_path: str, source_label: str, is_personal: bool = False,
                 force: bool = False) -> int:
    """
    Extracts, chunks, embeds, and upserts one file into ChromaDB.
    Returns number of chunks stored.
    """
    if not os.path.exists(file_path):
        print(f"  [SKIP] File not found: {file_path}")
        return 0

    print(f"\n{'='*70}")
    print(f"  PROCESSING: {source_label}")
    print(f"  File: {file_path}  ({'Personal Kundali' if is_personal else 'Classical Text'})")
    print(f"{'='*70}")

    # Extract
    try:
        text = extract_text(file_path)
    except Exception as e:
        print(f"  [ERROR] Extraction failed: {e}")
        return 0

    if not text.strip():
        print("  [ERROR] No text found.")
        return 0

    print(f"  [OK] Extracted {len(text):,} characters")

    # Chunk
    chunks = smart_chunk(text)
    print(f"  [OK] Created {len(chunks)} chunks")

    # If force, delete old entries for this source first
    if force:
        try:
            existing = COLLECTION.get(where={"source": source_label}, include=["ids"])
            if existing["ids"]:
                COLLECTION.delete(ids=existing["ids"])
                print(f"  [DEL] Deleted {len(existing['ids'])} old entries")
        except Exception:
            pass

    # Embed & upsert
    stored = 0
    batch_ids, batch_embs, batch_docs, batch_meta = [], [], [], []
    BATCH = 50

    for i, chunk in enumerate(chunks):
        try:
            emb = embed(chunk)
            chunk_id = f"kb_{source_label}_{i}"
            batch_ids.append(chunk_id)
            batch_embs.append(emb)
            batch_docs.append(chunk)
            batch_meta.append({
                "source":     source_label,
                "chunk":      i,
                "is_personal": str(is_personal),
                "type":       "personal_kundali" if is_personal else "classical_text",
            })

            if len(batch_ids) >= BATCH:
                COLLECTION.upsert(
                    ids=batch_ids, embeddings=batch_embs,
                    documents=batch_docs, metadatas=batch_meta
                )
                stored += len(batch_ids)
                print(f"    ... {stored}/{len(chunks)} chunks indexed")
                batch_ids, batch_embs, batch_docs, batch_meta = [], [], [], []

        except Exception as e:
            print(f"    [WARN] Chunk {i} failed: {e}")

    # Flush remainder
    if batch_ids:
        COLLECTION.upsert(
            ids=batch_ids, embeddings=batch_embs,
            documents=batch_docs, metadatas=batch_meta
        )
        stored += len(batch_ids)

    print(f"  [DONE] {stored} chunks stored for '{source_label}'")
    return stored


# ─────────────────────────────────────────────────────────────────────────────
# Main Runner
# -----------------------------------------------------------------------------

def show_status():
    """Print current knowledge base statistics."""
    total = COLLECTION.count()
    print(f"\n[KB STATUS]")
    print("-" * 50)
    print(f"  Total chunks indexed: {total:,}")

    try:
        existing = COLLECTION.get(include=["metadatas"])
        source_counts: dict[str, int] = {}
        for m in existing["metadatas"]:
            src = m.get("source", "unknown")
            source_counts[src] = source_counts.get(src, 0) + 1

        print(f"\n  Sources ({len(source_counts)} total):")
        for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            tag = " <- Personal Kundali" if "Personal" in src else ""
            print(f"    {src:<50} {count:>5} chunks{tag}")
    except Exception as e:
        print(f"  (Could not list sources: {e})")
    print()


def main():
    parser = argparse.ArgumentParser(description="Jyotish AI — Knowledge Base Ingestion")
    parser.add_argument("--force",  action="store_true",
                        help="Re-index all sources (overwrite existing)")
    parser.add_argument("--status", action="store_true",
                        help="Show current index statistics and exit")
    parser.add_argument("--source", type=str, default=None,
                        help="Process only a specific source label")
    args = parser.parse_args()

    # Check Ollama
    try:
        ollama.list()
        print("[OK] Ollama is running.")
    except Exception:
        print("[ERROR] Cannot reach Ollama. Start it with: ollama serve")
        sys.exit(1)

    if args.status:
        show_status()
        return

    print("\nJyotish AI -- Knowledge Base Ingestion")
    print(f"    Force re-index: {args.force}")
    print()

    indexed_sources = get_indexed_sources() if not args.force else set()
    total_new = 0

    # ── Process defined sources ──────────────────────────────────────────────
    for file_path, label, is_personal in SOURCES:
        if args.source and args.source not in label:
            continue
        if label in indexed_sources and not args.force:
            print(f"  [SKIP] '{label}' already indexed (use --force to re-index)")
            continue
        total_new += process_file(file_path, label, is_personal, force=args.force)

    # Auto-discover knowledge/*.txt
    if os.path.exists(KNOWLEDGE_DIR):
        for fname in os.listdir(KNOWLEDGE_DIR):
            if not fname.endswith(".txt"):
                continue
            label = f"knowledge_{os.path.splitext(fname)[0]}"
            if args.source and args.source not in label:
                continue
            if label in indexed_sources and not args.force:
                print(f"  [SKIP] '{label}' already indexed")
                continue
            fpath = os.path.join(KNOWLEDGE_DIR, fname)
            total_new += process_file(fpath, label, False, force=args.force)

    print(f"\n{'='*70}")
    print(f"  INGESTION COMPLETE -- {total_new:,} new chunks added")
    show_status()


if __name__ == "__main__":
    main()
