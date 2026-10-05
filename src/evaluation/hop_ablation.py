"""Documented 1-hop/2-hop ablation runner without fabricated QA values."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.analysis_utils import RESULTS_DIR, ROOT


def main() -> None:
    result = {
        "experiment": "hop_ablation",
        "status": "pending_generation",
        "dataset": "same deterministic 50-question ablation subset as existing ablation",
        "configurations": ["1-hop", "2-hop"],
        "metrics": ["rouge_l", "reference_token_coverage", "exact_match", "idk", "retrieval_context_size", "latency"],
        "reason": "The repository exposes two-hop retrieval but stores no per-question answers or latency traces for either hop setting; executing this requires a new additional-subset generation run.",
        "canonical_benchmark_untouched": True,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path = RESULTS_DIR / "hop_ablation_results.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Pending additional-subset generation; saved {path}")


if __name__ == "__main__":
    main()
