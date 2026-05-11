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
| Citation Count | citation_count_score | 0.832114 | 0.700125 | 1 | 4 | 12.628571 | 68.500000 |
| Unweighted PageRank | unweighted_pagerank_score | 0.941544 | 0.828372 | 4 | 5 | 7.200000 | 33.000000 |
| Time-aware PageRank | time_aware_pagerank_score | 0.995137 | 0.968026 | 5 | 10 | 1.352381 | 15.000000 |
| Semantic-weighted PageRank | semantic_pagerank_score_v2 | 0.996454 | 0.968761 | 5 | 10 | 1.314286 | 15.000000 |
| Semantic-temporal PageRank | semantic_temporal_score_v2 | 0.997595 | 0.979052 | 5 | 10 | 0.914286 | 9.000000 |
| Full model v2 | full_model_score_v2 | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Ablation

| Variant | Edge weight | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | 1 | 0.941544 | 0.828372 | 4 | 5 | 7.200000 | 33.000000 |
| Semantic only | q_ij | 0.996454 | 0.968761 | 5 | 10 | 1.314286 | 15.000000 |
| Semantic + temporal | q_ij * tau_ij | 0.997595 | 0.979052 | 5 | 10 | 0.914286 | 9.000000 |
| Semantic + relation | q_ij * rho_ij | 0.998797 | 0.980522 | 5 | 10 | 0.933333 | 6.000000 |
| Full model | q_ij * tau_ij * rho_ij | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Confidence robustness

| Variant | Setting | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Confidence-aware | epsilon=0.3 | 0.999876 | 0.997795 | 5 | 10 | 0.114286 | 4.000000 |
| Confidence-aware | epsilon=0.5 | 0.999876 | 0.997795 | 5 | 10 | 0.114286 | 4.000000 |
| Confidence-aware | epsilon=0.7 | 0.999959 | 0.998897 | 5 | 10 | 0.057143 | 2.000000 |

## Extended relation robustness

| Variant | Setting | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Extended relation | rho(co,tc,inst) | 0.999077 | 0.983829 | 5 | 10 | 0.761905 | 4.000000 |

## Future validation (main)

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.109484 | 0.119183 | 0.289216 | 0.400000 | 4 |
| Unweighted PageRank | -0.059121 | -0.056720 | 0.203180 | 0.400000 | 4 |
| Time-aware PageRank | 0.157901 | 0.086313 | 0.523067 | 0.500000 | 5 |
| Semantic-weighted PageRank v2 | 0.159379 | 0.091245 | 0.515858 | 0.500000 | 5 |
| Semantic-temporal PageRank v2 | 0.151743 | 0.086313 | 0.515847 | 0.500000 | 5 |
| Full model v2 | 0.153714 | 0.086313 | 0.513130 | 0.500000 | 5 |

## Future validation (cutoff=2021 robustness)

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.203900 | 0.200413 | 0.276238 | 0.400000 | 4 |
| Unweighted PageRank | -0.090808 | -0.071594 | 0.175383 | 0.300000 | 3 |
| Time-aware PageRank | 0.103717 | 0.066975 | 0.497714 | 0.400000 | 4 |
| Semantic-weighted PageRank v2 | 0.120855 | 0.076213 | 0.490243 | 0.400000 | 4 |
| Semantic-temporal PageRank v2 | 0.115958 | 0.080832 | 0.490243 | 0.400000 | 4 |
| Full model v2 | 0.125083 | 0.080832 | 0.487823 | 0.400000 | 4 |