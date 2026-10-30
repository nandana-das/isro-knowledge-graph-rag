"""Extract a generator's tokenizer from its Ollama GGUF blob.

The committed tokenizers under ``config/tokenizer/`` were produced by this
script; rerun it only if an Ollama model changes. Requires ``gguf``.

    python -m src.generator.extract_tokenizer
    python -m src.generator.extract_tokenizer --model llama3.1:8b-instruct-q4_K_M --out config/tokenizer/llama3.1-8b-instruct-q4_K_M
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.generator.ollama_api import MODEL_NAME
from src.generator.token_budget import TOKENIZER_PATH

OLLAMA_MODELS = Path.home() / ".ollama" / "models"
# The GGUF conversion gives Llama 3 tokenizers GPT-2's pre-tokenizer regex,
# which overcounts tokens. Llama 3's own split pattern makes counts match Ollama.
LLAMA3_PRE_TOKENIZER = {
    "type": "Sequence",
    "pretokenizers": [
        {
            "type": "Split",
            "pattern": {"Regex": r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"},
            "behavior": "Isolated",
            "invert": False,
        },
        {"type": "ByteLevel", "add_prefix_space": False, "trim_offsets": True, "use_regex": False},
    ],
}


def model_blob(model: str = MODEL_NAME) -> Path:
    name, tag = model.split(":", 1)
    manifest = OLLAMA_MODELS / "manifests" / "registry.ollama.ai" / "library" / name / tag
    layers = json.loads(manifest.read_text(encoding="utf8"))["layers"]
    digest = next(layer["digest"] for layer in layers if layer["mediaType"].endswith(".model"))
    return OLLAMA_MODELS / "blobs" / digest.replace(":", "-")


def main(model: str = MODEL_NAME, out: Path = TOKENIZER_PATH.parent) -> None:
    from transformers import AutoTokenizer

    blob = model_blob(model)
    tokenizer = AutoTokenizer.from_pretrained(str(blob.parent), gguf_file=blob.name)
    tokenizer.save_pretrained(str(out))
    if model.startswith("llama3"):
        path = out / "tokenizer.json"
        spec = json.loads(path.read_text(encoding="utf8"))
        spec["pre_tokenizer"] = LLAMA3_PRE_TOKENIZER
        path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf8")
    print(f"saved {out} from {blob.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=MODEL_NAME)
    parser.add_argument("--out", type=Path, default=TOKENIZER_PATH.parent)
    args = parser.parse_args()
    main(args.model, args.out)
