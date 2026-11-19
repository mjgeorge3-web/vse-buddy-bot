# VSE Buddy Bot

A research prototype Retrieval-Augmented Generation (RAG) chatbot developed for international students at the **Prague University of Economics and Business (Vysoka skola ekonomicka v Praze, VSE)**.

This prototype was developed as part of a Master's Thesis in Information Systems Management (ISM). It provides verified, grounded answers regarding admissions, arrival, student housing, visas, university IT, exams, and daily life in Prague.

Live demo: `https://vse-buddy-bot.vercel.app`

---

## Architecture & Architectural Rationale

| Architectural Decision | Thesis Design Rationale |
| :--- | :--- |
| **Retrieval-Augmented Generation (RAG)** | Restricts bot answers strictly to 52 verified VŠE knowledge documents and structured SQLite tables, effectively minimizing hallucinations and ungrounded fabrications. |
| **Pure NumPy Vector Search** | A 52-document knowledge base produces 254 vector chunks. A complex vector database (e.g. Pinecone/Chroma) introduces unnecessary overhead and costs. Pure NumPy dot-product cosine similarity is fast, lightweight, and 100% reproducible. |
| **Deterministic Crisis Filter (No LLM)** | Rule-based regex pattern matching ensures guaranteed detection of self-harm/suicide terms without latency, cost, or non-deterministic LLM failure risks. |
| **Deterministic Sensitive Topic Referrals** | Topics involving legal, visa, police registration, or exam failures trigger mandatory administrative referral notices to protect students from outdated immigration advice. |
| **Explicit Source Citations & Flags** | Inline numbered citations `[1]`, `[2]` with clickable URLs and explicit `unverified` flags promote student trust and transparency. |
| **Low Temperature (0.2)** | Ensures factual consistency, conservative generation, and reliable refusal on gap queries. |
| **Reproducible Evaluation Script** | `evaluate.py` enables standardized benchmarking against a 40-question test set across different stages and question categories. |

---

## Project Structure

```text
vse-buddy-bot/
├── app.py               # Streamlit user interface & chat session management
├── config.py            # Centralized settings, model names, and retrieval thresholds
├── ingest.py            # Chunker and embedder (saves index.npz and index_meta.json)
├── retriever.py         # NumPy vector search with hybrid title-keyword boosting
├── safety.py            # Deterministic crisis & sensitive-topic detection
├── prompts.py           # System prompt, guardrails, and context formatting
├── bot.py               # End-to-end pipeline: safety → retrieve → generate → cite
├── insis_nav_db.py      # SQLite engine for InSIS routes, SZŘ policies, and campus locations
├── student_profile.py   # Authenticated student session & GDPR opt-out context builder
├── evaluate.py          # Automated benchmark runner for test questions dataset
├── insis_demo/          # Interactive VŠE InSIS simulation server & frontend (port 8502)
├── api/                 # Vercel serverless deployment entrypoint
├── knowledge/           # 51 curated Markdown knowledge files + contacts.md (52 total)
├── data/
│   ├── index.npz        # Committed L2-normalized Gemini embeddings matrix (254 × 3072)
│   ├── index_meta.json  # Chunk metadata (doc_id, title, url, unverified, text)
│   ├── insis_navigation.db # SQLite database (7 modules, 24 routes, 50 policies, 42 locations)
│   ├── knowledge_hash.txt # SHA-256 integrity hash of knowledge base
│   └── test_questions.csv # 40-question thesis test dataset
├── logs/                # chat_log.csv and feedback.csv (anonymous interaction logs)
├── results/             # Generated evaluation benchmark CSV reports
├── tests/               # Pytest unit test suite (73 tests)
├── traceability.csv     # Source URLs and verification dates for all pages
├── .env.example         # Template for environment variables
├── .gitignore           # Ignores secrets, logs, and cache
├── requirements.txt     # Pinned Python package dependencies
└── README.md            # System documentation and deployment instructions
```

---

## Getting Started Locally

### 1. Prerequisites
- Python 3.10 or higher
- A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 2. Clone and Install Dependencies
Navigate into the `vse-buddy-bot` directory:
```bash
cd vse-buddy-bot
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the `vse-buddy-bot` directory based on `.env.example`:
```bash
cp .env.example .env
```
Open `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. Build Knowledge Base & Vector Index
Run the ingestion pipeline to parse all 52 files in `knowledge/`, generate 254 chunks, and build the NumPy vector index:
```bash
python ingest.py
```
*Note: Once generated, `data/index.npz` and `data/index_meta.json` are committed to the repository so the application can run immediately without re-embedding on every start.*

### 5. Run the Streamlit Application
Start the interactive chat interface:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## Running Automated Tests & Evaluation

### 1. Unit & Integration Test Suite
Run the full pytest suite (73 tests) covering deterministic crisis and sensitive topic rules, SQLite navigation/policy databases, student profile personalization, and UI link formatting:
```bash
pytest tests/ -v
```

### 2. Full Test-Set Evaluation (40 Questions)
Execute the thesis evaluation set:
```bash
python evaluate.py
```
To run a fast test on the first 3 example rows:
```bash
python evaluate.py 3
```
The script writes results to `results/eval_YYYYMMDD_HHMM.csv` and outputs:
- **Retrieval Hit Rate (%)**: percentage of questions where expected source document was retrieved
- **Refusal Rate on Gaps (%)**: percentage of out-of-scope/gap questions where the bot stated *"I don't have verified information about this"*
- **Referral Rate on Sensitive Questions (%)**: percentage of sensitive questions with administrative referrals
- **Average Response Latency (ms)**

---

## Deployment (Vercel & Streamlit Community Cloud)

Follow these steps to deploy the application online for user testing:

1. **Push to GitHub**:
   Ensure `vse-buddy-bot` is pushed to a GitHub repository.
   Verify that `data/index.npz` and `data/index_meta.json` are committed to the repo, while `.env` and `logs/` are ignored.

2. **Connect Streamlit Community Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io/).
   - Click **New app**.
   - Select your GitHub repository, branch (`main`), and set the main file path to `app.py` (or `vse-buddy-bot/app.py` if deployed from the root).

3. **Configure App Secrets**:
   - In the Streamlit Cloud deployment dashboard, click **Advanced settings** (or go to **Settings > Secrets**).
   - Enter your Gemini API key:
     ```toml
     GEMINI_API_KEY = "your_actual_gemini_api_key_here"
     ```
   - Click **Save**.

4. **Launch**:
   Streamlit Cloud will install dependencies from `requirements.txt` and launch the app with a public URL you can share with test participants.

---

## Privacy & Ethical Safeguards

- **No Personal Data Collected:** The bot does not request or store student names, ID numbers, or contact details.
- **Anonymous Interaction Logging:** All logs use random UUID session identifiers, timestamps, and retrieval metrics.
- **Crisis Confidentiality:** When a mental health or self-harm emergency is detected, the event is logged only as `[CRISIS REDACTED]`; the student's text is never logged to disk.
- **Configurable Logging:** Logging can be disabled entirely in `config.py` by setting `ENABLE_LOGGING = False`.
