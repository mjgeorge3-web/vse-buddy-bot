"""Ingestion pipeline for VŠE Buddy Bot.

Loads all Markdown knowledge files from knowledge/, parses metadata headers,
cleans boilerplates, chunks text logically by headings and paragraphs,
computes a SHA-256 integrity hash, embeds chunks via Google Gemini,
L2-normalizes the embedding vectors, and saves data/index.npz and data/index_meta.json.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from google import genai
from google.genai import types

import config


def compute_knowledge_hash(knowledge_dir: Path = config.KNOWLEDGE_DIR) -> str:
    """Compute a single deterministic SHA-256 hash for all *.md files in knowledge/.
    
    Normalizes CRLF/LF line endings so Windows, macOS, and Linux checkouts produce
    the exact same hash and never trigger unnecessary re-indexing on clone.
    """
    hasher = hashlib.sha256()
    md_files = sorted(knowledge_dir.glob("*.md"))
    for file_path in md_files:
        hasher.update(file_path.name.encode("utf-8"))
        normalized = file_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        hasher.update(normalized.encode("utf-8"))
    return hasher.hexdigest()


def split_section_paragraphs(
    section_text: str,
    max_chars: int = config.MAX_SECTION_CHARS,
    target_max: int = config.CHUNK_TARGET_MAX,
    overlap: int = config.CHUNK_OVERLAP,
) -> List[str]:
    """Split a section into paragraph-aligned chunks if it exceeds max_chars.
    
    Maintains a 100-character overlap between adjacent chunks where feasible.
    """
    if len(section_text) <= max_chars:
        return [section_text.strip()]

    # Split section on blank line paragraph breaks
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section_text) if p.strip()]
    if len(paragraphs) <= 1:
        # Fallback if no distinct paragraphs: chunk by lines
        lines = [l for l in section_text.splitlines() if l.strip()]
        chunks: List[str] = []
        current_lines: List[str] = []
        current_len = 0
        for line in lines:
            if current_len + len(line) + 1 > target_max and current_lines:
                chunks.append("\n".join(current_lines))
                # Retain previous chunk's last line if within overlap limit
                prev_line = current_lines[-1]
                if len(prev_line) <= overlap:
                    current_lines = [prev_line]
                    current_len = len(prev_line)
                else:
                    current_lines = []
                    current_len = 0
            current_lines.append(line)
            current_len += len(line) + 1
        if current_lines:
            chunks.append("\n".join(current_lines))
        return chunks if chunks else [section_text.strip()]

    chunks: List[str] = []
    current_paras: List[str] = []
    current_len = 0

    for para in paragraphs:
        p_len = len(para)
        # Check if adding this paragraph exceeds target chunk size
        if current_len + p_len + 2 > target_max and current_paras:
            chunks.append("\n\n".join(current_paras))
            # Create ~100 character overlap using the previous paragraph or suffix
            last_para = current_paras[-1]
            if len(last_para) <= overlap:
                current_paras = [last_para, para]
                current_len = len(last_para) + p_len + 2
            else:
                current_paras = [para]
                current_len = p_len
        else:
            current_paras.append(para)
            current_len += p_len + 2

    if current_paras:
        remaining = "\n\n".join(current_paras)
        if not chunks or remaining != chunks[-1]:
            chunks.append(remaining)

    return chunks


def parse_and_chunk_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse a single knowledge markdown file into indexed chunk dictionaries."""
    raw_content = file_path.read_text(encoding="utf-8")
    doc_id = file_path.name

    # 1. Parse HTML comment header or YAML frontmatter via regex
    header_match = re.search(r"<!--\s*(.*?)\s*-->", raw_content, re.DOTALL)
    yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw_content, re.DOTALL)
    source_url = ""
    title = ""
    date_saved = ""

    if header_match:
        header_text = header_match.group(1)
        src_m = re.search(r"^SOURCE:\s*(.*?)$", header_text, re.MULTILINE | re.IGNORECASE)
        title_m = re.search(r"^TITLE:\s*(.*?)$", header_text, re.MULTILINE | re.IGNORECASE)
        date_m = re.search(r"^DATE SAVED:\s*(.*?)$", header_text, re.MULTILINE | re.IGNORECASE)
        if src_m:
            # Take primary URL if comma-separated list is present
            source_url = src_m.group(1).split(",")[0].strip()
        if title_m:
            title = title_m.group(1).strip()
        if date_m:
            date_saved = date_m.group(1).strip()
    elif yaml_match:
        yaml_text = yaml_match.group(1)
        src_m = re.search(r"^source_url:\s*(.*?)$", yaml_text, re.MULTILINE | re.IGNORECASE)
        title_m = re.search(r"^title:\s*(.*?)$", yaml_text, re.MULTILINE | re.IGNORECASE)
        date_m = re.search(r"^date_saved:\s*(.*?)$", yaml_text, re.MULTILINE | re.IGNORECASE)
        if src_m:
            source_url = src_m.group(1).strip()
        if title_m:
            title = title_m.group(1).strip()
        if date_m:
            date_saved = date_m.group(1).strip()

    if not title:
        # Fallback to H1 heading if title not found in header
        h1_m = re.search(r"^#\s+(.*?)$", raw_content, re.MULTILINE)
        title = h1_m.group(1).strip() if h1_m else file_path.stem

    # 2. Check for explicit UNVERIFIED flag in file content
    unverified = bool(re.search(r"\bUNVERIFIED\b", raw_content))
    is_contacts = (file_path.name.lower() == "contacts.md")

    # 3. Strip header comment / YAML frontmatter and boilerplate disclaimer line
    body = re.sub(r"<!--.*?-->", "", raw_content, flags=re.DOTALL)
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", body, flags=re.DOTALL)
    cleaned_lines = [
        line for line in body.splitlines()
        if not line.strip().startswith("> General information only")
    ]
    cleaned_body = "\n".join(cleaned_lines).strip()

    # 4. Chunk by markdown headings (##)
    raw_sections = re.split(r"(?m)(?=^##\s+)", cleaned_body)
    sections: List[str] = []
    for s in raw_sections:
        s_clean = s.strip()
        if not s_clean:
            continue
        # If section is before the first ##, strip H1 if redundant
        if not s_clean.startswith("##"):
            s_without_h1 = re.sub(r"^#\s+.*?\n+", "", s_clean).strip()
            if len(s_without_h1) < 20:
                continue
            sections.append(s_without_h1)
        else:
            sections.append(s_clean)

    if not sections:
        sections = [cleaned_body]

    # Split large sections into sub-chunks if > 1200 chars
    all_chunks: List[Dict[str, Any]] = []
    chunk_index = 0
    for sec in sections:
        sub_chunks = split_section_paragraphs(sec)
        for sub_text in sub_chunks:
            sub_clean = re.sub(r"(?m)^\s*---+\s*$", "", sub_text).strip()
            if len(re.sub(r"[^A-Za-z0-9À-ž]", "", sub_clean)) < 30:
                continue
            # Prepend page TITLE to chunk text before embedding (improves recall)
            text_with_title = f"{title}\n\n{sub_clean}".strip()
            all_chunks.append({
                "chunk_id": f"{doc_id}#{chunk_index}",
                "doc_id": doc_id,
                "title": title,
                "source_url": source_url,
                "date_saved": date_saved,
                "unverified": unverified,
                "is_contacts": is_contacts,
                "text": text_with_title,
            })
            chunk_index += 1

    return all_chunks


