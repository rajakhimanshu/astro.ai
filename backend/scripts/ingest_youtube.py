"""
CLI: ingest YouTube videos/playlists into the knowledge base.

Usage:
    python scripts/ingest_youtube.py "https://youtube.com/watch?v=..."
    python scripts/ingest_youtube.py "https://youtube.com/playlist?list=..." --force
    python scripts/ingest_youtube.py url1 url2 url3
"""
import sys
import os
import argparse

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.youtube_ingest import ingest_urls


def main():
    parser = argparse.ArgumentParser(description="Ingest YouTube captions into Jyotish RAG")
    parser.add_argument("urls", nargs="+", help="YouTube video or playlist URL(s)")
    parser.add_argument("--force", action="store_true", help="Re-index even if already ingested")
    args = parser.parse_args()

    print("=" * 60)
    print("  Jyotish AI — YouTube Knowledge Ingest")
    print("=" * 60)
    result = ingest_urls(args.urls, force=args.force)
    print(f"\nVideos found: {result['videos_found']}")
    print(f"Indexed: {result['indexed']} | Skipped: {result['skipped']} | Failed: {result['failed']}")
    print(f"Total new chunks: {result['total_chunks']}")
    if result.get("parse_errors"):
        print("\nParse errors:")
        for e in result["parse_errors"]:
            print(f"  {e['url']}: {e['error']}")
    for r in result.get("results", []):
        icon = "✓" if r.get("status") == "success" else ("○" if r.get("status") == "skipped" else "✗")
        print(f"  {icon} {r.get('title', r.get('video_id'))} — {r.get('status')} ({r.get('chunks', 0)} chunks)")
    print("=" * 60)


if __name__ == "__main__":
    main()
