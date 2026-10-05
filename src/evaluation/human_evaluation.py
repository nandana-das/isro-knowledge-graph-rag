"""Create a stratified human-evaluation package without ratings."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.analysis_utils import ROOT, load_frozen_rows


def main() -> None:
    out_dir = ROOT / "data" / "human_eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = []
    for tier in (1, 2, 3):
        selected.extend([row for row in load_frozen_rows() if int(row.get("tier", 0)) == tier][:25])
    fields = ["question_id", "tier", "question", "reference_answer", "bm25_answer", "vanilla_rag_answer", "kg_rag_answer", "correctness_rating", "faithfulness_rating", "relevance_rating", "completeness_rating", "evaluator_id"]
    path = out_dir / "human_evaluation_template.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in selected:
            writer.writerow({
                "question_id": row["id"], "tier": row.get("tier"), "question": row.get("question", ""),
                "reference_answer": row.get("reference_answer", ""), "bm25_answer": row.get("bm25_answer", ""),
                "vanilla_rag_answer": row.get("vanilla_rag_answer", ""), "kg_rag_answer": row.get("kgrag_answer", ""),
            })
    (out_dir / "README.md").write_text("""# Human evaluation package\n\nThis package contains a 75-question stratified template (25 questions per benchmark tier) using the same questions and stored answers for all three systems.\n\nThe rating columns are intentionally blank. No human ratings or agreement statistics have been fabricated. Use a documented ordinal scale (for example 1–5) for correctness, faithfulness, relevance, and completeness, and record evaluator IDs. After annotation, calculate per-system mean, median, standard deviation, confidence intervals, and Cohen's kappa for two raters or Krippendorff's alpha for multiple raters.\n""", encoding="utf-8")
    print(f"Saved {path} ({len(selected)} questions)")


if __name__ == "__main__":
    main()
