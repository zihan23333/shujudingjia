| Variant | Edge weight | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | 1 | 0.938527 | 0.821022 | 4 | 5 | 7.466667 | 36.000000 |
| Semantic only | q_ij | 0.996713 | 0.972069 | 5 | 10 | 1.180952 | 13.000000 |
| Semantic + temporal | q_ij * tau_ij | 0.996796 | 0.977582 | 5 | 10 | 1.028571 | 11.000000 |
| Semantic + relation | q_ij * rho_ij | 0.998839 | 0.981992 | 5 | 10 | 0.780952 | 8.000000 |
| Full model | q_ij * tau_ij * rho_ij | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |