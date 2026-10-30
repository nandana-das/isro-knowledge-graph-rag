"""Check that local prompt-token counts match Ollama's for the active generator.

Sends a few probe prompts (one output token, a window large enough that
nothing is truncated) and compares ``prompt_eval_count`` with
``prompt_tokens``. The constant difference is the template overhead to set in
``token_budget.TEMPLATES``.

    set KG_RAG_MODEL=... & set KG_RAG_TOKENIZER=... & set KG_RAG_TEMPLATE=...
    python -m src.generator.calibrate_template
"""

from __future__ import annotations

import json

import requests

from src.config.runtime import CANONICAL_BENCHMARK_PATH as BENCHMARK
from src.config.runtime import ROOT
from src.generator.ollama_api import MODEL_NAME, OLLAMA_URL
from src.generator.prompt import SYSTEM_PROMPT, build_user_prompt
from src.generator.token_budget import TEMPLATE_NAME, TEMPLATE_OVERHEAD, prompt_tokens

PROBES = (
    ("Which vehicle launched AstroSat?", "AstroSat was launched by PSLV-C30 (XL) on 28 September 2015."),
    ("What does ASPEX study?", "ASPEX is an Aditya-L1 payload.\n\nIt studies the solar wind: protons, alpha particles and heavier ions."),
    ("Who developed SUIT?", "SUIT — Solar Ultraviolet Imaging Telescope — was developed by IUCAA, Pune (India) {braces} 100%."),
)


def study_probes(per_system: int = 3) -> list[tuple[str, str]]:
    """The longest real Study 2 evidence texts, if the evidence file exists."""
    path = ROOT / "data" / "results" / "study2_generators" / "evidence.jsonl"
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip()]
    questions = {q["question_id"]: q["question"] for q in json.loads(BENCHMARK.read_text(encoding="utf8"))["questions"]}
    probes = []
    for system in ("V_VANILLA", "A_CURRENT"):
        longest = sorted((r for r in rows if r["system"] == system), key=lambda r: -len(r["evidence"]))[:per_system]
        probes += [(questions[r["question_id"]], r["evidence"]) for r in longest]
    return probes


def main() -> None:
    rows = []
    for question, context in PROBES + tuple(study_probes()):
        user = build_user_prompt(context, question)
        payload = {
            "model": MODEL_NAME, "system": SYSTEM_PROMPT, "prompt": user, "stream": False,
            "options": {"num_ctx": 4096, "num_predict": 1, "temperature": 0},
        }
        observed = requests.post(OLLAMA_URL, json=payload, timeout=(5, 300)).json()["prompt_eval_count"]
        expected = prompt_tokens(SYSTEM_PROMPT, user)
        rows.append({"expected": expected, "observed": observed, "difference": observed - expected})
    print(json.dumps({"model": MODEL_NAME, "template": TEMPLATE_NAME, "overhead": TEMPLATE_OVERHEAD, "probes": rows}, indent=2))


if __name__ == "__main__":
    main()
