"""Retrieval module for VŠE Buddy Bot.

Handles query embedding, cosine similarity calculation against the precomputed
index.npz vector store, hybrid title-keyword boosting, and fallback contacts inclusion.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from google import genai
from google.genai import types

import config
import ingest

# English and Czech common stopwords for hybrid keyword boosting
STOPWORDS = {
    # English
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had",
    "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "it's", "its",
    "itself", "just", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of",
    "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over",
    "own", "same", "shan't", "she", "should", "shouldn't", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "were",
    "weren't", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "won't",
    "would", "wouldn't", "you", "your", "yours", "yourself", "yourselves",
    # Czech
    "a", "aby", "aj", "ale", "ani", "aniz", "ano", "asi", "az", "bez", "bude", "budem", "budes",
    "by", "byt", "ci", "clanek", "clanku", "co", "coz", "cz", "dalsi", "de", "do", "dva", "ho",
    "i", "jak", "jako", "je", "jeho", "jej", "jeji", "jejich", "jen", "jeste", "ji", "jine",
    "jiz", "jsme", "jsou", "k", "ka", "kde", "kdo", "kdyz", "ke", "ktera", "ktere", "kteri",
    "kterou", "ktery", "ma", "mate", "me", "mezi", "mi", "mit", "mne", "mnoho", "mohou", "muj",
    "muze", "my", "na", "nad", "nam", "napiste", "nas", "nasi", "ne", "nebo", "necht", "nejsou",
    "neni", "nez", "nic", "nove", "novy", "o", "od", "ode", "on", "ona", "oni", "ono", "ony",
    "osoby", "pak", "po", "pod", "podle", "pokud", "pouze", "prave", "pred", "pres", "pri", "pro",
    "proc", "proto", "protoze", "prvni", "pt", "s", "se", "si", "sice", "strana", "sve", "svych",
    "svym", "svymi", "ta", "tak", "take", "tato", "te", "teto", "tim", "timto", "tipy", "to",
    "toho", "tohle", "tom", "tomto", "tomuto", "tu", "tuto", "ty", "tyto", "u", "uz", "v", "vam",
    "vas", "vase", "ve", "vice", "vsak", "vse", "vsechno", "vy", "z", "za", "zda", "zde", "ze",
}


INTENT_EXPANSIONS = {
    "iweek": ["international", "week", "intensive", "courses"],
    "fees": ["tuition", "payment", "bank", "insis", "variable"],
    "fee": ["tuition", "payment", "bank", "insis"],
    "tuition": ["fees", "payment", "bank", "insis"],
    "police": ["foreign", "police", "olšanská", "registration", "residence"],
    "nostrifikace": ["foreign", "education", "assessment", "recognition", "diploma"],
    "nostrification": ["foreign", "education", "assessment", "recognition", "diploma"],
    "vouchers": ["credit", "voucher", "ects", "registration", "enrollment"],
    "voucher": ["credit", "voucher", "ects", "registration", "enrollment"],
    "scholarship": ["accommodation", "stipendium", "grant", "insis"],
    "scholarships": ["accommodation", "stipendium", "grant", "insis"],
    "stipendium": ["accommodation", "scholarship", "grant", "insis"],
    "wifi": ["eduroam", "network", "internet", "connection"],
    "eduroam": ["wifi", "network", "internet", "credentials"],
    "dorm": ["dormitories", "housing", "skm", "accommodation"],
    "dorms": ["dormitories", "housing", "skm", "accommodation"],
    "isic": ["student", "card", "identity"],
    "safeq": ["printing", "copying", "card", "library"],
    "print": ["safeq", "copying", "isic", "library"],
    "printing": ["safeq", "copying", "isic", "library"],
    "retake": ["exam", "failure", "credit"],
    "flunk": ["exam", "failure", "retake", "credit"],
}


class Retriever:
    """Retriever using numpy cosine similarity, hybrid title boosting, and contacts fallback."""

    def __init__(self):
        self.matrix: Optional[np.ndarray] = None
        self.metadata: List[Dict[str, Any]] = []
        self.client: Optional[genai.Client] = None
        self._ensure_index_loaded()

    def _ensure_index_loaded(self):
        """Load index from disk or automatically rebuild if knowledge changed."""
        current_hash = ingest.compute_knowledge_hash(config.KNOWLEDGE_DIR)
        rebuild_needed = True

        if (
            config.INDEX_PATH.exists()
            and config.INDEX_META_PATH.exists()
            and config.INDEX_HASH_PATH.exists()
        ):
            saved_hash = config.INDEX_HASH_PATH.read_text(encoding="utf-8").strip()
            if saved_hash == current_hash:
                rebuild_needed = False

        if rebuild_needed:
            print("[Retriever] Index missing or knowledge files changed. Building index...")
            matrix, metadata, _ = ingest.build_and_save_index(force=True)
            self.matrix = matrix
            self.metadata = metadata
        else:
            npz = np.load(config.INDEX_PATH)
            self.matrix = npz["embeddings"]
            with open(config.INDEX_META_PATH, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    def _get_client(self) -> genai.Client:
        """Lazily initialize Google Gemini API client."""
        if self.client is None:
            api_key = config.get_gemini_api_key()
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not configured. Please add it to your .env file or Streamlit secrets."
                )
            self.client = genai.Client(api_key=api_key)
        return self.client

    def embed_query(self, query: str) -> np.ndarray:
        """Embed user query with task_type='RETRIEVAL_QUERY' and L2-normalize.
        
        Includes exponential backoff retry in case of free-tier rate limits.
        """
        import time

        client = self._get_client()
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.embed_content(
                    model=config.EMBEDDING_MODEL,
                    contents=query,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
                )
                vec = np.array(response.embeddings[0].values, dtype=np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                return vec
            except Exception as e:
                err_str = str(e).lower()
                if ("429" in err_str or "quota" in err_str or "rate" in err_str) and attempt < max_retries - 1:
                    wait_sec = 3.0 * (2 ** attempt)
                    print(f"[Retriever rate-limit] Retrying in {wait_sec:.1f}s...")
                    time.sleep(wait_sec)
                else:
                    raise

    def extract_query_keywords(self, query: str) -> List[str]:
        """Extract lowercased keywords with length >= config.MIN_KEYWORD_LENGTH excluding stopwords,
        and expand with semantic intent synonyms for fragmented student queries.
        """
        words = re.findall(r"\w+", query.lower(), re.UNICODE)
        keywords = [
            w for w in words
            if len(w) >= config.MIN_KEYWORD_LENGTH and w not in STOPWORDS
        ]
        # Expand keywords using semantic intent dictionary
        expanded = set(keywords)
        for w in words:
            if w in INTENT_EXPANSIONS:
                for exp_w in INTENT_EXPANSIONS[w]:
                    if len(exp_w) >= config.MIN_KEYWORD_LENGTH and exp_w not in STOPWORDS:
                        expanded.add(exp_w)
        return list(expanded)

    def retrieve(
        self, query: str, k: int = config.TOP_K, min_score: float = config.MIN_SCORE
    ) -> Tuple[List[Dict[str, Any]], float, str]:
        """Retrieve top k chunks matching query.
        
        Steps:
        1. Embed query with task_type='RETRIEVAL_QUERY', normalise.
        2. Cosine similarity = dot product against the matrix.
        3. Hybrid boost: +0.05 for each query keyword (len >= 4, no stopwords) in chunk's title. Max boost 0.15.
        4. Return top k chunks with score >= min_score.
        5. Always ALSO return the best-matching contacts.md chunk (if not already included).
        6. Return (chunks, top_score, mode).
           If no chunk passes min_score -> mode = 'no_context'.
        """
        # Ensure index is ready
        if self.matrix is None or len(self.metadata) == 0:
            self._ensure_index_loaded()

        query_vec = self.embed_query(query)

        # Dot product against L2-normalized document matrix = cosine similarity
        raw_similarities = np.dot(self.matrix, query_vec)

        # Hybrid keyword boost
        keywords = self.extract_query_keywords(query)

        scored_chunks: List[Dict[str, Any]] = []
        for idx, (sim, meta) in enumerate(zip(raw_similarities, self.metadata)):
            chunk_copy = dict(meta)
            base_score = float(sim)
            title_lower = chunk_copy.get("title", "").lower()

            # Calculate keyword boost
            boost = 0.0
            for kw in keywords:
                if kw in title_lower:
                    boost += config.KEYWORD_BOOST
            boost = min(boost, config.MAX_KEYWORD_BOOST)

            final_score = base_score + boost
            chunk_copy["base_score"] = round(base_score, 4)
            chunk_copy["keyword_boost"] = round(boost, 4)
            chunk_copy["score"] = round(final_score, 4)
            scored_chunks.append(chunk_copy)

        # Sort all chunks by final score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        top_score = scored_chunks[0]["score"] if scored_chunks else 0.0

        # Filter chunks that pass minimum score threshold
        passing_chunks = [c for c in scored_chunks if c["score"] >= min_score]
        selected_chunks = passing_chunks[:k]

        # Mode determination: normal or no_context
        mode = "normal" if len(selected_chunks) > 0 else "no_context"

        # Always ALSO return the best-matching contacts.md chunk
        has_contacts = any(c.get("is_contacts") for c in selected_chunks)
        contacts_chunks = [c for c in scored_chunks if c.get("is_contacts")]
        best_contacts = contacts_chunks[0] if contacts_chunks else None

        if not has_contacts and best_contacts is not None:
            # Append best contacts chunk so the bot can always point to official contacts
            selected_chunks.append(best_contacts)

        return selected_chunks, top_score, mode

    def debug_scores(self, query: str, top_n: int = 5):
        """Debug helper to print detailed retrieval scores for a query."""
        chunks, top_score, mode = self.retrieve(query, k=top_n)
        print(f"\n[DEBUG RETRIEVAL] Query: '{query}'")
        print(f"Top Score: {top_score:.4f} | Mode: {mode} | Returned Chunks: {len(chunks)}")
        print("-" * 70)
        for i, c in enumerate(chunks, 1):
            flag_contact = " [CONTACTS]" if c.get("is_contacts") else ""
            flag_unver = " [UNVERIFIED]" if c.get("unverified") else ""
            print(
                f"#{i} Score: {c['score']:.4f} (Base: {c.get('base_score', 0):.4f} + "
                f"Boost: {c.get('keyword_boost', 0):.4f}) | Doc: {c['doc_id']}{flag_contact}{flag_unver}"
            )
            print(f"   Title: {c['title']}")
            print(f"   Excerpt: {c['text'][:120].replace(chr(10), ' ')}...")
            print("-" * 70)
