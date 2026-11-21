# VSE Buddy Bot

A research prototype Retrieval-Augmented Generation (RAG) chatbot developed for international students at the **Prague University of Economics and Business (Vysoka skola ekonomicka v Praze, VSE)**.

This prototype was developed as part of a Master's Thesis in Information Systems Management (ISM). It provides grounded guidance regarding admissions, arrival, student housing, visas, university IT, InSIS navigation, academic regulations, and daily life in Prague.

Live demo: https://vse-buddy-bot.vercel.app

---

## Independent Verification (Quick Audit)

A reviewer can verify the codebase and core claims in three steps:

1. **Automated Unit, Security & Data-Integrity Suite (No API Key Required):**
   ```bash
   pytest tests/ -v
   ```
   Runs **84 tests** covering deterministic crisis and sensitive-topic safety rules, real vector index integrity (`199 x 3072` L2-normalized embeddings and SHA-256 hash consistency), SQLite FTS5 routes/policies/campus lookup, opt-in personalisation boundaries, HTTP path security, and Vercel API parameter clamping.

2. **Knowledge Base Hash & Corpus Consistency Check (No API Key Required):**
   ```bash
   python -c "import config, ingest; print('Computed:', ingest.compute_knowledge_hash()); print('Recorded:', config.INDEX_HASH_PATH.read_text().strip())"
   ```
   Confirms that `data/index.npz` and `data/index_meta.json` match the exact 52 Markdown documents in `knowledge/` (`traceability.csv`).

3. **Live End-to-End Benchmark Execution (Requires `GEMINI_API_KEY`):**
   ```bash
   # Quick 3-query live check
   python evaluate.py 3

   # Full 40-query thesis benchmark (includes 5s delay between calls for free-tier rate limits)
   python evaluate.py
   ```
   Writes a timestamped raw CSV into `results/` recording retrieved sources, cited sources, raw cosine score, end-to-end latency, refusal checks, and separate tracking for **LLM-native referrals** vs. **guardrail-enforced referrals**, leaving `score (0-2)` and `notes` blank for manual rubric grading.

---

## Architecture & Design Rationale

| Architectural Decision | Thesis Design Rationale |
| :--- | :--- |
| **Retrieval-Augmented Generation (RAG)** | Restricts answers to 52 curated VSE Markdown guides and structured SQLite lookup tables to reduce unsupported fabrications. |
| **Pure NumPy Vector Search** | The 52-document corpus yields 199 chunks (`199 x 3072`). Exact dot-product cosine similarity in NumPy is fast, transparent, and easy to inspect without external vector-DB infrastructure. |
| **Two-Stage Anti-Hallucination Refusal** | Stage 1 gates raw `gemini-embedding-001` cosine similarity at `MIN_SCORE = 0.63` (before keyword boosting) to route off-topic queries into `no_context` mode (`contacts.md` only). Stage 2 applies strict prompt grounding (Rule 2) so in-domain knowledge gaps refuse and refer students to the responsible office. |
| **Deterministic Crisis Filter (No LLM)** | Rule-based regex matching intercepts self-harm/suicide expressions before retrieval or LLM invocation and returns emergency contacts (`112`, `116 123`, `ac@vse.cz`). |
| **Deterministic Sensitive-Topic Referrals** | Visa, Foreign Police, work permit, health insurance, legal, tuition payment, exam failure, and mental wellbeing queries trigger post-processing checks (`safety.has_explicit_referral`) and append an explicit verification notice if the LLM omitted one. |
| **Explicit Source Citations & UNVERIFIED Flags** | Inline numbered citations `[1]`, `[2]` map to clickable URLs, and dynamic external details (such as dormitory price lists and embassy booking links) carry explicit `UNVERIFIED` markers. |
| **Low Generation Temperature (`0.2`)** | Promotes factual consistency and conservative adherence to retrieved context. |
| **Auditable Evaluation Harness (`evaluate.py`)** | Runs the 40-question dataset (`28` Factual, `9` Referral, `3` Gap), logging both LLM-native referrals and deterministic guardrail referrals separately so safety enforcement is not conflated with raw LLM behavior. |

---

## Project Structure

