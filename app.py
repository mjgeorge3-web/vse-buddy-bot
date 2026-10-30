"""Streamlit web interface for VŠE Buddy Bot.

Features:
- Responsive Streamlit chat interface (st.chat_message) with custom university styling
- Permanent research prototype disclaimer
- Categorized quick questions across student journey stages (Before arrival, First weeks, Studying, Living in Prague)
- Inline user feedback (thumbs up / down + optional comment) logged anonymously to logs/feedback.csv
- Conversation export (download markdown chat transcript)
- Collapsible Researcher / Evaluation panel with live session metrics
- Anonymous UUID session management with no PII collection
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
    .vse-banner {
        background: linear-gradient(135deg, #00386b 0%, #005696 100%);
        color: white !important;
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .vse-banner h1 {
        color: white !important;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .vse-banner p {
        color: #e0e9f5 !important;
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
    }
    .disclaimer-box {
        background-color: #f8f9fa;
        border-left: 4px solid #f39c12;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        border-radius: 4px;
        font-size: 0.88rem;
        color: #555;
    }
    .stage-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.4rem;
        background-color: #e3f2fd;
        color: #0d47a1;
    }
    .stButton>button {
        border-radius: 8px;
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
        ⚠️ <strong>Academic Research Prototype:</strong> This bot provides grounded guidance from verified VŠE documentation. It is not an official university service. Always confirm critical visa, legal, financial, or academic decisions with the responsible office.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Sidebar Navigation & Controls
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Chat Controls")
    col_new, col_exp = st.columns([1, 1])
    with col_new:
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.pending_prompt = None
            st.session_state.feedback_submitted_ids = set()
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
            ("Course Enrollment in InSIS", "How do I enroll in courses and build my timetable in InSIS?"),
            ("Semester Credits & Vouchers", "How many credits do I need per semester and how do vouchers work?"),
            ("Exam Retakes & Grading Scale", "How does the grading scale work and how many exam retakes do I get?"),
            ("Final Thesis & Errata", "How do I submit my final thesis and how do I submit errata in InSIS?"),
            ("Library & Campus Printing (SafeQ)", "How do I use the university library and print on campus using SafeQ?"),
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
        st.markdown(f"- **Session ID:** `{st.session_state.session_id[:12]}...`")
        st.markdown(f"- **Messages Exchanged:** {msg_count}")
        st.markdown(f"- **Avg Assistant Latency:** {avg_lat:.0f} ms")
        st.markdown(f"- **Knowledge Files:** 48 markdown docs (122 chunks)")
        st.markdown(f"- **Retrieval Engine:** Pure NumPy Cosine Similarity")

    with st.expander("ℹ️ About & Privacy Safeguards"):
        st.markdown(
            """
            **About VŠE Buddy Bot**
            - Developed as a Master's Thesis research prototype in Information Systems Management (ISM).
            - Strictly grounded in 48 curated VŠE documentation pages to prevent ungrounded AI hallucinations.
            - **Tech Stack:** Python 3.14, Streamlit, Google Gemini (GenAI SDK), NumPy vector store.
            
            **Privacy & GDPR Compliance**
            - **Do NOT enter personal identifiable data** (names, birth dates, passport or student ID numbers).
            - Session identifiers are completely random UUIDs; no student accounts or IP addresses are logged.
            - Deterministic crisis guardrails automatically redact sensitive mental health emergencies from persistent logs.
            """
        )

# ---------------------------------------------------------------------
# Display Existing Messages & Feedback Controls
# ---------------------------------------------------------------------
for idx, message in enumerate(st.session_state.messages):
    role = message["role"]
    avatar = "🧑‍🎓" if role == "user" else "🎓"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

        # Display thumbs up / down feedback on assistant responses
        if role == "assistant" and message.get("mode") != "crisis":
            msg_id = message.get("feedback_id", f"msg_{idx}")
            is_submitted = msg_id in st.session_state.feedback_submitted_ids

            if not is_submitted:
                col1, col2, col3 = st.columns([1, 1, 6])
                with col1:
                    if st.button("👍", key=f"up_{msg_id}", help="Accurate and helpful answer"):
                        log_user_feedback(st.session_state.session_id, idx, "positive")
                        st.session_state.feedback_submitted_ids.add(msg_id)
                        st.toast("Thank you! Your feedback helps improve the bot for all students.", icon="👍")
                        st.rerun()
                with col2:
                    if st.button("👎", key=f"down_{msg_id}", help="Inaccurate, incomplete, or unhelpful"):
                        log_user_feedback(st.session_state.session_id, idx, "negative")
                        st.session_state.feedback_submitted_ids.add(msg_id)
                        st.toast("Feedback recorded. We are refining the knowledge base.", icon="👎")
                        st.rerun()
            else:
                st.caption("✓ Feedback submitted. Thank you!")

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
        with st.spinner("Searching verified VŠE documentation..."):
            result = st.session_state.bot.answer(
                question=prompt_to_process,
                history=st.session_state.messages,
                session_id=st.session_state.session_id,
            )
            answer_text = result["answer"]
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
