| Variant | Edge weight | Spearman with Full model v2 | Kendall with Full model v2 | Top-5 overlap | Top-10 overlap | Mean rank change | Max rank change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Structure only | 1 | 0.940352 | 0.824329 | 4 | 5 | 7.352381 | 34.000000 |
| Semantic only | q_ij | 0.996827 | 0.970967 | 5 | 9 | 1.142857 | 12.000000 |
| Semantic + temporal | q_ij * tau_ij | 0.997232 | 0.979419 | 5 | 9 | 0.933333 | 11.000000 |
| Semantic + relation | q_ij * rho_ij | 0.998600 | 0.980889 | 5 | 10 | 0.819048 | 9.000000 |
| Full model | q_ij * tau_ij * rho_ij | 1.000000 | 1.000000 | 5 | 10 | 0.000000 | 0.000000 |