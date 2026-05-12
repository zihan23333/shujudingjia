# Pricing Summary Final

- Base Case Top-5: TUBE, Query-based data pricing, Too Much Data: Prices and Inefficiencies in Data Markets, Smart data pricing, A survey of smart data pricing
- Pricing is computed only from Full model final scores.
- High-value but low-similarity papers remain moderated by the value-aware price mapping.
- High-similarity but lower-value papers are not allowed to dominate the final price ranking.
- Top-5 stability across scenarios: minimum overlap with Base Case = `4/5`.

| scenario | top5_overlap_with_base | mean_price_change | max_price_change | mean_rank_change | max_rank_change |
| --- | --- | --- | --- | --- | --- |
| Conservative | 4 | 0.018281 | 0.157231 | 3.028571 | 18.000000 |
| Base Case | 5 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| Aggressive | 5 | 0.018281 | 0.157231 | 1.104762 | 11.000000 |
| Quality Priority | 4 | 0.009442 | 0.250000 | 2.723810 | 17.000000 |
| Similarity Priority | 5 | 0.009442 | 0.250000 | 1.695238 | 24.000000 |