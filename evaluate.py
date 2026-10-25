"""Automated evaluation script for VŠE Buddy Bot.

Runs the test questions dataset from data/test_questions.csv through BuddyBot,
evaluates retrieval hits, refusals on gaps, referrals on sensitive topics,
and writes structured CSV output with blank manual scoring columns to results/.
Includes a 4-second delay between queries to respect free-tier Gemini API rate limits.
"""

import csv
from datetime import datetime
from pathlib import Path
import re
import time
from typing import Any, Dict, List

import config
from bot import BuddyBot


def evaluate_test_set(
    test_csv_path: Path = config.TEST_QUESTIONS_PATH,
    delay_between_calls: float = 4.0,
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
    with open(test_csv_path, "r", encoding="utf-8") as f:
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

    total_latency = 0.0

    for idx, row in enumerate(rows, 1):
        q_id = row.get("id", str(idx))
        stage = row.get("stage", "")
        q_type = row.get("type", "").strip().upper()
        question = row.get("question", "")
        expected_points = row.get("expected_points", "")
        expected_source = row.get("expected_source", "").strip()

        print(f"[{idx}/{len(rows)}] (ID: {q_id}, Type: {q_type}) {question[:60]}...")

        # Fresh conversation history for each test question
        result = bot.answer(question=question, history=[])
        answer = result.get("answer", "")
        mode = result.get("mode", "")
        top_score = result.get("top_score", 0.0)
        latency_ms = result.get("latency_ms", 0.0)
        total_latency += latency_ms

        # Extract doc_ids of retrieved/cited sources
        retrieved_sources = [
            s.get("doc_id", "") for s in result.get("sources", []) if s.get("doc_id")
        ]
        retrieved_sources_str = "; ".join(retrieved_sources)

        # -------------------------------------------------------------
        # Automatic Helper Checks
        # -------------------------------------------------------------
        # 1. Source match check
        if expected_source.lower() == "none":
            source_match = "N/A"
        else:
            is_match = any(expected_source.lower() == s.lower() for s in retrieved_sources)
            source_match = "Y" if is_match else "N"
            factual_or_ref_count += 1
            if is_match:
                source_hits += 1

        # 2. Refusal check (for Type G)
        if q_type == "G":
            gap_count += 1
            refused_correctly = (
                "Y"
                if "don't have verified" in answer.lower()
                or "do not have verified" in answer.lower()
                else "N"
            )
            if refused_correctly == "Y":
                refused_hits += 1
        else:
            refused_correctly = "N/A"

        # 3. Referral check (for Type R)
        if q_type == "R":
            referral_count += 1
            ref_keywords = [
                "confirm", "refer", "contact", "office", "department", "mvcr",
                "police", "counselling", "embassy", "international office"
            ]
            has_ref = any(kw in answer.lower() for kw in ref_keywords)
            referral_present = "Y" if has_ref else "N"
            if referral_present == "Y":
                referral_hits += 1
        else:
            referral_present = "N/A"

        eval_results.append({
            "id": q_id,
            "stage": stage,
            "type": q_type,
            "question": question,
            "expected_points": expected_points,
            "expected_source": expected_source,
            "retrieved_sources": retrieved_sources_str,
            "source_match": source_match,
            "refused_correctly": refused_correctly,
            "referral_present": referral_present,
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
        "source_match",
        "refused_correctly",
        "referral_present",
        "mode",
        "top_score",
        "latency_ms",
        "answer",
        "score (0-2)",
        "notes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
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

    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY REPORT")
    print("=" * 70)
    print(f"Results written to: {output_path}")
    print(f"Total questions evaluated: {len(rows)}")
    print(f"Retrieval Hit Rate (expected source matched): {hit_rate:.1f}% ({source_hits}/{factual_or_ref_count})")
    print(f"Refusal Rate on Gaps (Type G 'don't have verified'): {refusal_rate:.1f}% ({refused_hits}/{gap_count})")
    print(f"Referral Rate on Sensitive (Type R): {referral_rate:.1f}% ({referral_hits}/{referral_count})")
    print(f"Average Response Latency: {avg_latency:.1f} ms")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    # Optional --limit flag for quick dry runs on example rows
    limit_arg = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        limit_arg = int(sys.argv[1])
    evaluate_test_set(limit=limit_arg)
