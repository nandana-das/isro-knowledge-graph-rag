"""Post hoc exploratory analyses of the corrected rerun (preregistration §19).

    python -m src.evaluation.analyze_corrected_rerun_exploratory

Descriptive only: no hypothesis tests. Every analysis listed in §19 is
reported, whatever it shows.
"""

from __future__ import annotations

import json
from statistics import mean, median

from src.config.runtime import DEFAULT_GENERATION_OPTIONS as OPTIONS
from src.evaluation.analyze_corrected_rerun import SCORES, analysis_sets, describe, item_scores, load_ratings
from src.evaluation.build_corrected_rerun_human_package import BENCHMARK, RERUN, RESULTS, load_jsonl
from src.evaluation.evaluate_relational_qa import is_idk
from src.evaluation.run_corrected_rerun import FROZEN_GENERATIONS
from src.generator.kg_grounded_generator import _evidence_budget
from src.generator.prompt import SYSTEM_PROMPT
from src.generator.token_budget import EVIDENCE, _tokenizer, prompt_tokens, trim_to_tokens

OUTPUT = RERUN / "exploratory_analysis.json"
SPOTCHECKS = {
    "checker1": RERUN / "spotcheck_analysis.json",
    "checker2": RERUN / "spotcheck2_analysis.json",
    "checker3": RERUN / "spotcheck3_analysis.json",
}
SYSTEMS = ("V_VANILLA", "A_CURRENT", "C_TWO_STAGE")
PAIRS = (("A_CURRENT", "V_VANILLA"), ("C_TWO_STAGE", "V_VANILLA"), ("C_TWO_STAGE", "A_CURRENT"))
DENSE_MARKER = "[DENSE EVIDENCE]"
# Observed server behaviour for an over-long prompt (preregistration §1):
# the prompt is cut to its last 1,027 tokens once it no longer fits num_ctx.
KEPT_TAIL_TOKENS = 1027


def norm(text: str) -> str:
    return " ".join((text or "").casefold().split())


def answer_in(text: str, question: dict) -> bool:
    haystack = norm(text)
    answers = question.get("acceptable_answers") or [question["reference_answer"]]
    return any(norm(a) and norm(a) in haystack for a in answers)


def grouped(scores: dict, questions: dict, ids: list[str], field: str) -> dict:
    out = {}
    for value in sorted({questions[q][field] for q in ids}):
        group = [q for q in ids if questions[q][field] == value]
        out[value] = {
            "n": len(group),
            "means": {s: {d: round(mean(scores[(q, s)][d] for q in group), 6) for d in SCORES + ("unsupported_claim",)} for s in SYSTEMS},
            "correctness_diffs": {
                f"{t}_vs_{c}": describe([scores[(q, t)]["correctness"] - scores[(q, c)]["correctness"] for q in group])
                for t, c in PAIRS[:2]
            },
        }
    return out


def sent_context(frozen_row: dict, question: dict) -> str:
    """The evidence the rerun sent: frozen context trimmed to the shared evidence budget."""
    budget = _evidence_budget(SYSTEM_PROMPT, question["question"], EVIDENCE, OPTIONS)
    return trim_to_tokens(frozen_row["context"], budget)


def evidence_availability(scores: dict, questions: dict, ids: list[str], frozen: dict) -> dict:
    items = []
    for q in ids:
        question = questions[q]
        v_ctx = sent_context(frozen[(q, "vanilla_dense_rag")], question)
        a_row = frozen[(q, "relation_aware_kg_rag")]
        items.append({
            "question_id": q,
            "answer_in_v_context": answer_in(v_ctx, question),
            "answer_in_a_context": answer_in(sent_context(a_row, question), question),
            "required_path_found": str(a_row.get("required_path_found")) == "True",
            "a_minus_v_correctness": scores[(q, "A_CURRENT")]["correctness"] - scores[(q, "V_VANILLA")]["correctness"],
        })
    table = {}
    for flag in (True, False):
        group = [i for i in items if i["answer_in_v_context"] is flag]
        table[f"answer_in_v_context={flag}"] = describe([i["a_minus_v_correctness"] for i in group]) if group else {"n": 0}
    return {
        "counts": {
            "answer_in_v_context": sum(i["answer_in_v_context"] for i in items),
            "answer_in_a_context": sum(i["answer_in_a_context"] for i in items),
            "required_path_found": sum(i["required_path_found"] for i in items),
            "n": len(items),
        },
        "a_minus_v_by_answer_in_v_context": table,
        "items": items,
    }


