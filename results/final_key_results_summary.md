# Final Key Results Summary

## Final semantic layer

- 204 total citation edges
- 113 DeepSeek target-aligned scored edges
- 91 default fallback edges
- coverage ratio 55.39%
- no old `llm_results.csv`
- no offline fallback

## Ranking comparison final

| Method | Score column | Spearman with Full model final | Kendall with Full model final | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Citation Count | citation_count_score | 0.832845 | 0.705291 | 1 | 4 | 12.704762 | 69.500000 |
| Unweighted PageRank | unweighted_pagerank_score | 0.935541 | 0.818817 | 4 | 5 | 7.542857 | 44.000000 |
| Time-aware PageRank | time_aware_pagerank_score | 0.992711 | 0.951121 | 5 | 10 | 1.847619 | 21.000000 |
| Semantic-weighted PageRank final | semantic_pagerank_score_final | 0.996775 | 0.970599 | 5 | 10 | 1.295238 | 13.000000 |
| Semantic-temporal PageRank final | semantic_temporal_score_final | 0.997460 | 0.979419 | 5 | 10 | 0.895238 | 10.000000 |
| Full model final | full_model_score_final | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Ablation final

| Variant | Edge weight | Spearman with Full model final | Kendall with Full model final | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | unweighted_pagerank_score | 0.935541 | 0.818817 | 4 | 5 | 7.542857 | 44.000000 |
| Semantic only | semantic_pagerank_score_final | 0.996775 | 0.970599 | 5 | 10 | 1.295238 | 13.000000 |
| Semantic + temporal | semantic_temporal_score_final | 0.997460 | 0.979419 | 5 | 10 | 0.895238 | 10.000000 |
| Semantic + relation | semantic_relation_score_final | 0.998175 | 0.980889 | 5 | 10 | 0.876190 | 12.000000 |
| Full model final | full_model_score_final | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Robustness final

| Variant | Setting | Spearman with Full model final | Kendall with Full model final | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Confidence-aware | epsilon=0.3 | 0.999948 | 0.998162 | 5 | 10 | 0.095238 | 1.000000 |
| Confidence-aware | epsilon=0.5 | 0.999969 | 0.998897 | 5 | 10 | 0.057143 | 1.000000 |
| Confidence-aware | epsilon=0.7 | 0.999979 | 0.999265 | 5 | 10 | 0.038095 | 1.000000 |

| Variant | Setting | Spearman with Full model final | Kendall with Full model final | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Extended relation | rho(co,tc,inst) | 0.999440 | 0.988975 | 5 | 10 | 0.514286 | 4.000000 |

| Variant | Spearman with Full model final | Kendall with Full model final | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- |
| semantic-only-no-sentiment | 0.996775 | 0.971702 | 5 | 10 | 1.219048 | 15.000000 |
| semantic-temporal-no-sentiment | 0.997636 | 0.978684 | 5 | 10 | 0.990476 | 11.000000 |
| full-model-no-sentiment | 0.999399 | 0.991915 | 5 | 10 | 0.419048 | 8.000000 |

## Future citation validation final

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.109484 | 0.119183 | 0.289216 | 0.400000 | 4 |
| Unweighted PageRank | -0.059121 | -0.056720 | 0.203180 | 0.400000 | 4 |
| Time-aware PageRank | 0.157901 | 0.086313 | 0.523067 | 0.500000 | 5 |
| Semantic-weighted PageRank final | 0.181549 | 0.125771 | 0.515858 | 0.500000 | 5 |
| Semantic-temporal PageRank final | 0.168986 | 0.106042 | 0.522769 | 0.500000 | 5 |
| Full model final | 0.170711 | 0.110974 | 0.515847 | 0.500000 | 5 |

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.203900 | 0.200413 | 0.276238 | 0.400000 | 4 |
| Unweighted PageRank | -0.090808 | -0.071594 | 0.175383 | 0.300000 | 3 |
| Time-aware PageRank | 0.103717 | 0.066975 | 0.497714 | 0.400000 | 4 |
| Semantic-weighted PageRank final | 0.128199 | 0.103927 | 0.465271 | 0.400000 | 4 |
| Semantic-temporal PageRank final | 0.129312 | 0.090070 | 0.497714 | 0.400000 | 4 |
| Full model final | 0.135544 | 0.099308 | 0.490243 | 0.400000 | 4 |

## Pricing final

- Base Case Top-5: TUBE, Query-based data pricing, Too Much Data: Prices and Inefficiencies in Data Markets, Smart data pricing, A survey of smart data pricing