def load_all_chunks(
    knowledge_dir: Path = config.KNOWLEDGE_DIR,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Parse all markdown files in knowledge/ and return chunks and count per file."""
    md_files = sorted(knowledge_dir.glob("*.md"))
    all_chunks: List[Dict[str, Any]] = []
    chunk_counts: Dict[str, int] = {}

    for file_path in md_files:
        file_chunks = parse_and_chunk_file(file_path)
        chunk_counts[file_path.name] = len(file_chunks)
        all_chunks.extend(file_chunks)

    return all_chunks, chunk_counts


def embed_chunks_with_backoff(
    client: genai.Client,
    texts: List[str],
    model: str = config.EMBEDDING_MODEL,
    batch_size: int = config.EMBEDDING_BATCH_SIZE,
) -> np.ndarray:
    """Embed texts using Google Gemini API with batching and exponential backoff."""
    all_vectors: List[np.ndarray] = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        max_retries = 5
        base_delay = 2.0

        for attempt in range(max_retries):
            try:
                response = client.models.embed_content(
                    model=model,
                    contents=batch,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
                )
                for emb in response.embeddings:
                    all_vectors.append(np.array(emb.values, dtype=np.float32))
                break
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = ("429" in err_str or "quota" in err_str or "rate" in err_str)
                if attempt == max_retries - 1:
                    print(f"Error embedding batch {i}-{i+len(batch)}: {e}")
                    raise
                if is_rate_limit:
                    m = re.search(r"retry\s*(?:in|delay)?[^\d]*(\d+)", err_str)
                    wait_time = float(m.group(1)) + 2.0 if m else (30.0 + 15.0 * attempt)
                else:
                    wait_time = base_delay * (2 ** attempt)
                print(f"Rate limit / transient error on batch {i}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)

    # Convert to 2D numpy array
    matrix = np.array(all_vectors, dtype=np.float32)

    # L2-normalize vectors so cosine similarity is computed as dot product
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1e-12
    matrix_normalized = matrix / norms
    return matrix_normalized


def build_and_save_index(force: bool = False) -> Tuple[np.ndarray, List[Dict[str, Any]], Dict[str, int]]:
    """Build embedding index and metadata, saving to data/index.npz and data/index_meta.json.
    
    Checks SHA-256 hash to avoid unnecessary API calls when knowledge files haven't changed.
    """
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    current_hash = compute_knowledge_hash(config.KNOWLEDGE_DIR)

    # Check if index already exists and knowledge files are unchanged
    if (
        not force
        and config.INDEX_PATH.exists()
        and config.INDEX_META_PATH.exists()
        and config.INDEX_HASH_PATH.exists()
    ):
        saved_hash = config.INDEX_HASH_PATH.read_text(encoding="utf-8").strip()
        if saved_hash == current_hash:
            print("Knowledge files unchanged. Loading existing index from disk.")
            npz = np.load(config.INDEX_PATH)
            matrix = npz["embeddings"]
            with open(config.INDEX_META_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
            counts: Dict[str, int] = {}
            for item in meta:
                counts[item["doc_id"]] = counts.get(item["doc_id"], 0) + 1
            return matrix, meta, counts

    # Parse and chunk all knowledge files
    chunks, chunk_counts = load_all_chunks(config.KNOWLEDGE_DIR)
    chunk_texts = [c["text"] for c in chunks]

    # Reuse existing cached vectors only during incremental rebuilds (force=True rebuilds cleanly from scratch)
    cached_vecs: Dict[str, np.ndarray] = {}
    dim = 3072
    if not force and config.INDEX_PATH.exists() and config.INDEX_META_PATH.exists():
        try:
            old_npz = np.load(config.INDEX_PATH)
            old_mat = old_npz["embeddings"]
            if old_mat.ndim == 2 and old_mat.shape[1] > 1:
                dim = old_mat.shape[1]
            with open(config.INDEX_META_PATH, "r", encoding="utf-8") as f:
                old_meta = json.load(f)
            if len(old_meta) == len(old_mat):
                for m_item, vec in zip(old_meta, old_mat):
                    t_key = m_item.get("text", "")
                    if t_key:
                        cached_vecs[t_key] = vec
        except Exception:
            cached_vecs = {}

    missing_indices = [idx for idx, txt in enumerate(chunk_texts) if txt not in cached_vecs]

    # Verify Gemini API key
    api_key = config.get_gemini_api_key()
    if not api_key and missing_indices:
        raise ValueError(
            "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in .env before running ingest.py."
        )

    new_vecs_map: Dict[int, np.ndarray] = {}
    if missing_indices:
        missing_texts = [chunk_texts[idx] for idx in missing_indices]
        # HttpOptions.timeout is in milliseconds (30000 ms = 30 seconds)
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30000),
        )
        print(f"Generating embeddings for {len(missing_texts)} updated/new chunks (reusing {len(chunks) - len(missing_texts)} cached)...")
        embedded_missing = embed_chunks_with_backoff(client, missing_texts, model=config.EMBEDDING_MODEL)
        dim = embedded_missing.shape[1]
        for idx, vec in zip(missing_indices, embedded_missing):
            new_vecs_map[idx] = vec

    assembled: List[np.ndarray] = []
    for idx, txt in enumerate(chunk_texts):
        if txt in cached_vecs:
            assembled.append(cached_vecs[txt])
        else:
            assembled.append(new_vecs_map[idx])
    matrix_norm = np.vstack(assembled).astype(np.float32)

    # Save to disk
    np.savez_compressed(config.INDEX_PATH, embeddings=matrix_norm)
    with open(config.INDEX_META_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    config.INDEX_HASH_PATH.write_text(current_hash, encoding="utf-8")
    print(f"Successfully saved index to {config.INDEX_PATH} and metadata to {config.INDEX_META_PATH}")

    return matrix_norm, chunks, chunk_counts


def main():
    """Main function executed via `python ingest.py`."""
    print("==================================================")
    print("VŠE Buddy Bot - Knowledge Ingestion & Indexing")
    print("==================================================")
    _, chunks, chunk_counts = build_and_save_index(force=True)

    print("\n--- Chunk Count Per File ---")
    for filename, count in chunk_counts.items():
        print(f"  {filename}: {count} chunk(s)")
    print("----------------------------")
    print(f"Total files: {len(chunk_counts)}")
    print(f"Total chunks: {len(chunks)}")
    print("==================================================")


if __name__ == "__main__":
    main()
