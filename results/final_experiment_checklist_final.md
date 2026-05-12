# Final Experiment Checklist

- [x] `target_aligned_contexts_final.csv` generated
- [x] Final accepted alignment-approved edges frozen at 113
- [x] `table_semantic_layer_final_summary.csv` generated
- [x] `semantic_layer_final_summary.md` generated
- [x] No formal alignment file reuses old `llm_results.csv`
- [x] No offline fallback is mixed into the accepted alignment layer
- [ ] `llm_results_target_aligned_final.csv` generated with all 113 edges scored by DeepSeek
- [ ] `semantic_edge_weights_final.csv` generated over all 204 edges
- [ ] final ranking comparison regenerated
- [ ] final ablation regenerated
- [ ] final robustness regenerated
- [ ] final future citation validation regenerated
- [ ] final pricing regenerated

Blocker: 22 accepted edges still need real DeepSeek scoring. The current environment cannot connect to the DeepSeek API.
