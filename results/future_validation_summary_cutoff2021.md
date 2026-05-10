# Future Citation Validation Summary

- Validation type: `core-paper future citation validation`
- Cutoff year: `2021`
- Future citation window: `2022-2024`
- Number of papers with future citation labels = `105`
- Number of target papers evaluated = `30`
- Number of target papers with nonzero future citations = `30`
- Number of historical edges before cutoff = `133`
- Number of LLM-scored historical edges before cutoff = `94`
- Relation penalty parameter `eta_a = 0.5` and time decay parameter `b = 5.0`

## Main findings

- Highest Spearman: `Citation Count` (0.2039)
- Highest NDCG@10: `Citation Count` (0.3006)
- Full model vs Citation Count: `not better` in Spearman (-0.0839 vs 0.2039)
- Full model vs Unweighted PageRank: `better` in Spearman (-0.0839 vs -0.1360)
- Full model vs Time-aware PageRank: `better` in Spearman (-0.0839 vs -0.1080)

## Interpretation

The Full model is not necessarily the best on every future-citation metric.
Possible reasons include the small core-paper sample, the fact that future citations are influenced by topic popularity and paper age, and the fact that future citations are only an external proxy rather than a direct measure of article-level scholarly value.

## Metric table

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.203900 | 0.200413 | 0.300629 | 0.400000 | 4 |
| Unweighted PageRank | -0.136004 | -0.101735 | 0.228084 | 0.300000 | 3 |
| Time-aware PageRank | -0.107958 | -0.069365 | 0.229897 | 0.300000 | 3 |
| Semantic-weighted PageRank | -0.087063 | -0.055620 | 0.229897 | 0.300000 | 3 |
| Semantic-temporal PageRank | -0.081274 | -0.046350 | 0.228836 | 0.300000 | 3 |
| Full model | -0.083946 | -0.055620 | 0.229897 | 0.300000 | 3 |

All model scores were computed from cutoff-year historical information only, without using future-window citations, future-window LLM scores, or future-window citing papers.