def outcome_class(answer: str, correctness: float) -> str:
    if is_idk(answer):
        return "abstained"
    if correctness >= 4:
        return "correct"
    if correctness >= 3:
        return "partial"
    return "wrong"


def outcome_types(scores: dict, answers: dict, ids: list[str], questions: dict) -> dict:
    classes = {s: {} for s in SYSTEMS}
    for s in SYSTEMS:
        for q in ids:
            cls = outcome_class(answers[(q, s)], scores[(q, s)]["correctness"])
            classes[s].setdefault(cls, []).append(q)
    summary = {
        s: {
            cls: {"n": len(qs), "unsupported_rate": round(mean(scores[(q, s)]["unsupported_claim"] for q in qs), 6)}
            for cls, qs in sorted(groups.items())
        }
        for s, groups in classes.items()
    }
    examples = {}
    for t, c in PAIRS:
        diffs = {q: scores[(q, t)]["correctness"] - scores[(q, c)]["correctness"] for q in ids}
        for cell, test in (("win", lambda d: d > 0), ("loss", lambda d: d < 0)):
            chosen = sorted(q for q, d in diffs.items() if test(d))
            if chosen:
                q = chosen[0]
                examples[f"{t}_vs_{c}:{cell}"] = {
                    "question_id": q,
                    "question": questions[q]["question"],
                    "reference": questions[q]["reference_answer"],
                    t: {"answer": answers[(q, t)], "correctness": scores[(q, t)]["correctness"]},
                    c: {"answer": answers[(q, c)], "correctness": scores[(q, c)]["correctness"]},
                }
    return {"summary": summary, "examples": examples}


def truncation(frozen: dict, questions: dict, ids: list[str]) -> dict:
    tokenizer = _tokenizer()
    num_ctx = OPTIONS["num_ctx"]
    out = {}
    for system in ("vanilla_dense_rag", "relation_aware_kg_rag"):
        rows = []
        for q in ids:
            user = frozen[(q, system)]["final_prompt"]
            total = prompt_tokens(SYSTEM_PROMPT, user)
            truncated = total >= num_ctx
            lost = total - KEPT_TAIL_TOKENS if truncated else 0
            row = {"question_id": q, "prompt_tokens": total, "truncated": truncated, "tokens_lost": lost,
                   "answer_in_full_context": answer_in(frozen[(q, system)]["context"], questions[q])}
            # Same templated text that prompt_tokens counts; the server keeps its tail.
            token_ids = tokenizer.encode(f"[INST] {SYSTEM_PROMPT} {user} [/INST]", add_special_tokens=False).ids
            kept_text = tokenizer.decode(token_ids[-KEPT_TAIL_TOKENS:]) if truncated else user
            row["answer_in_kept_tail"] = answer_in(kept_text, questions[q])
            if system == "relation_aware_kg_rag" and DENSE_MARKER in user:
                kg_start = prompt_tokens(SYSTEM_PROMPT, "CONTEXT:\n")
                kg_tokens = prompt_tokens(SYSTEM_PROMPT, user[: user.index(DENSE_MARKER)]) - kg_start
                row["kg_section_tokens"] = kg_tokens
                kg_lost = min(max(lost - kg_start, 0), kg_tokens)
                row["kg_fraction_lost"] = round(kg_lost / kg_tokens, 6) if kg_tokens else 0.0
            rows.append(row)
        tr = [r for r in rows if r["truncated"]]
        summary = {
            "n": len(rows),
            "truncated": len(tr),
            "median_prompt_tokens": median(r["prompt_tokens"] for r in rows),
            "max_prompt_tokens": max(r["prompt_tokens"] for r in rows),
            "median_tokens_lost_when_truncated": median(r["tokens_lost"] for r in tr) if tr else 0,
            "answer_in_full_context": sum(r["answer_in_full_context"] for r in rows),
            "answer_in_kept_tail": sum(r["answer_in_kept_tail"] for r in rows),
        }
        kg = [r for r in rows if "kg_fraction_lost" in r]
        if kg:
            summary["kg_section_fully_lost"] = sum(r["kg_fraction_lost"] >= 1 for r in kg)
            summary["kg_section_partly_lost"] = sum(0 < r["kg_fraction_lost"] < 1 for r in kg)
            summary["median_kg_fraction_lost"] = median(r["kg_fraction_lost"] for r in kg)
        out[system] = {"summary": summary, "items": rows}
    return {"rule": f"prompt_tokens >= {num_ctx} -> keep last {KEPT_TAIL_TOKENS} tokens", **out}


