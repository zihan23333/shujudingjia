# Experiment Summary v2

| metric | value |
| --- | --- |
| total_citation_edges | 204.000000 |
| target_aligned_LLM_scored_edges | 78.000000 |
| default_fallback_edges | 126.000000 |
| target_aligned_LLM_coverage_ratio | 0.382353 |
| high_confidence_count | 63.000000 |
| grouped_count | 14.000000 |
| range_count | 1.000000 |
| ambiguous_count | 10.000000 |
| failed_count | 116.000000 |
| old_LLM_scored_edges_count | 123.000000 |
| old_LLM_retained_high_confidence_count | 54.000000 |

## Ranking comparison

| Method | Score column | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Citation Count | citation_count_score | 0.831315 | 0.704184 | 1 | 4 | 12.476190 | 70.500000 |
| Unweighted PageRank | unweighted_pagerank_score | 0.935717 | 0.819184 | 4 | 5 | 7.619048 | 33.000000 |
| Time-aware PageRank | time_aware_pagerank_score | 0.994806 | 0.964719 | 5 | 10 | 1.466667 | 18.000000 |
| Semantic-weighted PageRank | semantic_pagerank_score_v2 | 0.996921 | 0.972437 | 5 | 10 | 1.161905 | 14.000000 |
| Semantic-temporal PageRank | semantic_temporal_score_v2 | 0.997885 | 0.979787 | 5 | 10 | 0.876190 | 9.000000 |
| Full model v2 | full_model_score_v2 | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Ablation

| Variant | Edge weight | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | 1 | 0.935717 | 0.819184 | 4 | 5 | 7.619048 | 33.000000 |
| Semantic only | q_ij | 0.996921 | 0.972437 | 5 | 10 | 1.161905 | 14.000000 |
| Semantic + temporal | q_ij * tau_ij | 0.997885 | 0.979787 | 5 | 10 | 0.876190 | 9.000000 |
| Semantic + relation | q_ij * rho_ij | 0.999036 | 0.984197 | 5 | 10 | 0.685714 | 6.000000 |
| Full model | q_ij * tau_ij * rho_ij | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Confidence robustness

| Variant | Setting | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Confidence-aware | epsilon=0.3 | 0.999917 | 0.997795 | 5 | 10 | 0.114286 | 2.000000 |
| Confidence-aware | epsilon=0.5 | 0.999938 | 0.998162 | 5 | 10 | 0.095238 | 2.000000 |
| Confidence-aware | epsilon=0.7 | 0.999979 | 0.999265 | 5 | 10 | 0.038095 | 1.000000 |

## Extended relation robustness

| Variant | Setting | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Extended relation | rho(co,tc,inst) | 0.999326 | 0.986770 | 5 | 10 | 0.571429 | 4.000000 |

## Future validation (main)

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.109484 | 0.119183 | 0.289216 | 0.400000 | 4 |
| Unweighted PageRank | -0.059121 | -0.056720 | 0.203180 | 0.400000 | 4 |
| Time-aware PageRank | 0.157901 | 0.086313 | 0.523067 | 0.500000 | 5 |
| Semantic-weighted PageRank v2 | 0.156670 | 0.091245 | 0.515858 | 0.500000 | 5 |
| Semantic-temporal PageRank v2 | 0.125139 | 0.076449 | 0.513130 | 0.500000 | 5 |
| Full model v2 | 0.165538 | 0.101110 | 0.513695 | 0.500000 | 5 |

## Future validation (cutoff=2021 robustness)

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.203900 | 0.200413 | 0.276238 | 0.400000 | 4 |
| Unweighted PageRank | -0.090808 | -0.071594 | 0.175383 | 0.300000 | 3 |
| Time-aware PageRank | 0.103717 | 0.066975 | 0.497714 | 0.400000 | 4 |
| Semantic-weighted PageRank v2 | 0.090808 | 0.057737 | 0.465271 | 0.400000 | 4 |
| Semantic-temporal PageRank v2 | 0.088582 | 0.057737 | 0.497714 | 0.400000 | 4 |
| Full model v2 | 0.119742 | 0.076213 | 0.489123 | 0.400000 | 4 |