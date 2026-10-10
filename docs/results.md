# Ranker evaluation

Data: 57 hand-labelled postings (22 good fits), stratified sample
(top 25 / random middle 25 / random excluded 10), labelled blind.

| Version | p@5 | p@10 | AP | Notes |
|---|---|---|---|---|
| title-only baseline | 0.40 | 0.60 | 0.63 | |
| v1 ranker | 0.80 | 0.70 | 0.67 | 2 good fits removed by hard filters |