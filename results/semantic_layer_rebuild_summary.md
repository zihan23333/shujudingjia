# Semantic Layer Rebuild Summary

The old `llm_results.csv` is no longer used as the formal main semantic input.
The current v2 semantic layer is derived from target-aligned citation contexts, with ambiguous/failed edges falling back to the default semantic weight `q_ij = 0.3`.

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

- Main semantic backend observed in `llm_results_target_aligned_v2.csv`: `deepseek:deepseek-chat`
- Confidence is retained only as a quality-control field and does not enter the main formula.
- Institution relations remain excluded from the main model and are only used in extended robustness analysis.