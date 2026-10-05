"""Guarded abstention robustness evaluator.

It requires a manually verified input file and never treats benchmark
questions as unanswerable merely because a system said IDK.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.analysis_utils import RESULTS_DIR, ROOT


INPUT = ROOT / "data" / "abstention" / "unanswerable_questions.csv"


def main() -> None:
    rows = []
    if INPUT.exists():
        with INPUT.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    result = {
        "experiment": "unanswerable_abstention",
        "status": "not_executed" if not rows else "pending_manual_verification",
        "reason": "No trustworthy manually verified unanswerable set is present." if not rows else "Input exists but requires verification before scoring.",
        "input_template": str(INPUT.relative_to(ROOT)),
        "metrics": ["correct abstention rate", "unsupported-answer rate", "hallucination rate"],
        "n_questions": len(rows),
        "systems": ["BM25 + LLM", "Vanilla RAG", "KG-RAG"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path = RESULTS_DIR / "abstention_evaluation.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
