# Pre-registration: corrected-context rerun

Status: **APPROVED 2026-10-08** by the project owner, before any generation.
Raters: two or more independent raters confirmed (see §8). The commit hash of the approved version is recorded in
the run manifest, and any later change to this file is reported as a deviation.

## 1. Why this rerun exists

Every earlier generation run used Ollama `num_ctx=2048` with a 1,500-word
context. Prompts were often 2.4k–3.9k model tokens, and Ollama silently kept
only the last ~1,027, dropping the KG evidence placed first. Commit `7cb2d2a`
fixes this. The rerun answers one question: **with evidence that actually
reaches the generator, does KG-grounded generation improve human-judged answer
quality over vanilla dense RAG?**

All earlier results stay in the repository and are reported as as-implemented
results under truncation. This rerun does not replace them.

## 2. What is held fixed

- **Benchmark:** `relation_aware_qa_v2.json`, SHA-256 `6c7f3600…2b64`,
  unchanged. No questions, references or labels are edited.
- **Retrieval:** frozen. Contexts come from
  `data/results/relation_aware/generation_results.jsonl`, SHA-256 `e13e4c82…635c`.
  No retrieval is rerun.
- **Prompts and system prompts:** exactly as at commit `7cb2d2a`. No tuning.
- **Model:** `mistral:7b-instruct-q4_K_M`, temperature 0.1, `num_predict` 150,
  `num_ctx` 2048, `seed` 20261008.
- **Evidence budget:** at most 1,500 model tokens, **identical for all three
  systems**, and always within the window. Each context is trimmed to the
  budget from its tail (lowest-priority evidence) before sending. Dry run
  (`--dry-run`, no model calls): largest prompt 1,676 tokens against a
  1,890-token limit; no prompt needed trimming by the window guard.
- **Runner:** `src/evaluation/run_corrected_rerun.py`. It refuses to generate
  while this file is a draft or uncommitted, and while any source code is
  uncommitted.
- **One run.** No regeneration of any row for any reason except a logged
  transport failure (HTTP error or timeout), retried once and reported.

## 3. Systems (3)

| Label | System | Context |
|---|---|---|
| V | Vanilla dense RAG | frozen `vanilla_dense_rag` context |
| A | Relation-aware KG-RAG (A_CURRENT) | frozen `relation_aware_kg_rag` context |
| C | Two-stage KG-grounded (C_TWO_STAGE) | frozen KG facts + dense text, plan then answer |

These match the earlier human evaluations, so corrected and truncated results
compare directly. No other systems are generated.

## 4. Analysis sets

- **Primary:** the 60 `KG_REQUIRED = YES` items, as frozen.
- **Reported, not tested:** the 12 `KG_REQUIRED = NO` items, generated for
  completeness and summarised descriptively.
- **Sensitivity analyses (pre-specified, no inference beyond what is listed):**
  1. Deduplicated: one item per unique question text (45 items). The kept item
     is the lowest question ID.
  2. Excluding the 10 `DIRECT_CONTROL` items labelled `KG_REQUIRED = YES` (50 items).
  3. The 13 held-out items, described only. This set is too small to test, and
     it leaked (6 texts duplicated in development; 4 items used in the prompt
     diagnostic).
- **Not performed:** the KG_REQUIRED YES-vs-NO difference-in-differences. Five
  identical questions carry both labels, so the contrast is invalid.

## 5. Endpoints

**Primary:** human **correctness** (1–5), paired by question:
- C vs V
- A vs V

**Secondary:** completeness, groundedness, relevance (1–5); unsupported-claim
rate (0/1); C vs A on all endpoints; ROUGE-L, reference coverage and
"I don't know" rate (automated, reported as secondary only).

## 6. Statistical plan

- Paired Wilcoxon signed-rank test, two-sided; zero differences dropped
  (Wilcoxon method). Unsupported-claim rate: exact McNemar test.
- Holm correction across the **2 primary tests** at α = 0.05. Secondary tests
  are Holm-corrected within their own family and labelled exploratory.
- For every comparison, report mean and median difference, 10,000-resample
  paired bootstrap 95% CI (seed 20261008), Cohen's dz, and wins/losses/ties.
- **Power:** with n = 60 pairs, the primary tests have roughly 80% power for
  dz ≈ 0.41 at the Holm-adjusted α. Smaller true effects may be missed; a
  non-significant result is reported as "not detected", never as "no effect".

## 7. Decision rule (fixed now)

For each KG system (C, A) against V:
- **SUPPORTED:** the Holm-adjusted primary test has p < .05 with a positive
  mean difference, **and** the unsupported-claim rate is not higher than V's
  by a statistically significant margin (McNemar p < .05).
- **HARMFUL:** the Holm-adjusted primary test has p < .05 with a negative
  mean difference.
- **NOT SUPPORTED:** anything else. The CI is reported, and no equivalence is
  claimed.

The result is reported whatever it is. No further variants, prompts or reruns
follow from this outcome within this study.

## 8. Human evaluation protocol

- **Blinding:** candidates shuffled per question with seed 20261008; the
  mapping is kept outside the rater files.
- **Shown to raters:** the question, the reference answer and acceptable
  answers, and a **shared source-evidence pack**: the text of the item's
  `supporting_chunks` and its `supporting_triples`. The pack is identical for
  all three candidates, so it does not reveal system identity.
- **Correctness for set-valued questions:** an answer naming any member of the
  correct set that the evidence pack supports counts as correct. The single
  reference is shown as one example, not the only answer.
- **Groundedness and unsupported claims** are judged against the evidence pack.
- **Raters:** at least 2 independent raters, scoring all items. Agreement is
  reported as Krippendorff's α (ordinal) per dimension. The primary analysis
  uses the per-item mean of the raters. *If only one rater is available, this
  is stated as a limitation and no agreement figure is claimed.*
- Raters do not see automated metrics, system names or earlier results.

## 9. Integrity checks (run automatically, reported)

- For every model call: `prompt_eval_count` equals `prompt_tokens_expected`,
  and `ollama_truncated` is false. Any failure is reported, never hidden.
- The benchmark and frozen-context hashes match §2.
- Every candidate in the rater CSV matches its generation by hash.

## 10. Reporting

Report all three systems on all endpoints, all sensitivity sets, the
integrity-check results and every deviation from this plan. Report the
truncated (earlier) and corrected (this) results side by side.
