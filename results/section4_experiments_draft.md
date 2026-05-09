# 4 Experiments

## 4.1 Experimental data and setup

本文围绕主题 “data pricing” 构建文章级论文价值评估与个性化定价实验。实验所用数据由 OpenAlex 抓取并经过引用网络清洗、上下文抽取、LLM 语义标注与作者关系增强后得到。最终论文层引用网络包含 105 篇论文和 204 条 citation edges，且全部节点均位于同一最大弱连通分量中，没有孤立点，说明该主题下的知识传播网络具有较好的整体连通性。需要说明的是，异构学术图 `HIN_network.graphml` 中的总边数为 1030，但其中包含 `written_by`、`affiliated_with` 和 `cites` 三类关系，真正的论文—论文引用边仍然只有 204 条。因此，后文凡是涉及“引用边数”均统一指 204，而非异构图总边数。核心论文集合由最大连通子图上的标准 PageRank Top-30 构成。对 204 条引用边中的 123 条，本文获得了 LLM 语义评分，其余 81 条边采用默认低语义权重进行保留处理。异构关系方面，共识别出 27 条作者层面的自引或团队互引边，占全部引用边的 13.24%，平均共同作者数为 0.382。

本文比较以下五类排序模型：1) Citation Count；2) Unweighted PageRank；3) Semantic-weighted PageRank；4) Semantic-temporal PageRank；5) Full model。Full model 的边权定义为 `q_ij * tau_ij * rho_ij`，其中 `q_ij` 由引用位置、引用情感和引用相关性共同构成，`tau_ij` 为时间衰减因子，`rho_ij` 为共同作者驱动的关系惩罚因子。需要强调的是，机构关系不进入主模型；主模型只使用 `rho(co_ij)`。在稳健性分析中，本文进一步构造扩展关系惩罚项 `rho(co_ij, tc_ij, inst_ij)`，其中 `tc_ij` 表示施引论文与被引论文作者集合之间的团队协作连接强度，`inst_ij` 表示共享机构数量。定价实验则在 Full model 输出的文章级价值基础上，引入 query “data pricing” 的文本相似度，并通过明确的 value-aware 价格映射函数生成个性化价格。

具体地，设归一化后的文章级价值为 `\tilde{V}_i`，查询相似度为 `sim(u,p_i)`，则本文在实验中实际使用的支付意愿函数为：

`WTP_i = alpha * \tilde{V}_i + beta * (0.2 * sim(u,p_i) + 0.8 * \tilde{V}_i * sim(u,p_i)).`

其中，前半部分刻画论文自身价值，后半部分刻画需求侧相关性及其与价值的交互增强。随后，本文将支付意愿映射为最终价格：

`Price_i = (WTP_i / 2) * (0.3 + 0.7 * \tilde{V}_i).`

该 value-aware mapping 的含义是：高价值论文可以较充分地将支付意愿转化为价格，而低价值论文即使与 query 高度相似，也会受到温和抑制，从而避免价格完全由标题相关性主导。

## 4.2 Dataset and network statistics

表 [table_dataset_statistics.csv](D:/数据集/new/results/table_dataset_statistics.csv) 给出了数据集与网络的基本统计量。可以看到，该网络的平均入度和平均出度均为 1.943，最大入度和最大出度分别为 15 和 12，网络密度为 0.01868，说明这是一个典型的稀疏学术引用网络。由于所有 105 个节点均位于最大弱连通分量中，本文后续的传播分析不受碎片化子图干扰。LLM 语义评分覆盖率为 60.29%（123/204），未评分边占 39.71%，因此在实际建模中保留未评分边并赋予默认低语义权重是必要的，否则会破坏网络连通性并低估外围论文的知识传递作用。

从关系偏差角度看，27 条自引或团队互引边说明该主题中确实存在一定程度的局部关系放大现象，但其占比并不高。这一结果意味着关系惩罚应主要被视为“局部纠偏”而非“全局重写”机制。图 [fig_degree_distribution.png](D:/数据集/new/results/fig_degree_distribution.png) 进一步显示，入度和出度均呈现明显长尾分布，少数论文承担了大量知识汇聚与扩散功能，这也为引入质量加权传播而非单纯计数提供了结构基础。与此同时，异构学术图中的总边数达到 1030，说明作者与机构关系为后续关系偏差识别提供了充足的信息来源，但这些关系仅作为证据层进入模型，而不直接替代论文—论文传播主干。

## 4.3 Baseline comparison

