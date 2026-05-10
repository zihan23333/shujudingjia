# LLM Edge Record Summary

- LLM records total: `123`
- Unique citation edges: `123`
- Multi-instance edges: `0`
- Records with multiple contexts inside `citation_context`: `0`
- Average contexts per record: `1.00`
- Max contexts per record: `1`

## Interpretation

The current `llm_results.csv` behaves as single-context per edge: each row corresponds to one citation edge, and we did not find repeated `source_id + target_id` records or explicit multi-context records inside the parsed `citation_context` field.

The main experiment therefore uses edge-level scoring with one bundled context per edge. If future data contain multiple records or multiple extracted contexts for the same edge, the intended aggregation rule remains `q_edge = max_k q_instance`, and the best instance should be recorded explicitly for reproducibility.