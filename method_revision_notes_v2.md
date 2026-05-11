# Method Revision Notes v2

1. The old `llm_results.csv` is no longer used as the formal main semantic input.
2. The formal v2 semantic layer is derived from target-aligned citation contexts reconstructed in `target_aligned_contexts.csv`.
3. Edges with `alignment_status` in `{ambiguous, failed}` fall back to the default semantic weight `q_ij = 0.3`.
4. Grouped and range citations may still enter the semantic scorer, but their target marker and grouped/range status are recorded explicitly.
5. Confidence remains a quality-control field and does not enter the main weight formula.
6. Institution relations do not enter the main model and are only used in extended robustness analysis.

Current execution note: `task6.12_rerun_llm_on_target_aligned_contexts.py` supports API-based scoring, but in the present local environment network access was unavailable, so the produced v2 semantic file uses the script's offline fallback backend. This is recorded explicitly in `llm_results_target_aligned_v2.csv`.