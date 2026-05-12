# v2.2 Manual Promotion Summary

| metric | value |
| --- | --- |
| candidate_rescued_edges | 21.000000 |
| manually_accepted_edges | 21.000000 |
| rejected_ambiguous_edges | 0.000000 |
| rejected_wrong_edges | 0.000000 |
| final_target_aligned_edges | 112.000000 |
| final_coverage_ratio | 0.549020 |

- Review source: `rescued_edges_for_manual_review_v22_all_correct.csv`
- Formal v2.2 file written to `target_aligned_contexts_v22.csv`.
- Only rows with `human_alignment_status = correct` are promoted from the candidate alignment layer.
- Rows marked `ambiguous` or `wrong` stay on the original v2.1 alignment status and later fall back to default semantic weight if still unscored.