表 [table_ranking_comparison.csv](D:/数据集/new/results/table_ranking_comparison.csv) 展示了不同模型下的 Top-30 排名。Full model 的前五篇论文分别为 TUBE、Too Much Data: Prices and Inefficiencies in Data Markets、Nonrivalry and the Economics of Data、Optimal Sticky Prices under Rational Inattention 和 Query-based data pricing。与仅看全局被引次数不同，融合模型将高质量引用传播、时间衰减和关系独立性共同纳入考虑，因此部分虽然全局被引次数不占优势、但被高质量论文实质性吸收的论文获得了更高排名。

一个有代表性的现象是，Query-based data pricing 在 Citation Count 下仅位列第 27，但在 Full model 中上升到第 5；相反，部分高被引但 query 主题并不完全聚焦的数据市场经典论文，在融合模型中仍保持较高价值，但不再仅凭全局被引量主导排序。这说明本文模型并不是简单复现传统引文计数，而是对“被谁引用、如何被引用、何时被引用”进行了细粒度价值重估。

## 4.4 Ranking consistency and value re-estimation

表 [table_rank_correlation.csv](D:/数据集/new/results/table_rank_correlation.csv) 与表 [table_topk_overlap.csv](D:/数据集/new/results/table_topk_overlap.csv) 展示了融合模型与基线模型之间的一致性。Full model 与 Unweighted PageRank 的 Spearman 相关系数为 0.9191，说明融合模型总体上仍然保持了较强的领域共识；但其与 Citation Count 的 Spearman 仅为 0.8550，且 Top-5 重叠只有 1 篇，表明单纯被引次数无法充分刻画文章级价值。与此同时，Semantic-temporal 与 Semantic-only 的 Spearman 高达 0.9996，Full model 与 Semantic-temporal 的 Spearman 为 0.9969，说明时间项和关系项是在语义加权基础上的稳定修正，而不是对既有排序进行随机推翻。

表 [table_rank_changes.csv](D:/数据集/new/results/table_rank_changes.csv) 与图 [fig_rank_change_full_vs_baseline.png](D:/数据集/new/results/fig_rank_change_full_vs_baseline.png) 给出了 Full model 相对于 Unweighted PageRank 的排名变化。平均排名变化为 8.48，最大变化为 53，说明模型主要在中后部论文上进行较大幅度重排，而头部论文仍保留较强稳定性。这一现象支持本文的核心判断：多源融合模型的作用不是否定领域共识，而是在保留整体结构的前提下，对局部价值进行更合理的再估计。

## 4.5 Ablation study

表 [table_ablation_summary.csv](D:/数据集/new/results/table_ablation_summary.csv) 反映了各信息源的贡献。以 Full model 为参照，Structure only 的 Spearman 为 0.9191，明显低于包含语义信息的各类模型，说明仅依赖引用结构会损失大量边级质量信息。Semantic only 与 Full model 的 Spearman 已达到 0.9974，Top-10 overlap 为 9，说明 LLM 语义评分是提升文章级排序可信度的最核心因素。Semantic + temporal 与 Full model 的 Spearman 为 0.9969，也非常接近，说明时间衰减主要起到温和调整作用。

值得注意的是，Semantic + relation 与 Full model 的 Spearman 高达 0.9999，平均排名变化仅为 0.21，最大变化仅为 2。这意味着关系惩罚在整体层面是高度局部化的，不会破坏主题内的主流共识，但可以对少数存在团队互引放大的论文进行有效压制。综合来看，本文模型的主要增益来源于“语义质量建模”，而时间项和关系项分别提供“新近性修正”和“偏差校正”。

## 4.6 Heterogeneous relational penalty analysis

表 [table_self_citation_statistics.csv](D:/数据集/new/results/table_self_citation_statistics.csv) 显示，实验网络中共有 27 条被惩罚边，涉及 23 篇施引论文，惩罚边上的平均共同作者数达到 2.889，明显高于全样本边的 0.382，说明惩罚机制确实主要作用于作者关系紧密的引用。表 [table_penalty_rank_changes.csv](D:/数据集/new/results/table_penalty_rank_changes.csv) 与表 [table_penalty_score_changes.csv](D:/数据集/new/results/table_penalty_score_changes.csv) 则给出了惩罚前后的排序变化。

