"""Report the existing ablation and gate unsupported new configurations.

The repository does not retain per-question answers for the old ablation, and
the current retriever exposes no switches for entity/relation filtering.  The
script therefore records the comparable historical aggregates and marks new
configurations pending instead of generating unplanned answers.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.analysis_utils import RESULTS_DIR


def main() -> None:
    existing = json.loads((RESULTS_DIR / "ablation_results.json").read_text(encoding="utf-8-sig"))
    result = {
        "experiment": "component_ablation",
        "status": "partially_executed",
        "dataset": "existing deterministic stratified 50-question ablation subset",
        "canonical_benchmark_untouched": True,
        "existing_configurations": {
            "kg_only": {"status": "available_from_existing_artifact", "aggregate": existing.get("kg_only", {})},
            "faiss_only": {"status": "available_from_existing_artifact", "aggregate": existing.get("faiss_only", {})},
            "full_kgrag": {"status": "available_from_existing_artifact", "aggregate": existing.get("full_kgrag", {})},
        },
        "requested_configurations": {
            "kg_plus_faiss_without_entity_filtering": {"status": "pending", "reason": "No implemented configuration switch and no stored raw answers."},
            "kg_plus_faiss_without_relation_filtering": {"status": "pending", "reason": "No implemented configuration switch and no stored raw answers."},
            "kg_plus_faiss_1_hop": {"status": "pending", "reason": "New generation run required; no stored raw answers."},
            "kg_plus_faiss_2_hop": {"status": "pending", "reason": "New generation run required; no stored raw answers."},
        },
        "note": "The historical ablation_results.json was preserved and not overwritten.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path = RESULTS_DIR / "component_ablation_results.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
