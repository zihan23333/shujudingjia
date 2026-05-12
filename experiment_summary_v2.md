# Experiment Summary v2

## Semantic layer rebuild

| metric | value |
| --- | --- |
| llm_results_target_aligned_v2_rows | 91 |
| deepseek_backend_rows | 91 |
| offline_fallback_backend_rows | 0 |
| high_confidence_count | 73 |
| grouped_count | 17 |
| range_count | 1 |
| ambiguous_count | 16 |
| failed_count | 97 |
| target_aligned_llm_scored_edges | 91 |
| semantic_fallback_edges | 113 |
| semantic_edge_weights_v2_covers_all_204 | 1 |
| formal_experiments_still_read_old_llm_results_csv | 0 |
| ambiguous_failed_edges_using_old_llm_scores | 0 |
| pdf_roots_scored_edges_before_fix | 78 |
| pdf_roots_scored_edges_after_fix | 91 |
| pdf_roots_high_confidence_before_fix | 63 |
| pdf_roots_high_confidence_after_fix | 73 |

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

## Sentiment-neutralized robustness

| Variant | Spearman with Full model v2.1 | Kendall with Full model v2.1 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- |
| semantic-only-no-sentiment | 0.996910 | 0.970599 | 5 | 10 | 1.238095 | 12.000000 |
| semantic-temporal-no-sentiment | 0.997678 | 0.980154 | 5 | 10 | 0.895238 | 9.000000 |
| full-model-no-sentiment | 0.999730 | 0.994487 | 5 | 10 | 0.266667 | 4.000000 |

## Future validation (cutoff = 2020, future = 2021?2024)

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.109484 | 0.119183 | 0.289216 | 0.400000 | 4 |
| Unweighted PageRank | -0.059121 | -0.056720 | 0.203180 | 0.400000 | 4 |
| Time-aware PageRank | 0.157901 | 0.086313 | 0.523067 | 0.500000 | 5 |
| Semantic-weighted PageRank v2 | 0.177115 | 0.106042 | 0.515858 | 0.500000 | 5 |
| Semantic-temporal PageRank v2 | 0.150757 | 0.086313 | 0.515847 | 0.500000 | 5 |
| Full model v2 | 0.162828 | 0.101110 | 0.515847 | 0.500000 | 5 |

## Future validation (cutoff = 2021, future = 2022?2024)

| Method | Spearman | Kendall | NDCG@10 | Precision@10 | Top-10 overlap |
| --- | --- | --- | --- | --- | --- |
| Citation Count | 0.203900 | 0.200413 | 0.276238 | 0.400000 | 4 |
| Unweighted PageRank | -0.090808 | -0.071594 | 0.175383 | 0.300000 | 3 |
| Time-aware PageRank | 0.103717 | 0.066975 | 0.497714 | 0.400000 | 4 |
| Semantic-weighted PageRank v2 | 0.133096 | 0.085451 | 0.490243 | 0.400000 | 4 |
| Semantic-temporal PageRank v2 | 0.109281 | 0.066975 | 0.490243 | 0.400000 | 4 |
| Full model v2 | 0.124193 | 0.076213 | 0.490243 | 0.400000 | 4 |

## Pricing

| paper_id | title | full_model_score_v2 | value_norm | query_similarity | WTP | price | price_rank | scenario |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W2097281067 | TUBE | 0.872804 | 1.000000 | 0.000000 | 1.000000 | 0.500000 | 1 | Base Case |
| W2168402580 | Query-based data pricing | 0.144672 | 0.165756 | 0.430605 | 1.597966 | 0.332400 | 2 | Base Case |
| W2974598553 | Too Much Data: Prices and Inefficiencies in Data Markets | 0.379287 | 0.434562 | 0.090890 | 0.932318 | 0.281650 | 3 | Base Case |
| W2180742472 | Smart data pricing | 0.050457 | 0.057811 | 0.588335 | 1.506576 | 0.256470 | 4 | Base Case |
| W2010653253 | A survey of smart data pricing | 0.089331 | 0.102350 | 0.432037 | 1.320175 | 0.245318 | 5 | Base Case |
| W3123243120 | Nonrivalry and the Economics of Data | 0.341979 | 0.391817 | 0.062667 | 0.713582 | 0.204895 | 6 | Base Case |
| W2293940046 | Query-Based Data Pricing | 0.057179 | 0.065512 | 0.430605 | 1.152398 | 0.199283 | 7 | Base Case |
| W4323644227 | A Survey of Data Pricing for Data Marketplaces | 0.011321 | 0.012971 | 0.414625 | 0.885244 | 0.136805 | 8 | Base Case |
| W2743929098 | Data pricing strategy based on data quality | 0.030036 | 0.034413 | 0.341036 | 0.810375 | 0.131317 | 9 | Base Case |
| W3084177365 | A Survey on Data Pricing: From Economics to Data Science | 0.021208 | 0.024298 | 0.329108 | 0.746490 | 0.118322 | 10 | Base Case |