def cost(rows: list[dict]) -> dict:
    out = {}
    for s in SYSTEMS:
        sel = [r for r in rows if r["system"] == s]
        calls = [[r["generation_telemetry"]["plan"], r["generation_telemetry"]["final"]] if "final" in r["generation_telemetry"] else [r["generation_telemetry"]] for r in sel]
        out[s] = {
            "model_calls": sum(len(c) for c in calls),
            "median_prompt_tokens": median(max(x["prompt_tokens"] for x in c) for c in calls),
            "max_prompt_tokens": max(x["prompt_tokens"] for c in calls for x in c),
            "median_generated_tokens": median(sum(x["generated_tokens"] or 0 for x in c) for c in calls),
            "median_latency_s": round(median(r["elapsed_ms"] for r in sel) / 1000, 3),
            "max_latency_s": round(max(r["elapsed_ms"] for r in sel) / 1000, 3),
        }
    return out


def agreement_detail() -> dict:
    spot = {k: json.loads(p.read_text(encoding="utf8")) for k, p in SPOTCHECKS.items()}
    pairs = {f"rater1-{k}": v["krippendorff_alpha"] for k, v in spot.items()}
    pairs["checker1-checker2"] = spot["checker2"]["agreement_with_other_checker"]["krippendorff_alpha"]
    others = spot["checker3"]["agreement_with_other_checkers"]
    pairs["checker1-checker3"] = others["corrected_rerun_spotcheck_filled.csv"]["krippendorff_alpha"]
    pairs["checker2-checker3"] = others["corrected_rerun_spotcheck2_filled.csv"]["krippendorff_alpha"]
    return {"pairwise_alpha": pairs, "pooled_checkers_alpha": spot["checker3"]["pooled_alpha_all_checkers"]}


def main() -> None:
    questions = {q["question_id"]: q for q in json.loads(BENCHMARK.read_text(encoding="utf8"))["questions"]}
    ids = analysis_sets(list(questions.values()))["primary_kg_required"]
    ratings, _ = load_ratings()
    scores = item_scores(ratings)
    rows = load_jsonl(RESULTS)
    answers = {(r["question_id"], r["system"]): r["answer"] for r in rows}
    frozen = {(r["question_id"], r["system"]): r for r in load_jsonl(FROZEN_GENERATIONS)}
    result = {
        "preregistration": "reports/preregistration_corrected_rerun.md §19 (post hoc, exploratory)",
        "scores": "rater 1 (AI-drafted, human-reviewed)",
        "by_category": grouped(scores, questions, ids, "category"),
        "by_mission": grouped(scores, questions, ids, "mission"),
        "evidence_availability": evidence_availability(scores, questions, ids, frozen),
        "outcome_types": outcome_types(scores, answers, ids, questions),
        "truncation_in_frozen_run": truncation(frozen, questions, ids),
        "cost": cost(rows),
        "agreement_detail": agreement_detail(),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
