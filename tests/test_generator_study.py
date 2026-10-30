import json
import random

from src.evaluation.analyze_generator_study import analyze, combine
from src.evaluation.build_corrected_rerun_human_package import BENCHMARK
from src.evaluation.run_generator_study import GENERATORS, SYSTEMS

QUESTIONS = json.loads(BENCHMARK.read_text(encoding="utf8"))["questions"]
REQUIRED = [q["question_id"] for q in QUESTIONS if q["kg_required"] == "YES"]


def rater(a_score: int, v_score: int, noise: int = 0, seed: int = 0) -> dict:
    rng = random.Random(seed)
    scores = {}
    for q in REQUIRED:
        for g in GENERATORS:
            for s in SYSTEMS:
                base = a_score if s == "A_CURRENT" else v_score
                value = min(5, max(1, base + (rng.randint(-noise, noise) if noise else 0)))
                scores[(q, g, s)] = {"correctness": value, "completeness": value, "groundedness": value,
                                     "relevance": value, "unsupported_claim": int(s == "V_VANILLA")}
    return scores


def test_identical_raters_give_perfect_agreement_and_supported_decisions():
    result = analyze([rater(5, 2)] * 3, QUESTIONS)
    assert result["krippendorff_alpha"]["correctness"] == 1.0
    assert result["reliability_qualifier"] is None
    assert set(result["decisions"].values()) == {"SUPPORTED"}
    assert result["set_sizes"] == {"primary": 60, "compositional": 20}


def test_no_difference_is_not_supported():
    result = analyze([rater(3, 3, noise=1, seed=i) for i in range(3)], QUESTIONS)
    assert all(d.startswith("NOT SUPPORTED") or d == "HARMFUL" for d in result["decisions"].values())


def test_unsupported_claim_uses_majority_of_raters():
    key = (REQUIRED[0], "mistral", "A_CURRENT")
    one_flag = [rater(5, 2), rater(5, 2), rater(5, 2)]
    one_flag[0][key] = {**one_flag[0][key], "unsupported_claim": 1}
    assert combine(one_flag)[key]["unsupported_claim"] == 0
    one_flag[1][key] = {**one_flag[1][key], "unsupported_claim": 1}
    assert combine(one_flag)[key]["unsupported_claim"] == 1
