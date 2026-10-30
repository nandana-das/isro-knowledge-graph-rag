"""Pre-registered analysis of Study 2 (reports/preregistration_study2_generators.md §4-§7, §10).

Import each returned workbook first:

    python -m src.evaluation.analyze_generator_study --import path/to/rater_workbook.xlsx --rater 1
    python -m src.evaluation.analyze_generator_study
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean

from src.evaluation.analyze_corrected_rerun import (
    SCORES, analysis_sets, describe, holm, item_scores, krippendorff_alpha, load_ratings, mcnemar_p, wilcoxon_p,
)
from src.evaluation.build_corrected_rerun_human_package import ANNOTATIONS, BENCHMARK, answer_hash
from src.evaluation.build_study2_rating_package import BLANK, DIMENSIONS, LABELS, MAPPING
from src.evaluation.run_generator_study import GENERATORS, OUTPUT

RATERS = (1, 2, 3)
ALPHA = 0.05
RELIABILITY_THRESHOLD = 0.667
RELIABILITY_FLOOR = 0.40
OUTPUT_JSON = OUTPUT / "analysis.json"
OUTPUT_MD = OUTPUT / "analysis.md"


def rater_file(index: int) -> Path:
    return ANNOTATIONS / f"study2_rater{index}_filled.csv"


def load_rater(path: Path, mapping: dict) -> dict[tuple[str, str, str], dict[str, int]]:
    """Scores keyed by (question_id, generator, system); every answer checked against the package hash."""
    rows = list(csv.DictReader(path.open(encoding="utf8")))
    if sorted(r["question_id"] for r in rows) != sorted(mapping):
        raise RuntimeError(f"{path.name}: question set does not match the package")
    scores = {}
    for row in rows:
        entry = mapping[row["question_id"]]
        for label in LABELS:
            if answer_hash(row[f"candidate_{label}"]) != entry["label_hashes"][label]:
                raise RuntimeError(f"{path.name}: candidate hash mismatch {row['question_id']} {label}")
            cand = entry["label_to_candidate"][label]
            cell = {}
            for dimension in DIMENSIONS:
                raw = row[f"{label}_{dimension}"].strip()
                value = int(float(raw)) if raw and float(raw).is_integer() else None
                allowed = (0, 1) if dimension == "unsupported_claim" else (1, 2, 3, 4, 5)
                if value not in allowed:
                    raise RuntimeError(f"{path.name}: invalid {dimension}={raw!r} for {row['question_id']} {label}")
                cell[dimension] = value
            scores[(row["question_id"], cand["generator"], cand["system"])] = cell
    return scores


def combine(raters: list[dict]) -> dict:
    """Per item: rater mean on 1-5 scales; unsupported = 1 if a majority of raters flag it."""
    keys = raters[0].keys()
    return {
        key: {**{d: mean(r[key][d] for r in raters) for d in SCORES},
              "unsupported_claim": int(sum(r[key]["unsupported_claim"] for r in raters) * 2 > len(raters))}
        for key in keys
    }


def reliability(raters: list[dict]) -> dict:
    keys = sorted(raters[0])
    return {
        d: krippendorff_alpha([[r[k][d] for r in raters] for k in keys], "nominal" if d == "unsupported_claim" else "ordinal")
        for d in DIMENSIONS
    }


def compare(scores: dict, ids: list[str], generator: str, dimension: str) -> dict:
    a = [scores[(q, generator, "A_CURRENT")][dimension] for q in ids]
    v = [scores[(q, generator, "V_VANILLA")][dimension] for q in ids]
    if dimension == "unsupported_claim":
        p, worse, better = mcnemar_p(a, v)
        return {"rate_A": round(mean(a), 6), "rate_V": round(mean(v), 6), "rate_diff": round(mean(a) - mean(v), 6),
                "mcnemar_p": p, "A_worse": worse, "A_better": better}
    diffs = [x - y for x, y in zip(a, v)]
    return {**describe(diffs), "wilcoxon_p": wilcoxon_p(diffs)}


def decision(primary: dict, unsupported: dict) -> str:
    if primary["holm_p"] < ALPHA and primary["mean_diff"] > 0:
        if unsupported["rate_diff"] > 0 and unsupported["mcnemar_p"] < ALPHA:
            return "NOT SUPPORTED (unsupported claims significantly higher)"
        return "SUPPORTED"
    if primary["holm_p"] < ALPHA and primary["mean_diff"] < 0:
        return "HARMFUL"
    return "NOT SUPPORTED"


def analyze(raters: list[dict], questions: list[dict]) -> dict:
    sets = analysis_sets(questions)
    primary_ids = sets["primary_kg_required"]
    compositional = [q["question_id"] for q in questions if q["kg_required"] == "YES" and q["category"] in ("TWO_HOP_RELATION", "MULTI_RELATION")]
    scores = combine(raters)
    alpha = reliability(raters)

    primary = {g: compare(scores, primary_ids, g, "correctness") for g in GENERATORS}
    for g, p in holm({g: r["wilcoxon_p"] for g, r in primary.items()}).items():
        primary[g]["holm_p"] = p
    unsupported = {g: compare(scores, primary_ids, g, "unsupported_claim") for g in GENERATORS}
    decisions = {g: decision(primary[g], unsupported[g]) for g in GENERATORS}
    qualifier = None if alpha["correctness"] is not None and alpha["correctness"] >= RELIABILITY_THRESHOLD else "low inter-rater reliability"
    claimable = alpha["correctness"] is not None and alpha["correctness"] >= RELIABILITY_FLOOR

    h4 = {g: compare(scores, compositional, g, "correctness") for g in GENERATORS}
    for g, p in holm({g: r["wilcoxon_p"] for g, r in h4.items()}).items():
        h4[g]["holm_p"] = p

    secondary = {f"{g}:{d}": compare(scores, primary_ids, g, d) for g in GENERATORS for d in ("completeness", "groundedness", "relevance")}
    secondary.update({f"{g}:unsupported_claim": unsupported[g] for g in GENERATORS})
    pvals = {k: v.get("wilcoxon_p", v.get("mcnemar_p")) for k, v in secondary.items()}
    for k, p in holm(pvals).items():
        secondary[k]["holm_p_within_secondary"] = p

    means = {
        g: {s: {d: round(mean(scores[(q, g, s)][d] for q in primary_ids), 6) for d in SCORES + ("unsupported_claim",)}
            for s in ("V_VANILLA", "A_CURRENT")}
        for g in GENERATORS
    }
    sensitivity = {
        name: {g: describe([scores[(q, g, "A_CURRENT")]["correctness"] - scores[(q, g, "V_VANILLA")]["correctness"] for q in sets[name]])
               for g in GENERATORS}
        for name in ("sensitivity_deduplicated", "sensitivity_excluding_direct_control")
    }
    screen = {
        f"rater{i}": {d: {str(v): sum(r[k][d] == v for k in r) for v in sorted({r[k][d] for k in r})} for d in DIMENSIONS}
        for i, r in enumerate(raters, 1)
    }
    return {
        "preregistration": "reports/preregistration_study2_generators.md",
        "raters": len(raters),
        "set_sizes": {"primary": len(primary_ids), "compositional": len(compositional)},
        "krippendorff_alpha": alpha,
        "reliability_qualifier": qualifier,
        "supported_claimable_in_abstract": claimable,
        "means_primary": means,
        "primary_correctness_A_vs_V": primary,
        "decisions": decisions,
        "h4_compositional_correctness_A_vs_V": h4,
        "secondary_exploratory": secondary,
        "sensitivity_described": sensitivity,
        "rater_score_distributions": screen,
    }


def study1_comparison(scores: dict, questions: list[dict]) -> dict:
    """§10: Study 1 rater-1 vs Study 2 rater mean on Mistral's 120 answers (descriptive)."""
    ratings, _ = load_ratings()
    study1 = item_scores(ratings)
    ids = analysis_sets(questions)["primary_kg_required"]
    keys = [(q, s) for q in ids for s in ("V_VANILLA", "A_CURRENT")]
    return {
        "alpha_correctness_study1_vs_study2_mean": krippendorff_alpha(
            [[study1[k]["correctness"], scores[(k[0], "mistral", k[1])]["correctness"]] for k in keys], "interval"),
        "a_minus_v_study1": describe([study1[(q, "A_CURRENT")]["correctness"] - study1[(q, "V_VANILLA")]["correctness"] for q in ids]),
        "a_minus_v_study2": describe([scores[(q, "mistral", "A_CURRENT")]["correctness"] - scores[(q, "mistral", "V_VANILLA")]["correctness"] for q in ids]),
        "note": "Interval alpha because Study 2 item scores are means of three raters.",
    }


