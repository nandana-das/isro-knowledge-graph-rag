"""Create a deterministic KG-triple annotation sample; do not score it."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.analysis_utils import ROOT


def main() -> None:
    kg_path = ROOT / "data" / "kg" / "knowledge_graph.json"
    out_dir = ROOT / "data" / "human_eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    graph = json.loads(kg_path.read_text(encoding="utf-8"))
    edges = graph.get("edges", [])
    sampled = edges[:: max(1, len(edges) // 100)][:100]
    path = out_dir / "kg_quality_annotation_template.csv"
    fields = ["sample_index", "subject", "relation", "object", "source", "entity_correctness", "relation_correctness", "triple_validity", "annotator_id", "notes"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, edge in enumerate(sampled, 1):
            writer.writerow({"sample_index": index, "subject": edge.get("source", ""), "relation": edge.get("relation", ""), "object": edge.get("target", ""), "source": edge.get("doc_source", "")})
    result = {
        "experiment": "kg_quality_evaluation",
        "status": "pending_human_annotation",
        "sample_size": len(sampled),
        "sampling": "deterministic systematic sample from knowledge_graph.json edges; step=floor(N/100)",
        "metrics": ["entity correctness", "relation correctness", "triple validity", "error rate"],
        "result": "No precision or error rate computed because annotation columns are blank.",
        "template": str(path.relative_to(ROOT)),
    }
    (ROOT / "data" / "results" / "kg_quality_evaluation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (out_dir / "KG_QUALITY_README.md").write_text("# KG quality annotation\n\nThe CSV is a deterministic 100-triple sample. Fill the three correctness fields with independent human judgments before computing precision/error rates. This repository contains no completed KG-quality annotations.\n", encoding="utf-8")
    print(f"Saved {path} ({len(sampled)} triples)")


if __name__ == "__main__":
    main()
