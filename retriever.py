"""Retrieval module for VŠE Buddy Bot.

Handles query embedding, cosine similarity calculation against the precomputed
index.npz vector store, hybrid title-keyword boosting, and fallback contacts inclusion.
"""

import difflib
import json
import re
import concurrent.futures
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from google import genai
from google.genai import types

import config
import ingest

# Shared worker pool for timeout-isolated API calls (never blocks on shutdown)
_EMBED_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="embed_pool")

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
    "vouchers": ["credit", "voucher", "ects", "registration", "enrollment", "balance", "regulations"],
    "voucher": ["credit", "voucher", "ects", "registration", "enrollment", "balance", "regulations"],
    "scholarship": ["accommodation", "stipendium", "grant", "insis"],
    "scholarships": ["accommodation", "stipendium", "grant", "insis"],
    "stipendium": ["accommodation", "scholarship", "grant", "insis"],
    "wifi": ["eduroam", "network", "internet", "connection"],
    "eduroam": ["wifi", "network", "internet", "credentials"],
    "dorm": ["dormitories", "housing", "skm", "suz", "accommodation", "iskam"],
    "dorms": ["dormitories", "housing", "skm", "suz", "accommodation", "iskam"],
    "housing": ["dormitories", "accommodation", "iskam", "suz", "flat", "rent"],
    "accommodation": ["dormitories", "housing", "flat", "apartment", "iskam", "suz", "rent"],
    "accomodation": ["accommodation", "dormitories", "housing", "flat", "apartment", "iskam", "suz"],
    "flat": ["private", "accommodation", "rent", "housing", "apartment"],
    "flats": ["private", "accommodation", "rent", "housing", "apartment"],
    "apartment": ["private", "accommodation", "rent", "housing", "flat"],
    "apartments": ["private", "accommodation", "rent", "housing", "flat"],
    "rent": ["private", "accommodation", "flat", "housing", "lease"],
    "renting": ["private", "accommodation", "flat", "housing", "lease"],
    "iskam": ["dormitories", "housing", "accommodation", "suz", "deposit", "kauce"],
    "deposit": ["dormitories", "housing", "accommodation", "iskam", "kauce"],
    "isic": ["student", "card", "identity"],
    "safeq": ["printing", "copying", "card", "library"],
    "print": ["safeq", "copying", "isic", "library"],
    "printing": ["safeq", "copying", "isic", "library"],
    "retake": ["exam", "failure", "credit", "regulations"],
    "flunk": ["exam", "failure", "retake", "credit"],
    "fail": ["exam", "failure", "retake", "credit", "regulations"],
    "failed": ["exam", "failure", "retake", "credit", "regulations"],
    "counseling": ["psychological", "counselling", "stress", "anxiety", "academic", "centre"],
    "counselling": ["psychological", "counselling", "stress", "anxiety", "academic", "centre"],
    "psychologist": ["psychological", "counselling", "mental", "support", "academic", "centre"],
    "therapy": ["psychological", "counselling", "mental", "support", "academic"],
    "stress": ["psychological", "counselling", "mental", "anxiety", "academic", "centre"],
    "stressed": ["psychological", "counselling", "mental", "stress", "anxiety", "academic", "centre"],
    "stressful": ["psychological", "counselling", "mental", "stress", "anxiety", "academic"],
    "anxiety": ["psychological", "counselling", "mental", "stress", "academic", "centre"],
    "anxious": ["psychological", "counselling", "mental", "anxiety", "stress", "academic"],
    "homesick": ["psychological", "counselling", "adaptation", "culture", "shock"],
    "homesickness": ["psychological", "counselling", "adaptation", "homesick", "mental"],
    "mental": ["psychological", "counselling", "support", "wellbeing", "academic"],
    "mentally": ["psychological", "counselling", "mental", "stress", "wellbeing", "academic"],
    "depressed": ["psychological", "counselling", "mental", "depression", "support", "academic"],
    "depression": ["psychological", "counselling", "mental", "support", "academic", "centre"],
    "lonely": ["psychological", "counselling", "loneliness", "mental", "esn", "clubs"],
    "loneliness": ["psychological", "counselling", "mental", "support", "adaptation"],
    "overwhelmed": ["psychological", "counselling", "mental", "stress", "anxiety", "academic"],
    "burnout": ["psychological", "counselling", "mental", "stress", "academic"],
    "litacka": ["prague", "public", "transport", "pid", "metro", "tram", "student"],
    "lítačka": ["prague", "public", "transport", "pid", "metro", "tram", "student"],
    "transport": ["pid", "litacka", "metro", "tram", "bus", "student", "discount"],
    "metro": ["prague", "public", "transport", "pid", "litacka"],
    "tram": ["prague", "public", "transport", "pid", "litacka"],
    "menza": ["catering", "menza", "food", "lunch", "meals", "canteen"],
    "canteen": ["catering", "menza", "food", "lunch", "meals"],
    "cafeteria": ["catering", "menza", "food", "lunch"],
    "doctor": ["health", "insurance", "medical", "care", "emergency"],
    "medical": ["health", "insurance", "medical", "care", "doctor"],
    "hospital": ["health", "insurance", "medical", "care", "emergency", "doctor"],
    "insurance": ["health", "insurance", "medical", "pvzp", "ehic"],
    "timetable": ["insis", "course", "registration", "schedule", "classes"],
    "schedule": ["insis", "course", "registration", "timetable", "academic", "calendar"],
    "ects": ["credit", "voucher", "courses", "study", "regulations"],
    "internship": ["career", "services", "job", "fair", "sance"],
    "internships": ["career", "services", "job", "fair", "sance", "internship"],
    "work": ["employment", "during", "studies", "permit"],
    "job": ["career", "services", "fair", "sance", "employment"],
    "jobs": ["career", "services", "job", "fair", "sance"],
    "money": ["cost", "living", "budgeting", "expenses", "czk"],
    "email": ["microsoft", "365", "outlook", "teams", "onedrive"],
    "materials": ["moodle", "elearning", "assignments"],
    "meet": ["clubs", "esn", "buddy", "ambassadors"],
    "eat": ["catering", "menza", "canteen", "meals", "food"],
    "cheaply": ["catering", "menza", "canteen", "meals"],
    "errata": ["thesis", "submission", "insis", "corrections", "erratum", "defense"],
    "erratum": ["thesis", "errata", "submission", "insis", "corrections"],
    "thesis": ["final", "submission", "defense", "insis", "supervisor", "errata", "bachelor", "master"],
    "theses": ["final", "thesis", "submission", "defense", "insis", "supervisor"],
    "defense": ["thesis", "state", "exam", "szz", "obhajoba", "presentation", "reviews"],
    "obhajoba": ["defense", "thesis", "presentation", "opponent", "supervisor"],
    "opponent": ["review", "posudek", "thesis", "defense", "supervisor"],
    "posudek": ["review", "opponent", "supervisor", "thesis", "defense"],
    "plagiarism": ["theses", "validator", "similarity", "check", "thesis"],
    "szz": ["state", "final", "exam", "defense", "thesis", "insis"],
    "statnice": ["state", "final", "exam", "defense", "thesis", "szz"],
    "státnice": ["state", "final", "exam", "defense", "thesis", "szz"],
    "credit": ["ects", "voucher", "semester", "regulations", "study"],
    "credits": ["ects", "voucher", "semester", "regulations", "study", "minimum"],
    "semester": ["credits", "study", "regulations", "enrollment", "timetable"],
    "minimum": ["credits", "regulations", "threshold", "semester", "requirements"],
    "maximum": ["credits", "regulations", "semester", "limit"],
    "graduate": ["credits", "thesis", "defense", "szz", "requirements", "degree"],
    "graduation": ["credits", "thesis", "defense", "szz", "requirements", "degree"],
    "interrupt": ["interruption", "preruseni", "studies", "visa", "insis"],
    "interruption": ["preruseni", "studies", "visa", "insis", "regulations"],
    "recognize": ["recognition", "uznavani", "credits", "transcript", "courses"],
    "recognition": ["uznavani", "credits", "transcript", "courses", "vice-dean"],
    "grades": ["grading", "scale", "exam", "vyborne", "ects"],
    "grading": ["scale", "grades", "exam", "vyborne", "ects"],
    "expulsion": ["termination", "studies", "vouchers", "credits", "regulations"],
    "termination": ["studies", "vouchers", "credits", "expulsion", "regulations"],
    "portlet": ["portlets", "insis", "navigation", "student", "adjustment", "sidebar"],
    "portlets": ["portlet", "insis", "navigation", "student", "adjustment", "sidebar"],
    "admission": ["admissions", "application", "prihlaska", "apply", "programmes"],
    "admissions": ["admission", "application", "prihlaska", "apply", "programmes"],
    "visa": ["residence", "permit", "embassy", "embassies", "consulate", "mzv", "ipc", "frs", "insurance", "police"],
}


