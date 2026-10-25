"""Streamlit web interface for VŠE Buddy Bot.

Features:
- Streamlit chat interface (st.chat_message)
- Permanent research prototype disclaimer
- Sidebar with stage-based quick questions, new chat button, and privacy info
- Inline user feedback (thumbs up / down + comment) saved to logs/feedback.csv
- Anonymous UUID session management with no PII collection
"""

import csv
from datetime import datetime, timezone
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


# ---------------------------------------------------------------------
# Header & Permanent Disclaimer
# ---------------------------------------------------------------------
st.title("VŠE Buddy Bot 🎓")
st.markdown(
    "**Student research prototype, not an official VŠE service. "
    "Always confirm important information with the responsible office.**"
)
st.divider()

# ---------------------------------------------------------------------
# Sidebar Navigation & Controls
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Chat Controls")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

    st.subheader("💡 Quick Questions")
    st.caption("Common questions by student journey stage:")

    quick_questions = {
        "🛫 Before arrival": "How do I apply for a VŠE dormitory?",
        "🎒 First weeks": "How do I connect to Wi-Fi on campus?",
        "📚 Studying": "How many credits should I take per semester?",
        "🏰 Living in Prague": "What is the emergency number in the Czech Republic?",
    }

    for stage_label, query in quick_questions.items():
        if st.button(f"{stage_label}\n*{query}*", key=f"btn_{stage_label}", use_container_width=True):
            st.session_state.pending_prompt = query
            st.rerun()

    st.divider()

    with st.expander("ℹ️ About & Privacy"):
        st.markdown(
            """
            **About VŠE Buddy Bot**
            - Developed as a Master's Thesis research prototype at VŠE Prague.
            - Built to help international students navigate admissions, arrival, studies, and life in Prague.
            - **Tech Stack:** Python, Streamlit, Google Gemini (Flash 2.5 + Embeddings), NumPy vector search.
            
            **Privacy Notice**
            - **Do NOT enter personal data** (names, passport numbers, birth dates, student ID numbers).
            - Logging records only anonymous session IDs, timestamps, question texts, retrieval scores, and response latency.
            - Crisis emergency events are automatically redacted and never store message content.
            - Feedback ratings are used exclusively for academic evaluation.
            """
        )

# ---------------------------------------------------------------------
# Display Existing Messages & Feedback Controls
# ---------------------------------------------------------------------
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Display thumbs up / down feedback on assistant responses
        if message["role"] == "assistant" and message.get("mode") != "crisis":
            feedback_key = f"fb_{idx}_{message.get('feedback_id', 'msg')}"
            if not message.get("feedback_submitted", False):
                col1, col2, col_spacer = st.columns([1, 1, 8])
                with col1:
                    if st.button("👍", key=f"up_{feedback_key}", help="Helpful answer"):
                        log_user_feedback(st.session_state.session_id, idx, "positive")
                        message["feedback_submitted"] = True
                        st.toast("Thank you for your feedback!", icon="👍")
                        st.rerun()
                with col2:
                    if st.button("👎", key=f"down_{feedback_key}", help="Unhelpful or inaccurate answer"):
                        log_user_feedback(st.session_state.session_id, idx, "negative")
                        message["feedback_submitted"] = True
                        st.toast("Thank you for your feedback!", icon="👎")
                        st.rerun()

# ---------------------------------------------------------------------
# Handle User Input (Typed or Quick Question)
# ---------------------------------------------------------------------
user_input = st.chat_input("Ask a question about VŠE, admissions, housing, visas, or Prague...")

prompt_to_process = None
if st.session_state.pending_prompt:
    prompt_to_process = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
elif user_input:
    prompt_to_process = user_input

if prompt_to_process:
    # 1. Render and record user message
    st.session_state.messages.append({"role": "user", "content": prompt_to_process})
    with st.chat_message("user"):
        st.markdown(prompt_to_process)

    # 2. Invoke BuddyBot
    with st.chat_message("assistant"):
        with st.spinner("Finding verified information..."):
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
        "feedback_submitted": False,
    })
    st.rerun()
