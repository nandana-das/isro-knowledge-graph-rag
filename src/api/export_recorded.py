"""Record live answers for the example questions, for the hosted website.

Runs the live pipeline (system A) on every /api/examples question and writes
kgrag-web/public/recorded_answers.json. The website serves these instantly,
labelled as recorded, even while the live API is offline. Needs Ollama and
the local index, like live mode.

    python -m src.api.export_recorded
"""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from src.api.app import _examples
from src.api.pipeline import GenerationUnavailable, LivePipeline
from src.generator.ollama_api import MODEL_NAME

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "kgrag-web" / "public" / "recorded_answers.json"
PASSAGE_CHARS = 1200  # passages can be ~16k characters; keep the download small


def norm(text: str) -> str:
    return " ".join(text.casefold().split())


def main() -> None:
    pipeline = LivePipeline()
    pipeline.warm_up()
    if pipeline.status != "ready":
        raise RuntimeError(f"Live pipeline not ready: {pipeline.detail}")
    examples = _examples()
    answers = {}
    for number, example in enumerate(examples, 1):
        started = time.perf_counter()
        for attempt in range(3):
            try:
                response = pipeline.answer(example.question).model_dump()
                break
            except GenerationUnavailable as exc:
                # Ollama's runner can crash on a GPU/driver error; it restarts on the next request.
                if attempt == 2:
                    raise
                print(f"   retrying after: {exc}", flush=True)
                time.sleep(10)
        response["mode"] = "recorded"
        for passage in response["passages"]:
            if len(passage["text"]) > PASSAGE_CHARS:
                passage["text"] = passage["text"][:PASSAGE_CHARS].rstrip() + " …"
        answers[norm(example.question)] = response
        print(f"{number}/{len(examples)} {time.perf_counter() - started:.0f}s {example.question}", flush=True)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": MODEL_NAME,
        "code_commit": commit,
        "examples": [e.model_dump() for e in examples],
        "answers": answers,
    }, ensure_ascii=False) + "\n", encoding="utf8")
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