从整体看，Full model 与 Semantic-temporal 的 Spearman 为 0.9969，Top-5 完全一致，Top-10 仅有 1 篇差异，说明关系惩罚没有破坏领域主流结构。头部前五篇论文在惩罚前后排名完全不变，其中 TUBE 虽然分数下降 0.1225，但仍然稳居第 1，说明真正具有强外部支撑的基石论文不会因为少量关系边而失去主导地位。另一方面，Smart data pricing: To share or not to share?、A Survey of Smart Data Pricing: Past Proposals, Current Plans, and Future Trends 以及 Smart data pricing models for the internet of things: a bundling strategy approach 的排名分别下降 10、10 和 9 位，说明关系惩罚能够对局部放大现象产生可见影响。

进一步看，无自引论文的排名变化中位数为 0，说明惩罚机制对绝大多数无关系偏差论文几乎没有干扰。结合图 [fig_penalty_rank_change.png](D:/数据集/new/results/fig_penalty_rank_change.png) 和图 [fig_common_author_distribution.png](D:/数据集/new/results/fig_common_author_distribution.png)，可以认为关系惩罚主要体现为一种“稀疏而有效”的校正机制：它不会整体推翻原有排序，但能压低被自引或团队互引放大的局部论文，同时保持无自引基石论文的稳定性。

## 4.7 LLM semantic evidence analysis

表 [table_llm_semantic_statistics.csv](D:/数据集/new/results/table_llm_semantic_statistics.csv) 与表 [table_section_weight_analysis.csv](D:/数据集/new/results/table_section_weight_analysis.csv) 表明，LLM 语义评分包含显著信息量。123 条已评分边的平均 sentiment 为 0.5004，平均 relevance 为 0.7333，平均 confidence 为 0.8686，且低置信度样本比例为 0，说明当前语义标注结果整体较稳定。平均语义质量因子 `q_ij` 为 0.4107，中位数为 0.3675；relevance 与最终语义质量之间的相关系数为 0.7709，说明相关性分数对边权区分具有显著贡献。

从章节分布看，Method 类引用共 74 条，平均 `q_ij` 为 0.5287；Discussion 类 24 条，平均 `q_ij` 为 0.3302；Introduction 类 21 条，平均 `q_ij` 仅为 0.1311。也就是说，出现在方法部分的引用整体上显著强于引言性引用，这与本文关于“不同引用位置承载不同知识依赖强度”的理论设定一致。图 [fig_section_distribution.png](D:/数据集/new/results/fig_section_distribution.png)、[fig_sentiment_distribution.png](D:/数据集/new/results/fig_sentiment_distribution.png)、[fig_relevance_distribution.png](D:/数据集/new/results/fig_relevance_distribution.png)、[fig_confidence_distribution.png](D:/数据集/new/results/fig_confidence_distribution.png) 和 [fig_semantic_quality_distribution.png](D:/数据集/new/results/fig_semantic_quality_distribution.png) 也从分布层面支持了这一结论。

## 4.8 Confidence-aware robustness variant

尽管 LLM 输出了 confidence 字段，本文并未在主模型中直接将其纳入边权，而是将其视为质量控制信息。表 [table_confidence_variant.csv](D:/数据集/new/results/table_confidence_variant.csv) 给出的稳健性实验支持了这一处理方式。当 `epsilon` 分别取 0.3、0.5 和 0.7 时，confidence-aware 变体与主模型之间的 Spearman 分别为 0.99999、1.00000 和 1.00000，Top-5 与 Top-10 全部保持不变，平均排名变化最高也仅为 0.019。

这一结果说明，confidence 在当前样本上的边际信息增量非常有限。一方面，当前 LLM 评分本身已经具有较高置信度；另一方面，若强行把 confidence 直接乘入主权重，只会增加模型复杂度，却难以带来稳定的排序收益。因此，主文中的默认公式仍不建议将 confidence 纳入 `q_ij`，而应将其保留为稳健性分析和低质量样本筛查工具。

## 4.9 Extended robustness with team and institution relations

虽然机构关系不进入主模型，但从 Information Fusion 的视角出发，检验更丰富异构关系是否会改变排序结果仍然是有意义的。为此，本文构造扩展惩罚项：

`rho_ij^{ext} = 1 / (1 + eta_a * co_ij + eta_c * tc_ij + eta_i * inst_ij),`

并在此基础上形成扩展稳健性模型 `q_ij * tau_ij * rho_ij^{ext}`。其中，`co_ij` 为共同作者数量，`tc_ij` 为两篇论文作者集合之间的团队协作连接数，`inst_ij` 为共享机构数。表 [table_extended_relation_robustness.csv](D:/数据集/new/results/table_extended_relation_robustness.csv) 表明，该扩展模型与主模型之间的 Spearman 相关系数达到 0.9988，Top-5 和 Top-10 完全一致，平均排名变化仅为 0.743，最大变化为 7。

