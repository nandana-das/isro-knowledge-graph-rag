# Data (`data/`)

The system uses **two chunk collections**:

| Collection | What it is | Used for | In git |
|---|---|---|---|
| `data/corpus/` (audited corpus) | 33 official ISRO/ISSDC sources, 1,006 chunks, manually reviewed facts | Building the knowledge graph (123 entities, 134 triples) | yes |
| `data/chunks/chunks.json` (pilot crawl) | Automated crawl of isro.gov.in: 791 documents, 27,545 chunks, not manually curated | Dense (FAISS) and BM25 text retrieval, for all three systems | no (local only) |

The corrected rerun reuses frozen retrieved contexts (`results/relation_aware/generation_results.jsonl`). Reproducing the rerun therefore needs no local index. Live mode in the API does need it.

## Tracked in git

- `corpus/`: the audited corpus and KG. Main files:
  - `document_registry.json`: sources, URLs and SHA-256 checksums;
  - `chunks.jsonl`;
  - `fact_annotations.jsonl`;
  - `entities.jsonl`;
  - `triples.jsonl`;
  - `ontology.json`, `relations.json`;
  - validation reports.

  Details in [`corpus/README.md`](corpus/README.md).
- `documents/aditya_l1/official/`: official Aditya-L1 documents. They feed the pilot store, and one of them, the second booklet, is also a registered corpus source.
- `source_manifest.csv`: the Aditya-L1 source list for the pilot store.
- `relation_aware_benchmark/`: the frozen 72-question Relation-Aware QA v2 benchmark used in the rerun.
- `annotations/`: rating sheets and guidelines. See [`annotations/README.md`](annotations/README.md).
- `results/`: rerun outputs and the frozen retrieval input. See [`results/README.md`](results/README.md).

## Local only (git-ignored)

- `raw/`: pilot crawl output.
- `chunks/`: pilot chunks, including `chunks.json`.
- `index/faiss_index.index`: the dense index.
- `cleaned/`, `kg/`: intermediate files.

## Rebuilding the audited corpus and KG

Run from the repository root:

```bash
python -m src.corpus.download_documents   # 1. download registered official sources
python -m src.corpus.extract_documents    # 2. extract text with section/page structure
python -m src.corpus.clean_documents      # 3. normalise whitespace, drop repeated margins
python -m src.corpus.chunk_documents      # 4. section/page-aware chunks
python -m src.corpus.build_kg_ready       # 5. entities and triples from fact annotations
python -m src.corpus.coverage_analysis    # 6. relation coverage statistics
python -m src.corpus.validate_corpus      # 7. integrity and provenance checks
```

`fact_annotations.jsonl` holds the manually reviewed facts. Step 5 validates them against the sources; it never generates facts with a model.

## Rebuilding the pilot retrieval store

The crawl needs a Firecrawl API key in `.env`. The live site has changed since the original crawl, so a new crawl will not reproduce the 27,545 chunks exactly. The original run was not logged command by command, so treat this order as a best reconstruction.

```bash
python -m src.scraper.crawl              # 1. crawl isro.gov.in into data/raw/
python -m src.corpus.expand_aditya_l1    # 2. add official Aditya-L1 pages (58 chunks) to data/raw/
python -m src.preprocessing.chunk        # 3. chunk data/raw/ into data/chunks/chunks.json (512 words, stride 128)
python -m src.corpus.rebuild_index       # 4. FAISS index (all-MiniLM-L6-v2) in data/index/
```

Step 2 records its sources in `source_manifest.csv` and `results/aditya_l1_collection_report.json`. The PDFs and pages it reads are in `documents/aditya_l1/official/`.
