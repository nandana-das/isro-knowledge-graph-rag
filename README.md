# KG-RAG: Knowledge Graph-Augmented Retrieval-Augmented Generation for ISRO Domain Question Answering

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Backend](https://img.shields.io/badge/Backend-Complete-brightgreen)
![Frontend](https://img.shields.io/badge/Frontend-Pending-orange)

> A local ISRO-domain QA system that combines a domain knowledge graph with FAISS passage retrieval and Ollama-based generation. This repository currently implements the backend pipeline and the canonical benchmark evaluation protocol.

The project builds a knowledge graph from ISRO documents, retrieves evidence from both the graph and the vector index, and evaluates the outputs on a deterministic 20-dev / 180-test split. The current canonical metrics are lexical metrics: ROUGE-L, reference-token coverage, exact match, and IDK rate. No RAGAS evaluation is currently executed in the official benchmark pipeline.

---

## Research framing

Knowledge-graph augmentation provides targeted retrieval benefits for relational and temporal ISRO questions under local inference constraints.

This project is developed as part of the **ISRO Bharatiya Antariksh Hackathon 2025 (BAH-02)** and serves as the Capstone Project for the M.Tech in Artificial Intelligence and Data Science programme at Alliance School of Advanced Computing, Alliance University (2025–2027).

---

## Canonical benchmark protocol

The repository uses a fixed, deterministic split over the 200-question ISRO benchmark:

- total benchmark: 200 questions
- development set: 20 questions
- test set: 180 questions
- evaluation: only the 180-question test set is used for final benchmark reporting
- dev/test overlap: none
- split: tier-aware and seeded for reproducibility

The authoritative result file is `data/results/evaluation_results.json`.

The canonical benchmark is frozen. The additional journal analyses below read
the saved per-question outputs and do not rerun generation or replace the
canonical result file.

---

## Local pipeline and configuration

The current benchmark pipeline runs locally with:

- model: `mistral:7b-instruct-q4_K_M`
- inference backend: Ollama local API
- embedding/index: FAISS retrieval on chunk embeddings
- knowledge graph: NetworkX graph built from extracted entities and relations
- canonical metrics: `rouge_l`, `reference_token_coverage`, `exact_match`, `idk_rate`

This is a lexical evaluation pipeline; it does not establish factual correctness in a human-judged sense. It measures answer overlap and question-level abstention, not semantic faithfulness or full factual verification.

---

## Current benchmark results

Results below are taken from the executed canonical evaluation on the 180-question test set.

| System | ROUGE-L | Reference-token coverage | Exact match | IDK rate |
|---|---:|---:|---:|---:|
| BM25 + LLM | 0.2915 | 0.4340 | 0.0278 | 0.0167 |
| Vanilla RAG | 0.2780 | 0.3989 | 0.0333 | 0.1222 |
| KG-RAG | 0.2736 | 0.3921 | 0.0333 | 0.1167 |

### Tier-wise results (180 questions total)

| System | Tier | N | ROUGE-L | Coverage | Exact match | IDK rate |
|---|---:|---:|---:|---:|---:|---:|
| BM25 + LLM | 1 | 90 | 0.3220 | 0.5199 | 0.0556 | 0.0333 |
| BM25 + LLM | 2 | 54 | 0.2587 | 0.3448 | 0.0000 | 0.0000 |
| BM25 + LLM | 3 | 36 | 0.2647 | 0.3532 | 0.0000 | 0.0000 |
| Vanilla RAG | 1 | 90 | 0.3222 | 0.4632 | 0.0667 | 0.1222 |
| Vanilla RAG | 2 | 54 | 0.2306 | 0.3213 | 0.0000 | 0.1111 |
| Vanilla RAG | 3 | 36 | 0.2387 | 0.3546 | 0.0000 | 0.1389 |
| KG-RAG | 1 | 90 | 0.3080 | 0.4381 | 0.0667 | 0.1556 |
| KG-RAG | 2 | 54 | 0.2246 | 0.3462 | 0.0000 | 0.0926 |
| KG-RAG | 3 | 36 | 0.2611 | 0.3456 | 0.0000 | 0.0556 |

These results do not show universal KG superiority. The evidence is tier- and metric-specific, and the project explicitly notes that lexical metrics do not establish factual correctness.

---

## Ablation experiment

The repository also contains a separate 50-question ablation experiment, reported separately from the main 180-question benchmark.

| System | N | ROUGE-L | Coverage | IDK rate |
|---|---:|---:|---:|---:|
| KG-only | 50 | 0.0927 | 0.1078 | 0.7600 |
| FAISS-only | 50 | 0.2830 | 0.4077 | 0.3400 |
| Full KG-RAG | 50 | 0.2952 | 0.4564 | 0.1000 |

This is a separate experiment and must not be mixed with the main benchmark results.

## Additional journal experiments

The reproducible experiment ledger is `data/results/q1_experiment_summary.json`.
Every experiment has a script under `src/evaluation/` and writes a separate
artifact under `data/results/`.

Executed from frozen outputs:

- paired bootstrap confidence intervals, Wilcoxon signed-rank tests, and paired effect sizes in `statistical_tests.json`
- complete Tier 1/2/3 paired analysis in `tier_statistical_tests.json`
- tier comparison data and `paper/figures/tier_comparison.png`
- a guarded retrieval-quality check that correctly reports no execution because chunk relevance judgments are not available
- a preserved report of the existing 50-question ablation plus explicit pending status for unsupported variants
- a partial, retrieval-only resource profile for three BM25 queries; dense retrieval attempted unavailable Hugging Face network access and LLM timing was not measured
- human-evaluation, KG-quality, and paraphrase annotation templates without fabricated ratings

Pending or not feasible:

- retrieval Recall@k/MRR requires manually verified relevance labels
- two-hop, alternate top-k, and expanded component ablations require additional generation runs
- KG precision, human evaluation, paraphrase robustness, and abstention robustness require manual annotation/verification

Run the full non-generative journal analysis package with:

```powershell
.venv\Scripts\python.exe src\evaluation\statistical_tests.py
.venv\Scripts\python.exe src\evaluation\tier_statistical_tests.py
.venv\Scripts\python.exe src\evaluation\tier_analysis.py
.venv\Scripts\python.exe src\evaluation\retrieval_quality.py
.venv\Scripts\python.exe src\evaluation\component_ablation.py
.venv\Scripts\python.exe src\evaluation\hop_ablation.py
.venv\Scripts\python.exe src\evaluation\topk_sensitivity.py
.venv\Scripts\python.exe src\evaluation\human_evaluation.py
.venv\Scripts\python.exe src\evaluation\kg_quality.py
.venv\Scripts\python.exe src\evaluation\abstention_evaluation.py
.venv\Scripts\python.exe src\evaluation\paraphrase_robustness.py
.venv\Scripts\python.exe src\evaluation\q1_summary.py
```

The resource profiler is intentionally partial and local-only:

```powershell
.venv\Scripts\python.exe src\evaluation\resource_profile.py --systems bm25_llm --questions-per-tier 1
```

No RAGAS result is included: it is not part of the executed evaluation path.

---

## System architecture

The backend implements the following pieces:

- document ingestion and chunking
- local knowledge-graph construction from ISRO text
- FAISS index construction and retrieval
- graph-based retrieval context extraction
- local generation via Ollama using `mistral:7b-instruct-q4_K_M`
- canonical evaluation pipeline over the 180-question test set

The current application in `app.py` loads the canonical file and displays benchmark values from `data/results/evaluation_results.json` instead of stale hard-coded numbers.

---

## Current implementation status

Implemented:

- backend QA pipeline
- deterministic split generation
- canonical evaluation over 180 test questions
- local Open-source model inference with Ollama
- KG + FAISS retrieval logic
- tests and benchmark verification

Pending or not in the current public app scope:

- full React frontend
- additional human factual evaluation
- a broader RAGAS-style factual benchmark
- large-scale corpus expansion beyond the current local dataset

---

## Data and artifacts

The canonical benchmark depends on the following local artifacts:

- `data/benchmark/isro_qa.json`
- `data/benchmark/dev_ids.json`
- `data/benchmark/test_ids.json`
- `data/chunks/chunks.json`
- `data/index/faiss_index.index`
- `data/kg/knowledge_graph.pkl` or the corresponding graph export
- local Ollama model `mistral:7b-instruct-q4_K_M`

These artifacts are required for reproduction of the official benchmark.

---

## Notes on evaluation

- `reference_token_coverage` is a lexical retrieval overlap metric, not a factual correctness score.
- Exact match is a strict lexical comparison after normalization.
- IDK rate reflects abstention or empty outputs.
- The benchmark is resource-constrained and local-only; this matters for claims about retrieval quality and system robustness.
- KG edge quality and retrieval quality vary by question type; gains are most relevant for relational and temporal queries.

---

## Repository status

The repository contains one authoritative result file: `data/results/evaluation_results.json`.

Historical or experimental outputs may remain, but they must be treated as historical artifacts rather than the final canonical benchmark.           # Context merging pipeline│   │   └── query.py            # CLI query entrypoint
│   │
│   ├── generator/
│   │   ├── prompt.py           # Prompt templates
│   │   └── ollama_api.py       # Ollama REST API integration
│   │
│   ├── baselines/
│   │   ├── bm25_llm.py         # BM25 + Mistral baseline
│   │   ├── vanilla_rag.py      # FAISS-only RAG baseline
│   │   ├── graphrag.py         # GraphRAG baseline
│   │   └── run_baselines.py    # Batch baseline runner
│   │
│   └── evaluation/
│       ├── evaluate.py         # ROUGE-L / coverage / exact-match scorer
│       ├── ablation.py         # Ablation study scripts
│       └── plot_results.py     # Result visualisation (matplotlib)
│
├── frontend/                   # ⚠ Placeholder — React UI not yet implemented
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatBox.jsx     # Placeholder
│   │   │   ├── QueryInput.jsx  # Placeholder
│   │   │   └── Answer.jsx      # Placeholder
│   │   ├── App.jsx             # Placeholder
│   │   └── index.jsx
│   └── package.json
│
├── notebooks/                  # ⚠ Placeholder — content not yet written
│   ├── kg_analysis.ipynb
│   ├── retrieval_analysis.ipynb
│   └── results_analysis.ipynb
│
├── paper/
│   ├── main.tex                # IEEE paper LaTeX source
│   ├── references.bib          # Bibliography (WIP)
│   └── figures/
│       ├── results_comparison.png
│       ├── ablation_results.png
│       └── idk_per_tier.png
│
├── tests/
│   ├── test_graph_directory.py
│   ├── test_indexer.py
│   ├── test_kg_builder.py
│   └── test_preprocessing.py
│
├── app.py                      # Minimal Flask/CLI app wrapper
├── app_v2.py                   # Extended app with streaming support
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.10+
- NVIDIA GPU with 4GB+ VRAM
- [Ollama](https://ollama.ai) installed and running
- Node.js 18+ (for frontend)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/KG-RAG-ISRO.git
cd KG-RAG-ISRO
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# Windows PowerShell
venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### 4. Pull Mistral model via Ollama

```bash
ollama pull mistral:7b-instruct-q4_K_M
```

### 5. Set up environment variables (optional for the HTTP fallback)

```bash
cp .env.example .env
# Add FIRECRAWL_API_KEY to .env to use Firecrawl scraping.
# Without a key, the scraper uses its local HTTP fallback.
```

### 6. Install frontend dependencies (once the React UI is implemented)

```bash
cd frontend
npm install
npm run dev
```

> **Note:** The frontend is not yet implemented. The `npm start` script is a placeholder.

---

## Usage

### Step 1 — Collect documents

```bash
python src/scraper/crawl.py
```

The crawler writes Markdown files to `data/raw/`. Use `python src/scraper/crawl.py --help`
to inspect crawl limits and seed options.

### Step 2 — Clean and chunk

```bash
python src/preprocessing/clean.py --input-dir data/raw --output-dir data/cleaned
python src/preprocessing/chunk.py --input-dir data/cleaned --output-dir data/chunks
```

The commands write cleaned documents to `data/cleaned/` and chunk JSON files to
`data/chunks/`.

### Step 3 — Build knowledge graph

```bash
python src/kg_builder/build_kg.py
```

### Step 4 — Build FAISS index

The retriever expects `data/index/faiss_index.index` and the matching
`data/chunks/chunks.json`. The indexer utilities encode the project chunks and write the
FAISS index. They can be invoked from Python as follows:

```python
from src.indexer.encode import encode_chunks
from src.indexer.build_index import build_faiss_index

vectors = encode_chunks("data/chunks")
build_faiss_index(vectors, "data/index")
```

### Step 5 — Run the QA system

```bash
python src/retriever/query.py --question "What is the primary payload of Chandrayaan-2?"
```

The query command expects the generated KG and FAISS index and a running local Ollama
model. It prints the generated answer to the terminal.

### Step 6 — Run all baselines

```bash
python src/baselines/run_baselines.py
```

Runs BM25 + LLM, Vanilla RAG, and GraphRAG baselines and writes results to
`data/results/baseline_results.json`.

### Step 7 — Evaluate the canonical benchmark

```bash
python src/evaluation/evaluate.py
```

Reads the benchmark and the canonical test split, then writes the authoritative metrics to
`data/results/evaluation_results.json`. The official evaluation reports ROUGE-L,
`reference_token_coverage`, exact match, and IDK rate on the 180-question test set.

### Step 8 — Run ablation study

```bash
python src/evaluation/ablation.py
```

### Step 9 — Plot results

```bash
python src/evaluation/plot_results.py
```

Generates comparison charts to `paper/figures/`.

### Step 10 — Run tests

```bash
pytest -q
```

---

## ISRO-QA Benchmark

ISRO-QA is a curated benchmark of 200 domain-specific question-answer pairs across three
difficulty tiers, stored at `data/benchmark/isro_qa.json`:

| Tier | Type | Count |
|---|---|---|
| 1 | Factoid | 100 |
| 2 | Multi-hop relational | 60 |
| 3 | Timeline reasoning | 40 |
| **Total** | | **200** |

---

## Tech Stack

| Component | Tool |
|---|---|
| Web scraping | Firecrawl API (optional fallback) |
| NER + parsing | spaCy `en_core_web_lg` |
| Knowledge graph | NetworkX 3.x |
| Embeddings | `all-MiniLM-L6-v2` |
| Vector index | FAISS-CPU |
| LLM | `mistral:7b-instruct-q4_K_M` |
| LLM serving | Ollama |
| Evaluation | canonical lexical metrics (ROUGE-L, coverage, exact match, IDK rate) |
| Frontend | Streamlit app — current public interface |

---

## Implementation Status

| Component | Status | Notes |
|---|---|---|
| Web scraper | ✅ Complete | Firecrawl API + HTTP fallback |
| Preprocessing | ✅ Complete | Cleaning, deduplication, chunking |
| NER + entity ruler | ✅ Complete | spaCy + ISRO-domain patterns |
| KG construction | ✅ Complete | NetworkX, dep. parsing, triple extraction |
| FAISS indexer | ✅ Complete | MiniLM-L6-v2 + Flat L2 index |
| KG retriever | ✅ Complete | 1-hop neighbourhood expansion |
| Hybrid retriever | ✅ Complete | KG + FAISS context merging |
| Generator | ✅ Complete | Ollama REST + prompt templates |
| Baselines | ✅ Complete | BM25, Vanilla RAG, GraphRAG |
| Evaluation | ✅ Complete | ROUGE-L, reference-token coverage, exact match, IDK rate on 180-question test set |
| Ablation study | ✅ Complete | Separate 50-question ablation in `data/results/ablation_results.json` |
| Unit tests | ✅ Complete | `pytest -q` on the project test suite |
| ISRO-QA benchmark | ✅ Complete | 200 QA pairs, `data/benchmark/isro_qa.json` |
| Result figures | ✅ Complete | charts in `paper/figures/` |
| Paper (LaTeX) | ✅ Current | `paper/main.tex` aligned to canonical results |
| Streamlit app | ✅ Current | app loads canonical metrics from `data/results/evaluation_results.json` |
| React frontend | ❌ Pending | not part of the current implemented scope |
| Analysis notebooks | ❌ Pending | placeholder notebooks remain |

---

## Team

| Name | Role | Institution |
|---|---|---|
| Nandana Narayan Das | KG pipeline, retrieval, evaluation, paper | Alliance School of Advanced Computing, Alliance University |
| Gowri Kannan | Data collection, generation, baselines, frontend | VJCET |

---

## Citation

If you use this work or the ISRO-QA benchmark, please cite:

```bibtex
@inproceedings{narayandas2027kgrag,
  title     = {KG-RAG: Knowledge Graph-Augmented Retrieval-Augmented Generation
               for ISRO Domain Question Answering on Resource-Constrained Hardware},
  author    = {Narayan Das, Nandana and Kannan, Gowri},
  booktitle = {Proceedings of the International Conference on Natural Language Processing (ICNLP)},
  year      = {2027}
}
```

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## Acknowledgements

This work is conducted under the ISRO Bharatiya Antariksh Hackathon 2025 (BAH-02) framework.
We thank Alliance School of Advanced Computing, Alliance University for academic support.
