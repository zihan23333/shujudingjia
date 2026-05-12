# Method Revision Notes Final

1. The formal semantic layer is derived from target-aligned citation contexts rather than the archived exploratory `llm_results.csv`.
2. The final semantic layer contains 113 DeepSeek target-aligned scored citation edges out of 204 total citation edges.
3. The final semantic coverage ratio is 55.39%, and the remaining 91 edges use the default semantic weight `q_ij = 0.3`.
4. Confidence is retained only as a quality-control field and does not enter the main formula.
5. Institution relations do not enter the main model and are used only in extended robustness analysis.
6. Grouped and range citations may be scored only when the target marker is explicitly traceable in the target-aligned context.
7. No formal experiment reads the old `llm_results.csv`, and no offline fallback backend is mixed into the final semantic layer.