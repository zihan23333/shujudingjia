# Experiment Summary v2

| metric | value |
| --- | --- |
| total_citation_edges | 204.000000 |
| target_aligned_LLM_scored_edges | 91.000000 |
| default_fallback_edges | 113.000000 |
| target_aligned_LLM_coverage_ratio | 0.446078 |
| high_confidence_count | 73.000000 |
| grouped_count | 17.000000 |
| range_count | 1.000000 |
| ambiguous_count | 16.000000 |
| failed_count | 97.000000 |
| old_LLM_scored_edges_count | 123.000000 |
| old_LLM_retained_high_confidence_count | 67.000000 |

## Ranking comparison

| Method | Score column | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Citation Count | citation_count_score | 0.835266 | 0.707874 | 1 | 4 | 12.561905 | 65.500000 |
| Unweighted PageRank | unweighted_pagerank_score | 0.938527 | 0.821022 | 4 | 5 | 7.466667 | 36.000000 |
| Time-aware PageRank | time_aware_pagerank_score | 0.994733 | 0.959941 | 5 | 10 | 1.714286 | 12.000000 |
| Semantic-weighted PageRank | semantic_pagerank_score_v2 | 0.996713 | 0.972069 | 5 | 10 | 1.180952 | 13.000000 |
| Semantic-temporal PageRank | semantic_temporal_score_v2 | 0.996796 | 0.977582 | 5 | 10 | 1.028571 | 11.000000 |
| Full model v2 | full_model_score_v2 | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Ablation

| Variant | Edge weight | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | 1 | 0.938527 | 0.821022 | 4 | 5 | 7.466667 | 36.000000 |
| Semantic only | q_ij | 0.996713 | 0.972069 | 5 | 10 | 1.180952 | 13.000000 |
| Semantic + temporal | q_ij * tau_ij | 0.996796 | 0.977582 | 5 | 10 | 1.028571 | 11.000000 |
| Semantic + relation | q_ij * rho_ij | 0.998839 | 0.981992 | 5 | 10 | 0.780952 | 8.000000 |
| Full model | q_ij * tau_ij * rho_ij | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Confidence robustness

| Variant | Setting | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Confidence-aware | epsilon=0.3 | 0.999969 | 0.998897 | 5 | 10 | 0.057143 | 1.000000 |
| Confidence-aware | epsilon=0.5 | 0.999969 | 0.998897 | 5 | 10 | 0.057143 | 1.000000 |
| Confidence-aware | epsilon=0.7 | 0.999979 | 0.999265 | 5 | 10 | 0.038095 | 1.000000 |

## Extended relation robustness

| Variant | Setting | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Extended relation | rho(co,tc,inst) | 0.999305 | 0.986770 | 5 | 10 | 0.628571 | 3.000000 |

## Future validation (main)

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.109484 | 0.119183 | 0.289216 | 0.400000 | 4 |
| Unweighted PageRank | -0.059121 | -0.056720 | 0.203180 | 0.400000 | 4 |
| Time-aware PageRank | 0.157901 | 0.086313 | 0.523067 | 0.500000 | 5 |
| Semantic-weighted PageRank v2 | 0.177115 | 0.106042 | 0.515858 | 0.500000 | 5 |
| Semantic-temporal PageRank v2 | 0.150757 | 0.086313 | 0.515847 | 0.500000 | 5 |
| Full model v2 | 0.162828 | 0.101110 | 0.515847 | 0.500000 | 5 |

## Future validation (cutoff=2021 robustness)

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.203900 | 0.200413 | 0.276238 | 0.400000 | 4 |
| Unweighted PageRank | -0.090808 | -0.071594 | 0.175383 | 0.300000 | 3 |
| Time-aware PageRank | 0.103717 | 0.066975 | 0.497714 | 0.400000 | 4 |
| Semantic-weighted PageRank v2 | 0.133096 | 0.085451 | 0.490243 | 0.400000 | 4 |
| Semantic-temporal PageRank v2 | 0.109281 | 0.066975 | 0.490243 | 0.400000 | 4 |
| Full model v2 | 0.124193 | 0.076213 | 0.490243 | 0.400000 | 4 |