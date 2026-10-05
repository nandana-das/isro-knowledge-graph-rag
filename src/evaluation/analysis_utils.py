"""Shared, non-generative helpers for additional journal analyses.

The helpers in this module read frozen benchmark artifacts only.  They never
call Ollama and never write the canonical benchmark result file.
"""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from statistics import mean, median
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "data" / "results"
BENCHMARK_PATH = ROOT / "data" / "benchmark" / "isro_qa.json"
TEST_IDS_PATH = ROOT / "data" / "benchmark" / "test_ids.json"
BASELINE_PATH = RESULTS_DIR / "baseline_results.json"
SEED = 42


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", (text or "").lower().strip())


def is_idk(answer: str) -> bool:
    text = (answer or "").lower().strip()
    return not text or "i don't know" in text or "i do not know" in text or "don't know" in text


def lcs_length(left: list[str], right: list[str]) -> int:
    previous = [0] * (len(right) + 1)
    for token_left in left:
        current = [0]
        for j, token_right in enumerate(right, 1):
            current.append(previous[j - 1] + 1 if token_left == token_right else max(previous[j], current[-1]))
        previous = current
    return previous[-1]


def rouge_l(prediction: str, reference: str) -> float:
    pred = normalize(prediction).split()
    ref = normalize(reference).split()
    if not pred or not ref:
        return 0.0
    lcs = lcs_length(ref, pred)
    precision = lcs / len(pred)
    recall = lcs / len(ref)
    return (2 * precision * recall / (precision + recall)) if precision + recall else 0.0


def coverage(prediction: str, reference: str) -> float:
    pred = set(normalize(prediction).split())
    ref = set(normalize(reference).split())
    return len(pred & ref) / len(ref) if ref else 0.0


def exact_match(prediction: str, reference: str) -> float:
    return float(normalize(prediction) == normalize(reference))


def load_frozen_rows() -> list[dict]:
    """Load the stored per-question rows for the canonical test IDs."""
    test_ids = set(load_json(TEST_IDS_PATH))
    rows = [row for row in load_json(BASELINE_PATH) if row.get("id") in test_ids]
    if len(rows) != len(test_ids):
        raise RuntimeError(f"Expected {len(test_ids)} stored test rows, found {len(rows)}")
    return sorted(rows, key=lambda row: row["id"])


def metric_value(row: dict, system: str, metric: str) -> float:
    answer_key = {"kg_rag": "kgrag_answer", "bm25_llm": "bm25_answer", "vanilla_rag": "vanilla_rag_answer"}[system]
    answer = row.get(answer_key, "")
    reference = row.get("reference_answer", "")
    if metric == "rouge_l":
        return rouge_l(answer, reference) if not is_idk(answer) else 0.0
    if metric in {"reference_token_coverage", "coverage"}:
        return coverage(answer, reference) if not is_idk(answer) else 0.0
    if metric == "exact_match":
        return exact_match(answer, reference)
    if metric == "idk":
        return float(is_idk(answer))
    raise KeyError(metric)


def paired_values(rows: Iterable[dict], left: str, right: str, metric: str) -> tuple[list[float], list[float], list[dict]]:
    left_values, right_values, details = [], [], []
    for row in rows:
        lv = metric_value(row, left, metric)
        rv = metric_value(row, right, metric)
        left_values.append(lv)
        right_values.append(rv)
        details.append({"id": row["id"], "tier": row.get("tier"), "left": lv, "right": rv, "difference": lv - rv})
    return left_values, right_values, details


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def bootstrap_mean_ci(differences: list[float], *, seed: int = SEED, resamples: int = 5000) -> list[float]:
    """Percentile bootstrap CI for the paired mean difference."""
    if not differences:
        return [None, None]
    import random

    rng = random.Random(seed)
    samples = []
    n = len(differences)
    for _ in range(resamples):
        samples.append(sum(differences[rng.randrange(n)] for _ in range(n)) / n)
    return [round(percentile(samples, 0.025), 6), round(percentile(samples, 0.975), 6)]


def wilcoxon_result(differences: list[float]) -> dict:
    """Run Wilcoxon when scipy is available; otherwise record the limitation."""
    nonzero = [value for value in differences if value != 0]
    if len(nonzero) < 2:
        return {"available": True, "n_nonzero": len(nonzero), "statistic": None, "p_value": None, "note": "Fewer than two non-zero paired differences."}
    try:
        from scipy.stats import wilcoxon

        result = wilcoxon(differences, zero_method="wilcox", alternative="two-sided", method="auto")
        return {"available": True, "n_nonzero": len(nonzero), "statistic": float(result.statistic), "p_value": float(result.pvalue), "alternative": "two-sided"}
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"available": False, "n_nonzero": len(nonzero), "statistic": None, "p_value": None, "note": f"scipy Wilcoxon unavailable: {exc}"}


def rank_biserial(differences: list[float]) -> float | None:
    """Paired rank-biserial correlation, positive when left wins."""
    nonzero = [(abs(value), value) for value in differences if value != 0]
    if not nonzero:
        return None
    nonzero.sort(key=lambda item: item[0])
    rank_sum_positive = sum(index for index, (_, value) in enumerate(nonzero, 1) if value > 0)
    rank_sum_negative = sum(index for index, (_, value) in enumerate(nonzero, 1) if value < 0)
    denominator = len(nonzero) * (len(nonzero) + 1) / 2
    return (rank_sum_positive - rank_sum_negative) / denominator if denominator else None


def summarize_pair(left: list[float], right: list[float], metric: str) -> dict:
    differences = [a - b for a, b in zip(left, right)]
    return {
        "metric": metric,
        "n_questions": len(differences),
        "unit_of_analysis": "question",
        "left_mean": round(mean(left), 6) if left else None,
        "right_mean": round(mean(right), 6) if right else None,
        "mean_difference_left_minus_right": round(mean(differences), 6) if differences else None,
        "median_difference_left_minus_right": round(median(differences), 6) if differences else None,
        "bootstrap_95_percent_ci_mean_difference": bootstrap_mean_ci(differences),
        "wilcoxon_signed_rank": wilcoxon_result(differences),
        "rank_biserial_effect_size": round(rank_biserial(differences), 6) if rank_biserial(differences) is not None else None,
    }


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
