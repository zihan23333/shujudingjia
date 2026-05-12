# Future Citation Validation Summary_cutoff2021_final

- Validation scope: `core-paper future citation validation`
- Cutoff year: `2021`
- Future window: `2022-2024`
- Target papers evaluated: `30`
- Historical edges before cutoff: `133`
- Historical final LLM-scored edges before cutoff: `78`
- Full model final vs Citation Count: `not better`
- Full model final vs Unweighted PageRank: `better`
- Full model final vs Time-aware PageRank: `better`

If Citation Count remains stronger on some future-citation metrics, this should be interpreted as evidence that future citations are more closely tied to subsequent diffusion scale and citation heat than to the semantically calibrated notion of article-level value targeted in this paper.

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.203900 | 0.200413 | 0.276238 | 0.400000 | 4 |
| Unweighted PageRank | -0.090808 | -0.071594 | 0.175383 | 0.300000 | 3 |
| Time-aware PageRank | 0.103717 | 0.066975 | 0.497714 | 0.400000 | 4 |
| Semantic-weighted PageRank final | 0.128199 | 0.103927 | 0.465271 | 0.400000 | 4 |
| Semantic-temporal PageRank final | 0.129312 | 0.090070 | 0.497714 | 0.400000 | 4 |
| Full model final | 0.135544 | 0.099308 | 0.490243 | 0.400000 | 4 |