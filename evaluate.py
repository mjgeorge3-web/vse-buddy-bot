"""Automated evaluation script for VŠE Buddy Bot.

Runs the test questions dataset from data/test_questions.csv through BuddyBot,
evaluates retrieval hits, refusals on gaps, referrals on sensitive topics,
and writes structured CSV output with blank manual scoring columns to results/.
Includes a 5-second delay between queries to respect free-tier Gemini API rate limits.
"""

import csv
from datetime import datetime
from pathlib import Path
import time
from typing import Any, Dict, List

import config
import ingest
import safety
from bot import BuddyBot


def evaluate_test_set(
    test_csv_path: Path = config.TEST_QUESTIONS_PATH,
    delay_between_calls: float = 5.0,
    limit: int = None,
):
    """Run evaluation on test questions and generate summary report and CSV."""
    if not test_csv_path.exists():
        print(f"Error: Test file {test_csv_path} does not exist.")
        return

    # Create results directory
    results_dir = config.BASE_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Read test questions
    rows: List[Dict[str, str]] = []
    with open(test_csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    if limit:
        rows = rows[:limit]

    print(f"Loaded {len(rows)} test questions from {test_csv_path.name}.")
    print(f"Target delay between questions: {delay_between_calls}s (rate-limit safety).")
    print("=" * 70)

    bot = BuddyBot()
    eval_results: List[Dict[str, Any]] = []

    # Metrics counters
    factual_or_ref_count = 0
    source_hits = 0

    gap_count = 0
    refused_hits = 0

    referral_count = 0
    referral_hits = 0
    llm_native_referral_hits = 0
    guardrail_enforced_hits = 0

    total_latency = 0.0

    for idx, row in enumerate(rows, 1):
        q_id = row.get("id", str(idx))
        stage = row.get("stage", "")
        q_type = row.get("type", "").strip().upper()
        question = row.get("question", "")
        expected_points = row.get("expected_points", "")
        expected_source = row.get("expected_source", "").strip()

        print(f"[{idx}/{len(rows)}] (ID: {q_id}, Type: {q_type}) {question[:60]}...", flush=True)

        # Fresh conversation history for each test question
        result = bot.answer(question=question, history=[])
        answer = result.get("answer", "")
        mode = result.get("mode", "")
        top_score = result.get("top_score", 0.0)
        latency_ms = result.get("latency_ms", 0.0)
        total_latency += latency_ms

        # Extract full retrieved doc_ids (true retrieval) and cited doc_ids (post-LLM)
        retrieved_sources = list(result.get("retrieved_sources") or [])
        cited_sources = [
            s.get("doc_id", "") for s in result.get("sources", []) if s.get("doc_id")
        ]
        if not retrieved_sources:
            retrieved_sources = list(cited_sources)
        retrieved_sources_str = "; ".join(retrieved_sources)
        cited_sources_str = "; ".join(cited_sources)

        # -------------------------------------------------------------
        # Automatic Helper Checks (Retrieval, Refusal, Referral)
        # -------------------------------------------------------------
        # 1. Source match check (checks true retrieved chunks against expected_source)
        if expected_source.lower() == "none":
            source_match = "N/A"
        else:
            expected_sources = [es.strip().lower() for es in expected_source.split(";") if es.strip()]
            retrieved_sources_lower = [s.lower() for s in retrieved_sources]
            is_match = any(es in retrieved_sources_lower for es in expected_sources)
            source_match = "Y" if is_match else "N"
            factual_or_ref_count += 1
            if is_match:
                source_hits += 1

        # 2. Refusal check (for Type G)
        if q_type == "G":
            gap_count += 1
            ans_lower = answer.lower()
            refusal_cues = (
                "don't have verified",
                "do not have verified",
                "no verified information",
                "not covered in the provided",
            )
            refused_correctly = "Y" if any(cue in ans_lower for cue in refusal_cues) else "N"
            if refused_correctly == "Y":
                refused_hits += 1
        else:
            refused_correctly = "N/A"

        # 3. Referral check (for Type R - distinguishes LLM-native referral vs. deterministic guardrail append)
        if q_type == "R":
            referral_count += 1
            has_ref = safety.has_explicit_referral(answer)
            referral_present = "Y" if has_ref else "N"
            native_ref = bool(result.get("llm_native_referral", False))
            enforced_ref = bool(result.get("referral_enforced", False))
            llm_native_referral = "Y" if native_ref else "N"
            referral_enforced = "Y" if enforced_ref else "N"
            if referral_present == "Y":
                referral_hits += 1
            if native_ref:
                llm_native_referral_hits += 1
            if enforced_ref:
                guardrail_enforced_hits += 1
        else:
            referral_present = "N/A"
            llm_native_referral = "N/A"
            referral_enforced = "N/A"

        # Leave score (0-2) and notes blank for manual researcher grading
        eval_results.append({
            "id": q_id,
            "stage": stage,
            "type": q_type,
            "question": question,
            "expected_points": expected_points,
            "expected_source": expected_source,
            "retrieved_sources": retrieved_sources_str,
            "cited_sources": cited_sources_str,
            "source_match": source_match,
            "refused_correctly": refused_correctly,
            "referral_present": referral_present,
            "llm_native_referral": llm_native_referral,
            "referral_enforced": referral_enforced,
            "mode": mode,
            "top_score": top_score,
            "latency_ms": latency_ms,
            "answer": answer,
            "score (0-2)": "",
            "notes": "",
        })

        if idx < len(rows):
            time.sleep(delay_between_calls)

    # Write output to results/eval_YYYYMMDD_HHMM.csv
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = results_dir / f"eval_{timestamp_str}.csv"

    fieldnames = [
        "id",
        "stage",
        "type",
        "question",
        "expected_points",
        "expected_source",
        "retrieved_sources",
        "cited_sources",
        "source_match",
        "refused_correctly",
        "referral_present",
        "llm_native_referral",
        "referral_enforced",
        "mode",
        "top_score",
        "latency_ms",
        "answer",
        "score (0-2)",
        "notes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(eval_results)

    # -------------------------------------------------------------
    # Print Evaluation Summary
    # -------------------------------------------------------------
    avg_latency = total_latency / len(rows) if rows else 0.0
    hit_rate = (source_hits / factual_or_ref_count * 100) if factual_or_ref_count > 0 else 0.0
    refusal_rate = (refused_hits / gap_count * 100) if gap_count > 0 else 0.0
    referral_rate = (referral_hits / referral_count * 100) if referral_count > 0 else 0.0
    native_ref_rate = (llm_native_referral_hits / referral_count * 100) if referral_count > 0 else 0.0
    kb_hash = ingest.compute_knowledge_hash(config.KNOWLEDGE_DIR)

    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY REPORT")
    print("=" * 70)
    print(f"Results written to: {output_path}")
    print(f"Model: {config.CHAT_MODEL} | Knowledge SHA-256: {kb_hash[:12]}")
    print(f"Total questions evaluated: {len(rows)}")
    print(f"Retrieval Hit Rate (expected source matched): {hit_rate:.1f}% ({source_hits}/{factual_or_ref_count})")
    print(f"Refusal Rate on Gaps (Type G): {refusal_rate:.1f}% ({refused_hits}/{gap_count})")
    print(f"Referral Rate on Sensitive (Type R, final): {referral_rate:.1f}% ({referral_hits}/{referral_count})")
    print(f"  - LLM-native referral: {native_ref_rate:.1f}% ({llm_native_referral_hits}/{referral_count}) | Appended by guardrail: {guardrail_enforced_hits}/{referral_count}")
    print(f"Average Response Latency: {avg_latency:.1f} ms")
    print("Note: 'score (0-2)' and 'notes' columns are left blank for manual grading.")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    limit_arg = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        limit_arg = int(sys.argv[1])
    evaluate_test_set(limit=limit_arg)
