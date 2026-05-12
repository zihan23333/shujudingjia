# Future Citation Validation Summary v2

- Validation scope: `core-paper future citation validation`
- Cutoff year: `2020`
- Future window: `2021-2024`
- Target papers evaluated: `29`
- Historical edges before cutoff: `106`
- Historical v2 LLM-scored edges before cutoff: `40`
- Full model v2 vs Citation Count: `better`
- Full model v2 vs Unweighted PageRank: `better`
- Full model v2 vs Time-aware PageRank: `better`
- Compared with the old semantic layer, Full model Spearman changed from `-0.0839` to `0.1655` and NDCG@10 changed from `0.2299` to `0.5137`.

If Citation Count still ranks highest, this should be interpreted as evidence that future citations are more closely tied to subsequent diffusion scale and cumulative citation heat than to the semantically calibrated notion of article-level value targeted in this paper.

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.109484 | 0.119183 | 0.289216 | 0.400000 | 4 |
| Unweighted PageRank | -0.059121 | -0.056720 | 0.203180 | 0.400000 | 4 |
| Time-aware PageRank | 0.157901 | 0.086313 | 0.523067 | 0.500000 | 5 |
| Semantic-weighted PageRank v2 | 0.156670 | 0.091245 | 0.515858 | 0.500000 | 5 |
| Semantic-temporal PageRank v2 | 0.125139 | 0.076449 | 0.513130 | 0.500000 | 5 |
| Full model v2 | 0.165538 | 0.101110 | 0.513695 | 0.500000 | 5 |