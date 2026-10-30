"""Main orchestration bot for VŠE Buddy Bot.

Executes the pipeline:
1. Safety checks (crisis and sensitive topic)
2. Query formulation & semantic retrieval with hybrid ranking
3. Prompt assembly & Google Gemini generation
4. Python post-processing (inline citations, official referral append)
5. Privacy-preserving event logging
"""

import csv
from datetime import datetime, timezone
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from google import genai
from google.genai import types

import config
import prompts
from retriever import Retriever
import safety

REFERRAL_TARGETS = {
    "visa_residence": "the VŠE International Office and the Czech Ministry of the Interior (mvcr.cz)",
    "foreign_police": "the Czech Foreign Police and the VŠE International Office",
    "employment_work": "the Czech Ministry of the Interior (mvcr.cz) and the VŠE International Office",
    "health_insurance": "the official health insurance provider and the VŠE International Office",
    "legal": "the VŠE Legal Department or an authorized legal advisor",
    "tuition_payment": "your faculty Study Department or the VŠE Admission Office",
    "academic_failure_expulsion": "your faculty Study Department and official VŠE Study Regulations",
}


class BuddyBot:
    """Orchestrates safety, retrieval, generation, and citation formatting."""

    def __init__(self):
        self.retriever = Retriever()
        self.client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Lazily initialize genai.Client with API key."""
        if self.client is None:
            api_key = config.get_gemini_api_key()
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your .env file or Streamlit secrets."
                )
            self.client = genai.Client(api_key=api_key)
        return self.client

    def build_retrieval_query(self, question: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """Build retrieval query by combining the current turn with the previous user turn.
        
        Handles conversational follow-ups (e.g. 'and how much does it cost?').
        """
        if not history:
            return question.strip()

        # Find the most recent previous user message
        prev_user_turn = ""
        for msg in reversed(history):
            if msg.get("role") == "user" and msg.get("content", "").strip() != question.strip():
                prev_user_turn = msg.get("content", "").strip()
                break

        if prev_user_turn:
            return f"{prev_user_turn} {question}".strip()
        return question.strip()

    def format_sources_section(self, raw_answer: str, chunks: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """Parse inline citations [1], [2] and append verified Sources links in markdown."""
        if not chunks:
            return "", []

        # Find cited chunk numbers (e.g., [1], [2], or multi-citations like [1, 3])
        cited_indices: List[int] = []
        for bracket_content in re.findall(r"\[([\d\s,]+)\]", raw_answer):
            for part in bracket_content.split(","):
                part_clean = part.strip()
                if part_clean.isdigit():
                    cited_indices.append(int(part_clean))
        valid_indices = [idx for idx in cited_indices if 1 <= idx <= len(chunks)]

        # If chunks were cited, only list the cited chunks (preserving citation order)
        if valid_indices:
            seen_docs = set()
            selected_chunks = []
            for idx in valid_indices:
                chunk = chunks[idx - 1]
                doc_key = chunk.get("source_url") or chunk.get("doc_id") or chunk.get("title")
                if doc_key not in seen_docs:
                    seen_docs.add(doc_key)
                    selected_chunks.append(chunk)
        else:
            # If none cited, list unique top chunks as background context
            seen_docs = set()
            selected_chunks = []
            for chunk in chunks[:3]:
                doc_key = chunk.get("source_url") or chunk.get("doc_id") or chunk.get("title")
                if doc_key not in seen_docs:
                    seen_docs.add(doc_key)
                    selected_chunks.append(chunk)

        # Format markdown sources block
        source_lines = ["\n\n**Sources:**"]
        for c in selected_chunks:
            title = c.get("title", "VŠE Information")
            url = c.get("source_url", "")
            unverified_label = " *(unverified - please confirm)*" if c.get("unverified") else ""
            if url:
                source_lines.append(f"- [{title}]({url}){unverified_label}")
            else:
                source_lines.append(f"- {title}{unverified_label}")

        return "\n".join(source_lines), selected_chunks

    def log_interaction(
        self,
        session_id: str,
        question: str,
        mode: str,
        top_score: float,
        latency_ms: float,
        feedback: str = "",
    ):
        """Privacy-preserving logging.
        
        Stores timestamp, anonymous session UUID, question, mode, score, latency, and feedback.
        Never logs message text for crisis events.
        """
        if not config.ENABLE_LOGGING:
            return

        try:
            config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            file_exists = config.CHAT_LOG_PATH.exists()

            with open(config.CHAT_LOG_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow([
                        "timestamp",
                        "session_id",
                        "question",
                        "mode",
                        "top_score",
                        "latency_ms",
                        "feedback",
                    ])

                # Log only event type for crisis, never the user's message
                logged_question = "[CRISIS REDACTED]" if mode == "crisis" else question
                now_iso = datetime.now(timezone.utc).isoformat()
                writer.writerow([
                    now_iso,
                    session_id,
                    logged_question,
                    mode,
                    round(top_score, 4),
                    round(latency_ms, 1),
                    feedback,
                ])
        except Exception as e:
            print(f"[Logger Warning] Could not write to chat log: {e}")

    def answer(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Main end-to-end question answering pipeline.
        
        Returns dictionary:
        {
            'answer': str,
            'sources': list[dict],
            'mode': 'normal' | 'no_context' | 'crisis',
            'sensitive': bool,
            'sensitive_topic': str | None,
            'top_score': float,
            'latency_ms': float
        }
        """
        start_time = time.perf_counter()
        session_uuid = session_id or str(uuid.uuid4())

        # -------------------------------------------------------------
        # 1. Deterministic crisis check (runs BEFORE retrieval & Gemini)
        # -------------------------------------------------------------
        if safety.check_crisis(question):
            latency = (time.perf_counter() - start_time) * 1000
            crisis_msg = safety.get_crisis_response()
            self.log_interaction(
                session_id=session_uuid,
                question=question,
                mode="crisis",
                top_score=0.0,
                latency_ms=latency,
            )
            return {
                "answer": crisis_msg,
                "sources": [],
                "mode": "crisis",
                "sensitive": False,
                "sensitive_topic": None,
                "top_score": 0.0,
                "latency_ms": round(latency, 1),
            }

        # -------------------------------------------------------------
        # 2. Sensitive topic check
        # -------------------------------------------------------------
        is_sensitive, sensitive_topic = safety.check_sensitive(question)

        # -------------------------------------------------------------
        # 3. Retrieval query construction
        # -------------------------------------------------------------
        retrieval_query = self.build_retrieval_query(question, history)

        # -------------------------------------------------------------
        # 4. Semantic retrieval & ranking
        # -------------------------------------------------------------
        try:
            chunks, top_score, mode = self.retriever.retrieve(retrieval_query)
        except Exception as e:
            print(f"[Retriever Error]: {e}")
            latency = (time.perf_counter() - start_time) * 1000
            error_msg = (
                "I am having difficulty accessing the knowledge index right now. "
                "Please verify that your Gemini API key is configured properly."
            )
            return {
                "answer": error_msg,
                "sources": [],
                "mode": "error",
                "sensitive": is_sensitive,
                "sensitive_topic": sensitive_topic,
                "top_score": 0.0,
                "latency_ms": round(latency, 1),
            }

        # In no_context mode: only provide contacts chunk so the bot can refuse & refer
        if mode == "no_context":
            contacts_chunks = [c for c in chunks if c.get("is_contacts")]
            context_chunks = contacts_chunks if contacts_chunks else []
        else:
            context_chunks = chunks

        # -------------------------------------------------------------
        # 5. Gemini Generation
        # -------------------------------------------------------------
        prompt_content = prompts.build_prompt_with_context(question, context_chunks)

        # Format conversation history for Gemini (last 6 messages)
        recent_history = history[-config.MAX_HISTORY_MESSAGES:] if history else []
        gemini_contents: List[types.Content] = []

        for msg in recent_history:
            role = "user" if msg.get("role") == "user" else "model"
            gemini_contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.get("content", ""))],
                )
            )

        # Append current user prompt
        gemini_contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt_content)],
            )
        )

        raw_answer = None
        models_to_try = [config.CHAT_MODEL, "gemini-3.5-flash-lite", "gemini-3-flash-preview"]
        last_error = None

        client = self._get_client()
        for candidate_model in models_to_try:
            try:
                response = client.models.generate_content(
                    model=candidate_model,
                    contents=gemini_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=prompts.SYSTEM_PROMPT,
                        temperature=config.TEMPERATURE,
                        max_output_tokens=config.MAX_OUTPUT_TOKENS,
                    ),
                )
                if response.text:
                    raw_answer = response.text.strip()
                    break
            except Exception as e:
                last_error = e
                continue

        if not raw_answer:
            if last_error:
                print(f"[Generation Error]: {last_error}")
            latency = (time.perf_counter() - start_time) * 1000
            error_msg = (
                "I apologize, but I encountered an error connecting to the Gemini service. "
                "Please check your API key and connection."
            )
            return {
                "answer": error_msg,
                "sources": [],
                "mode": "error",
                "sensitive": is_sensitive,
                "sensitive_topic": sensitive_topic,
                "top_score": top_score,
                "latency_ms": round(latency, 1),
            }

        # -------------------------------------------------------------
        # 6. Post-processing (Citations & Referral)
        # -------------------------------------------------------------
        sources_text, cited_chunks = self.format_sources_section(raw_answer, context_chunks)
        final_answer = raw_answer

        # If sensitive topic and answer does not explicitly refer student, append referral note
        if is_sensitive:
            referral_keywords = [
                "confirm", "refer", "contact", "office", "department", "mvcr",
                "embassy", "police", "counselling", "skm", "ozs"
            ]
            has_referral = any(kw in raw_answer.lower() for kw in referral_keywords)
            if not has_referral:
                target_office = REFERRAL_TARGETS.get(
                    sensitive_topic or "",
                    "the responsible official office or faculty department"
                )
                final_answer += f"\n\n⚠️ Please confirm this with {target_office}."

        # Append clickable markdown sources
        final_answer += sources_text

        latency = (time.perf_counter() - start_time) * 1000
        self.log_interaction(
            session_id=session_uuid,
            question=question,
            mode=mode,
            top_score=top_score,
            latency_ms=latency,
        )

        return {
            "answer": final_answer,
            "sources": cited_chunks,
            "mode": mode,
            "sensitive": is_sensitive,
            "sensitive_topic": sensitive_topic,
            "top_score": round(top_score, 4),
            "latency_ms": round(latency, 1),
        }
