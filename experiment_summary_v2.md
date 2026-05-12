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
| Citation Count | citation_count_score | 0.828183 | 0.700125 | 1 | 4 | 12.609524 | 71.500000 |
| Unweighted PageRank | unweighted_pagerank_score | 0.940352 | 0.824329 | 4 | 5 | 7.352381 | 34.000000 |
| Time-aware PageRank | time_aware_pagerank_score | 0.996423 | 0.968394 | 5 | 10 | 1.390476 | 11.000000 |
| Semantic-weighted PageRank | semantic_pagerank_score_v2 | 0.996827 | 0.970967 | 5 | 9 | 1.142857 | 12.000000 |
| Semantic-temporal PageRank | semantic_temporal_score_v2 | 0.997232 | 0.979419 | 5 | 9 | 0.933333 | 11.000000 |
| Full model v2 | full_model_score_v2 | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Ablation

| Variant | Edge weight | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | 1 | 0.940352 | 0.824329 | 4 | 5 | 7.352381 | 34.000000 |
| Semantic only | q_ij | 0.996827 | 0.970967 | 5 | 9 | 1.142857 | 12.000000 |
| Semantic + temporal | q_ij * tau_ij | 0.997232 | 0.979419 | 5 | 9 | 0.933333 | 11.000000 |
| Semantic + relation | q_ij * rho_ij | 0.998600 | 0.980889 | 5 | 10 | 0.819048 | 9.000000 |
| Full model | q_ij * tau_ij * rho_ij | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Confidence robustness

| Variant | Setting | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Confidence-aware | epsilon=0.3 | 0.999844 | 0.995957 | 5 | 10 | 0.190476 | 2.000000 |
| Confidence-aware | epsilon=0.5 | 0.999917 | 0.997427 | 5 | 10 | 0.114286 | 2.000000 |
| Confidence-aware | epsilon=0.7 | 0.999959 | 0.998897 | 5 | 10 | 0.057143 | 2.000000 |

## Extended relation robustness

| Variant | Setting | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Extended relation | rho(co,tc,inst) | 0.999160 | 0.984932 | 5 | 10 | 0.685714 | 4.000000 |

## Future validation (main)

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.109484 | 0.119183 | 0.289216 | 0.400000 | 4 |
| Unweighted PageRank | -0.059121 | -0.056720 | 0.203180 | 0.400000 | 4 |
| Time-aware PageRank | 0.157901 | 0.086313 | 0.523067 | 0.500000 | 5 |
| Semantic-weighted PageRank v2 | 0.132282 | 0.086313 | 0.523333 | 0.500000 | 5 |
| Semantic-temporal PageRank v2 | 0.122922 | 0.061652 | 0.521469 | 0.500000 | 5 |
| Full model v2 | 0.125878 | 0.071517 | 0.515847 | 0.500000 | 5 |

## Future validation (cutoff=2021 robustness)

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.203900 | 0.200413 | 0.276238 | 0.400000 | 4 |
| Unweighted PageRank | -0.090808 | -0.071594 | 0.175383 | 0.300000 | 3 |
| Time-aware PageRank | 0.103717 | 0.066975 | 0.497714 | 0.400000 | 4 |
| Semantic-weighted PageRank v2 | 0.084353 | 0.057737 | 0.497714 | 0.400000 | 4 |
| Semantic-temporal PageRank v2 | 0.075451 | 0.030023 | 0.496779 | 0.400000 | 4 |
| Full model v2 | 0.082573 | 0.043880 | 0.490243 | 0.400000 | 4 |