def write_markdown(result: dict) -> None:
    lines = [
        "# Study 2 analysis (pre-registered)", "",
        f"Raters: {result['raters']}. Krippendorff's alpha: "
        + ", ".join(f"{d} {v:.3f}" if v is not None else f"{d} n/a" for d, v in result["krippendorff_alpha"].items()),
        f"Reliability qualifier: {result['reliability_qualifier'] or 'none'}", "",
        "## Primary: correctness, A vs V, 60 KG-required items (Holm over 3 generators)", "",
        "| Generator | Mean diff | 95% CI | dz | W/L/T | Wilcoxon p | Holm p | Decision |", "|---|---|---|---|---|---|---|---|",
    ]
    for g, r in result["primary_correctness_A_vs_V"].items():
        lines.append(f"| {g} | {r['mean_diff']:+.3f} | [{r['ci95'][0]:.3f}, {r['ci95'][1]:.3f}] | {r['dz']} | "
                     f"{'/'.join(map(str, r['wins_losses_ties']))} | {r['wilcoxon_p']:.4f} | {r['holm_p']:.4f} | {result['decisions'][g]} |")
    lines += ["", "## H4: compositional items (Holm over 3)", "", "| Generator | Mean diff | 95% CI | Holm p |", "|---|---|---|---|"]
    for g, r in result["h4_compositional_correctness_A_vs_V"].items():
        lines.append(f"| {g} | {r['mean_diff']:+.3f} | [{r['ci95'][0]:.3f}, {r['ci95'][1]:.3f}] | {r['holm_p']:.4f} |")
    lines += ["", "Secondary, sensitivity and Study 1 comparison: see analysis.json.", ""]
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf8")


def main() -> None:
    mapping = json.loads(MAPPING.read_text(encoding="utf8"))["mapping"]
    questions = json.loads(BENCHMARK.read_text(encoding="utf8"))["questions"]
    missing = [i for i in RATERS if not rater_file(i).exists()]
    if missing:
        raise RuntimeError(f"Rater files missing: {[rater_file(i).name for i in missing]}")
    raters = [load_rater(rater_file(i), mapping) for i in RATERS]
    result = analyze(raters, questions)
    result["study1_comparison"] = study1_comparison(combine(raters), questions)
    OUTPUT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    write_markdown(result)
    print(OUTPUT_MD.read_text(encoding="utf8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--import", dest="workbook", type=Path, help="Returned workbook (.xlsx or CSV export) to import")
    parser.add_argument("--rater", type=int, choices=RATERS)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.workbook:
        from src.evaluation.import_spotcheck_workbook import main as import_workbook

        if not args.rater:
            parser.error("--rater is required with --import")
        import_workbook(args.workbook, args.force, rater_file(args.rater), BLANK, LABELS)
    else:
        main()
