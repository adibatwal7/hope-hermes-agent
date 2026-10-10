# Ranker evaluation

| Version | Labels | p@5 | p@10 | AP | Notes |
|---|---|---|---|---|---|
| title-only baseline | 57 | 0.40 | 0.60 | 0.63 | random ≈ 0.39 |
| v1 ranker | 57 | 0.80 | 0.70 | 0.67 | 2 good fits removed by hard filters |
| title-only baseline | 94 | 0.40 | 0.60 | 0.62 | random ≈ 0.31 |
| v1 ranker | 94 | 0.80 | 0.70 | 0.65 | |
| tuned ranker | 94 | 1.00 | 0.70 | 0.74 | removed `stripe` (leakage), skills_cap 8→5, entry_level 1→2 |

## Held-out test (frozen, evaluated once)

60 postings (30 good fits), no overlap with the dev set, labelled after tuning.

| Version | p@5 | p@10 | AP |
|---|---|---|---|
| title-only baseline | 1.00 | 0.90 | 0.91 |
| tuned ranker | 1.00 | 1.00 | 0.95 |

p@5 and p@10 hit the ceiling for both, so AP is the discriminating metric.

## Bootstrap confidence intervals

AP(ranker) − AP(title-only), 1,000 resamples of postings with replacement, percentile 95% CI.

| Set | Point diff | 95% CI |
|---|---|---|
| Dev (tuned on) | +0.12 | +0.01 to +0.31 |
| Held-out | +0.05 | −0.01 to +0.24 |

The dev interval excludes zero, but that set was used for tuning, so it is optimistic.
On held-out data the gain is positive, but the interval crosses zero at n = 60:
promising, not yet significant. Next: label more held-out postings.