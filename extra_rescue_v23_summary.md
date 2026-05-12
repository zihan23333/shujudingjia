# Extra Rescue v2.3 Summary

- Candidate count: `1`
- Human confirmed `correct`: `0`
- Human confirmed `ambiguous`: `0`
- Human confirmed `wrong`: `0`
- Current formal scored edges remain: `112`
- Current formal coverage ratio remains: `54.90%`
- Suggest upgrade to v2.3 now: `No`

Interpretation:
- This is intentionally a single, conservative extra-rescue round on top of the formal v2.2 layer.
- Only edges from `title_fuzzy_match_failed` and `citation_marker_not_found` were considered.
- `missing_pdf_or_text` was not revisited.
- If manual review later confirms at least 8 additional edges as `correct`, then a formal `target_aligned_contexts_v23.csv` upgrade can be justified; otherwise the current 112-edge v2.2 layer should remain the formal semantic layer.