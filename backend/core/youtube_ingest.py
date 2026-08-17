"""
core/youtube_ingest.py
────────────────────────────────────────────────────────────────────────
Ingest YouTube videos & playlists into the RAG knowledge base.
Supports Hindi, English, and Hinglish via captions + smart normalization.
────────────────────────────────────────────────────────────────────────
"""

import json
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.knowledge_base import (
    chunk_text,
    embed_text,
    knowledge_collection,
    KNOWLEDGE_DIR,
    source_is_indexed,
    upsert_knowledge_chunks,
)

YOUTUBE_DIR = KNOWLEDGE_DIR / "youtube"
TEMP_DIR = Path(__file__).resolve().parent.parent / "temp" / "youtube"

# Noise patterns in auto-captions
NOISE_LINE = re.compile(
    r"^\[?(music|applause|laughter|silence|intro|outro)\]?$",
    re.I,
)
VIDEO_ID_RE = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})"
)


def _ensure_dirs():
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    YOUTUBE_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def extract_video_id(url: str) -> Optional[str]:
    url = url.strip()
    m = VIDEO_ID_RE.search(url)
    return m.group(1) if m else None


def _yt_dlp_available() -> bool:
    return shutil.which("yt-dlp") is not None


def expand_url_to_videos(url: str) -> list[dict]:
    """Single video or full playlist → list of {id, title, url}."""
    url = url.strip()
    if not url:
        return []

    is_playlist = "list=" in url or "/playlist" in url

    if is_playlist:
        if not _yt_dlp_available():
            raise RuntimeError(
                "Playlists need yt-dlp installed. Run: pip install yt-dlp"
            )
        proc = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J", url],
            capture_output=True,
            text=True,
            timeout=180,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {proc.stderr[:500]}")
        data = json.loads(proc.stdout)
        entries = data.get("entries") or []
        out = []
        for e in entries:
            vid = e.get("id")
            if not vid or len(vid) != 11:
                continue
            out.append({
                "id": vid,
                "title": e.get("title") or vid,
                "url": f"https://www.youtube.com/watch?v={vid}",
            })
        return out

    vid = extract_video_id(url)
    if not vid:
        raise ValueError(f"Could not parse YouTube URL: {url}")
    title = _fetch_title(vid) or vid
    return [{"id": vid, "title": title, "url": url}]