```text
vse-buddy-bot/
|-- app.py                     # Streamlit chat interface & inline feedback logging
|-- bot.py                     # End-to-end pipeline: safety -> retrieve -> generate -> cite
|-- cli.py                     # Interactive terminal chat mode
|-- config.py                  # Centralized settings, model names, thresholds & paths
|-- ingest.py                  # Structural Markdown chunker & Gemini embedder
|-- retriever.py               # NumPy cosine search with hybrid title-keyword boosting
|-- safety.py                  # Deterministic crisis filter, sensitive topics & referral helpers
|-- prompts.py                 # System prompt, grounding rules & context formatting
|-- insis_nav_db.py            # SQLite FTS5 engine for InSIS routes, policies & campus offices
|-- vse_data_fixtures.py       # Verified core VSE policy rules (18) and campus offices (12)
|-- student_profile.py         # Simulated opt-in student profile & onboarding checklists
|-- evaluate.py                # Automated live benchmark runner for the 40-question dataset
|-- api/
|   |-- index.py               # Vercel serverless API handler (/api/chat, search endpoints)
|   `-- requirements.txt       # Pinned runtime dependencies for Vercel
|-- public/                    # Single canonical web frontend (served by Vercel & local server)
|   |-- index.html             # Simulated InSIS portal & embedded Buddy Bot UI
|   |-- app.js                 # Frontend router, session control, HTML escaping & chat client
|   |-- styles.css             # Portal and chat styling
|   |-- all_urls.json          # Reference index of public/authenticated InSIS paths
|   `-- assets/                # Official VSE logo assets
|-- insis_demo/
|   `-- server.py              # Local ThreadingHTTPServer serving public/ on port 8502
|-- knowledge/                 # 51 curated Markdown guides + contacts.md (52 files total)
|-- data/
|   |-- index.npz              # Pre-built L2-normalized Gemini embeddings (199 x 3072)
|   |-- index_meta.json        # Chunk metadata (doc_id, title, url, unverified, text)
|   |-- insis_navigation.db    # SQLite DB (7 modules, 24 routes, 18 core policies, 12 offices)
|   |-- knowledge_hash.txt     # Normalized SHA-256 hash of knowledge/ (CRLF/LF-safe)
|   `-- test_questions.csv     # 40-question thesis benchmark (28 Factual, 9 Referral, 3 Gap)
|-- results/                   # Live benchmark evaluation CSV outputs
|-- tests/                     # Pytest suite (84 unit, HTTP security & integrity tests)
|-- traceability.csv           # Source URLs, journey stages, and verification dates
|-- insis_reference_links.csv  # Audited InSIS reference URL directory
|-- vercel.json                # Vercel deployment routing and serverless function config
|-- requirements.txt           # Local Python dependencies (Python 3.10+)
|-- ARCHITECTURE.md            # ArchiMate / UML / BPMN alignment specification
`-- README.md                  # Setup and independent verification guide
```

---

## Getting Started Locally

### 1. Prerequisites
- Python 3.10 or higher
- A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 2. Clone and Install Dependencies
```bash
git clone https://github.com/mjgeorge3-web/vse-buddy-bot.git
cd vse-buddy-bot
pip install -r requirements.txt
```

### 3. Configure API Key
```bash
cp .env.example .env
```
Add your key to `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. Run the Prototype Locally
The pre-built Gemini vector index (`data/index.npz` and `data/index_meta.json`) is included in the repository so you can run immediately without re-embedding:

- **Option A - Interactive InSIS Portal Simulation (serving `public/` on port 8502):**
  ```bash
  python insis_demo/server.py
  ```
  Open `http://localhost:8502`.  
  *To test the simulated logged-in Opt-In Personalisation mode (synthetic demo student record showing 90/120 ECTS earned, 24 enrolled, 30/144 credit vouchers remaining, and relative sample deadlines), click **Log in to Personal administration**, enter any demo name (e.g., `Alex Novak`), and use the demo password `ism_mastersthesis`.*

- **Option B - Streamlit Chat UI:**
  ```bash
  streamlit run app.py
  ```
  Open `http://localhost:8501`.

- **Option C - Terminal Interactive Mode:**
  ```bash
  python cli.py
  ```

*(Optional) To rebuild the vector index from scratch from `knowledge/`, run `python ingest.py` (requires `GEMINI_API_KEY`).*

---

## Privacy, Known Limitations & Transparency Notes

- **No Real Personal Data / No Live InSIS SSO:** The public prototype does not collect student names, UCO identifiers, or real InSIS credentials. The logged-in view uses strictly synthetic placeholder records (`student_profile.py`).
- **Anonymous Local Logging:** Local runs append anonymous session UUIDs to `logs/chat_log.csv` (gitignored) and redact crisis inputs as `[CRISIS REDACTED]`. On Vercel's read-only serverless runtime, local file logging is skipped automatically.
- **Hosted LLM Variability:** Generation uses Google's `gemini-flash-lite-latest` alias (`temperature = 0.2`), so exact phrasing and response latency vary across live runs. Evaluation runs therefore record timestamp, model identifier, and knowledge-base SHA-256 hash.
- **Knowledge Snapshot Boundaries:** Institutional rules and external visa schedules change over time; the corpus represents a curated static snapshot rather than a live institutional API feed.
- **Development Tools Disclosure:** AI coding assistants were used as development aids for frontend UI and boilerplate code in accordance with VSE academic guidelines; all empirical data (student survey and ambassador interviews), knowledge-base sources, architectural design decisions, test verification, and manual benchmark grading were curated and verified by the thesis author.
