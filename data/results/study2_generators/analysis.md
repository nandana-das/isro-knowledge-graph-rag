# Study 2 analysis (pre-registered)

Raters: 3. Krippendorff's alpha: correctness 0.938, completeness 0.957, groundedness 0.941, relevance 0.919, unsupported_claim 0.866
Reliability qualifier: none

## Primary: correctness, A vs V, 60 KG-required items (Holm over 3 generators)

| Generator | Mean diff | 95% CI | dz | W/L/T | Wilcoxon p | Holm p | Decision |
|---|---|---|---|---|---|---|---|
| mistral | +1.000 | [0.561, 1.456] | 0.563546 | 25/8/27 | 0.0001 | 0.0001 | SUPPORTED |
| llama3.1 | +1.294 | [0.789, 1.800] | 0.645072 | 30/9/21 | 0.0000 | 0.0000 | SUPPORTED |
| qwen2.5 | +1.339 | [0.833, 1.839] | 0.666162 | 35/5/20 | 0.0000 | 0.0000 | SUPPORTED |

## H4: compositional items (Holm over 3)

| Generator | Mean diff | 95% CI | Holm p |
|---|---|---|---|
| mistral | -0.117 | [-0.667, 0.367] | 1.0000 |
| llama3.1 | +0.200 | [-0.550, 0.867] | 0.9241 |
| qwen2.5 | +0.183 | [-0.650, 0.967] | 1.0000 |

Secondary, sensitivity and Study 1 comparison: see analysis.json.
