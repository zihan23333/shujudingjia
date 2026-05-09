# Experiment Summary

## Input status
| file_name | exists | resolved_path |
| --- | --- | --- |
| all_connected_papers.csv | True | D:\数据集\数据定价\all_connected_papers.csv |
| all_network_edges.csv | True | D:\数据集\数据定价\all_network_edges.csv |
| contexts.csv | True | D:\数据集\数据定价\contexts.csv |
| contexts_final.csv | True | D:\数据集\数据定价\contexts_final.csv |
| llm_results.csv | True | D:\数据集\数据定价\llm_results.csv |
| weighted_edge_weights.csv | True | D:\数据集\数据定价\weighted_edge_weights.csv |
| weighted_pagerank_ranking.csv | True | D:\数据集\数据定价\weighted_pagerank_ranking.csv |
| unweighted_pagerank_ranking.csv | True | D:\数据集\数据定价\unweighted_pagerank_ranking.csv |
| weighted_pagerank_ranking_with_penalty.csv | True | D:\数据集\new\weighted_pagerank_ranking_with_penalty.csv |
| ranking_comparison_detailed.csv | True | D:\数据集\new\ranking_comparison_detailed.csv |
| weighted_edges_comparison.csv | True | D:\数据集\new\weighted_edges_comparison.csv |
| weighted_wtp_analysis.csv | True | D:\数据集\数据定价\weighted_wtp_analysis.csv |
| weighted_wtp_analysis_with_penalty.csv | True | D:\数据集\new\weighted_wtp_analysis_with_penalty.csv |
| penalty_pricing_comparison.csv | True | D:\数据集\new\penalty_pricing_comparison.csv |
| sensitivity_analysis.csv | True | D:\数据集\数据定价\sensitivity_analysis.csv |
| HIN_network.graphml | True | D:\数据集\new\HIN_network.graphml |
| authorships_network.csv | True | D:\数据集\new\authorships_network.csv |
| enhanced_paper_edges.csv | True | D:\数据集\new\enhanced_paper_edges.csv |

## Dataset statistics
| metric | value |
| --- | --- |
| paper_nodes | 105 |
| citation_edges | 204 |
| heterogeneous_total_edges | 1030 |
| heterogeneous_citation_edges | 204 |
| largest_weak_component_nodes | 105 |
| average_in_degree | 1.942857 |
| average_out_degree | 1.942857 |
| max_in_degree | 15 |
| max_out_degree | 12 |
| network_density | 0.01868132 |
| has_isolates | No |
| isolate_count | 0 |
| core_paper_count | 30 |
| llm_scored_edges | 123 |
| unscored_edges | 81 |
| self_citation_edges | 27 |
| self_citation_ratio | 0.132353 |
| average_shared_authors | 0.382353 |

## Ranking consistency
| comparison | spearman | top5_overlap | top10_overlap | avg_rank_change | max_rank_change |
| --- | --- | --- | --- | --- | --- |
| Full vs Unweighted PageRank | 0.919087 | 4 | 5 | 8.476190 | 53.000000 |
| Full vs Citation Count | 0.854959 | 1 | 4 | 11.504762 | 72.500000 |
| Semantic-Temporal vs Semantic | 0.999627 | 5 | 10 | 0.419048 | 4.000000 |
| Full vs Semantic-Temporal | 0.996879 | 5 | 9 | 0.952381 | 14.000000 |

## Ablation summary
| comparison | spearman | top5_overlap | top10_overlap | avg_rank_change | max_rank_change |
| --- | --- | --- | --- | --- | --- |
| structure_only | 0.919087 | 4 | 5 | 8.476190 | 53.000000 |
| semantic_only | 0.997356 | 5 | 9 | 0.971429 | 11.000000 |
| semantic_temporal | 0.996879 | 5 | 9 | 0.952381 | 14.000000 |
| semantic_relation | 0.999855 | 5 | 10 | 0.209524 | 2.000000 |
| full_model | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Confidence-aware variant
| epsilon | spearman | top5_overlap | top10_overlap | avg_rank_change | max_rank_change |
| --- | --- | --- | --- | --- | --- |
| 0.300000 | 0.999990 | 5 | 10 | 0.019048 | 1.000000 |
| 0.500000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |
| 0.700000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## Extended relation robustness
| comparison | spearman | top5_overlap | top10_overlap | avg_rank_change | max_rank_change | penalized_edges_main | penalized_edges_extended | edges_with_team_collab | edges_with_shared_institutions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Extended relation robustness | 0.998839 | 5 | 10 | 0.742857 | 7.000000 | 27 | 43 | 28 | 40 |

## Pricing sensitivity
| scenario | alpha | beta | top5_overlap | avg_price_change | max_price_change | avg_rank_change | max_rank_change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Conservative | 1.000000 | 5.000000 | 5 | 0.018909 | 0.167410 | 3.009524 | 17.000000 |
| Base Case | 1.000000 | 10.000000 | 5 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| Aggressive | 1.000000 | 15.000000 | 5 | 0.018909 | 0.167410 | 1.409524 | 12.000000 |
| Quality Priority | 1.500000 | 8.000000 | 5 | 0.010005 | 0.250000 | 2.723810 | 15.000000 |
| Similarity Priority | 0.500000 | 12.000000 | 5 | 0.010005 | 0.250000 | 2.057143 | 23.000000 |