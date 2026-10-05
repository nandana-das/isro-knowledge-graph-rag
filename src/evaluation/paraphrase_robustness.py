"""Create a manually reviewed paraphrase annotation template."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.analysis_utils import RESULTS_DIR, ROOT, load_frozen_rows


def main() -> None:
    out_dir = ROOT / "data" / "paraphrase"
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = []
    for tier in (1, 2, 3):
        selected.extend([row for row in load_frozen_rows() if int(row.get("tier", 0)) == tier][:10])
    path = out_dir / "paraphrase_review_template.csv"
    fields = ["question_id", "tier", "original_question", "paraphrased_question", "paraphrase_reviewed", "semantic_equivalence", "reviewer_id", "notes"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in selected:
            writer.writerow({"question_id": row["id"], "tier": row.get("tier"), "original_question": row.get("question", "")})
    result = {
        "experiment": "paraphrase_robustness",
        "status": "pending_manual_paraphrase_review",
        "subset_size": len(selected),
        "template": str(path.relative_to(ROOT)),
        "metrics": ["ROUGE-L", "coverage", "IDK"],
        "reason": "No paraphrase was accepted without manual semantic-equivalence review; no robustness score was fabricated.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (RESULTS_DIR / "paraphrase_robustness.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {path} ({len(selected)} questions)")


if __name__ == "__main__":
    main()
