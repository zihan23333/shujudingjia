# Future Citation Validation Summary v2

- Validation scope: `core-paper future citation validation`
- Cutoff year: `2021`
- Future window: `2022-2024`
- Target papers evaluated: `30`
- Historical edges before cutoff: `133`
- Historical v2 LLM-scored edges before cutoff: `67`
- Full model v2 vs Citation Count: `not better`
- Full model v2 vs Unweighted PageRank: `better`
- Full model v2 vs Time-aware PageRank: `better`
- Compared with the old semantic layer, Full model Spearman changed from `-0.0839` to `0.1242` and NDCG@10 changed from `0.2299` to `0.4902`.

If Citation Count still ranks highest, this should be interpreted as evidence that future citations are more closely tied to subsequent diffusion scale and cumulative citation heat than to the semantically calibrated notion of article-level value targeted in this paper.

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.203900 | 0.200413 | 0.276238 | 0.400000 | 4 |
| Unweighted PageRank | -0.090808 | -0.071594 | 0.175383 | 0.300000 | 3 |
| Time-aware PageRank | 0.103717 | 0.066975 | 0.497714 | 0.400000 | 4 |
| Semantic-weighted PageRank v2 | 0.133096 | 0.085451 | 0.490243 | 0.400000 | 4 |
| Semantic-temporal PageRank v2 | 0.109281 | 0.066975 | 0.490243 | 0.400000 | 4 |
| Full model v2 | 0.124193 | 0.076213 | 0.490243 | 0.400000 | 4 |