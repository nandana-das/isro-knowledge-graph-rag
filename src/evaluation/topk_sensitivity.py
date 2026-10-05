"""Documented top-k sensitivity runner.

No QA values are inferred from canonical answers because changing k changes the
retrieved context and requires new generation outputs.
"""

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
        "experiment": "topk_sensitivity",
        "status": "pending_generation",
        "subset": "deterministic representative subset to be generated in a future run",
        "k_values": [1, 3, 5, 10],
        "metrics": ["rouge_l", "coverage", "idk", "latency"],
        "reason": "No stored per-question outputs exist for alternate k values; no curve or figure was fabricated.",
        "figure_status": "not_created_without_measured_values",
        "canonical_benchmark_untouched": True,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path = RESULTS_DIR / "topk_sensitivity.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Pending additional-subset generation; saved {path}")


if __name__ == "__main__":
    main()
