# Section 4 Draft Final

## 4.1 Experimental setup

The final experiment pipeline uses 113 DeepSeek-scored target-aligned citation edges and 91 default-fallback citation edges. Confidence does not enter the main model, and institution relations remain outside the main model.

## 4.2 Target-aligned semantic layer reconstruction

The formal semantic layer was reconstructed conservatively from target-aligned citation contexts. Coverage increased from 91 to 112 and then to 113 accepted target-aligned edges after conservative rescue and manual verification. We stop further rescue at this point because the remaining bottlenecks are mainly missing PDF/text sources, reference parsing failures, and citation-marker detection limits; pushing coverage further would materially increase the risk of target-context misalignment.

## 4.3 Future citation validation

Under the main setting (cutoff=2020, future=2021-2024), the Full model final reaches Spearman `0.1707` and NDCG@10 `0.5158`. Under the robustness setting (cutoff=2021, future=2022-2024), the Full model final reaches Spearman `0.1355` and NDCG@10 `0.4902`.

## 4.4 Overall ranking comparison

| Method | Score column | Spearman with Full model final | Kendall with Full model final | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Citation Count | citation_count_score | 0.832845 | 0.705291 | 1 | 4 | 12.704762 | 69.500000 |
| Unweighted PageRank | unweighted_pagerank_score | 0.935541 | 0.818817 | 4 | 5 | 7.542857 | 44.000000 |
| Time-aware PageRank | time_aware_pagerank_score | 0.992711 | 0.951121 | 5 | 10 | 1.847619 | 21.000000 |
| Semantic-weighted PageRank final | semantic_pagerank_score_final | 0.996775 | 0.970599 | 5 | 10 | 1.295238 | 13.000000 |
| Semantic-temporal PageRank final | semantic_temporal_score_final | 0.997460 | 0.979419 | 5 | 10 | 0.895238 | 10.000000 |
| Full model final | full_model_score_final | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## 4.5 Ablation study

| Variant | Edge weight | Spearman with Full model final | Kendall with Full model final | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | unweighted_pagerank_score | 0.935541 | 0.818817 | 4 | 5 | 7.542857 | 44.000000 |
| Semantic only | semantic_pagerank_score_final | 0.996775 | 0.970599 | 5 | 10 | 1.295238 | 13.000000 |
| Semantic + temporal | semantic_temporal_score_final | 0.997460 | 0.979419 | 5 | 10 | 0.895238 | 10.000000 |
| Semantic + relation | semantic_relation_score_final | 0.998175 | 0.980889 | 5 | 10 | 0.876190 | 12.000000 |
| Full model final | full_model_score_final | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |

## 4.6 Robustness and sensitivity analysis

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

The no-sentiment robustness remains highly consistent with the full model final, supporting the interpretation that sentiment mainly serves as an auxiliary calibration signal, while section and relevance dominate semantic quality estimation.

## 4.7 Personalized pricing analysis

Under the Base Case, the Top-5 priced papers are: TUBE, Query-based data pricing, Too Much Data: Prices and Inefficiencies in Data Markets, Smart data pricing, A survey of smart data pricing.

## 4.8 Summary

The final 113-edge DeepSeek target-aligned semantic layer preserves the main conclusions of the paper while using a substantially cleaner semantic input than the earlier exploratory semantic layer.

### LLM semantic evaluation reliability

A representative sample and a hard-case audit sample have been prepared from the final 113-edge DeepSeek semantic layer. After human annotation is completed, we will report section accuracy, relevance correlation, human_q vs LLM_q correlation, and a separate hard-case audit summary. No reliability metrics are inserted here before human annotation is completed.