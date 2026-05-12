# DeepSeek v2.1 Semantic Layer Audit

The formal v2.1 experiments use DeepSeek-scored target-aligned citation contexts. The old llm_results.csv is archived and no longer used as the main semantic input.

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

## Acceptance sample (10 edges for manual spot-check)

| sample_id | edge_id | citing_paper_title | cited_paper_title | alignment_status | section | sentiment | relevance | q_ij |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A01 | W3195579788->W3084177365 | Data pricing in machine learning pipelines | A Survey on Data Pricing: From Economics to Data Science | grouped | Discussion | 0.000000 | 0.700000 | 0.171500 |
| A02 | W4377865288->W2910976764 | The Dimensions of Data Labor: A Road Map for Researchers, Activists, and Policymakers to Empower Data Producers | Nonrivalry and the Economics of Data | grouped | Introduction | 0.500000 | 0.700000 | 0.147000 |
| A03 | W2934375453->W2743929098 | Personal Data Market Optimization Pricing Model Based on Privacy Level | Data pricing strategy based on data quality | grouped | Methodology | 0.500000 | 0.600000 | 0.270000 |
| A04 | W4226305897->W2920282816 | Business Data Sharing through Data Marketplaces: A Systematic Literature Review | Pricing for Revenue Maximization in IoT Data Markets: An Information Design Perspective | grouped | Result | 0.500000 | 0.700000 | 0.367500 |
| A05 | W3021125948->W2996741051 | Contract Design in Hierarchical Game for Sponsored Content Service Market | Dynamic Pricing for Revenue Maximization in Mobile Social Data Market With Network Effects | high_confidence | Conclusion | 0.000000 | 0.400000 | 0.040000 |
| A06 | W3195579788->W2612128091 | Data pricing in machine learning pipelines | QIRANA | high_confidence | Discussion | 0.500000 | 0.700000 | 0.257250 |
| A07 | W2996741051->W2581979418 | Dynamic Pricing for Revenue Maximization in Mobile Social Data Market With Network Effects | When Social Network Effect Meets Congestion Effect in Wireless Networks: Data Usage Equilibrium and Optimal Pricing | high_confidence | Introduction | 0.500000 | 0.900000 | 0.243000 |
| A08 | W3084177365->W2168402580 | A Survey on Data Pricing: From Economics to Data Science | Query-based data pricing | high_confidence | Methodology | 0.500000 | 0.800000 | 0.480000 |
| A09 | W3084177365->W2126626399 | A Survey on Data Pricing: From Economics to Data Science | The Price Is Right | high_confidence | Other | 0.500000 | 0.600000 | 0.054000 |
| A10 | W2790400697->W2734426755 | A Survey on Big Data Market: Pricing, Trading and Protection | An Online Pricing Mechanism for Mobile Crowdsensing Data Markets | high_confidence | Result | 0.300000 | 0.600000 | 0.234000 |

- PDF_ROOTS fix improved scored-edge coverage from `78` to `91` and high-confidence edges from `63` to `73`.
- DeepSeek backend rows: `91`; offline fallback backend rows: `0`.
- `semantic_edge_weights_v2.csv` covers all `204` citation edges and uses fallback `q=0.3` for `113` edges.
- Ambiguous/failed edges reusing old LLM scores: `0`.