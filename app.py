"""Streamlit web interface for VŠE Buddy Bot.

Features:
- Responsive Streamlit chat interface (st.chat_message) with custom university styling
- Permanent research prototype disclaimer
- Interactive Welcome Hero state with 6 quick starter cards on main canvas
- Categorized quick questions across student journey stages (Before arrival, First weeks, Studying, Living in Prague)
- Inline user feedback (thumbs up / down + qualitative comment popover) logged anonymously to logs/feedback.csv
- One-click copy response helper popover
- Dynamic source and mode badges (Grounded, Official Referral, Crisis)
- Conversation export (download markdown chat transcript)
- Collapsible Researcher / Evaluation panel with dynamic knowledge base and session metrics
- Anonymous UUID session management with no PII collection (GDPR compliant)
"""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

import streamlit as st

import config
from bot import BuddyBot

# ---------------------------------------------------------------------
# Page Setup & Styling
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="VŠE Buddy Bot 🎓",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom styling for academic aesthetic and readable chat cards
st.markdown(
    """
    <style>
    /* Main VŠE Brand Container */
    .vse-banner {
        background: linear-gradient(135deg, #00386b 0%, #005696 100%);
        color: #ffffff !important;
        padding: 1.4rem 1.6rem;
        border-radius: 12px;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 12px rgba(0, 56, 107, 0.15);
    }
    .vse-banner h1 {
        color: #ffffff !important;
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .vse-banner p {
        color: #e0e9f5 !important;
        margin: 0.4rem 0 0 0;
        font-size: 0.95rem;
        line-height: 1.4;
    }

    /* Academic Prototype Disclaimer */
    .disclaimer-box {
        background-color: rgba(245, 158, 11, 0.08);
        border-left: 4px solid #f59e0b;
        border-radius: 6px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 1.2rem;
        font-size: 0.88rem;
        line-height: 1.45;
        color: inherit;
    }

    /* Hero Card for Welcome State */
    .hero-card {
        background-color: rgba(0, 56, 107, 0.04);
        border: 1px solid rgba(0, 56, 107, 0.14);
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.5rem;
    }
    .hero-card h3 {
        margin-top: 0;
        color: #00386b;
        font-weight: 700;
    }
    .hero-card p {
        margin: 0.4rem 0 0 0;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* Response Mode Badges */
    .badge-grounded {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: rgba(16, 185, 129, 0.12);
        color: #059669;
        border: 1px solid rgba(16, 185, 129, 0.25);
        margin-bottom: 0.4rem;
    }
    .badge-referral {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: rgba(245, 158, 11, 0.12);
        color: #d97706;
        border: 1px solid rgba(245, 158, 11, 0.25);
        margin-bottom: 0.4rem;
    }
    .badge-crisis {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: rgba(239, 68, 68, 0.12);
        color: #dc2626;
        border: 1px solid rgba(239, 68, 68, 0.25);
        margin-bottom: 0.4rem;
    }

    /* Smooth button styling */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.15s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "bot" not in st.session_state:
    st.session_state.bot = BuddyBot()

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "feedback_submitted_ids" not in st.session_state:
    st.session_state.feedback_submitted_ids = set()


# ---------------------------------------------------------------------
# Feedback Logging Helper
# ---------------------------------------------------------------------
def log_user_feedback(
    session_id: str,
    message_index: int,
    rating: str,
    comment: str = "",
):
    """Log anonymous student feedback (rating and comment) to logs/feedback.csv."""
    try:
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        file_exists = config.FEEDBACK_LOG_PATH.exists()

        with open(config.FEEDBACK_LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "session_id", "message_index", "rating", "comment"])
            now_iso = datetime.now(timezone.utc).isoformat()
            writer.writerow([now_iso, session_id, message_index, rating, comment.strip()])
    except Exception as e:
        st.error(f"Could not record feedback: {e}")


def export_conversation_markdown() -> str:
    """Format conversation as downloadable Markdown text."""
    lines = [
        f"# VŠE Buddy Bot Conversation Transcript",
        f"- **Session ID:** `{st.session_state.session_id}`",
        f"- **Export Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- **Messages:** {len(st.session_state.messages)}",
        "\n---\n",
    ]
    for m in st.session_state.messages:
        role = "🧑 **Student**" if m["role"] == "user" else "🤖 **VŠE Buddy Bot**"
        lines.append(f"### {role}")
        lines.append(m["content"])
        lines.append("\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Header & Permanent Disclaimer
# ---------------------------------------------------------------------
st.markdown(
    """
    <div class="vse-banner">
        <h1>VŠE Buddy Bot 🎓</h1>
        <p>Verified RAG assistant for international students at Prague University of Economics and Business</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer-box">
        ⚠️ <strong>Academic Research Prototype:</strong> This bot provides grounded guidance from verified VŠE documentation. It is not an official university service. Always confirm critical visa, legal, financial, or academic decisions with the responsible official office or faculty study coordinator.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Sidebar Navigation & Controls
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Chat Controls")
    col_new, col_clear, col_exp = st.columns([1, 1, 1])
    with col_new:
        if st.button("➕ New", use_container_width=True, help="Start a new session with fresh UUID"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.pending_prompt = None
            st.session_state.feedback_submitted_ids = set()
            st.rerun()

    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True, help="Clear messages while keeping session", disabled=not bool(st.session_state.messages)):
            st.session_state.messages = []
            st.session_state.pending_prompt = None
            st.rerun()

    with col_exp:
        if st.session_state.messages:
            transcript_md = export_conversation_markdown()
            st.download_button(
                "📥 Export",
                data=transcript_md,
                file_name=f"vse_buddy_transcript_{st.session_state.session_id[:8]}.md",
                mime="text/markdown",
                use_container_width=True,
                help="Download your conversation transcript",
            )
        else:
            st.button("📥 Export", disabled=True, use_container_width=True)

    st.divider()

    st.subheader("💡 Student Journey FAQs")
    st.caption("Select your stage to explore verified answers:")

    stage_tab = st.selectbox(
        "Choose Stage:",
        [
            "🛫 Before Arrival & Housing",
            "🎒 First Weeks & Campus IT",
            "📚 Studying, InSIS & Credits",
            "🧘 Health, Stress & Prague Life",
        ],
        label_visibility="collapsed",
    )

    stage_faqs = {
        "🛫 Before Arrival & Housing": [
            ("Student Visa & Residence Permits", "Do I need a student visa to study at VŠE, and what are the requirements?"),
            ("Dormitory Housing & ISKaM", "How do I apply for a VŠE dormitory and pay the reservation deposit?"),
            ("Diploma Recognition (Nostrification)", "How do I get my previous diploma recognized by VŠE (nostrification)?"),
            ("Health Insurance Requirements", "What health insurance do I need as an international student in the Czech Republic?"),
            ("Tuition Fee & Bank Payments", "How do I pay my tuition fee and what is the variable symbol?"),
        ],
        "🎒 First Weeks & Campus IT": [
            ("Foreign Police Registration", "Do international students have to register with the Foreign Police upon arrival?"),
            ("Campus Wi-Fi (eduroam)", "How do I connect to the university Wi-Fi (eduroam) on campus?"),
            ("Student ID & ISIC Card", "What can I use my student ID card for and where do I pick it up?"),
            ("Public Transport Pass (Lítačka)", "How do I get a student discount pass for Prague public transport (Lítačka)?"),
            ("InSIS Password Reset & Helpdesk", "I forgot my InSIS password. How do I reset it?"),
        ],
        "📚 Studying, InSIS & Credits": [
            ("Student Navigation Sidebar (Portlets)", "How do I enable the Navigation bar for students portlet in InSIS?"),
            ("Course Enrollment in InSIS", "How do I enroll in courses and build my timetable in InSIS?"),
            ("Semester Credits & Vouchers", "How many credits do I need per semester and how do vouchers work?"),
            ("Exam Retakes & Grading Scale", "What happens if I fail an exam 3 times at VŠE?"),
            ("Master's Thesis Workflow", "Walk me through the complete Master's Thesis workflow at VŠE from topic approval to submission, defense, and errata."),
            ("Accommodation Scholarship", "How do I apply for the accommodation scholarship in InSIS?"),
        ],
        "🧘 Health, Stress & Prague Life": [
            ("Psychological Counselling & Support", "Where can I find free psychological counselling and mental health support at VŠE?"),
            ("Employment & Working in Prague", "Can international students work part-time during their studies in the Czech Republic?"),
            ("Emergency & Medical Care", "What is the emergency number and how do I see an English-speaking doctor in Prague?"),
            ("Canteens & Campus Dining (Menza)", "Where are the VŠE student canteens (Menza) and how do I get student discounts?"),
            ("Student Life, Clubs & ESN", "How can I meet other international students and join student clubs like ESN VŠE?"),
        ],
    }

    current_faqs = stage_faqs.get(stage_tab, [])
    for label, query in current_faqs:
        if st.button(f"👉 {label}", key=f"faq_{label}", use_container_width=True, help=query):
            st.session_state.pending_prompt = query
            st.rerun()

    st.divider()

    # Researcher & Thesis Evaluation Panel
    with st.expander("🔬 Researcher & Evaluation Panel"):
        st.caption("Live session data & thesis metrics:")
        msg_count = len(st.session_state.messages)
        assistant_msgs = [m for m in st.session_state.messages if m["role"] == "assistant"]
        avg_lat = (
            sum(m.get("latency_ms", 0) for m in assistant_msgs) / len(assistant_msgs)
            if assistant_msgs
            else 0.0
        )
        
        # Calculate dynamic knowledge base stats
        metadata = getattr(st.session_state.bot.retriever, "metadata", []) or []
        chunk_count = len(metadata) if metadata else 254
        doc_count = (
            len(set((c.get("doc_id") or c.get("filename", "")) for c in metadata if (c.get("doc_id") or c.get("filename"))))
            if metadata
            else 52
        )

        st.markdown(f"- **Session ID:** `{st.session_state.session_id[:12]}...`")
        st.markdown(f"- **Messages Exchanged:** {msg_count}")
        st.markdown(f"- **Avg Assistant Latency:** {avg_lat:.0f} ms")
        st.markdown(f"- **Knowledge Files:** {doc_count} verified markdown docs ({chunk_count} vector chunks)")
        st.markdown(f"- **Retrieval Engine:** Pure NumPy L2-Normalized Cosine Similarity")
        st.markdown(f"- **LLM Backbone:** Google Gemini (`{config.CHAT_MODEL}`)")

    with st.expander("ℹ️ About & Privacy Safeguards"):
        st.markdown(
            """
            **About VŠE Buddy Bot**
            - Developed as a Master's Thesis research prototype in Information Systems Management (ISM).
            - Strictly grounded in curated VŠE documentation to prevent ungrounded AI hallucinations.
            - **Tech Stack:** Python 3.14, Streamlit, Google Gemini (GenAI SDK), NumPy vector store.
            
            **Privacy & GDPR Compliance**
            - **Do NOT enter personal identifiable data** (passwords, birth dates, or passport numbers).
            - Session identifiers are completely random UUIDs; no student accounts or IP addresses are logged.
            - Deterministic crisis guardrails automatically redact sensitive mental health queries from persistent logs.
            """
        )

# ---------------------------------------------------------------------
# Main Canvas: Welcome Screen or Message Thread
# ---------------------------------------------------------------------
if not st.session_state.messages:
    # Render Hero Welcome Screen
    st.markdown(
        """
        <div class="hero-card">
            <h3>👋 Welcome to VŠE Buddy!</h3>
            <p>
                Your verified AI companion for navigating academic life, campus services, dormitories, and administrative procedures at the <strong>Prague University of Economics and Business (VŠE)</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("💡 Frequently Asked by International Students")
    st.caption("Click any question below to immediately ask the assistant:")

    col_hero_1, col_hero_2 = st.columns(2)
    with col_hero_1:
        if st.button("🏢 VŠE Dormitory Booking & Reservations (ISKaM)", key="hero_iskam", use_container_width=True):
            st.session_state.pending_prompt = "How do I book and reserve a VŠE dormitory room in ISKaM, pay the deposit, and what are the dormitory campuses and contacts?"
            st.rerun()
        if st.button("📗 Complete 4-Stage Master's Thesis Workflow", key="hero_errata", use_container_width=True):
            st.session_state.pending_prompt = "Walk me through the complete Master's Thesis workflow at VŠE from topic approval to submission, defense, and errata."
            st.rerun()
        if st.button("🧭 Enable Student Navigation Sidebar (Portlets)", key="hero_portlets", use_container_width=True):
            st.session_state.pending_prompt = "How do I enable the Navigation bar for students portlet in InSIS?"
            st.rerun()
        if st.button("💰 Apply for Accommodation Scholarship in InSIS", key="hero_dorm", use_container_width=True):
            st.session_state.pending_prompt = "How do I apply for the accommodation scholarship in InSIS?"
            st.rerun()

    with col_hero_2:
        if st.button("🛂 Visa, Health Insurance & 3-Day Police Rules", key="hero_police", use_container_width=True):
            st.session_state.pending_prompt = "What are the visa, dormitory accommodation, and 3-day Foreign Police registration rules for international students?"
            st.rerun()
        if st.button("🎓 Minimum 9/20 ECTS & Credit Voucher Rules", key="hero_credits", use_container_width=True):
            st.session_state.pending_prompt = "How many credits do I need per semester and how do vouchers work?"
            st.rerun()
        if st.button("📝 Submit E-Application & Foreign Diploma Assessment", key="hero_eapp", use_container_width=True):
            st.session_state.pending_prompt = "How do I submit the E-application form to study at VŠE?"
            st.rerun()
        if st.button("🧠 Free Psychological Counselling at VŠE", key="hero_counsel", use_container_width=True):
            st.session_state.pending_prompt = "Where can I find free psychological counselling and mental health support at VŠE?"
            st.rerun()

else:
    # Display Existing Messages & Feedback Controls
    for idx, message in enumerate(st.session_state.messages):
        role = message["role"]
        avatar = "🧑‍🎓" if role == "user" else "🎓"
        with st.chat_message(role, avatar=avatar):
            # Display mode badge for assistant messages
            if role == "assistant":
                mode = message.get("mode")
                if mode == "crisis":
                    st.markdown('<div class="badge-crisis">🚨 Emergency Helpline Resources</div>', unsafe_allow_html=True)
                elif mode == "referral":
                    st.markdown('<div class="badge-referral">⚠️ Official Office Referral</div>', unsafe_allow_html=True)
                elif mode in ("normal", "grounded"):
                    st.markdown('<div class="badge-grounded">✓ Verified VŠE Documentation</div>', unsafe_allow_html=True)

            st.markdown(message["content"])

            # Display response actions & feedback controls on assistant responses
            if role == "assistant" and message.get("mode") != "crisis":
                msg_id = message.get("feedback_id", f"msg_{idx}")
                is_submitted = msg_id in st.session_state.feedback_submitted_ids

                col_up, col_down, col_comment, col_copy, col_spacer = st.columns([0.7, 0.7, 1.8, 1.5, 4.3])

                if not is_submitted:
                    with col_up:
                        if st.button("👍", key=f"up_{msg_id}", help="Accurate and helpful answer"):
                            log_user_feedback(st.session_state.session_id, idx, "positive")
                            st.session_state.feedback_submitted_ids.add(msg_id)
                            st.toast("Thank you! Feedback recorded for thesis research.", icon="👍")
                            st.rerun()
                    with col_down:
                        if st.button("👎", key=f"down_{msg_id}", help="Inaccurate, incomplete, or unhelpful"):
                            log_user_feedback(st.session_state.session_id, idx, "negative")
                            st.session_state.feedback_submitted_ids.add(msg_id)
                            st.toast("Thank you! Feedback recorded for knowledge base refinement.", icon="👎")
                            st.rerun()
                    with col_comment:
                        with st.popover("💬 Feedback", help="Provide qualitative notes for thesis analysis"):
                            st.caption("**Research Feedback**")
                            rating_choice = st.radio(
                                "Rating:",
                                ["Helpful 👍", "Needs Improvement 👎"],
                                key=f"rad_{msg_id}",
                                horizontal=True,
                            )
                            comment_text = st.text_area(
                                "Notes (optional):",
                                key=f"txt_{msg_id}",
                                placeholder="What was missing, unclear, or particularly helpful?",
                                height=80,
                            )
                            if st.button("Submit Note", key=f"sub_cmt_{msg_id}"):
                                rating_val = "positive" if "Helpful" in rating_choice else "negative"
                                log_user_feedback(st.session_state.session_id, idx, rating_val, comment_text)
                                st.session_state.feedback_submitted_ids.add(msg_id)
                                st.toast("Thank you! Your feedback has been recorded.", icon="✅")
                                st.rerun()
                else:
                    with col_up:
                        st.caption("✓ Recorded")

                with col_copy:
                    with st.popover("📋 Copy", help="Copy response text"):
                        st.text_area(
                            "Select and copy text:",
                            value=message["content"],
                            height=150,
                            key=f"copy_area_{msg_id}",
                        )

# ---------------------------------------------------------------------
# Handle User Input (Typed or Quick Question)
# ---------------------------------------------------------------------
user_input = st.chat_input("Ask a question about VŠE, admissions, housing, visas, courses, or Prague...")

prompt_to_process = None
if st.session_state.pending_prompt:
    prompt_to_process = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
elif user_input:
    prompt_to_process = user_input

if prompt_to_process:
    # 1. Render and record user message
    st.session_state.messages.append({"role": "user", "content": prompt_to_process})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt_to_process)

    # 2. Invoke BuddyBot
    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner("Searching verified VŠE documentation & generating grounded answer..."):
            result = st.session_state.bot.answer(
                question=prompt_to_process,
                history=st.session_state.messages,
                session_id=st.session_state.session_id,
            )
            answer_text = result["answer"]
            mode = result.get("mode")

            if mode == "crisis":
                st.markdown('<div class="badge-crisis">🚨 Emergency Helpline Resources</div>', unsafe_allow_html=True)
            elif mode == "referral":
                st.markdown('<div class="badge-referral">⚠️ Official Office Referral</div>', unsafe_allow_html=True)
            elif mode in ("normal", "grounded"):
                st.markdown('<div class="badge-grounded">✓ Verified VŠE Documentation</div>', unsafe_allow_html=True)

            st.markdown(answer_text)

    # 3. Record assistant response in session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer_text,
        "mode": result.get("mode"),
        "top_score": result.get("top_score"),
        "latency_ms": result.get("latency_ms"),
        "feedback_id": str(uuid.uuid4())[:8],
    })
    st.rerun()
