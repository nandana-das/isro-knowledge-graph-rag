"""Study 2: V vs A across three generators (reports/preregistration_study2_generators.md).

Every generator receives exactly the evidence text Mistral received in the
corrected rerun, so only the generator changes. Mistral's answers are taken
unchanged from the corrected rerun; Llama 3.1 and Qwen 2.5 are generated once.

    python -m src.evaluation.run_generator_study --build-evidence   # Mistral tokenizer; writes evidence.jsonl
    python -m src.evaluation.run_generator_study --dry-run          # fit every prompt, no model calls
    python -m src.evaluation.run_generator_study                    # import Mistral, generate the others

Refuses to generate unless the Study 2 pre-registration is approved and committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREREGISTRATION = ROOT / "reports" / "preregistration_study2_generators.md"
OUTPUT = ROOT / "data" / "results" / "study2_generators"
EVIDENCE_FILE = OUTPUT / "evidence.jsonl"
STUDY1_RESULTS = ROOT / "data" / "results" / "corrected_rerun" / "generation_results.jsonl"
STUDY1_SHA256 = "2d9b6f4799bbd003f5c9277d25d8072724ceddbffcdf3f9522e78cd98986d3b5"
SYSTEMS = ("V_VANILLA", "A_CURRENT")
FROZEN_SYSTEM = {"V_VANILLA": "vanilla_dense_rag", "A_CURRENT": "relation_aware_kg_rag"}
GENERATORS = {
    "mistral": {"model": "mistral:7b-instruct-q4_K_M", "tokenizer": "mistral-7b-instruct-q4_K_M", "template": "mistral"},
    "llama3.1": {"model": "llama3.1:8b-instruct-q4_K_M", "tokenizer": "llama3.1-8b-instruct-q4_K_M", "template": "llama3"},
    "qwen2.5": {"model": "qwen2.5:7b-instruct-q4_K_M", "tokenizer": "qwen2.5-7b-instruct-q4_K_M", "template": "qwen2"},
}
GENERATED = ("llama3.1", "qwen2.5")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()


def results_path(generator: str) -> Path:
    return OUTPUT / f"generation_results_{generator}.jsonl"


def generator_env(generator: str) -> dict[str, str]:
    spec = GENERATORS[generator]
    return {
        **os.environ,
        "KG_RAG_MODEL": spec["model"],
        "KG_RAG_TOKENIZER": str(ROOT / "config" / "tokenizer" / spec["tokenizer"] / "tokenizer.json"),
        "KG_RAG_TEMPLATE": spec["template"],
    }


def check_preregistration() -> str:
    text = PREREGISTRATION.read_text(encoding="utf8")
    if "DRAFT, awaiting approval" in text:
        raise RuntimeError("Study 2 pre-registration is still a draft; approve and commit it first")
    if git("status", "--porcelain", "--", str(PREREGISTRATION.relative_to(ROOT))):
        raise RuntimeError("Study 2 pre-registration has uncommitted changes")
    if git("status", "--porcelain", "--untracked-files=no", "--", "src", "config"):
        raise RuntimeError("Source code or tokenizers have uncommitted changes; commit before generating")
    return git("log", "-1", "--format=%H", "--", str(PREREGISTRATION.relative_to(ROOT)))


def build_evidence() -> None:
    """Write the exact evidence text Mistral received in the corrected rerun."""
    from src.config.runtime import DEFAULT_GENERATION_OPTIONS as OPTIONS
    from src.evaluation.run_corrected_rerun import check_inputs, load_inputs
    from src.generator.kg_grounded_generator import _evidence_budget
    from src.generator.prompt import SYSTEM_PROMPT
    from src.generator.token_budget import EVIDENCE, TEMPLATE_NAME, trim_to_tokens

    if TEMPLATE_NAME != "mistral":
        raise RuntimeError("Build the evidence with the default (Mistral) tokenizer")
    check_inputs()
    questions, frozen = load_inputs()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with EVIDENCE_FILE.open("w", encoding="utf8", newline="\n") as handle:
        for q in questions:
            budget = _evidence_budget(SYSTEM_PROMPT, q["question"], EVIDENCE, OPTIONS)
            for system in SYSTEMS:
                text = trim_to_tokens(frozen[(q["question_id"], FROZEN_SYSTEM[system])]["context"], budget)
                handle.write(json.dumps({"question_id": q["question_id"], "system": system, "evidence": text,
                                         "sha256": hashlib.sha256(text.encode("utf8")).hexdigest()}, ensure_ascii=False) + "\n")
    print(f"wrote {EVIDENCE_FILE} ({sha256(EVIDENCE_FILE)})")


def load_evidence() -> dict[tuple[str, str], str]:
    rows = [json.loads(line) for line in EVIDENCE_FILE.read_text(encoding="utf8").splitlines() if line.strip()]
    return {(r["question_id"], r["system"]): r["evidence"] for r in rows}


def import_mistral() -> None:
    """Copy Mistral's V and A answers unchanged from the corrected rerun."""
    if sha256(STUDY1_RESULTS) != STUDY1_SHA256:
        raise RuntimeError("Corrected-rerun results differ from the recorded hash")
    out = results_path("mistral")
    with out.open("w", encoding="utf8", newline="\n") as handle:
        for line in STUDY1_RESULTS.read_text(encoding="utf8").splitlines():
            row = json.loads(line)
            if row["system"] in SYSTEMS:
                handle.write(json.dumps({**row, "generator": "mistral", "source": "corrected_rerun"}, ensure_ascii=False) + "\n")
    print(f"imported {out}")


