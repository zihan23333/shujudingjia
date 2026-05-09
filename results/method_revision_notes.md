# Method Revision Notes

## 1. Unified data scope

论文正文中需要区分两种“边数”：

- `204`：论文—论文 citation edges，也是本文排序模型、消融实验和定价实验实际使用的引用边数。
- `1030`：异构学术图 `HIN_network.graphml` 的总边数，包含 `204` 条 `cites`、`409` 条 `written_by` 和 `417` 条 `affiliated_with`。

建议正文统一表述为：

“The paper-level citation network contains 105 papers and 204 citation edges. The heterogeneous academic graph contains 1030 edges in total, including citation, authorship, and affiliation relations.”

## 2. Main relation penalty

主模型保持为共同作者驱动的关系惩罚：

`rho_ij = 1 / (1 + eta_a * co_ij).`

对应融合边权：

`w_ij^{fusion} = q_ij * tau_ij * rho_ij.`

建议在 Method 中明确写出：

“Institutional relations are not included in the main model due to data completeness considerations; they are only used in an extended robustness analysis.”

## 3. Extended robustness relation penalty

扩展稳健性模型可写为：

`rho_ij^{ext} = 1 / (1 + eta_a * co_ij + eta_c * tc_ij + eta_i * inst_ij),`

`w_ij^{ext} = q_ij * tau_ij * rho_ij^{ext}.`

其中：

- `co_ij`：共同作者数量。
- `tc_ij`：施引论文与被引论文作者集合之间的团队协作连接数。
- `inst_ij`：两篇论文作者机构集合的共享机构数量。

建议在正文中将其定位为：

“an extended robustness variant rather than the main model.”

## 4. Pricing function used in experiments

实验中实际使用的定价函数不应只写成一般形式 `Price_i = g(WTP_i)`，建议替换为下面的可复现表达。

首先，对 Full model 输出的文章级价值分数做 Min-Max 归一化，记为 `\tilde{V}_i`。设 query 相似度为 `sim(u, p_i)`，则支付意愿函数为：

`WTP_i = alpha * \tilde{V}_i + beta * (0.2 * sim(u,p_i) + 0.8 * \tilde{V}_i * sim(u,p_i)).`

最终价格映射为：

`Price_i = (WTP_i / 2) * (0.3 + 0.7 * \tilde{V}_i).`

该映射的含义是：

- 当论文价值较高时，支付意愿可以更充分地转化为价格。
- 当论文价值较低时，即使 query 相似度较高，价格也会受到温和抑制。

## 5. Suggested paper wording

可直接放入 Method 的英文式表达思路：

“We first normalize the article-level value score into `\tilde{V}_i \in [0,1]`. The willingness-to-pay is then modeled as a joint function of supply-side value and demand-side relevance:
`WTP_i = alpha \tilde{V}_i + beta (0.2 sim(u,p_i) + 0.8 \tilde{V}_i sim(u,p_i))`.
To avoid overpricing low-value but keyword-similar papers, we further adopt a value-aware price mapping:
`Price_i = (WTP_i / 2)(0.3 + 0.7 \tilde{V}_i)`.”
