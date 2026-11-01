# Pre-registration: Study 2, independent human rating across three generators

Status: **APPROVED 2026-10-30** by the project owner, before any Study 2
generation or rating. The commit of this approved version is recorded in the
run manifest. Any later change to this file is reported as a deviation.

## 1. Why this study exists

The corrected rerun (Study 1, `reports/preregistration_corrected_rerun.md`)
found that relation-aware KG-RAG (A) beat vanilla dense RAG (V) on correctness,
but it has two weaknesses:

1. **Unvalidated scores:** the primary scores were AI-drafted and reviewed by
   one human (99.2% unchanged), and the pre-registered independent spot-check
   failed (correctness α = 0.64).
2. **One generator:** only Mistral-7B was tested.

Study 1's post hoc analyses (§19 there) also suggested that A's gain comes
from single-relation questions, not from two-hop or multi-relation ones.

Study 2 asks three questions:

- **Q1:** Does A beat V on correctness when scored by three independent human
  raters who never see model-drafted scores?
- **Q2:** Does this hold for two further generators?
- **Q3:** Is there any gain on compositional (two-hop and multi-relation)
  questions?

## 2. What is held fixed

- **Benchmark:** `relation_aware_qa_v2.json`, SHA-256 `6c7f3600…2b64`,
  unchanged. Known defects (duplicates, KG-derived references, label
  conflicts) are the same as in Study 1 and are reported, not repaired.
- **Evidence:** every generator receives exactly the evidence text Mistral
  received in Study 1.
  - The text is stored in `data/results/study2_generators/evidence.jsonl`
    (SHA-256 `1e718359…69e1`).
  - It was checked before this draft: all 144 V/A evidence texts match
    Study 1's token counts exactly.
  - No retrieval is run, and nothing is re-trimmed per generator unless a
    prompt does not fit that generator's window. That case is logged and
    reported as a deviation.
- **Prompts:** the Study 1 system prompt and user prompt, unchanged.
- **Settings:** temperature 0.1, `num_predict` 150, `num_ctx` 2048,
  seed 20261008, for every generator.
- **Token counting:** exact, per generator.
  - Each generator's tokenizer is extracted from its GGUF file and committed
    under `config/tokenizer/`.
  - Each generator's Ollama prompt template is calibrated against
    `prompt_eval_count` before approval.
  - Every call checks that the prompt was neither truncated nor trimmed.
  - **Calibration, done before this draft:** for each generator, 3 short
    probes and the 6 longest real evidence prompts (about 1,370–1,610
    tokens) were compared with `prompt_eval_count`. All matched exactly
    (`src/generator/calibrate_template.py`).
  - **Llama 3.1 fix:** its GGUF-extracted tokenizer used GPT-2's
    pre-tokenizer regex, which overcounted by 8–11 tokens. Llama 3's own
    split pattern, now applied by `extract_tokenizer.py`, fixed this.
  - **Dry run** (no model calls): the largest prompt is 1,432 tokens for
    Llama and 1,469 for Qwen, against the 1,890-token limit. No prompt needed
    trimming.
- **One run.** No regeneration of any row for any reason except a logged
  transport failure, retried once and reported.

## 3. Generators and systems

| Generator | Ollama model | Source of answers |
|---|---|---|
| Mistral-7B-Instruct v0.x | `mistral:7b-instruct-q4_K_M` | Study 1 answers, unchanged |
| Llama-3.1-8B-Instruct | `llama3.1:8b-instruct-q4_K_M` | generated once in this study |
| Qwen2.5-7B-Instruct | `qwen2.5:7b-instruct-q4_K_M` | generated once in this study |

Systems: **V** (vanilla dense RAG) and **A** (relation-aware KG-RAG), as in
Study 1. System C is not included: Study 1 found no advantage for it, and it
would add 60 answers per rater.

## 4. Analysis sets

- **Primary:** the 60 `KG_REQUIRED = YES` items.
- **Compositional subset (for H4):** the 20 TWO_HOP_RELATION and
  MULTI_RELATION items.
- **Sensitivity (described only):** the 45 deduplicated items (lowest
  question ID kept per unique text), and the 50 items without DIRECT_CONTROL.
- **Not rated:** the 12 `KG_REQUIRED = NO` items. They are generated but not
  rated, to keep rating time manageable.

## 5. Hypotheses and endpoints

**Primary endpoint:** human correctness (1–5), averaged over the three
raters, paired by question.

- **H1 (Mistral, replication of Study 1):** A > V.
- **H2 (Llama 3.1):** A > V.
- **H3 (Qwen 2.5):** A > V.

**Secondary hypothesis:**

- **H4:** for each generator, A > V on correctness on the 20 compositional
  items. These are 3 tests, in their own Holm family. With 20 pairs, power
  is low (about 80% only for dz ≈ 0.68). A non-significant result is
  reported as "not detected".

**Secondary endpoints:**

- completeness, groundedness and relevance (1–5);
- the unsupported-claim rate;
- automated metrics (ROUGE-L, reference coverage, "I don't know" rate);
- the generator comparison: A's correctness across generators, described only.

## 6. Statistical plan

- **Tests:**
  - scales: paired Wilcoxon signed-rank, two-sided, `zero_method="wilcox"`
    (scipy default method);
  - unsupported claims: exact McNemar test.
- **Holm correction:**
  - across the 3 primary tests (H1–H3) at α = 0.05;
  - separately across the 3 H4 tests;
  - separately across all other secondary human comparisons, which are
    labelled exploratory;
  - automated metrics: uncorrected p-values, labelled exploratory.
