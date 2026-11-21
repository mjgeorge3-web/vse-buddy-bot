"""Unit tests for bot post-processing, history deduplication, and retriever expansion."""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot import BuddyBot
from retriever import Retriever


class TestBotFormattingAndHistory:
    """Tests for BuddyBot post-processing and conversational history handling."""

    def test_format_sources_section_single_and_multi(self):
        bot = BuddyBot()
        chunks = [
            {"title": "Study Regulations", "source_url": "https://vse.cz/study", "doc_id": "doc1"},
            {"title": "Dormitory Housing", "source_url": "https://vse.cz/dorms", "doc_id": "doc2"},
            {"title": "Thesis Submission", "source_url": "https://vse.cz/thesis", "doc_id": "doc3"},
        ]

        # Case 1: Answer cites [1] and [3]
        raw_answer = "You must register on InSIS [1] and submit errata in the archive [3]."
        sources_text, cited_chunks = bot.format_sources_section(raw_answer, chunks)
        assert len(cited_chunks) == 2
        assert cited_chunks[0]["title"] == "Study Regulations"
        assert cited_chunks[1]["title"] == "Thesis Submission"
        assert "[Study Regulations](https://vse.cz/study)" in sources_text
        assert "[Thesis Submission](https://vse.cz/thesis)" in sources_text

        # Case 2: Composite citation [1, 2]
        raw_answer_2 = "Refer to the housing and regulation guidelines [1, 2]."
        sources_text_2, cited_chunks_2 = bot.format_sources_section(raw_answer_2, chunks)
        assert len(cited_chunks_2) == 2
        assert cited_chunks_2[0]["title"] == "Study Regulations"
        assert cited_chunks_2[1]["title"] == "Dormitory Housing"

        # Case 3: No citation bracket in raw answer -> top chunks fallback
        raw_answer_3 = "General answer without explicit brackets."
        sources_text_3, cited_chunks_3 = bot.format_sources_section(raw_answer_3, chunks)
        assert len(cited_chunks_3) == 3
        assert "**Sources:**" in sources_text_3

    def test_history_deduplication_logic(self):
        """Verify that BuddyBot.prepare_past_history removes a trailing duplicate current question."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"},
            {"role": "user", "content": "How many credits per semester?"},
        ]
        question = "How many credits per semester?"

        past_history = BuddyBot.prepare_past_history(question, history)
        assert len(past_history) == 2
        assert past_history[-1]["role"] == "assistant"
        assert past_history[-1]["content"] == "Hi! How can I help?"

        # Non-matching trailing user message should be preserved
        other_past = BuddyBot.prepare_past_history("Where is the library?", history)
        assert len(other_past) == 3

    def test_missing_api_key_reports_clear_error(self, monkeypatch):
        """Verify that missing GEMINI_API_KEY fails fast with an explicit key error (not a timeout)."""
        import config
        bot = BuddyBot()
        monkeypatch.setattr(bot.retriever, "embed_query", lambda q: None)
        monkeypatch.setattr(config, "get_gemini_api_key", lambda: "")
        bot.client = None

        result = bot.answer("What are the library opening hours?")
        assert result["mode"] == "error"
        assert "GEMINI_API_KEY" in result["answer"]
        assert "did not respond within 15 seconds" not in result["answer"]


class TestVectorIndexIntegrity:
    """Tests that verify real NumPy vector embeddings (no random-noise corruption) and hash match."""

    def test_vector_index_has_real_embeddings_and_valid_hash(self):
        import numpy as np
        import config, ingest

        retriever = Retriever()
        assert retriever.matrix is not None
        assert retriever.matrix.ndim == 2
        assert retriever.matrix.shape[1] == 3072
        assert len(retriever.metadata) == retriever.matrix.shape[0]

        # Normalized SHA-256 hash matches disk so clones never trigger unintended re-indexing
        assert ingest.compute_knowledge_hash(config.KNOWLEDGE_DIR) == config.INDEX_HASH_PATH.read_text(encoding="utf-8").strip()

        # Real semantic embeddings have strong off-diagonal neighbor similarity; random 3072-d noise sits near ~0.04
        sims = retriever.matrix @ retriever.matrix.T
        np.fill_diagonal(sims, 0.0)
        max_neighbor_sims = sims.max(axis=1)
        assert float(max_neighbor_sims.min()) > 0.35, (
            f"Detected corrupted/random embedding vector with max neighbor similarity {max_neighbor_sims.min():.4f}"
        )
        # No identical stub chunks (e.g. lone horizontal rules "---")
        assert float(max_neighbor_sims.max()) < 0.995, (
            f"Detected duplicate stub chunk with cosine similarity {max_neighbor_sims.max():.4f}"
        )

    def test_anaphoric_word_boundary_no_false_merge(self):
        """Ensure 'it' inside words like 'dormitory' or 'security' does not merge previous turn."""
        bot = BuddyBot()
        history = [
            {"role": "user", "content": "What are the library opening hours?"},
            {"role": "assistant", "content": "Mon 9-19, Tue-Thu 8-19, Fri 8-18."},
        ]
        # Contains substring 'it' in 'university' and 'security', but is an independent question
        q = "How does campus security work at the university?"
        assert bot.build_retrieval_query(q, history) == q
        # Genuine pronoun 'it' with word boundary still merges short follow-ups
        merged = bot.build_retrieval_query("Is it open on Friday?", history)
        assert "library opening hours" in merged.lower()

    def test_unverified_docs_are_flagged_in_index(self):
        retriever = Retriever()
        unverified_docs = {m["doc_id"] for m in retriever.metadata if m.get("unverified")}
        assert "13-czech-embassies-abroad-mzv.md" in unverified_docs
        assert "15-dormitories-and-student-housing.md" in unverified_docs


class TestRetrieverIntentExpansion:
    """Tests for keyword-based query expansion in Retriever."""

    def test_thesis_errata_expansion(self):
        retriever = Retriever()
        query = "How do I submit errata for my final thesis?"
        keywords = retriever.extract_query_keywords(query)
        assert "errata" in keywords
        assert "thesis" in keywords
        assert "insis" in keywords

    def test_credit_voucher_expansion(self):
        retriever = Retriever()
        query = "How many credits in a semester?"
        keywords = retriever.extract_query_keywords(query)
        assert "credits" in keywords
        assert "ects" in keywords
        assert "voucher" in keywords


class TestSecurityAndPipelineBehavior:
    """Behavioral tests for chunking edge cases, config handling, HTTP security, and end-to-end guardrails."""

    def test_ingest_line_chunking_does_not_duplicate_lines(self):
        import ingest
        # Single long paragraph split by lines (no blank lines)
        lines = [f"Line {i:02d} short text." for i in range(1, 40)]
        text = "\n".join(lines)
        chunks = ingest.split_section_paragraphs(text, max_chars=200, target_max=150, overlap=60)
        assert len(chunks) > 1
        for ch in chunks:
            ch_lines = ch.splitlines()
            for a, b in zip(ch_lines, ch_lines[1:]):
                assert a != b, f"Duplicate consecutive line in chunk: {a!r}"

    def test_config_does_not_permanently_cache_empty_api_key(self, monkeypatch):
        import config
        monkeypatch.setattr(config, "_CACHED_GEMINI_API_KEY", None)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setitem(sys.modules, "streamlit", None)
        assert config.get_gemini_api_key() == ""
        # Setting env var afterwards must be picked up cleanly
        monkeypatch.setenv("GEMINI_API_KEY", "test_key_after_load")
        assert config.get_gemini_api_key() == "test_key_after_load"
        monkeypatch.setattr(config, "_CACHED_GEMINI_API_KEY", None)

    def test_out_of_domain_no_context_not_bypassed_by_policy_keyword(self, monkeypatch):
        """A query rejected into no_context by retriever must not be flipped to normal by a policy keyword."""
        bot = BuddyBot()
        monkeypatch.setattr(
            bot.retriever,
            "retrieve",
            lambda q: ([{"doc_id": "contacts.md", "title": "Contacts", "source_url": "https://www.vse.cz/english/contacts/", "text": "Contacts", "is_contacts": True}], 0.35, "no_context"),
        )
        # Capture the exact mode & error path without calling Gemini
        monkeypatch.setattr(bot, "_get_client", lambda: (_ for _ in ()).throw(ValueError("No key")))
        res = bot.answer("What is the penalty kick rule in FIFA World Cup?")
        # Even though "penalty" is in policy_triggers, no policy chunk is injected
        assert "50-vse-policies-rules-and-regulations.md" not in res.get("retrieved_sources", [])

    def test_end_to_end_citation_and_referral_tracking(self, monkeypatch):
        """Verify BuddyBot distinguishes LLM-native referrals from guardrail-enforced referrals."""
        from types import SimpleNamespace
        bot = BuddyBot()
        sample_chunks = [{
            "doc_id": "12-visa-and-residence-permit-general.md",
            "title": "Visa and Residence Permit General Guide",
            "source_url": "https://ozs.vse.cz/english/visa/",
            "date_saved": "2026-11-04",
            "unverified": False,
            "text": "Non-EU students require a long-stay study visa.",
            "score": 0.88,
        }]
        monkeypatch.setattr(bot.retriever, "retrieve", lambda q: (sample_chunks, 0.88, "normal"))

        class _FakeClient:
            def __init__(self, reply_text):
                self.models = SimpleNamespace(
                    generate_content=lambda **kwargs: SimpleNamespace(text=reply_text)
                )

        # Case 1: LLM omits explicit referral -> deterministic guardrail appends notice
        monkeypatch.setattr(bot, "_get_client", lambda: _FakeClient("Non-EU students need a study visa [1]."))
        res_enforced = bot.answer("Do I need a student visa for VŠE?")
        assert res_enforced["sensitive"] is True
        assert res_enforced["llm_native_referral"] is False
        assert res_enforced["referral_enforced"] is True
        assert "Please confirm this with" in res_enforced["answer"]
        assert "[Visa and Residence Permit General Guide](https://ozs.vse.cz/english/visa/)" in res_enforced["answer"]

        # Case 2: LLM natively includes referral -> guardrail does not append duplicate notice
        monkeypatch.setattr(bot, "_get_client", lambda: _FakeClient("Non-EU students need a study visa [1]. Please contact ozs@vse.cz to confirm."))
        res_native = bot.answer("Do I need a student visa for VŠE?")
        assert res_native["sensitive"] is True
        assert res_native["llm_native_referral"] is True
        assert res_native["referral_enforced"] is False
        assert "Please confirm this with" not in res_native["answer"]

    def test_demo_server_http_security_and_api_validation(self):
        """Spin up InSISDemoHandler on an ephemeral port and verify real HTTP security & API responses."""
        import json
        import threading
        import urllib.error
        import urllib.request
        from http.server import ThreadingHTTPServer
        from insis_demo.server import InSISDemoHandler

        server = ThreadingHTTPServer(("127.0.0.1", 0), InSISDemoHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{port}"

            # Blocked extensions must return HTTP 403
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(f"{base}/server.py", timeout=5)
            assert exc_info.value.code == 403

            # Malformed limit parameter must clamp safely instead of crashing with 500
            with urllib.request.urlopen(f"{base}/api/insis/navigate?q=scholarship&limit=invalid", timeout=5) as resp:
                assert resp.status == 200
                data = json.loads(resp.read().decode("utf-8"))
                assert data["count"] >= 1

            # Root path serves the canonical HTML application
            with urllib.request.urlopen(f"{base}/", timeout=5) as resp:
                assert resp.status == 200
                html = resp.read().decode("utf-8")
                assert "InSIS" in html
        finally:
            server.shutdown()
            server.server_close()

    def test_vercel_api_helpers_parse_limit_and_routes(self):
        """Verify Vercel serverless helper functions clamp limits and resolve rewritten routes."""
        from api.index import _parse_limit, resolve_api_path

        assert _parse_limit({"limit": ["5"]}) == 5
        assert _parse_limit({"limit": ["abc"]}) == 3
        assert _parse_limit({"limit": ["-4"]}) == 1
        assert _parse_limit({"limit": ["999"]}) == 20

        path, params = resolve_api_path("/api/index.py?__route=vse/policies&q=retake", {})
        assert path == "/api/vse/policies"
        assert params["q"] == ["retake"]

    def test_canonical_frontend_html_escaping_and_mode_badges(self):
        """Verify canonical public/app.js escapes HTML before markdown formatting and gates guidance badges."""
        app_js = (Path(__file__).resolve().parent.parent / "public" / "app.js").read_text(encoding="utf-8")
        assert "escapeHtml(str)" in app_js
        assert 'mode === "normal" && !hasUnverifiedWarning' in app_js
        assert "Česká spořitelna" in app_js
        assert "24242442 / 0800" in app_js