这一结果说明，将机构关系和团队协作关系进一步纳入惩罚后，只会在局部产生温和修正，而不会改变主模型结论。换言之，主模型采用 `rho(co_ij)` 已足以支撑核心实验，而 `rho(co_ij, tc_ij, inst_ij)` 更适合作为扩展稳健性分析，用于证明本文框架具有向更复杂异构关系平滑扩展的能力。

## 4.10 Personalized pricing analysis

表 [table_pricing_results.csv](D:/数据集/new/results/table_pricing_results.csv) 与表 [table_top_priced_papers.csv](D:/数据集/new/results/table_top_priced_papers.csv) 展示了个性化定价结果。在 Base Case 下，价格排名前五的论文分别为 TUBE、Too Much Data: Prices and Inefficiencies in Data Markets、Query-based data pricing、Nonrivalry and the Economics of Data 和 A survey of smart data pricing。与单纯由 query 匹配主导的结果不同，本文的价格映射函数对低价值论文施加了 value-aware moderation，因此高相似度但价值较低的论文不会被无限推高。

这一点在典型样本中表现得较为明显。TUBE 的 Full model 排名为第 1，但 query similarity 为 0，因此其价格虽仍居第 1，却仅为 0.5000，说明高价值但低需求相关性的论文价格会被抑制。相反，Smart data pricing 的 query similarity 最高，为 0.5883，但其 Full model 排名仅为第 51，最终价格仅排第 7，而没有进入 Top-5，说明高相似度本身不足以压倒文章级价值。与此同时，Query-based data pricing 同时具备较高价值和较高相似度，因此价格排到第 3，体现了供给侧价值与需求侧相关性的协同作用。图 [fig_value_similarity_price_scatter.png](D:/数据集/new/results/fig_value_similarity_price_scatter.png) 和图 [fig_price_distribution.png](D:/数据集/new/results/fig_price_distribution.png) 进一步表明，价格并不是价值或相似度的单变量函数，而是两者交互后的结果。

## 4.11 Pricing sensitivity analysis

表 [table_pricing_sensitivity.csv](D:/数据集/new/results/table_pricing_sensitivity.csv) 和表 [table_top5_price_stability.csv](D:/数据集/new/results/table_top5_price_stability.csv) 给出了定价敏感性分析结果。在 Conservative、Base Case、Aggressive、Quality Priority 和 Similarity Priority 五种场景下，Top-5 价格论文集合完全一致，说明本文定价机制在头部结果上具有较强稳健性。不同场景下的平均价格变化均不超过 0.019，最大价格变化也仅在 0.1674 到 0.2500 之间，表明参数变化主要影响价格幅度，而非颠覆性地改变头部结果。

虽然 Similarity Priority 场景下最大排名变化达到 23，但其 Top-5 集合仍与 Base Case 完全相同，说明参数调整的影响主要集中在中后段论文。这一现象表明，本文提出的个性化定价模型对参数设定具有较好的鲁棒性，可以在保持头部定价稳定的同时，对边缘论文进行柔性调节。

## 4.12 Case study

表 [table_case_study.csv](D:/数据集/new/results/table_case_study.csv) 给出了代表性案例。首先，Full model Top-3 论文均具有较高的平均语义质量，且惩罚前后排名稳定，说明真正的高价值论文主要由高质量外部引用支撑，而非关系网络放大。其次，在关系惩罚后下降最大的论文中，A Survey of Smart Data Pricing: Past Proposals, Current Plans, and Future Trends 存在 2 条自引或团队互引边，且平均语义质量很低，仅为 0.008，这表明其排名下降具有明确的结构解释。再次，高价值但低相似度的论文如 Optimal Sticky Prices under Rational Inattention，虽然 Full model 排名第 4，但价格仅为 0.0500，说明需求侧相关性能够有效抑制“价值高但当前需求弱”的论文价格。最后，Smart data pricing 等高相似度但中低价值论文虽然获得价格提升，但在 value-aware 的价格映射下并未进入价格 Top-5，说明本文定价机制能够在相关性提升与价值约束之间取得相对平衡。

综上，实验结果整体支持本文提出的多源异构信息融合框架：LLM 语义评分提供了最核心的边级区分能力，时间项和关系项分别提供温和的新近性修正与局部偏差校正，confidence 不必纳入主公式，而个性化定价则在文章级价值与需求侧相关性之间建立了稳定、可解释且参数稳健的连接。
