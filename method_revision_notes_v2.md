# Method Revision Notes v2

1. The old `llm_results.csv` is archived and no longer used as the formal main semantic input.
2. The formal semantic layer is rebuilt from target-aligned citation contexts and rescored by DeepSeek.
3. The rebuilt semantic layer contains `91` DeepSeek-scored edges out of `204` citation edges, for a coverage ratio of `44.61%`.
4. Among the scored edges, `73` are high-confidence, `17` are grouped citations, and `1` is a range citation.
5. Edges with `alignment_status` in `{ambiguous, failed}` use the default semantic weight `q_ij = 0.3`.
6. Confidence remains a quality-control field and does not enter the main weight formula.
7. Institution relations do not enter the main model and are only used in extended robustness analysis.
8. The current DeepSeek semantic layer produces no negative sentiment predictions; this limitation must be stated explicitly.
9. Sentiment-neutralized robustness shows that the no-sentiment full-model variant keeps Spearman `0.9997` and Top-10 overlap `10 / 10` relative to the formal Full model v2.1, supporting the interpretation that sentiment is only an auxiliary calibration signal.
10. Future citation validation windows remain `2021?2024` and `2022?2024`; do not write `2021?2025`.