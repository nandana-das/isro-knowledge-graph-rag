"""Paired KG-RAG tier analysis over the frozen 180-question outputs."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.analysis_utils import RESULTS_DIR, load_frozen_rows, paired_values, summarize_pair, write_csv


METRICS = ("rouge_l", "reference_token_coverage", "exact_match", "idk")


def main() -> None:
    rows = load_frozen_rows()
    output = {
        "experiment": "tier_wise_statistical_analysis",
        "status": "executed",
        "unit_of_analysis": "question",
        "source": "data/results/baseline_results.json filtered by data/benchmark/test_ids.json",
        "comparisons": {},
        "per_question": [],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    csv_rows = []
    for tier in (1, 2, 3):
        tier_rows = [row for row in rows if int(row.get("tier", 0)) == tier]
        for right in ("vanilla_rag", "bm25_llm"):
            comparison = f"tier_{tier}_kg_rag_vs_{right}"
            output["comparisons"][comparison] = {"n_questions": len(tier_rows), "metrics": {}}
            for metric in METRICS:
                left_values, right_values, details = paired_values(tier_rows, "kg_rag", right, metric)
                output["comparisons"][comparison]["metrics"][metric] = summarize_pair(left_values, right_values, metric)
                for detail in details:
                    row = {"comparison": comparison, "metric": metric, **detail}
                    output["per_question"].append(row)
                    csv_rows.append(row)
    out_json = RESULTS_DIR / "tier_statistical_tests.json"
    out_csv = RESULTS_DIR / "tier_statistical_tests.csv"
    out_json.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    write_csv(out_csv, csv_rows, ["comparison", "metric", "id", "tier", "left", "right", "difference"])
    print(f"Saved {out_json}")
    print(f"Saved {out_csv}")


if __name__ == "__main__":
    main()
