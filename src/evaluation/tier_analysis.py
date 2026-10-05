"""Create tier comparison data and a publication-ready figure from frozen rows."""

from __future__ import annotations

import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.analysis_utils import RESULTS_DIR, ROOT, load_frozen_rows, metric_value


def main() -> None:
    rows = load_frozen_rows()
    records = []
    for tier in (1, 2, 3):
        tier_rows = [row for row in rows if int(row.get("tier", 0)) == tier]
        for system in ("bm25_llm", "vanilla_rag", "kg_rag"):
            records.append({
                "tier": tier,
                "n": len(tier_rows),
                "system": system,
                "rouge_l": round(sum(metric_value(row, system, "rouge_l") for row in tier_rows) / len(tier_rows), 6),
                "reference_token_coverage": round(sum(metric_value(row, system, "reference_token_coverage") for row in tier_rows) / len(tier_rows), 6),
                "exact_match": round(sum(metric_value(row, system, "exact_match") for row in tier_rows) / len(tier_rows), 6),
                "idk_rate": round(sum(metric_value(row, system, "idk") for row in tier_rows) / len(tier_rows), 6),
            })
    data_path = RESULTS_DIR / "tier_comparison_data.json"
    data_path.write_text(json.dumps({"source": "frozen per-question outputs", "records": records}, indent=2) + "\n", encoding="utf-8")

    colors = {"bm25_llm": "#C00000", "vanilla_rag": "#375623", "kg_rag": "#012258"}
    labels = {"bm25_llm": "BM25 + LLM", "vanilla_rag": "Vanilla RAG", "kg_rag": "KG-RAG"}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)
    x = np.arange(3)
    width = 0.24
    for offset, system in zip((-width, 0, width), ("bm25_llm", "vanilla_rag", "kg_rag")):
        values = [next(item["rouge_l"] for item in records if item["tier"] == tier and item["system"] == system) for tier in (1, 2, 3)]
        axes[0].bar(x + offset, values, width, label=labels[system], color=colors[system])
        values = [next(item["reference_token_coverage"] for item in records if item["tier"] == tier and item["system"] == system) for tier in (1, 2, 3)]
        axes[1].bar(x + offset, values, width, color=colors[system])
    for ax, title, ylabel in ((axes[0], "ROUGE-L by tier", "ROUGE-L"), (axes[1], "Reference-token coverage by tier", "Coverage")):
        ax.set_title(title)
        ax.set_xlabel("Benchmark tier")
        ax.set_ylabel(ylabel)
        ax.set_xticks(x, ["Tier 1", "Tier 2", "Tier 3"])
        ax.set_ylim(0, max(0.6, ax.get_ylim()[1]))
        ax.grid(axis="y", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, fontsize=8)
    out = ROOT / "paper" / "figures" / "tier_comparison.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {data_path}")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