def _fetch_title(video_id: str) -> str:
    if not _yt_dlp_available():
        return video_id
    try:
        proc = subprocess.run(
            ["yt-dlp", "--print", "title", f"https://youtu.be/{video_id}"],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()[:200]
    except Exception:
        pass
    return video_id


def fetch_transcript_raw(video_id: str) -> tuple[list[dict], str, bool]:
    """
    Fetch captions via youtube-transcript-api.
    Returns (segments, language_code, is_auto_generated).
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise RuntimeError(
            "Install youtube-transcript-api: pip install youtube-transcript-api"
        )

    preferred = ["hi", "en", "en-IN", "en-US", "hi-IN"]
    errors = []
    api = YouTubeTranscriptApi()

    # New API (v1+): instance.fetch / instance.list
    try:
        fetched = api.fetch(video_id, languages=preferred)
        segments = [{"text": s.text} for s in fetched.snippets]
        return segments, fetched.language_code, fetched.is_generated
    except Exception as e:
        errors.append(str(e))

    try:
        tlist = api.list(video_id)
        for lang in ["hi", "en", "en-IN"]:
            try:
                t = tlist.find_transcript([lang])
                raw = t.fetch()
                segments = [{"text": s.text} for s in raw.snippets]
                return segments, lang, t.is_generated
            except Exception:
                continue
        try:
            t = tlist.find_generated_transcript(["hi"])
            en = t.translate("en")
            raw = en.fetch()
            segments = [{"text": s.text} for s in raw.snippets]
            return segments, "hi→en", True
        except Exception:
            pass
    except Exception as e:
        errors.append(str(e))

    # Legacy static API
    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=preferred)
        return segments, "multi", True
    except Exception as e:
        errors.append(str(e))

    # yt-dlp subtitle fallback
    if _yt_dlp_available():
        text = _fetch_subs_ytdlp(video_id)
        if text:
            return [{"text": text}], "ytdlp", True

    raise RuntimeError(
        f"No captions for {video_id}. Enable captions on the video or install yt-dlp. "
        f"Errors: {' | '.join(errors[:2])}"
    )


def _fetch_subs_ytdlp(video_id: str) -> str:
    out_tpl = str(TEMP_DIR / f"{video_id}")
    subprocess.run(
        [
            "yt-dlp", "--skip-download",
            "--write-auto-sub", "--write-sub",
            "--sub-lang", "hi,en,hin-English,en-orig",
            "--sub-format", "vtt",
            "-o", out_tpl,
            f"https://youtu.be/{video_id}",
        ],
        capture_output=True,
        timeout=120,
    )
    for p in TEMP_DIR.glob(f"{video_id}*"):
        if p.suffix in (".vtt", ".srt"):
            return _parse_vtt(p.read_text(encoding="utf-8", errors="replace"))
    return ""


def _parse_vtt(vtt: str) -> str:
    lines = []
    seen = set()
    for line in vtt.splitlines():
        line = line.strip()
        if not line or line.startswith("WEBVTT") or "-->" in line:
            continue
        if re.match(r"^\d+$", line):
            continue
        if line in seen:
            continue
        seen.add(line)
        lines.append(line)
    return " ".join(lines)


def segments_to_text(segments: list) -> str:
    parts = []
    prev = ""
    for seg in segments:
        t = (seg.get("text") if isinstance(seg, dict) else str(seg)).strip()
        t = re.sub(r"\s+", " ", t)
        if not t or NOISE_LINE.match(t):
            continue
        if t == prev:
            continue
        prev = t
        parts.append(t)
    return " ".join(parts)


def _devanagari_ratio(text: str) -> float:
    if not text:
        return 0.0
    dev = len(re.findall(r"[\u0900-\u097F]", text))
    return dev / max(len(text), 1)


def normalize_for_rag(text: str) -> tuple[str, str]:
    """
    Normalize Hindi / Hinglish / English for embedding.
    Returns (normalized_text, lang_label).
    """
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "", "empty"

    dev_ratio = _devanagari_ratio(text)

    # Pure or mostly Hindi (Devanagari)
    if dev_ratio > 0.25:
        translated = _translate_hindi_chunks(text)
        return translated, "hindi→english"

    # Detect roman Hindi / hinglish
    try:
        from langdetect import detect, LangDetectException
        sample = text[:800]
        lang = detect(sample)
    except Exception:
        lang = "unknown"

    hinglish_markers = [
        "kya", "hai", "hoga", "mein", "aap", "yeh", "woh", "ke", "ki", "ka",
        "grah", "dasha", "gochar", "shaadi", "naukri", "kundli", "lagna",
    ]
    lower = text.lower()
    hinglish_score = sum(1 for m in hinglish_markers if f" {m} " in f" {lower} ")

    if lang == "hi" or hinglish_score >= 3:
        # Hinglish: keep original (works for mixed queries) + light English gloss on key lines
        gloss = _translate_hindi_chunks(text) if lang == "hi" else text
        if gloss != text and len(gloss) > len(text) * 0.5:
            return f"{text}\n\n[English gloss for retrieval]\n{gloss}", "hinglish+bilingual"
        return text, "hinglish"

    return text, "english"


def _translate_hindi_chunks(text: str, chunk_size: int = 4500) -> str:
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        return text  # index raw Hindi if translator missing

    translator = GoogleTranslator(source="auto", target="en")
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    out = []
    for ch in chunks:
        try:
            out.append(translator.translate(ch))
        except Exception:
            out.append(ch)
    return " ".join(out)


def ingest_video(
    video_id: str,
    title: str = "",
    force: bool = False,
) -> dict:
    """Ingest one video into ChromaDB. Returns result dict."""
    _ensure_dirs()
    source_label = f"youtube_{video_id}"
    title = title or video_id

    if not force and source_is_indexed(source_label):
        return {
            "video_id": video_id,
            "title": title,
            "status": "skipped",
            "reason": "already_indexed",
            "chunks": 0,
        }

    segments, lang, auto = fetch_transcript_raw(video_id)
    raw_text = segments_to_text(segments)
    if len(raw_text) < 80:
        return {
            "video_id": video_id,
            "title": title,
            "status": "failed",
            "reason": "transcript_too_short",
            "chunks": 0,
        }

    normalized, lang_label = normalize_for_rag(raw_text)
    header = (
        f"[YouTube: {title}]\n"
        f"[Video ID: {video_id}]\n"
        f"[Caption language: {lang} | normalized: {lang_label} | auto={auto}]\n\n"
    )
    full_doc = header + normalized

    txt_path = YOUTUBE_DIR / f"{video_id}.txt"
    txt_path.write_text(full_doc, encoding="utf-8")

    chunks = chunk_text(full_doc, chunk_size=900, overlap=150)
    chunks = [c for c in chunks if len(c.strip()) >= 60]
    if not chunks:
        chunks = [full_doc[:2000]]

    meta = {
        "type": "youtube",
        "video_id": video_id,
        "title": title[:200],
        "caption_lang": lang,
        "normalized_lang": lang_label,
        "auto_caption": str(auto),
        "ingested_at": datetime.now().isoformat(),
    }

    stored = upsert_knowledge_chunks(
        source_label=source_label,
        chunks=chunks,
        metadata=meta,
        force=force,
    )

    return {
        "video_id": video_id,
        "title": title,
        "status": "success",
        "chunks": stored,
        "chars": len(full_doc),
        "lang": lang_label,
        "saved_to": str(txt_path),
    }


def ingest_urls(urls: list[str], force: bool = False) -> dict:
    """Ingest multiple URLs (videos or playlists)."""
    _ensure_dirs()
    if embed_text("test") is None:
        raise RuntimeError(
            "Ollama must be running with nomic-embed-text for indexing. "
            "Start Ollama, then: ollama pull nomic-embed-text"
        )

    all_videos = []
    parse_errors = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            all_videos.extend(expand_url_to_videos(url))
        except Exception as e:
            parse_errors.append({"url": url, "error": str(e)})

    # Deduplicate by video id
    seen = set()
    unique = []
    for v in all_videos:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)

    results = []
    total_chunks = 0
    for v in unique:
        try:
            r = ingest_video(v["id"], title=v.get("title", ""), force=force)
            results.append(r)
            if r.get("status") == "success":
                total_chunks += r.get("chunks", 0)
        except Exception as e:
            results.append({
                "video_id": v["id"],
                "title": v.get("title", ""),
                "status": "failed",
                "reason": str(e),
                "chunks": 0,
            })

    ok = sum(1 for r in results if r.get("status") == "success")
    skipped = sum(1 for r in results if r.get("status") == "skipped")

    return {
        "videos_found": len(unique),
        "indexed": ok,
        "skipped": skipped,
        "failed": len(results) - ok - skipped,
        "total_chunks": total_chunks,
        "parse_errors": parse_errors,
        "results": results,
    }
