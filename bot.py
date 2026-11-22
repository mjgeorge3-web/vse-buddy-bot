"""Main orchestration bot for VŠE Buddy Bot.

Executes the pipeline:
1. Safety checks (deterministic crisis filter and sensitive topic detection)
2. Query formulation & semantic retrieval with hybrid ranking + SQLite knowledge enrichment
3. Prompt assembly & live Google Gemini generation (15s timeout with rate-limit retry)
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
import concurrent.futures

from google import genai
from google.genai import types

import config
import prompts
from retriever import Retriever
import safety
import student_profile

# Shared worker pool for timeout-isolated LLM calls
_LLM_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm_pool")


class BuddyBot:
    """Orchestrates safety, retrieval, live Gemini generation, and citation formatting."""

    def __init__(self):
        self.retriever = Retriever()
        self.client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Lazily initialize genai.Client with API key and 15s (15000ms) timeout."""
        if self.client is None:
            api_key = config.get_gemini_api_key()
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your .env file or Streamlit secrets."
                )
            self.client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=15000, api_version="v1beta"),
            )
        return self.client

    @staticmethod
    def prepare_past_history(
        question: str, history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Remove a trailing duplicate copy of the current user question from conversation history."""
        if not history:
            return []
        if (
            history[-1].get("role") == "user"
            and history[-1].get("content", "").strip() == question.strip()
        ):
            return list(history[:-1])
        return list(history)

    def build_retrieval_query(self, question: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """Build retrieval query, smartly incorporating context only for genuine follow-up questions.
        
        Avoids corrupting independent queries (e.g., asking about accommodation after asking about visas).
        """
        clean_q = question.strip()
        if not history or not clean_q:
            return clean_q

        q_lower = clean_q.lower()
        words = q_lower.split()

        # Follow-up cues indicating the user is referring to the previous turn
        is_short_followup = len(words) <= 4
        anaphoric_cues = [
            "it", "that", "this", "there", "then", "cost", "how much", "how long",
            "what about", "and for", "how about", "more", "else", "details",
            "who", "where is it", "why", "is it", "are they", "does it",
        ]
        has_anaphoric_cue = any(
            re.search(rf"\b{re.escape(cue)}\b", q_lower) for cue in anaphoric_cues
        )

        # Independent topic cues that indicate a new question topic
        independent_topic_cues = [
            "voucher", "vouchers", "credit", "credits", "ects", "thesis", "errata",
            "accommodation", "accomodation", "dorm", "dorms", "housing", "flat",
            "visa", "visas", "police", "insurance", "library", "menza", "canteen",
            "timetable", "schedule", "admission", "application", "apply",
            "study plan", "exam", "exams", "retake", "gpa", "tuition",
        ]
        has_independent_topic = any(
            re.search(rf"\b{re.escape(cue)}\b", q_lower) for cue in independent_topic_cues
        )

        # Only combine with previous turn if it's genuinely a follow-up AND doesn't introduce a new topic
        if (is_short_followup or has_anaphoric_cue) and not (has_independent_topic and len(words) >= 4):
            prev_user_turn = ""
            for msg in reversed(history):
                if msg.get("role") == "user" and msg.get("content", "").strip() != clean_q:
                    prev_user_turn = msg.get("content", "").strip()
                    break

            if prev_user_turn:
                return f"{prev_user_turn} {clean_q}".strip()

        return clean_q

    def format_sources_section(self, raw_answer: str, chunks: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """Parse inline citations [1], [2] and append verified Sources links in markdown.

        Avoids duplicating links whose URLs are already rendered as inline markdown buttons.
        """
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
            for chunk in chunks:
                doc_key = chunk.get("source_url") or chunk.get("doc_id") or chunk.get("title")
                if doc_key not in seen_docs:
                    seen_docs.add(doc_key)
                    selected_chunks.append(chunk)
                    if len(selected_chunks) >= 3:
                        break

        # Suppress source bullets whose exact URL is already linked inline in raw_answer
        inline_urls = {
            u.rstrip("/")
            for u in re.findall(r"\]\((https?://[^\s\)]+)\)", raw_answer)
        }

        if not valid_indices and inline_urls:
            return "", selected_chunks

        bullet_lines = []
        for c in selected_chunks:
            if c.get("is_dynamic_context"):
                continue
            title = c.get("title", "VŠE Information")
            url = c.get("source_url", "")
            if url and url.rstrip("/") in inline_urls:
                continue
            unverified_label = " *(unverified - please confirm)*" if c.get("unverified") else ""
            if url:
                bullet_lines.append(f"- [{title}]({url}){unverified_label}")
            else:
                bullet_lines.append(f"- {title}{unverified_label}")

        if not bullet_lines:
            return "", selected_chunks

        return "\n\n**Sources:**\n" + "\n".join(bullet_lines), selected_chunks

    def log_interaction(
        self,
        session_id: str,
        question: str,
        mode: str,
        top_score: float,
        latency_ms: float,
        feedback: str = "",
    ):
        """Log interaction to logs/chat_log.csv while redacting crisis text."""
        if not config.ENABLE_LOGGING or os.getenv("VERCEL"):
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
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Main end-to-end question answering pipeline.
        
        Returns dictionary:
        {
            'answer': str,
            'sources': list[dict],
            'mode': 'normal' | 'no_context' | 'crisis' | 'error',
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
                "retrieved_sources": [],
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
        ql = question.lower()

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
                "retrieved_sources": [],
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
            context_chunks = list(chunks)

        # -------------------------------------------------------------
        # 4b. Structured SQLite Enrichment (InSIS Routes, Policies, Campus)
        # -------------------------------------------------------------
        # General domain-level triggers (no test-question strings hardcoded).
        insis_nav_triggers = [
            "in insis", "portlet", "portlets", "contact centre", "contact center",
            "general query", "variable symbol", "financing of study", "study financing",
            "accommodation scholarship", "confirmation of study", "odevzdavarna",
            "coursework submission", "errata", "iskam", "two-factor", "authenticator",
            "totp", "course evaluation", "anketa", "document server",
        ]
        is_direct_nav = any(p in ql for p in insis_nav_triggers)

        campus_triggers = [
            "bibliobox", "which floor", "what floor", "room number",
            "coordinator office", "study coordinator", "ism coordinator",
            "likesova", "likešova", "vencovskeho", "vencovského",
            "admission office", "it helpdesk", "menza", "av gastro",
        ]
        has_room_code = bool(re.search(r"\b(?:sb|nb|rb|jm)\s*\d{2,3}\b", ql))
        is_direct_campus = has_room_code or any(cue in ql for cue in campus_triggers)

        policy_triggers = [
            "retake", "4+", "4 plus", "vouchers", "voucher", "penalty", "sanction",
            "expelled", "expulsion", "interruption", "grading scale",
            "plagiarism", "credit recognition", "fail an exam", "failed an exam", "fail exam",
        ]
        is_policy_query = any(pc in ql for pc in policy_triggers)

        try:
            import insis_nav_db
            candidates = []
            # When vector retrieval rejected an out-of-domain query (mode == "no_context"),
            # ONLY allow explicit InSIS navigation queries to enrich — never let generic
            # policy/campus keyword hits bypass the Stage 1 similarity gate.
            allow_policy_campus = mode != "no_context"
            if is_direct_nav or (allow_policy_campus and (is_direct_campus or is_policy_query)):
                search_res = insis_nav_db.unified_search(question, limit=2)

                if is_direct_nav and search_res.get("insis_routes"):
                    for r in search_res["insis_routes"][:1]:
                        candidates.append(("insis", r.get("rank", -5.0) - 10.0, r))
                if allow_policy_campus and is_policy_query and search_res.get("policies"):
                    for p in search_res["policies"][:1]:
                        candidates.append(("policy", p.get("rank", -5.0), p))
                if allow_policy_campus and is_direct_campus and search_res.get("campus_locations"):
                    for loc in search_res["campus_locations"][:1]:
                        candidates.append(("campus", loc.get("rank", -5.0), loc))

            candidates.sort(key=lambda c: c[1])

            db_chunk = None
            best_kind = None
            if candidates:
                best_kind, _, best_item = candidates[0]

                if best_kind == "policy":
                    pol = best_item
                    db_chunk = {
                        "id": f"policy_{pol['rule_id']}",
                        "doc_id": "50-vse-policies-rules-and-regulations.md",
                        "title": f"VŠE Policy [{pol['rule_id']}]: {pol['title']}",
                        "source_url": pol.get("official_url") or "https://www.vse.cz/english/students/study/study-regulations/",
                        "date_saved": config.STRUCTURED_DATA_DATE,
                        "unverified": False,
                        "score": round(top_score, 4),
                        "text": (
                            f"Policy Title: {pol['title']}\n"
                            f"Category: {pol['category']} | Official Reference: {pol['official_reference']}\n"
                            f"Rule Summary: {pol['summary']}\n"
                            f"Detailed Regulation:\n{pol['rule_text']}\n"
                            f"Sanctions / Penalties for Non-Compliance:\n{pol.get('penalty_or_consequence', 'None')}\n"
                        ),
                        "is_policy": True,
                    }
                elif best_kind == "campus":
                    loc = best_item
                    db_chunk = {
                        "id": f"campus_{loc['location_id']}",
                        "doc_id": "51-vse-campus-offices-and-services.md",
                        "title": f"VŠE Campus Directory: {loc['name']} ({loc['room_number']})",
                        "source_url": loc.get("official_url") or "https://www.vse.cz/english/students/campus-services/campus-and-classrooms/",
                        "date_saved": config.STRUCTURED_DATA_DATE,
                        "unverified": False,
                        "score": round(top_score, 4),
                        "text": (
                            f"Location Name: {loc['name']}\n"
                            f"Building: {loc['building']} | Floor: {loc['floor']} | Room Number: {loc['room_number']}\n"
                            f"Facility Type: {loc['facility_type']}\n"
                            f"Directions:\n{loc['directions_from_entrance']}\n"
                            f"Amenities & Contacts: {loc.get('amenities_accessibility', 'Standard')}\n"
                            f"Hours / Availability: {loc.get('hours_or_availability', 'Standard building hours')}\n"
                        ),
                        "is_campus_loc": True,
                    }
                elif best_kind == "insis":
                    top_nav = best_item
                    tid = top_nav["task_id"]
                    if tid in ("TASK_THESIS_SUBMISSION", "TASK_THESIS_ERRATA"):
                        backing_doc_id = "48-final-thesis-submission-defense-and-errata.md"
                    elif tid in ("TASK_SCHOLARSHIP_ACCOMMODATION", "TASK_ACCOMMODATION_SCHOLARSHIP"):
                        backing_doc_id = "46-scholarships-campus-navigation-and-printing.md"
                    elif tid in ("TASK_DORM_ISKAM", "TASK_ISKAM_HOUSING"):
                        backing_doc_id = "15-dormitories-and-student-housing.md"
                    elif tid in ("TASK_COURSE_REGISTRATION", "TASK_CREDIT_VOUCHERS", "TASK_EXAM_REGISTRATION"):
                        backing_doc_id = "44-insis-course-registration-and-credit-system.md"
                    else:
                        backing_doc_id = "17-insis-portal.md"

                    db_chunk = {
                        "id": f"insis_nav_{top_nav['task_id']}",
                        "doc_id": backing_doc_id,
                        "title": f"InSIS Navigation Guide: {top_nav['title_en']}",
                        "source_url": top_nav["official_url"],
                        "date_saved": config.STRUCTURED_DATA_DATE,
                        "unverified": tid == "TASK_DORM_ISKAM",
                        "score": round(top_score, 4),
                        "text": (
                            f"InSIS Navigation Task: {top_nav['title_en']} ({top_nav['title_cs']})\n"
                            f"Category: {top_nav['category']} | InSIS Path: {top_nav['portal_path']}\n"
                            f"Breadcrumb Trail: {top_nav['breadcrumbs']}\n"
                            f"Step-by-Step Instructions:\n{top_nav['step_by_step_instructions']}\n"
                            f"Prerequisites: {top_nav.get('prerequisites', 'None')}\n"
                            f"Important Note: {top_nav.get('common_pitfalls', 'None')}\n"
                            f"Official URL: {top_nav['official_url']}\n"
                        ),
                        "is_insis_nav": True,
                    }

            if db_chunk:
                context_chunks = [db_chunk] + context_chunks
                if mode == "no_context" and best_kind == "insis":
                    mode = "normal"
        except Exception as e:
            print(f"[Knowledge DB Query Warning]: {e}")

        # -------------------------------------------------------------
        # 4c. Opt-In Personalised Student Study Profile Context
        # -------------------------------------------------------------
        if user_context:
            try:
                dyn_chunks = student_profile.build_dynamic_context_chunks(question, user_context)
                if dyn_chunks:
                    context_chunks = dyn_chunks + [c for c in context_chunks if not c.get("is_dynamic_context")]
                    if mode == "no_context":
                        mode = "normal"
            except Exception as e:
                print(f"[Dynamic Context Warning]: {e}")

        # Record all retrieved non-dynamic document IDs prior to LLM citation filtering
        retrieved_doc_ids: List[str] = []
        for c in context_chunks:
            did = c.get("doc_id", "")
            if did and not c.get("is_dynamic_context") and did not in retrieved_doc_ids:
                retrieved_doc_ids.append(did)

        # -------------------------------------------------------------
        # 5. Live Google Gemini Generation (15s timeout + single retry on 429)
        # -------------------------------------------------------------
        raw_answer = None
        last_error = None
        is_auth_error = False

        try:
            # Fail fast before retries if GEMINI_API_KEY is missing
            client = self._get_client()

            prompt_content = prompts.build_prompt_with_context(question, context_chunks)
            past_history = self.prepare_past_history(question, history)
            recent_history = past_history[-config.MAX_HISTORY_MESSAGES:] if past_history else []
            gemini_contents: List[types.Content] = []

            last_role = None
            for msg in recent_history:
                role = "user" if msg.get("role") == "user" else "model"
                content = msg.get("content", "").strip()
                if not content or role == last_role:
                    continue
                gemini_contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=content)],
                    )
                )
                last_role = role

            if gemini_contents and gemini_contents[-1].role == "user":
                gemini_contents.pop()

            gemini_contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt_content)],
                )
            )

            def _generate_with_gemini(m_name: str):
                return client.models.generate_content(
                    model=m_name,
                    contents=gemini_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=prompts.SYSTEM_PROMPT,
                        temperature=config.TEMPERATURE,
                        max_output_tokens=config.MAX_OUTPUT_TOKENS,
                    ),
                )

            for attempt_idx in range(2):
                try:
                    future = _LLM_EXECUTOR.submit(_generate_with_gemini, config.CHAT_MODEL)
                    response = future.result(timeout=15.0)
                    if response and response.text:
                        raw_answer = response.text.strip()
                        break
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    err_upper = err_str.upper()
                    if any(tok in err_upper for tok in ("API_KEY_INVALID", "API KEY", "PERMISSION_DENIED", "UNAUTHENTICATED", "401", "403")):
                        is_auth_error = True
                        break
                    if attempt_idx == 0:
                        wait_s = 5.0 if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_upper or "quota" in err_str.lower()) else 2.0
                        time.sleep(wait_s)
                        continue
        except ValueError as e:
            last_error = e
            is_auth_error = True
        except Exception as e:
            last_error = e

        if not raw_answer:
            print(f"[Gemini API Error]: {last_error}")
            latency = (time.perf_counter() - start_time) * 1000
            err_text = str(last_error or "")
            if is_auth_error:
                honest_msg = (
                    "⚠️ **Gemini API Key Missing or Invalid:** Please configure a valid `GEMINI_API_KEY` "
                    "in your `.env` file (see `.env.example`) or Streamlit secrets and try again."
                )
            elif "429" in err_text or "RESOURCE_EXHAUSTED" in err_text or "quota" in err_text.lower():
                honest_msg = (
                    "⚠️ **API Rate Limit Reached:** The Google Gemini free-tier rate limit "
                    "was temporarily reached. Please wait a few seconds and try your question again."
                )
            else:
                honest_msg = (
                    "⚠️ **AI Service Temporarily Unavailable:** The live Google Gemini model did not respond "
                    "within 15 seconds. Please wait a moment and try again."
                )
            return {
                "answer": honest_msg,
                "sources": [],
                "retrieved_sources": retrieved_doc_ids,
                "mode": "error",
                "sensitive": is_sensitive,
                "sensitive_topic": sensitive_topic,
                "top_score": round(top_score, 4),
                "latency_ms": round(latency, 1),
            }

        # -------------------------------------------------------------
        # 6. Post-processing (Citations & Referral)
        # -------------------------------------------------------------
        insis_navs = [c for c in context_chunks if c.get("is_insis_nav")]
        if insis_navs:
            top_nav_chunk = insis_navs[0]
            nav_url = top_nav_chunk.get("source_url", "")
            nav_title = top_nav_chunk.get("title", "InSIS Page").replace("InSIS Navigation Guide: ", "")
            if nav_url and nav_url not in raw_answer:
                raw_answer += f"\n\n[Open {nav_title} in InSIS]({nav_url})"

        sources_text, cited_chunks = self.format_sources_section(raw_answer, context_chunks)
        final_answer = raw_answer

        # If sensitive topic and answer lacks explicit verification/contact referral phrasing, append notice
        llm_native_referral = False
        referral_enforced = False
        if is_sensitive:
            llm_native_referral = safety.has_explicit_referral(raw_answer)
            if not llm_native_referral:
                target_office = safety.REFERRAL_TARGETS.get(
                    sensitive_topic or "",
                    "the responsible official office or faculty department"
                )
                final_answer += f"\n\n⚠️ Please confirm this with {target_office}."
                referral_enforced = True

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
            "retrieved_sources": retrieved_doc_ids,
            "mode": mode,
            "sensitive": is_sensitive,
            "sensitive_topic": sensitive_topic,
            "llm_native_referral": llm_native_referral,
            "referral_enforced": referral_enforced,
            "top_score": round(top_score, 4),
            "latency_ms": round(latency, 1),
        }
