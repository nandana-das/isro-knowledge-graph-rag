# Annotations (`data/annotations/`)

Rating sheets for the pre-registered corrected rerun. Scale: Correctness, Completeness, Groundedness, Relevance (1–5) and Unsupported Claims (yes/no).

## Guidelines

- `corrected_rerun_human_eval_guidelines.md`: the rubric given to every rater.

## Primary evaluation (72 questions × 3 systems)

- `corrected_rerun_human_eval_rater1.csv`, `corrected_rerun_human_eval_rater2.csv`: the blank, blinded sheets. The two are byte-identical, one per rater.
- `corrected_rerun_rater1_model_draft_AUDIT_ONLY.csv`: the model-drafted scores, before human review. Kept only for audit.
- `corrected_rerun_human_eval_rater1_filled.csv`: rater 1's reviewed scores, which the primary analysis uses. Rater 1 accepted 99.2% of the drafted scores unchanged, so report these as AI-drafted and human-reviewed.

## Independent spot-check (20 random questions)

- `corrected_rerun_spotcheck.csv`: the blank spot-check sheet.
- **Checker 1** (pre-registered):
  - original workbook: `corrected_rerun_spotcheck_rater_IS.xlsx`;
  - normalised CSV: `corrected_rerun_spotcheck_filled.csv`, made by `src.evaluation.import_spotcheck_workbook`.
- **Checker 2** (exploratory):
  - sheet export: `corrected_rerun_spotcheck2_sheet_export.csv`;
  - normalised CSV: `corrected_rerun_spotcheck2_filled.csv`.
- **Checker 3** (exploratory; did not see the scores and did not use AI):
  - original workbook: `corrected_rerun_spotcheck3_rater.xlsx`;
  - normalised CSV: `corrected_rerun_spotcheck3_filled.csv`.

Analyses are in `data/results/corrected_rerun/`.
