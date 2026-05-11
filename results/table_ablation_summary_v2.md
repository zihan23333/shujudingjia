| Variant | Edge weight | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | 1 | 0.941544 | 0.828372 | 4 | 5 | 7.200000 | 33.000000 |
| Semantic only | q_ij | 0.996454 | 0.968761 | 5 | 10 | 1.314286 | 15.000000 |
| Semantic + temporal | q_ij * tau_ij | 0.997595 | 0.979052 | 5 | 10 | 0.914286 | 9.000000 |
| Semantic + relation | q_ij * rho_ij | 0.998797 | 0.980522 | 5 | 10 | 0.933333 | 6.000000 |
| Full model | q_ij * tau_ij * rho_ij | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |