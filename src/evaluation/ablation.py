"""Deterministic ablation study over a stratified 50-question subset."""

from __future__ import annotations

import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

BENCHMARK_PATH = ROOT / "data" / "benchmark" / "isro_qa.json"
OUTPUT_PATH = ROOT / "data" / "results" / "ablation_results.json"
SEED = 42


def normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return text


def rouge_l(prediction: str, reference: str) -> float:
    pred_tokens = normalize(prediction).split()
    ref_tokens = normalize(reference).split()
    if not pred_tokens or not ref_tokens:
        return 0.0
    m, n = len(ref_tokens), len(pred_tokens)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_tokens[i - 1] == pred_tokens[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    lcs = dp[m][n]
    precision = lcs / n if n else 0.0
    recall = lcs / m if m else 0.0
    if precision + recall == 0:
        return 0.0
    return round((2 * precision * recall) / (precision + recall), 4)


def reference_token_coverage(prediction: str, reference: str) -> float:
    pred_tokens = set(normalize(prediction).split())
    ref_tokens = set(normalize(reference).split())
    if not ref_tokens:
        return 0.0
    return round(len(pred_tokens & ref_tokens) / len(ref_tokens), 4)


def is_idk(answer: str) -> bool:
    text = (answer or "").lower().strip()
    return not text or "i don't know" in text or "i do not know" in text or "don't know" in text


def score_answers(answers: list[str], references: list[str]) -> dict:
    rouge_scores: list[float] = []
    coverage_scores: list[float] = []
    idk_count = 0
    for answer, reference in zip(answers, references):
        if is_idk(answer):
            idk_count += 1
            rouge_scores.append(0.0)
            coverage_scores.append(0.0)
        else:
            rouge_scores.append(rouge_l(answer, reference))
            coverage_scores.append(reference_token_coverage(answer, reference))
    n = len(answers)
    return {
        "rouge_l": round(sum(rouge_scores) / n, 4) if n else 0.0,
        "coverage": round(sum(coverage_scores) / n, 4) if n else 0.0,
        "idk_rate": round(idk_count / n, 4) if n else 0.0,
        "n": n,
    }


def select_ablation_ids(benchmark: list[dict]) -> list[str]:
    by_tier: dict[int, list[dict]] = defaultdict(list)
    for item in benchmark:
        by_tier[int(item.get("tier", 1))].append(item)

    desired = {1: 25, 2: 15, 3: 10}
    selected_ids: list[str] = []
    for tier in sorted(by_tier):
        rng = random.Random(SEED + tier)
        items = by_tier[tier][:]
        rng.shuffle(items)
        selected_ids.extend(item["id"] for item in items[: desired.get(tier, 0)])

    return selected_ids


def get_answer_kg_only(question: str) -> str:
    from src.generator.ollama_api import generate
    from src.retriever.kg_retriever import get_kg_context
    import spacy

    nlp = spacy.load("en_core_web_lg")
    doc = nlp(question)
    entities = [ent.text for ent in doc.ents if ent.text.strip()]
    context = get_kg_context(entities)
    if not context.strip():
        return "I don't know."
    return generate(question, context)


def get_answer_faiss_only(question: str) -> str:
    from src.generator.ollama_api import generate
    from src.retriever.faiss_retriever import get_passage_context

    context = get_passage_context(question, top_k=3)
    if not context.strip():
        return "I don't know."
    return generate(question, context)


def get_answer_full_kgrag(question: str) -> str:
    from src.generator.ollama_api import generate
    from src.retriever.hybrid import retrieve

    context = retrieve(question, passage_limit=3, max_tokens=1500)
    if not context.strip():
        return "I don't know."
    return generate(question, context)


def main() -> None:
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8-sig"))
    bench_map = {item["id"]: item for item in benchmark}
    selected_ids = select_ablation_ids(benchmark)
    selected_questions = [bench_map[qid]["question"] for qid in selected_ids]
    selected_references = [bench_map[qid]["answer"] for qid in selected_ids]

    systems = {
        "kg_only": get_answer_kg_only,
        "faiss_only": get_answer_faiss_only,
        "full_kgrag": get_answer_full_kgrag,
    }

    results = {
        "seed": SEED,
        "selected_ids": selected_ids,
        "selected_count": len(selected_ids),
        "tier_distribution": {"tier_1": 25, "tier_2": 15, "tier_3": 10},
        "systems": {},
    }

    for name, fn in systems.items():
        answers: list[str] = []
        for question in selected_questions:
            try:
                answers.append(fn(question))
            except Exception:
                answers.append("I don't know.")
        results["systems"][name] = score_answers(answers, selected_references)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()