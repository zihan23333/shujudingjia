# 4 Experiments

## 4.1 Experimental setup

The revised v2.1 pipeline no longer uses the archived exploratory `llm_results.csv` as the main semantic input. Instead, the formal semantic layer is built from target-aligned citation contexts and rescored by DeepSeek. The citation network still contains 105 papers and 204 citation edges, while the semantic layer now covers 91 target-aligned citation edges and falls back to the default semantic weight on the remaining 113 edges.

## 4.2 Target-aligned semantic layer reconstruction

The alignment audit yields 73 high-confidence edges, 17 grouped edges, 1 range edge, 16 ambiguous edges, and 97 failed edges. Therefore, the formal v2.1 semantic layer covers 44.61% of all citation edges with DeepSeek-scored target-aligned contexts. The old `llm_results.csv` is retained only as an archived exploratory result and is no longer used in formal experiments.

## 4.3 Future citation validation

Under the main validation setting (cutoff = 2020, future window = 2021?2024), the Full model v2.1 reaches Spearman 0.1628, compared with 0.1095 for Citation Count, -0.0591 for Unweighted PageRank, and 0.1579 for Time-aware PageRank. Under the robustness setting (cutoff = 2021, future window = 2022?2024), the Full model v2.1 reaches Spearman 0.1242, compared with 0.2039 for Citation Count, -0.0908 for Unweighted PageRank, and 0.1037 for Time-aware PageRank. Citation Count remains the strongest predictor of future citation volume in Spearman terms, which is consistent with the fact that future citations are more directly tied to cumulative diffusion scale and topic popularity than to the semantically calibrated notion of article-level value targeted here.

## 4.4 Overall ranking comparison

The top five papers under the Full model v2.1 are TUBE, Too Much Data: Prices and Inefficiencies in Data Markets, Nonrivalry and the Economics of Data, Optimal Sticky Prices under Rational Inattention, Query-based data pricing. Full model v2.1 remains highly consistent with the Time-aware, Semantic-only, and Semantic-temporal variants, while showing larger but still structured deviations from Citation Count and Unweighted PageRank. This indicates that the target-aligned semantic rebuild preserves the head structure while refining mid- and lower-ranked papers.

## 4.5 Ablation study

The ablation results continue to show that semantic information is the main differentiating signal. Structure only reaches Spearman 0.9385 with respect to the Full model v2.1, while Semantic + temporal and Semantic + relation remain much closer to the full model. This pattern supports the interpretation that section and relevance provide the main semantic gain, while temporal and relation-aware terms act as calibration factors.

## 4.6 Robustness analysis

Confidence-aware variants remain almost unchanged relative to the Full model v2.1, so confidence is still kept outside the main formula. The extended relation model also remains close to the main model, which supports keeping institution relations outside the main specification. In addition, the DeepSeek semantic layer currently produces no negative sentiment predictions. The sentiment-neutralized robustness test shows that the no-sentiment full-model variant still keeps Spearman 0.9997, Kendall 0.9945, Top-5 overlap 5 / 5, and Top-10 overlap 10 / 10 relative to the formal Full model v2.1, indicating that sentiment mainly acts as an auxiliary calibration signal, while section and relevance dominate semantic quality estimation.

## 4.7 Personalized pricing analysis

Under the refreshed Full model v2.1 scores, the top five priced papers in the Base Case are TUBE, Query-based data pricing, Too Much Data: Prices and Inefficiencies in Data Markets, Smart data pricing, A survey of smart data pricing. The pricing sensitivity analysis remains stable at the head: the Base Case Top-5 stays largely consistent across scenarios, while parameter changes mainly alter price magnitudes and middle-to-lower ranking positions rather than overturning the head results.

## 4.8 Summary

Overall, the v2.1 pipeline replaces the archived exploratory semantic layer with DeepSeek-scored target-aligned citation contexts, keeps confidence and institution relations outside the main model, and shows that the main ranking and pricing conclusions remain stable after the semantic rebuild. The main remaining limitation is that the current DeepSeek layer produces no negative sentiment predictions, but the sentiment-neutralized robustness test indicates that this limitation does not materially overturn the core ranking conclusions.