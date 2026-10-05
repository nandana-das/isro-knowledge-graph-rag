"""Guarded retrieval-quality evaluation.

The benchmark has source references, but not manually verified chunk-level
relevance judgments.  This script deliberately refuses to treat URL/source
provenance as relevance ground truth.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.analysis_utils import BENCHMARK_PATH, RESULTS_DIR, ROOT, load_json


MESSAGE = "Retrieval-level evaluation requires manually verified relevance judgments and was not executed."


def main() -> None:
    benchmark = load_json(BENCHMARK_PATH)
    out = {
        "experiment": "retrieval_quality",
        "status": "not_executed",
        "reason": MESSAGE,
        "candidate_source_fields": ["source_url", "source_note"],
        "label_decision": "Source URLs and source notes identify verification provenance, not relevant chunk IDs; no labels were inferred.",
        "required_future_input": "Manually verified relevant chunk/document judgments for each evaluated question.",
        "candidate_questions": len(benchmark),
        "systems": ["BM25", "FAISS", "KG", "Hybrid KG + FAISS"],
        "metrics": ["Recall@1", "Recall@3", "Recall@5", "Recall@10", "MRR"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path = RESULTS_DIR / "retrieval_metrics.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    doc = ROOT / "data" / "results" / "retrieval_quality_pending.md"
    doc.write_text(f"# Retrieval-level evaluation\n\n{MESSAGE}\n\nNo retrieval metric was computed and no relevance label was inferred from benchmark source provenance.\n", encoding="utf-8")
    print(MESSAGE)
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
