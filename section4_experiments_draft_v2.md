# Section 4 Draft v2

## 4.1 Experimental setup

The revised experiment pipeline no longer uses the archived exploratory `llm_results.csv` as the formal semantic input. Instead, the v2 semantic layer is rebuilt from target-aligned citation contexts. Edges with ambiguous or failed alignment fall back to the default semantic weight.

## 4.2 Target-aligned semantic layer reconstruction

Target-alignment reconstruction covers 204 citation edges. The audit yields 63 high-confidence edges, 14 grouped edges, 1 range edges, 10 ambiguous edges, and 116 failed edges. The formal v2 semantic layer therefore covers 38.24% of citation edges with target-aligned semantic scores, while the remaining edges use the default semantic weight.

## 4.3 Future citation validation

Under the main validation setting (cutoff=2020, future window=2021–2024), the Full model v2 reaches Spearman 0.1655, compared with 0.1095 for Citation Count. This result should be interpreted carefully: future citations are more directly tied to cumulative diffusion scale and topic heat, whereas the present framework targets semantically calibrated article-level value.

## 4.4 Overall ranking comparison

The top-ranked papers under Full model v2 remain led by TUBE, Too Much Data: Prices and Inefficiencies in Data Markets, Nonrivalry and the Economics of Data, Optimal Sticky Prices under Rational Inattention, Query-based data pricing. This indicates that target-aligned semantic reconstruction preserves the head structure while replacing the archived exploratory semantic layer.

## 4.5 Ablation study

The ablation study shows that semantic information remains the strongest differentiating component, while temporal and relation-aware factors act as calibration terms. Structure only reaches Spearman 0.9357 with respect to Full model v2.

## 4.6 Robustness analysis

Confidence-aware variants remain close to the Full model v2, supporting the decision not to inject confidence into the main formula. The extended relation model also remains close to the main model, which justifies keeping institution relations outside the main specification.

## 4.7 Personalized pricing analysis

Under the v2 Full model, the top price papers are TUBE, Query-based data pricing, Smart data pricing, Too Much Data: Prices and Inefficiencies in Data Markets, A survey of smart data pricing. The pricing results still show the intended moderation pattern: high-value but low-similarity papers are not over-priced, while high-similarity but lower-value papers are not allowed to dominate the head purely through query matching.

## 4.8 Summary

Overall, the v2 pipeline replaces the archived exploratory semantic layer with a target-aligned semantic reconstruction, preserves the core ranking and pricing logic, and keeps confidence and institution relations outside the main model while retaining them for robustness analysis.