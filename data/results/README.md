# Results (`data/results/`)

Only the pre-registered corrected rerun is reported. All earlier experiments ran
with a context-truncation bug (Ollama `num_ctx=2048` silently dropped the start of
over-long prompts, which held the KG evidence), so their outputs are not valid
evidence. They are preserved in the git tag `archive/full-research-history`.

## `corrected_rerun/`: pre-registered corrected rerun

Protocol: [`reports/preregistration_corrected_rerun.md`](../../reports/preregistration_corrected_rerun.md).

| File | Contents | Produced by |
|---|---|---|
| `generation_results.jsonl` | 72 questions × 3 systems (V, A, C) with exact prompt token counts; every prompt fits the 2,048-token window | `src.evaluation.run_corrected_rerun` |
| `run_manifest.json` | Model, Ollama version, settings, and SHA-256 hashes of the inputs and outputs | `src.evaluation.run_corrected_rerun` |
| `human_eval_mapping.json`, `human_eval_package_manifest.json` | Blinding key and package manifest for the rating sheets | `src.evaluation.build_corrected_rerun_human_package` |
| `analysis.json`, `analysis.md` | Primary analysis of the rater-1 scores (AI-drafted, human-reviewed) | `src.evaluation.analyze_corrected_rerun` |
| `spotcheck_selection.json` | The 20 randomly sampled spot-check questions | `src.evaluation.build_corrected_rerun_spotcheck` |
| `spotcheck_analysis.json` | Pre-registered independent spot-check, Checker 1 | `src.evaluation.analyze_corrected_rerun_spotcheck` |
| `exploratory_analysis.json` | Post hoc, descriptive analyses (preregistration §19). Breakdowns by category and mission, evidence availability, outcome types, estimated truncation in the earlier run, cost, and pairwise agreement | `src.evaluation.analyze_corrected_rerun_exploratory` |
| `spotcheck2_analysis.json`, `spotcheck3_analysis.json` | Exploratory spot-checks, Checkers 2 and 3 (added post hoc, preregistration §17–§18) | `src.evaluation.analyze_corrected_rerun_spotcheck` |

Main findings:

- **Primary result:** System A beats Vanilla on correctness (+1.17, 95% CI [0.72, 1.62], Holm p < .001). System C beats Vanilla (+0.93, p = .0011). C does not differ significantly from A.
- **Spot-check:** the pre-registered spot-check **failed** its agreement threshold (Krippendorff's α = 0.64 < 0.667 for correctness). Report the primary scores as AI-drafted and human-reviewed, not as independently validated.
- **Direction:** every rater scored A above Vanilla.

## `study2_generators/`: Study 2, independent rating across three generators (in progress)

Protocol: [`reports/preregistration_study2_generators.md`](../../reports/preregistration_study2_generators.md).

| File | Contents | Produced by |
|---|---|---|
| `evidence.jsonl` | The exact evidence text Mistral received in the corrected rerun; given unchanged to every generator | `src.evaluation.run_generator_study --build-evidence` |
| `generation_results_{mistral,llama3.1,qwen2.5}.jsonl` | V and A answers for the 72 questions. Mistral's are imported unchanged from the corrected rerun | `src.evaluation.run_generator_study` |
| `run_manifest.json`, `run_log.txt` | Approved-protocol commit, hashes, Ollama version, per-call log | `src.evaluation.run_generator_study` |
| `rating_mapping.json`, `rating_package_manifest.json` | Blinding key (labels A–F) for the rating package; raters never see it | `src.evaluation.build_study2_rating_package` |

Ratings: three independent raters, imported with `python -m src.evaluation.analyze_generator_study --import <workbook> --rater N`. Analysis: `python -m src.evaluation.analyze_generator_study`.

## `relation_aware/`: frozen retrieval input

`generation_results.jsonl` is the earlier relation-aware run. The rerun reuses only its **retrieved contexts** (frozen retrieval) and regenerates every answer. Its answers and scores are not used. `run_manifest.json` records how that retrieval was produced (`src.evaluation.run_relation_aware_experiment`).

`aditya_l1_collection_report.json` is the collection log for the Aditya-L1 pages in the pilot retrieval store (see `data/README.md`).
