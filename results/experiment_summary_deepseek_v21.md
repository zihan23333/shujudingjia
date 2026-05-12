# DeepSeek v2.1 Experiment Summary

## Ranking comparison

- Full model v2.1 vs Citation Count: Spearman `0.8353`
- Full model v2.1 vs Unweighted PageRank: Spearman `0.9385`
- Full model v2.1 vs Time-aware PageRank: Spearman `0.9947`
- Full model v2.1 vs Semantic-only: Spearman `0.9967`
- Full model v2.1 vs Semantic-temporal: Spearman `0.9968`

## Future citation validation

- cutoff = 2020, future = 2021?2024: Full model v2.1 is `better` than Citation Count, `better` than Unweighted PageRank, and `better` than Time-aware PageRank in Spearman.
- cutoff = 2021, future = 2022?2024: Full model v2.1 is `not better` than Citation Count, `better` than Unweighted PageRank, and `better` than Time-aware PageRank in Spearman.

## Ablation

| Variant | Edge weight | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | 1 | 0.938527 | 0.821022 | 4 | 5 | 7.466667 | 36.000000 |
| Semantic only | q_ij | 0.996713 | 0.972069 | 5 | 10 | 1.180952 | 13.000000 |
| Semantic + temporal | q_ij * tau_ij | 0.996796 | 0.977582 | 5 | 10 | 1.028571 | 11.000000 |
| Semantic + relation | q_ij * rho_ij | 0.998839 | 0.981992 | 5 | 10 | 0.780952 | 8.000000 |
| Full model | q_ij * tau_ij * rho_ij | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Pricing

- Base Case Top-5 papers: TUBE, Query-based data pricing, Too Much Data: Prices and Inefficiencies in Data Markets, Smart data pricing, A survey of smart data pricing
- Pricing sensitivity remains stable at the head, with Top-5 overlap across scenarios ranging from `4` to `5`.

## Sentiment limitation

- Negative sentiment predictions: `0`
- No-sentiment full-model robustness: Spearman `0.9997`, Top-10 overlap `10 / 10`.