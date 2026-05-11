# Final Experiment Checklist v2

[x] target_aligned_contexts.csv exists
[x] llm_results_target_aligned_v2.csv exists
[x] semantic_edge_weights_v2.csv covers all 204 citation edges
[x] ranking v2 generated
[x] ablation v2 generated
[x] confidence robustness v2 generated
[x] extended relation robustness v2 generated
[x] future validation cutoff=2020 v2 generated
[x] future validation cutoff=2021 v2 generated
[x] pricing v2 generated
[x] LLM reliability annotation package v2 generated
[x] section4_experiments_draft_v2.md generated

## Manual consistency checks

- Formal v2 scripts should not read the old `llm_results.csv` as the main semantic input.
- No future window should be written as 2021–2025.
- Institution relations must stay outside the main model.
- Confidence must stay outside the main model.
- Ambiguous/failed edges must not reuse old LLM scores.