- **Reported for every comparison:** mean and median difference,
  10,000-resample paired bootstrap 95% CI (seed 20261008), Cohen's dz, and
  wins/losses/ties.
- **Item scores:**
  - 1–5 scales: the mean of the three raters;
  - unsupported claim: 1 if at least two of three raters flag it (majority).
    This differs from Study 1, which had one rater.
- **Power:** with 60 pairs, each primary test has about 80% power for
  dz ≈ 0.40 at the Holm-adjusted α.

## 7. Decision rule (fixed now)

For each generator:

- **SUPPORTED:** the Holm-adjusted primary test gives p < .05 with a positive
  mean difference, and A's unsupported-claim rate is not significantly
  higher than V's (McNemar p < .05).
- **HARMFUL:** Holm-adjusted p < .05 with a negative mean difference.
- **NOT SUPPORTED:** anything else.

**Reliability qualifier** (applies to all decisions):

- **Measurement:** ordinal Krippendorff's α across the three raters, for
  each dimension, over all 360 rated answers. Unsupported claims use nominal α.
- **Below threshold:** if correctness α is below 0.667, every decision is
  reported with the qualifier "low inter-rater reliability". The paper then
  describes it as tentative.
- **Below 0.40:** if correctness α is below 0.40, no SUPPORTED decision is
  claimed in the abstract or conclusion.

The result is reported whatever it is. No further generators, prompts or
reruns follow from this outcome within this study.

## 8. Human rating protocol

- **Raters:**
  - three people; none is a member of the project team;
  - none has seen Study 1's scores, the AI draft, any analysis output or
    `data/results/`;
  - the project owner attests to this, and the analysis does not verify it.
- **Package:**
  - 60 questions, each with six candidate answers (V and A × three
    generators);
  - the six candidates are shuffled per question with seed 20261008 and
    labelled A–F;
  - the mapping is kept outside the rater files;
  - every rater gets an identical workbook.
- **Shown to raters:**
  - the question, the reference and acceptable answers;
  - the same shared evidence pack as Study 1 (supporting triples and chunks),
    identical for all six candidates.
- **Rubric:** word-for-word the Study 1 rubric, including the set-valued
  correctness rule and the "I don't know" rule.
- **Independence rules:**
  - no AI tools;
  - no discussion until all three raters have finished;
  - no other ratings or results to be viewed.
- **Time:** about 6–8 hours per rater. Two or more sessions are allowed.
  Raters record the date and duration of each session.
- **Import:** returned workbooks are converted with the hash-checked
  importer. Every answer text must match the package, and every score must
  be an allowed value.
- **Screen:** before any analysis, the number of sessions, the total time
  and the score distribution are recorded for each rater. A rater is not
  excluded on these grounds. Unusual patterns are reported, such as total
  time under one hour or more than 90% identical scores.

## 9. Integrity checks (run automatically, reported)

- For every generated call: `prompt_eval_count` equals the expected count,
  `ollama_truncated` is false, and `context_trimmed` is false.
- The evidence file, benchmark and Study 1 results hashes match §2.
- Every candidate in every rater file matches its generation by hash.

## 10. Comparison with Study 1 (described only)

For Mistral only, report agreement between the Study 1 rater-1 scores and
the Study 2 rater-mean scores on the same 120 answers. Use Krippendorff's α
(ordinal) and the A−V difference under each.

## 11. Code (committed before any rating exists)

| Script | Purpose |
|---|---|
| `src/evaluation/run_generator_study.py` | Generation |
| `src/evaluation/build_study2_rating_package.py` | Rating package and evaluator kit |
| `src/evaluation/analyze_generator_study.py` | Analysis |

## 12. Ratings received and screening (recorded before analysis)

Recorded 2026-11-02, before `analyze_generator_study.py` was run on any
rating. No A-vs-V result had been computed.

**Files received:**

| Rater | Original workbook | SHA-256 |
|---|---|---|
| AM | `data/annotations/study2_rater_AM.xlsx` | `65887f0e…593e` |
| IS | `data/annotations/study2_rater_IS.xlsx` | `8a9a7b36…24cd` |
| RD | `data/annotations/study2_rater_RD.xlsx` | `5c27efdc…afa` |

**Screening findings (§8):**
- **Identical ratings:** AM and IS are identical in all 1,800 score cells,
  and their session logs are identical: one session, 1 Nov, 23:49–23:55,
  with the same note.
- **Overlap with RD:** RD matches the other two in 1,499 of 1,800 cells
  (83.3%) and in 242 of 360 answers. RD has no session log.
- **Not saved from Excel:** all three workbooks have document creator
  "openpyxl", the Python library, and creation times within 1.2 seconds of
  each other (2026-11-01 18:37:14–15 UTC). This means a script wrote them,
  not a person saving in Excel.
- **Initials:** "IS" are also the initials of Study 1's Checker 1.

**What these findings mean:**
- The three files are not independent human ratings in the sense of §8.
- At most two distinct rating sets exist, and their origin is not verified.
- The project owner instructed that all three be analysed as the three
  checkers. The analysis below follows that instruction and §4–§7
  unchanged.

**Consequences for interpretation:**
- **Agreement:** the reported Krippendorff's α includes a duplicated rater,
  so it overstates agreement. It is not an inter-rater reliability estimate.
- **Description:** Study 2 cannot be described as an independent human
  evaluation. Any report must state these findings.
