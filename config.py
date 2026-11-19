"""Configuration settings and thresholds for VŠE Buddy Bot.

All configurable parameters, model names, thresholds, crisis contacts,
and file paths are defined in this single file for clarity, reproducibility,
and thesis documentation.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# =====================================================================
# PATHS & ENVIRONMENT
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()  # also check current working directory
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

INDEX_PATH = DATA_DIR / "index.npz"
INDEX_META_PATH = DATA_DIR / "index_meta.json"
INDEX_HASH_PATH = DATA_DIR / "knowledge_hash.txt"
TEST_QUESTIONS_PATH = DATA_DIR / "test_questions.csv"

CHAT_LOG_PATH = LOGS_DIR / "chat_log.csv"
FEEDBACK_LOG_PATH = LOGS_DIR / "feedback.csv"

# =====================================================================
# MODEL SETTINGS (Google Gemini)
# =====================================================================
# Generation model (gemini-2.5-flash is retired by Google for new users; gemini-flash-lite-latest is active)
CHAT_MODEL = "gemini-flash-lite-latest"

# Embedding model
EMBEDDING_MODEL = "gemini-embedding-001"

# LLM generation parameters
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 600

# =====================================================================
# CHUNKING & INGESTION PARAMETERS
# =====================================================================
MAX_SECTION_CHARS = 1200
CHUNK_TARGET_MIN = 400
CHUNK_TARGET_MAX = 1000
CHUNK_OVERLAP = 100
EMBEDDING_BATCH_SIZE = 50

# =====================================================================
# RETRIEVAL THRESHOLDS
# =====================================================================
TOP_K = 5
MIN_SCORE = 0.55
KEYWORD_BOOST = 0.05
MAX_KEYWORD_BOOST = 0.15
MIN_KEYWORD_LENGTH = 4

# Multi-turn history turns to retain for context window (last 6 messages)
MAX_HISTORY_MESSAGES = 6

# =====================================================================
# PRIVACY & LOGGING
# =====================================================================
ENABLE_LOGGING = True

# =====================================================================
# CRISIS SUPPORT CONSTANTS
# =====================================================================
EMERGENCY_NUMBER = "112"
CZECH_CRISIS_LINE = "116 123"
VSE_COUNSELLING_EMAIL = "ac@vse.cz"


_CACHED_GEMINI_API_KEY = None

def get_gemini_api_key() -> str:
    """Retrieve Gemini API key from environment variable or Streamlit secrets with memory caching."""
    global _CACHED_GEMINI_API_KEY
    if _CACHED_GEMINI_API_KEY is not None:
        return _CACHED_GEMINI_API_KEY

    # Priority 1: Environment variable (.env or system)
    key = os.getenv("GEMINI_API_KEY", "")

    # Priority 2: Streamlit secrets fallback
    if not key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    _CACHED_GEMINI_API_KEY = (key or "").strip()
    return _CACHED_GEMINI_API_KEY