class Retriever:
    """Retriever using numpy cosine similarity, hybrid title boosting, and contacts fallback."""

    def __init__(self):
        self.matrix: Optional[np.ndarray] = None
        self.metadata: List[Dict[str, Any]] = []
        self.client: Optional[genai.Client] = None
        self._vocab_set: Set[str] = set()
        self._ensure_index_loaded()

    def _build_vocabulary(self):
        """Build a set of known domain terms from INTENT_EXPANSIONS and indexed document text for fuzzy typo recovery."""
        vocab: Set[str] = set(INTENT_EXPANSIONS.keys())
        for vals in INTENT_EXPANSIONS.values():
            vocab.update(vals)
        for m in self.metadata:
            for w in re.findall(r"\w+", (m.get("title", "") + " " + m.get("text", "")).lower(), re.UNICODE):
                if len(w) >= 4 and w not in STOPWORDS:
                    vocab.add(w)
        self._vocab_set = vocab

    def _resolve_word_and_stems(self, word: str) -> List[str]:
        """Return candidate root forms, applying fuzzy typo recovery if a word >= 5 chars is unknown to the corpus."""
        stems = self._candidate_stems(word)
        if not self._vocab_set:
            return stems
        if any(s in self._vocab_set for s in stems):
            return stems
        if len(word) >= 5:
            matches = difflib.get_close_matches(word, self._vocab_set, n=1, cutoff=0.78)
            if matches:
                return self._candidate_stems(matches[0])
        return stems

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
        self._build_vocabulary()

    def _get_client(self) -> genai.Client:
        """Lazily initialize Google Gemini API client with 15s (15000ms) timeout."""
        if self.client is None:
            api_key = config.get_gemini_api_key()
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not configured. Please add it to your .env file or Streamlit secrets."
                )
            self.client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=15000, api_version="v1beta"),
            )
        return self.client

    def embed_query(self, query: str) -> Optional[np.ndarray]:
        """Embed user query with task_type='RETRIEVAL_QUERY' and L2-normalize.
        
        Uses a 15.0s timeout with automatic retry on transient rate limits.
        """
        import time

        client = self._get_client()

        def _do_embed():
            response = client.models.embed_content(
                model=config.EMBEDDING_MODEL,
                contents=query,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
            )
            vec = np.array(response.embeddings[0].values, dtype=np.float32)
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 0 else vec

        for attempt in range(2):
            try:
                future = _EMBED_EXECUTOR.submit(_do_embed)
                return future.result(timeout=15.0)
            except Exception as e:
                if attempt == 0 and ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower()):
                    time.sleep(4.0)
                    continue
                return None
        return None

    @staticmethod
    def _candidate_stems(word: str) -> List[str]:
        """Return candidate root forms for common English inflections (-ly, -ed, -ing, -es, -s)."""
        stems = [word]
        if len(word) >= 6 and word.endswith("ly"):
            stems.append(word[:-2])
        if len(word) >= 6 and word.endswith("ed"):
            stems.append(word[:-2])
            stems.append(word[:-1])
        if len(word) >= 6 and word.endswith("ing"):
            stems.append(word[:-3])
            stems.append(word[:-3] + "e")
        if len(word) >= 5 and word.endswith("es"):
            stems.append(word[:-2])
        elif len(word) >= 5 and word.endswith("s") and not word.endswith("ss"):
            stems.append(word[:-1])
        return [s for s in stems if len(s) >= 3]

    def extract_query_keywords(self, query: str) -> List[str]:
        """Extract lowercased keywords with length >= config.MIN_KEYWORD_LENGTH excluding stopwords,
        and expand with semantic intent synonyms for fragmented student queries.
        """
        norm_q = query.lower().replace("wi-fi", "wifi").replace("e-mail", "email")
        words = re.findall(r"\w+", norm_q, re.UNICODE)
        keywords = [
            w for w in words
            if len(w) >= config.MIN_KEYWORD_LENGTH and w not in STOPWORDS
        ]
        # Expand keywords using semantic intent dictionary (including stemmed & typo-recovered roots)
        expanded = set(keywords)
        for w in words:
            for candidate in self._resolve_word_and_stems(w):
                if len(candidate) >= config.MIN_KEYWORD_LENGTH and candidate not in STOPWORDS:
                    expanded.add(candidate)
                if candidate in INTENT_EXPANSIONS:
                    for exp_w in INTENT_EXPANSIONS[candidate]:
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
           If embedding fails (e.g. offline, timeout, quota), gracefully falls back
           to keyword relevance scoring over the verified knowledge corpus.
        3. Hybrid boost: +0.05 for each query keyword (len >= 4, no stopwords) in chunk's title. Max boost 0.15.
        4. Return top k chunks with score >= min_score.
        5. Always ALSO return the best-matching contacts.md chunk (if not already included).
        6. Return (chunks, top_score, mode).
           If no chunk passes min_score -> mode = 'no_context'.
        """
        # Ensure index is ready
        if self.matrix is None or len(self.metadata) == 0:
            self._ensure_index_loaded()

        query_vec = None
        try:
            query_vec = self.embed_query(query)
        except Exception as e:
            query_vec = None

        keywords = self.extract_query_keywords(query)
        norm_q = query.lower().replace("wi-fi", "wifi").replace("e-mail", "email")
        raw_words = [
            w for w in re.findall(r"\w+", norm_q, re.UNICODE)
            if len(w) >= 3 and w not in STOPWORDS
        ]
        direct_words = set()
        for w in raw_words:
            for s in self._resolve_word_and_stems(w):
                if s not in STOPWORDS:
                    direct_words.add(s)
        ubiquitous_terms = {
            "vše", "vse", "student", "students", "international", "university",
            "prague", "czech", "study", "studying", "campus", "english",
            "courses", "course", "find", "need", "apply", "access",
        }
        generic_qualifiers = {
            "central", "centre", "center", "office", "department", "service",
            "services", "system", "portal", "page", "option", "options",
            "information", "help", "question", "guide", "rules", "rule",
        }
        specific_words = direct_words - ubiquitous_terms - generic_qualifiers
        word_patterns = {
            w: re.compile(rf"\b{re.escape(w)}", re.UNICODE)
            for w in (direct_words | set(keywords))
        }

        if query_vec is not None:
            raw_similarities = np.dot(self.matrix, query_vec)
        else:
            raw_similarities = np.zeros(len(self.metadata), dtype=np.float32)

        scored_chunks: List[Dict[str, Any]] = []
        for idx, (sim, meta) in enumerate(zip(raw_similarities, self.metadata)):
            chunk_copy = dict(meta)
            base_score = float(sim)
            title_lower = chunk_copy.get("title", "").lower()
            doc_id_lower = chunk_copy.get("doc_id", "").lower().replace("-", " ")
            header_lower = f"{title_lower} {doc_id_lower}"
            text_lower = chunk_copy.get("text", "").lower()

            if query_vec is None:
                # High-fidelity keyword retrieval weighting specific domain words and word boundaries
                direct_title = 0.0
                direct_text = 0.0
                specific_hits = 0
                for w in direct_words:
                    pat = word_patterns[w]
                    is_spec = w in specific_words
                    if is_spec:
                        weight = 1.0
                    elif w in generic_qualifiers:
                        weight = 0.85
                    else:
                        weight = 0.20 if specific_words else 1.0
                    in_hdr = bool(pat.search(header_lower))
                    in_txt = bool(pat.search(text_lower))
                    if in_hdr:
                        direct_title += weight
                    if in_txt:
                        direct_text += weight
                    if is_spec and (in_hdr or in_txt):
                        specific_hits += 1

                exp_title = sum(
                    1.0 for kw in keywords
                    if kw not in direct_words and word_patterns[kw].search(header_lower)
                )
                exp_text = sum(
                    1.0 for kw in keywords
                    if kw not in direct_words and word_patterns[kw].search(text_lower)
                )
                # Strict topicality gate: if the query has specific topic words and this chunk matches
                # zero specific words and zero expanded keywords, never let generic words cross MIN_SCORE.
                if specific_words and specific_hits == 0 and exp_title == 0 and exp_text == 0:
                    base_score = 0.25
                elif keywords or direct_words:
                    weighted = (direct_title * 5.5) + (direct_text * 2.5) + (exp_title * 1.5) + (exp_text * 0.4)
                    effective_len = len(specific_words) if specific_words else len(direct_words)
                    denom = max(float(effective_len * 5.0 + 4.0), 6.0)
                    base_score = min(0.95, 0.45 + (weighted / denom) * 0.50) if weighted > 0 else 0.20
                else:
                    base_score = 0.50

            # Calculate keyword boost
            boost = 0.0
            for kw in keywords:
                if word_patterns[kw].search(header_lower):
                    boost += config.KEYWORD_BOOST
            boost = min(boost, config.MAX_KEYWORD_BOOST)

            final_score = base_score + boost
            chunk_copy["base_score"] = round(base_score, 4)
            chunk_copy["keyword_boost"] = round(boost, 4)
            chunk_copy["score"] = round(final_score, 4)
            scored_chunks.append(chunk_copy)

        # Sort all chunks by final score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        # Report top_score on the exact same basis used for threshold gating so logs/UI never contradict mode
        if query_vec is not None:
            top_score = max((c["base_score"] for c in scored_chunks), default=0.0)
            passing_chunks = [c for c in scored_chunks if c["base_score"] >= min_score]
        else:
            top_score = scored_chunks[0]["score"] if scored_chunks else 0.0
            passing_chunks = [c for c in scored_chunks if c["score"] >= min_score]
        selected_chunks: List[Dict[str, Any]] = []
        doc_counts: Dict[str, int] = {}
        for c in passing_chunks:
            did = c.get("doc_id", "")
            if doc_counts.get(did, 0) < 2:
                selected_chunks.append(c)
                doc_counts[did] = doc_counts.get(did, 0) + 1
                if len(selected_chunks) >= k:
                    break

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
