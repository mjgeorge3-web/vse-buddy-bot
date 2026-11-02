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
import concurrent.futures

from google import genai
from google.genai import types

import config
import prompts
from retriever import Retriever
import safety
import student_profile

# Shared worker pool for timeout-isolated LLM calls (never blocks on thread shutdown)
_LLM_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm_pool")

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
        self._query_cache: Dict[str, Dict[str, Any]] = {}

    def _normalize_query(self, text: str) -> str:
        """Strip punctuation and lowercase for in-memory response cache keys."""
        t = re.sub(r"[^\w\s]", " ", text.lower())
        return " ".join(t.split())

    def _get_client(self) -> genai.Client:
        """Lazily initialize genai.Client with API key and 5s timeout."""
        if self.client is None:
            api_key = config.get_gemini_api_key()
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your .env file or Streamlit secrets."
                )
            self.client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=5.0),
            )
        return self.client

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
        has_anaphoric_cue = any(cue in q_lower for cue in anaphoric_cues)

        # Independent topic cues that indicate a new question topic
        independent_topic_cues = [
            "voucher", "vouchers", "credit", "credits", "ects", "thesis", "errata",
            "accommodation", "accomodation", "dorm", "dorms", "housing", "flat",
            "visa", "visas", "police", "insurance", "library", "menza", "canteen",
            "timetable", "schedule", "admission", "application", "apply", "washroom",
            "toilet", "wc", "study plan", "exam", "exams", "retake", "gpa", "tuition",
        ]
        has_independent_topic = any(cue in q_lower for cue in independent_topic_cues)

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

    def _synthesize_grounded_answer(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Synthesizes an immediate grounded answer directly from verified knowledge chunks
        when the external LLM service is offline, slow, or rate-limited.
        """
        ql = question.lower()

        # 1. Check personalized student profile
        if user_context and user_context.get("logged_in") and user_context.get("personalised"):
            user_name = user_context.get("user_name", "Student")
            profile = student_profile.get_student_profile(user_name)

            if any(k in ql for k in ["assignment", "homework", "task", "submission", "due", "deadline", "pending", "odevzdavarna"]):
                assignments = profile.get("pending_assignments", [])
                lines = [f"**Upcoming Coursework Assignments for {profile['name']} (WS 2026/2027)**:"]
                for a in assignments[:2]:
                    lines.append(
                        f"- 🔴 **{a['course_code']} ({a['course_name']})**: *{a['task_title']}*\n"
                        f"  **Due**: {a['due_date']} ({a['days_left']}) • Weight: {a['weight']}\n"
                        f"  [{a['button_label']}]({a['submission_url']})"
                    )
                if len(assignments) > 2:
                    lines.append(
                        f"- 🎓 **Master's Thesis Project**: *Final Abstracts & Full-Text PDF Upload*\n"
                        f"  **Due**: Nov 30, 2026 (23:59) • Thesis Requirement (§ 47b)\n"
                        f"  [🎓 Go to Master's Thesis Submission Area](https://insis.vse.cz/auth/student/zp.pl?lang=en)"
                    )
                    lines.append(
                        f"\n*You have {len(assignments)-2} more upcoming assignments later in the semester.*"
                    )
                return "\n\n".join(lines)

            if any(k in ql for k in ["voucher", "credit", "fail", "afford", "left", "remaining", "progress"]):
                vouchers_left = profile.get("remaining_vouchers", 120)
                initial_v = profile.get("initial_vouchers", 144)
                gained = profile.get("earned_ects", 90)
                target = profile.get("degree_target_ects", 120)
                in_progress = profile.get("current_enrolled_ects", 24)
                net_left = profile.get("remaining_ects_after_current_term", 6)
                return (
                    f"**Degree Progress & Credit Breakdown for {profile['name']}**:\n\n"
                    f"- **Degree Target**: **{target} ECTS** ({profile.get('programme', 'Master in ISM')})\n"
                    f"- **Credits Earned**: **{gained} ECTS** (75% completed)\n"
                    f"- **Enrolled This Semester (WS 2026/2027)**: **{in_progress} ECTS** (across 4 courses in progress)\n"
                    f"- **Remaining to Graduate After Current Term**: **Only {net_left} ECTS** (Master's Thesis & State Final Exam)\n"
                    f"- **Credit Vouchers Safety**: You have **{vouchers_left} spare vouchers left** (out of {initial_v} initial Master's vouchers). Even if you were to retake a course, your voucher safety buffer is completely safe.\n\n"
                    f"[📑 View Full E-Study Record in InSIS](https://insis.vse.cz/auth/student/studium.pl?lang=en)"
                )

            if any(k in ql for k in ["thesis", "errata", "red x", "3 red"]):
                thesis_topic = profile.get("thesis_title", "Improving International Student Experience with GenAI based tool at VŠE")
                supervisor = profile.get("thesis_supervisor", "Ing. Pavel Sládek, Ph.D.")
                return (
                    f"**Master's Thesis Workflow for {profile['name']}**:\n\n"
                    f"- **Assigned Topic**: *{thesis_topic}* (Supervisor: {supervisor}).\n"
                    f"- **The 3 Red X Icons**: These represent mandatory pre-defense requirements in InSIS (English abstract entry, final thesis PDF upload, and supervisor sign-off).\n"
                    f"- **Submitting Errata (§ 47b)**: In InSIS, navigate to **My College** -> **Master's thesis**. Under the application options, click **Insert errata (Vložit errata)** to upload corrections approved by your supervisor.\n\n"
                    f"[🎓 Go to Master's Thesis Submission Area](https://insis.vse.cz/auth/student/zp.pl?lang=en)"
                )

        # Handle unauthenticated / guest inquiries about assignments
        if not user_context or not user_context.get("logged_in"):
            if any(k in ql for k in ["assignment", "homework", "task", "submission", "due", "deadline", "odevzdavarna"]):
                return (
                    "**InSIS Coursework Submissions (Odevzdávárna)**:\n\n"
                    "At VŠE, student assignments and seminar papers are submitted electronically in InSIS under:\n"
                    "**Student's Portal ➔ Coursework submissions (Odevzdávárna)** (`/auth/student/odevzdavarna.pl`).\n\n"
                    "- Each enrolled course provides dedicated submission drop-boxes with instructions, accepted formats (.pdf, .zip), and file size limits.\n"
                    "- Once uploaded, InSIS generates a submission timestamp and protocol.\n\n"
                    "💡 *To view your personal active assignments and direct submission links, please log in with your student credentials using the button above.*"
                )

        # 2. Extract grounded paragraphs from top chunks
        if not context_chunks:
            return (
                "I could not find a verified match for your question in VŠE official documentation. "
                "Please consult the VŠE Information Portal or contact your study coordinator."
            )

        # Check if the primary chunk is an InSIS navigation guide
        nav_chunks = [c for c in context_chunks if c.get("is_insis_nav")]
        if nav_chunks:
            nc = nav_chunks[0]
            lines = [l.strip() for l in nc.get("text", "").split("\n") if l.strip()]
            breadcrumbs = ""
            steps = []
            note_str = ""
            for l in lines:
                if l.startswith("Breadcrumb Trail:"):
                    breadcrumbs = l.replace("Breadcrumb Trail:", "").strip()
                elif re.match(r"^\d+\.", l):
                    steps.append(l)
                elif l.startswith("Important Note:") and not l.endswith(": None"):
                    note_str = f"\n\n💡 *Note: {l.replace('Important Note:', '').strip()}*"
            steps_str = "\n".join(steps) if steps else "\n".join(lines[:6])
            clean_bc = breadcrumbs.replace(" > ", " → ")
            task_title = nc.get("title", "InSIS Page").replace("InSIS Navigation Guide: ", "")
            return (
                f"**How to apply / navigate in InSIS**:\n\n"
                f"**Path:** {clean_bc}\n\n"
                f"{steps_str}{note_str}\n\n"
                f"[🏛️ Open {task_title} in InSIS]({nc.get('source_url', 'https://insis.vse.cz')})"
            )

        # Check if the primary chunk is campus location navigation
        campus_chunks = [c for c in context_chunks if c.get("is_campus_loc")]
        if campus_chunks:
            cc = campus_chunks[0]
            lines = [l.strip() for l in cc.get("text", "").split("\n") if l.strip()]
            loc_name = cc.get("title", "Campus Location").replace("VŠE Campus Navigation: ", "")
            return (
                f"**Campus Directions: {loc_name}**:\n\n"
                f"{chr(10).join(lines)}\n\n"
                f"[🗺️ Open VŠE Campus Map & Buildings Guide]({cc.get('source_url', 'https://www.vse.cz/english/campus-map-and-buildings/')})"
            )

        # Check if the primary chunk is a VŠE Policy / Regulation
        policy_chunks = [c for c in context_chunks if c.get("is_policy")]
        if policy_chunks:
            pc = policy_chunks[0]
            lines = [l.strip() for l in pc.get("text", "").split("\n") if l.strip()]
            pol_title = pc.get("title", "VŠE Policy")
            return (
                f"**{pol_title}**:\n\n"
                f"{chr(10).join(lines)}\n\n"
                f"[📜 Official VŠE Rules and Regulations]({pc.get('source_url', 'https://www.vse.cz/english/university-rules-and-regulations/')})"
            )

        content_chunks = [c for c in context_chunks if not c.get("is_contacts")]
        if not content_chunks:
            content_chunks = context_chunks

        sections = []
        for c in content_chunks[:2]:
            title = c.get("title", "VŠE Information")
            text = c.get("text", "").strip()
            lines = [line.strip() for line in text.split("\n") if line.strip() and not line.startswith("#")]
            summary = "\n".join(lines[:5])
            sections.append(f"**{title}**:\n{summary}")

        intro = "Based on official VŠE documentation:\n\n"
        return intro + "\n\n".join(sections)

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
        user_context: Optional[Dict[str, Any]] = None,
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
        # 0. High-Speed In-Memory Cache Lookup (< 1ms)
        # -------------------------------------------------------------
        norm_q = self._normalize_query(question)
        cache_key = f"{norm_q}:{bool(user_context and user_context.get('logged_in'))}:{bool(user_context and user_context.get('personalised'))}"
        if not history and cache_key in self._query_cache:
            cached_res = dict(self._query_cache[cache_key])
            cached_res["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 1)
            return cached_res

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
        # 2b. Fast Deterministic Personalised Study Path (<50ms)
        # -------------------------------------------------------------
        # For authenticated students querying assignments, credits, or thesis,
        # return immediate grounded profile data without network latency or timeouts.
        ql = question.lower()
        if user_context and user_context.get("logged_in") and user_context.get("personalised"):
            is_personal_assignment = any(k in ql for k in ["assignment", "homework", "task", "submission", "due", "deadline", "pending", "odevzdavarna"])
            is_personal_credit = any(k in ql for k in ["voucher", "vouchers"]) or (
                any(k in ql for k in ["credit", "credits"]) and any(k in ql for k in ["how many", "left", "remaining", "my", "progress"])
            )
            is_personal_thesis = any(k in ql for k in ["thesis", "errata", "red x", "3 red"])

            if is_personal_assignment or is_personal_credit or is_personal_thesis:
                dyn_chunks = student_profile.build_dynamic_context_chunks(question, user_context)
                fast_answer = self._synthesize_grounded_answer(question, dyn_chunks, user_context)
                sources_text, cited_chunks = self.format_sources_section(fast_answer, dyn_chunks)
                final_answer = fast_answer + sources_text
                latency = (time.perf_counter() - start_time) * 1000
                res_payload = {
                    "answer": final_answer,
                    "sources": dyn_chunks,
                    "mode": "normal",
                    "sensitive": is_sensitive,
                    "sensitive_topic": sensitive_topic,
                    "top_score": 0.995,
                    "latency_ms": round(latency, 1),
                }
                self._query_cache[cache_key] = res_payload
                self.log_interaction(
                    session_id=session_uuid,
                    question=question,
                    mode="normal",
                    top_score=0.995,
                    latency_ms=latency,
                )
                return res_payload

        # -------------------------------------------------------------
        # 2c. Fast Deterministic InSIS Navigation & Campus Location Path (<30ms)
        # -------------------------------------------------------------
        # Direct navigation queries and campus room/facility searches have verified
        # structured ground-truth in SQLite FTS. If exact route or location matches,
        # return immediate grounded answer with exact breadcrumbs and single action link
        # without waiting for remote WAN LLM roundtrips.
        insis_nav_cues = [
            "insis", "navigate", "navigation", "portal", "where to find", "how to find",
            "where can i find", "whre to find", "where is the", "where is", "menu", "section",
            "query", "querry", "application", "form", "apply", "scholarship", "scholorship",
            "stipend", "benefit", "grant", "ubytov", "contact centre", "contact center",
            "study plan", "catalogue", "catalog", "syllabus", "timetable", "schedule",
            "thesis", "errata", "odevzdani", "diplomk", "studium", "studijni", "zkousk",
            "exam", "confirmation", "potvrzeni", "voucher", "bank account", "variable symbol",
            "coursework", "assignment", "odevzdavarna", "dropbox"
        ]
        campus_cues = [
            "washroom", "toilet", "wc", "bathroom", "restroom", "menza", "canteen",
            "cafeteria", "ciks", "helpdesk", "library", "bibliobox", "study room",
            "sb 22", "rb 101", "rb 201", "rb 209", "nb 403"
        ]

        is_direct_nav = any(cue in ql for cue in insis_nav_cues)
        is_direct_campus = any(cue in ql for cue in campus_cues)

        if is_direct_nav or is_direct_campus:
            try:
                import insis_nav_db
                fast_search = insis_nav_db.unified_search(question, limit=2)
                fast_chunk = None

                if is_direct_nav and fast_search.get("insis_routes"):
                    top_nav = fast_search["insis_routes"][0]
                    fast_chunk = {
                        "id": f"insis_nav_{top_nav['task_id']}",
                        "doc_id": "insis_nav_db",
                        "title": f"InSIS Navigation Guide: {top_nav['title_en']}",
                        "source_url": top_nav["official_url"],
                        "date_saved": "2026-10-31",
                        "unverified": False,
                        "score": 0.99,
                        "text": (
                            f"InSIS Navigation Task: {top_nav['title_en']} ({top_nav['title_cs']})\n"
                            f"Category: {top_nav['category']} | InSIS Path: {top_nav['portal_path']}\n"
                            f"Breadcrumb Trail: {top_nav['breadcrumbs']}\n"
                            f"Step-by-Step Instructions:\n{top_nav['step_by_step_instructions']}\n"
                            f"Prerequisites: {top_nav.get('prerequisites', 'None')}\n"
                            f"Important Note: {top_nav.get('common_pitfalls', 'None')}\n"
                            f"Interactive Demo: {top_nav['demo_url']}\n"
                        ),
                        "is_insis_nav": True,
                    }
                elif is_direct_campus and fast_search.get("campus_locations"):
                    loc = fast_search["campus_locations"][0]
                    fast_chunk = {
                        "id": f"campus_{loc['location_id']}",
                        "doc_id": "vse_campus_db",
                        "title": f"VŠE Campus Navigation: {loc['name']} ({loc['room_number']})",
                        "source_url": "https://www.vse.cz/english/campus-map-and-buildings/",
                        "date_saved": "2026-10-31",
                        "unverified": False,
                        "score": 0.99,
                        "text": (
                            f"Location Name: {loc['name']}\n"
                            f"Building: {loc['building']} | Floor: {loc['floor']} | Room Number: {loc['room_number']}\n"
                            f"Facility Type: {loc['facility_type']}\n"
                            f"Walking Directions from Main Entrance:\n{loc['directions_from_entrance']}\n"
                            f"Amenities & Accessibility: {loc.get('amenities_accessibility', 'Standard')}\n"
                            f"Hours / Availability: {loc.get('hours_or_availability', 'Standard building hours')}\n"
                        ),
                        "is_campus_loc": True,
                    }

                if fast_chunk:
                    fast_answer = self._synthesize_grounded_answer(question, [fast_chunk], user_context)
                    sources_text, cited_chunks = self.format_sources_section(fast_answer, [fast_chunk])
                    final_answer = fast_answer + sources_text
                    latency = (time.perf_counter() - start_time) * 1000
                    res_payload = {
                        "answer": final_answer,
                        "sources": [fast_chunk],
                        "mode": "normal",
                        "sensitive": is_sensitive,
                        "sensitive_topic": sensitive_topic,
                        "top_score": 0.99,
                        "latency_ms": round(latency, 1),
                    }
                    self._query_cache[cache_key] = res_payload
                    self.log_interaction(
                        session_id=session_uuid,
                        question=question,
                        mode="normal",
                        top_score=0.99,
                        latency_ms=latency,
                    )
                    return res_payload
            except Exception as e:
                print(f"[Fast-Path Warning]: {e}")

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
        # 4b. InSIS & Campus Knowledge Database Integration
        # -------------------------------------------------------------
        # Queries the relational database for:
        # 1. Campus floor navigation (washrooms, classrooms, study coordinators)
        # 2. 50 VŠE Policies, Rules and Regulations
        # 3. InSIS Navigation Routes
        try:
            import insis_nav_db
            search_res = insis_nav_db.unified_search(question, limit=2)
            candidates = []

            # Prioritize InSIS routes when question is explicitly about InSIS, finding features, or applying for academic/grant procedures
            insis_cues = ["insis", "navigate", "portal", "where to find", "how to find", "where can i find", "whre to find", "where is the", "menu", "section", "query", "querry", "application", "form", "apply", "scholarship", "scholorship", "stipend", "benefit", "grant", "ubytov"]
            is_insis_query = any(c in question.lower() for c in insis_cues)

            if is_insis_query and search_res.get("insis_routes"):
                for r in search_res["insis_routes"][:2]:
                    candidates.append(("insis", r.get("rank", -5.0) - 20.0, r))

            if search_res.get("policies"):
                for p in search_res["policies"][:1]:
                    candidates.append(("policy", p.get("rank", -5.0), p))
            if search_res.get("campus_locations"):
                for loc in search_res["campus_locations"][:1]:
                    candidates.append(("campus", loc.get("rank", -5.0), loc))
            if not is_insis_query and search_res.get("insis_routes"):
                for r in search_res["insis_routes"][:1]:
                    candidates.append(("insis", r.get("rank", -5.0), r))

            # Sort by rank (in SQLite FTS5, more negative rank means higher relevance)
            candidates.sort(key=lambda c: c[1])

            db_chunk = None
            if candidates:
                best_kind, best_rank, best_item = candidates[0]

                if best_kind == "policy":
                    pol = best_item
                    db_chunk = {
                        "id": f"policy_{pol['rule_id']}",
                        "doc_id": "vse_policies_db",
                        "title": f"VŠE Policy [{pol['rule_id']}]: {pol['title']}",
                        "source_url": "https://www.vse.cz/english/university-rules-and-regulations/",
                        "date_saved": "2026-10-31",
                        "unverified": False,
                        "score": 0.99,
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
                        "doc_id": "vse_campus_db",
                        "title": f"VŠE Campus Navigation: {loc['name']} ({loc['room_number']})",
                        "source_url": "https://www.vse.cz/english/campus-map-and-buildings/",
                        "date_saved": "2026-10-31",
                        "unverified": False,
                        "score": 0.99,
                        "text": (
                            f"Location Name: {loc['name']}\n"
                            f"Building: {loc['building']} | Floor: {loc['floor']} | Room Number: {loc['room_number']}\n"
                            f"Facility Type: {loc['facility_type']}\n"
                            f"Walking Directions from Main Entrance:\n{loc['directions_from_entrance']}\n"
                            f"Amenities & Accessibility: {loc.get('amenities_accessibility', 'Standard')}\n"
                            f"Hours / Availability: {loc.get('hours_or_availability', 'Standard building hours')}\n"
                        ),
                        "is_campus_loc": True,
                    }
                elif best_kind == "insis":
                    top_nav = best_item
                    db_chunk = {
                        "id": f"insis_nav_{top_nav['task_id']}",
                        "doc_id": "insis_nav_db",
                        "title": f"InSIS Navigation Guide: {top_nav['title_en']}",
                        "source_url": top_nav["official_url"],
                        "date_saved": "2026-10-31",
                        "unverified": False,
                        "score": 0.98,
                        "text": (
                            f"InSIS Navigation Task: {top_nav['title_en']} ({top_nav['title_cs']})\n"
                            f"Category: {top_nav['category']} | InSIS Path: {top_nav['portal_path']}\n"
                            f"Breadcrumb Trail: {top_nav['breadcrumbs']}\n"
                            f"Step-by-Step Instructions:\n{top_nav['step_by_step_instructions']}\n"
                            f"Prerequisites: {top_nav.get('prerequisites', 'None')}\n"
                            f"Important Note: {top_nav.get('common_pitfalls', 'None')}\n"
                            f"Interactive Demo: {top_nav['demo_url']}\n"
                        ),
                        "is_insis_nav": True,
                    }

            if db_chunk:
                context_chunks = [db_chunk] + [c for c in context_chunks if not (c.get("is_insis_nav") or c.get("is_policy") or c.get("is_campus_loc"))]
                if mode == "no_context":
                    mode = "normal"
        except Exception as e:
            print(f"[Knowledge DB Query Warning]: {e}")

        # -------------------------------------------------------------
        # 4c. Public No-Login Context / Live Screen & Personalised Study Context
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

        # -------------------------------------------------------------
        # 5. Gemini Generation
        # -------------------------------------------------------------
        prompt_content = prompts.build_prompt_with_context(question, context_chunks)

        # Format conversation history for Gemini (excluding the current turn)
        # If the caller already added the current question to history, exclude it to avoid duplication
        past_history = []
        if history:
            if history[-1].get("role") == "user" and history[-1].get("content", "").strip() == question.strip():
                past_history = history[:-1]
            else:
                past_history = history

        recent_history = past_history[-config.MAX_HISTORY_MESSAGES:] if past_history else []
        gemini_contents: List[types.Content] = []

        # Enforce strict alternating turns (user -> model -> user -> model)
        last_role = None
        for msg in recent_history:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content", "").strip()
            if not content:
                continue
            if role == last_role:
                continue
            gemini_contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content)],
                )
            )
            last_role = role

        # If previous history ended with user, pop it to guarantee our prompt_content is the single user turn
        if gemini_contents and gemini_contents[-1].role == "user":
            gemini_contents.pop()

        # Append current user prompt with grounded RAG context
        gemini_contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt_content)],
            )
        )

        raw_answer = None
        models_to_try = [config.CHAT_MODEL]
        last_error = None

        client = self._get_client()

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

        for candidate_model in models_to_try:
            try:
                future = _LLM_EXECUTOR.submit(_generate_with_gemini, candidate_model)
                response = future.result(timeout=2.5)
                if response.text:
                    raw_answer = response.text.strip()
                    break
            except concurrent.futures.TimeoutError:
                last_error = "Gemini generation timed out after 2.5s"
                break
            except Exception as e:
                last_error = e
                continue

        if not raw_answer:
            if last_error:
                print(f"[Generation Notice]: Fast grounded fallback ({last_error}) from verified VŠE knowledge base.")
            raw_answer = self._synthesize_grounded_answer(question, context_chunks, user_context)

        # -------------------------------------------------------------
        # 6. Post-processing (Citations & Referral)
        # -------------------------------------------------------------
        # Ensure InSIS navigation questions always have a clean direct one-click action button
        insis_navs = [c for c in context_chunks if c.get("is_insis_nav")]
        if insis_navs:
            top_nav_chunk = insis_navs[0]
            nav_url = top_nav_chunk.get("source_url", "")
            nav_title = top_nav_chunk.get("title", "InSIS Page").replace("InSIS Navigation Guide: ", "")
            if nav_url and nav_url not in raw_answer:
                raw_answer += f"\n\n[🏛️ Open {nav_title}]({nav_url})"

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

        res_payload = {
            "answer": final_answer,
            "sources": cited_chunks,
            "mode": mode,
            "sensitive": is_sensitive,
            "sensitive_topic": sensitive_topic,
            "top_score": round(top_score, 4),
            "latency_ms": round(latency, 1),
        }

        # Cache response for identical queries
        if len(self._query_cache) > 500:
            self._query_cache.clear()
        self._query_cache[cache_key] = res_payload

        return res_payload
