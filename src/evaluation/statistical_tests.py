"""Paired significance tests over the frozen 180-question test outputs.

This script reads ``baseline_results.json`` and ``test_ids.json`` only.  It
does not regenerate answers or modify ``evaluation_results.json``.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.analysis_utils import RESULTS_DIR, load_frozen_rows, paired_values, summarize_pair, write_csv


COMPARISONS = [("kg_rag", "bm25_llm"), ("kg_rag", "vanilla_rag")]
METRICS = ("rouge_l", "reference_token_coverage", "exact_match", "idk")


def main() -> None:
    rows = load_frozen_rows()
    output = {
        "experiment": "statistical_significance",
        "status": "executed",
        "unit_of_analysis": "question",
        "source": "data/results/baseline_results.json filtered by data/benchmark/test_ids.json",
        "canonical_test_questions": len(rows),
        "bootstrap": {"resamples": 5000, "seed": 42, "interval": "percentile 95% CI"},
        "comparisons": {},
        "per_question": [],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    csv_rows = []
    for left, right in COMPARISONS:
        name = f"{left}_vs_{right}"
        output["comparisons"][name] = {}
        for metric in METRICS:
            left_values, right_values, details = paired_values(rows, left, right, metric)
            output["comparisons"][name][metric] = summarize_pair(left_values, right_values, metric)
            for detail in details:
                output["per_question"].append({"comparison": name, "metric": metric, **detail})
                csv_rows.append({"comparison": name, "metric": metric, **detail})

    out_json = RESULTS_DIR / "statistical_tests.json"
    out_csv = RESULTS_DIR / "statistical_tests.csv"
    out_json.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    write_csv(out_csv, csv_rows, ["comparison", "metric", "id", "tier", "left", "right", "difference"])
    print(f"Saved {out_json}")
    print(f"Saved {out_csv}")


if __name__ == "__main__":
    main()