def worker(generator: str, dry_run: bool) -> None:
    """Generate one generator's rows; runs in a process whose env selects the model."""
    from src.evaluation.evaluate_relational_qa import metrics
    from src.evaluation.run_corrected_rerun import OPTIONS, load_inputs
    from src.generator import ollama_api
    from src.generator.prompt import SYSTEM_PROMPT, build_user_prompt
    from src.generator.token_budget import EVIDENCE, TEMPLATE_NAME, fit_evidence

    if TEMPLATE_NAME != GENERATORS[generator]["template"] or ollama_api.MODEL_NAME != GENERATORS[generator]["model"]:
        raise RuntimeError("Worker environment does not match the generator")
    questions, _ = load_inputs()
    evidence = load_evidence()
    if dry_run:
        fits = [fit_evidence(SYSTEM_PROMPT, build_user_prompt(EVIDENCE, q["question"]), evidence[(q["question_id"], s)], OPTIONS)[1]
                for q in questions for s in SYSTEMS]
        print(json.dumps({"generator": generator, "prompts": len(fits),
                          "max_prompt_tokens": max(f["prompt_tokens_expected"] for f in fits),
                          "trimmed_by_window_guard": sum(f["context_trimmed"] for f in fits)}))
        return
    out = results_path(generator)
    done = {(r["question_id"], r["system"]) for r in map(json.loads, out.read_text(encoding="utf8").splitlines())} if out.exists() else set()
    for q in questions:
        for system in SYSTEMS:
            if (q["question_id"], system) in done:
                continue
            started = time.perf_counter()
            answer, telemetry = ollama_api.generate_with_metrics(q["question"], evidence[(q["question_id"], system)], options=OPTIONS)
            retried = False
            if telemetry.get("status") != "ok":
                # Pre-registered: one retry for transport failures only.
                retried = True
                answer, telemetry = ollama_api.generate_with_metrics(q["question"], evidence[(q["question_id"], system)], options=OPTIONS)
            row = {
                "question_id": q["question_id"], "question": q["question"], "reference_answer": q["reference_answer"],
                "category": q["category"], "kg_required": q["kg_required"], "split": q["split"],
                "system": system, "generator": generator, "answer": answer,
                "metrics": metrics(answer, q["reference_answer"]),
                "integrity": {
                    "status_ok": telemetry.get("status") == "ok",
                    "prompt_count_match": telemetry.get("prompt_tokens") == telemetry.get("prompt_tokens_expected"),
                    "ollama_truncated": bool(telemetry.get("ollama_truncated")),
                    "context_trimmed": bool(telemetry.get("context_trimmed")),
                    "retried": retried,
                },
                "generation_configuration": OPTIONS, "generation_telemetry": telemetry,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }
            with out.open("a", encoding="utf8", newline="\n") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"{generator} {q['question_id']} {system} ok={row['integrity']}", flush=True)


def run(dry_run: bool) -> None:
    if not dry_run:
        prereg_commit = check_preregistration()
        import_mistral()
    for generator in GENERATED:
        cmd = [sys.executable, "-m", "src.evaluation.run_generator_study", "--worker", generator] + (["--dry-run"] if dry_run else [])
        subprocess.run(cmd, cwd=ROOT, env=generator_env(generator), check=True)
    if dry_run:
        return
    manifest = {
        "preregistration": str(PREREGISTRATION.relative_to(ROOT)),
        "preregistration_commit": prereg_commit,
        "preregistration_sha256": sha256(PREREGISTRATION),
        "code_commit": git("rev-parse", "HEAD"),
        "evidence_sha256": sha256(EVIDENCE_FILE),
        "results_sha256": {g: sha256(results_path(g)) for g in GENERATORS},
        "generators": GENERATORS,
        "ollama_version": subprocess.run(["ollama", "--version"], capture_output=True, text=True).stdout.strip(),
        "python": sys.version,
        "platform": platform.platform(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUTPUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-evidence", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--worker", choices=GENERATED)
    args = parser.parse_args()
    if args.build_evidence:
        build_evidence()
    elif args.worker:
        worker(args.worker, args.dry_run)
    else:
        run(args.dry_run)
