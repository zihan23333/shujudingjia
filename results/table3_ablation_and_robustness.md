| section | model_or_variant | spearman | top5_overlap | top10_overlap | avg_rank_change | max_rank_change | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ablation | structure_only | 0.919087 | 4.000000 | 5.000000 | 8.476190 | 53.000000 |  |
| Ablation | semantic_only | 0.997356 | 5.000000 | 9.000000 | 0.971429 | 11.000000 |  |
| Ablation | semantic_temporal | 0.996879 | 5.000000 | 9.000000 | 0.952381 | 14.000000 |  |
| Ablation | semantic_relation | 0.999855 | 5.000000 | 10.000000 | 0.209524 | 2.000000 |  |
| Ablation | full_model | 1.000000 | 5.000000 | 10.000000 | 0.000000 | 0.000000 |  |
| Extended robustness | team_and_institution_relations | 0.998839 | 5.000000 | 10.000000 | 0.742857 | 7.000000 | main penalized edges=27; extended penalized edges=43 |
| Confidence robustness | confidence_epsilon_0.3 | 0.999990 | 5.000000 | 10.000000 | 0.019048 | 1.000000 |  |
| Confidence robustness | confidence_epsilon_0.5 | 1.000000 | 5.000000 | 10.000000 | 0.000000 | 0.000000 |  |
| Confidence robustness | confidence_epsilon_0.7 | 1.000000 | 5.000000 | 10.000000 | 0.000000 | 0.000000 |  |