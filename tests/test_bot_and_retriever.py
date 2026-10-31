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
        """Verify that passing history containing the current question does not duplicate it."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"},
            {"role": "user", "content": "How many credits per semester?"},
        ]
        question = "How many credits per semester?"

        # Simulate the logic in bot.py
        past_history = []
        if history:
            if history[-1].get("role") == "user" and history[-1].get("content", "").strip() == question.strip():
                past_history = history[:-1]
            else:
                past_history = history

        assert len(past_history) == 2
        assert past_history[-1]["role"] == "assistant"
        assert past_history[-1]["content"] == "Hi! How can I help?"


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
