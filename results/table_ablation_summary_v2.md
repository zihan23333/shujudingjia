| Variant | Edge weight | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | 1 | 0.935717 | 0.819184 | 4 | 5 | 7.619048 | 33.000000 |
| Semantic only | q_ij | 0.996921 | 0.972437 | 5 | 10 | 1.161905 | 14.000000 |
| Semantic + temporal | q_ij * tau_ij | 0.997885 | 0.979787 | 5 | 10 | 0.876190 | 9.000000 |
| Semantic + relation | q_ij * rho_ij | 0.999036 | 0.984197 | 5 | 10 | 0.685714 | 6.000000 |
| Full model | q_ij * tau_ij * rho_ij | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |