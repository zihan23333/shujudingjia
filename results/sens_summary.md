# 参数敏感性分析汇总（基于代码真实设定 run_experiments.py）

- 边数 204，论文 105，核心论文 30
- 有 LLM 语义分的边 113，自引边 27
- 年份 fallback 端点数 0（填 2020）；重复边 0
- 自检：重算 Main vs 文件 w_full_final 排序 Spearman = 1.0000（应≈1.0，验证重算公式与已存边权一致）

## 组1：section 位置权重
（Theory-strong=论文原版含 Other=1.0 混合效应；Theory-strong-fixed=Other 保持 0.2 的纯区分度对照）

| variant | Spearman_all | Spearman_core | Top10_overlap | Top5_overlap | avg_rank_change | max_rank_change |
| --- | --- | --- | --- | --- | --- | --- |
| Main | 1.0 | 1.0 | 10 | 5 | 0.0 | 0.0 |
| Equal | 0.9991 | 0.9996 | 10 | 5 | 0.571 | 8.0 |
| Conservative | 0.9996 | 1.0 | 10 | 5 | 0.286 | 7.0 |
| Theory-strong | 0.9994 | 0.9996 | 10 | 5 | 0.4 | 8.0 |
| Theory-strong-fixed | 0.9995 | 1.0 | 10 | 5 | 0.362 | 7.0 |

## 组2：时间衰减 TIME_BIAS（tau=TIME_BIAS/(TIME_BIAS+Δt)）

| variant | Spearman_all | Spearman_core | Top10_overlap | Top5_overlap | avg_rank_change | max_rank_change |
| --- | --- | --- | --- | --- | --- | --- |
| no_decay | 0.9982 | 0.9938 | 10 | 5 | 0.876 | 12.0 |
| strong(2) | 0.9995 | 0.9996 | 10 | 5 | 0.438 | 5.0 |
| Main(5) | 1.0 | 1.0 | 10 | 5 | 0.0 | 0.0 |
| weak(8) | 0.9998 | 0.9996 | 10 | 5 | 0.229 | 4.0 |
| veryweak(15) | 0.9991 | 0.9973 | 10 | 5 | 0.495 | 9.0 |

## 组3：关系惩罚 ETA_A（rho=1/(1+ETA_A·shared)）

| variant | Spearman_all | Spearman_core | Top10_overlap | Top5_overlap | avg_rank_change | max_rank_change |
| --- | --- | --- | --- | --- | --- | --- |
| no_penalty(0) | 0.9975 | 0.9742 | 10 | 5 | 0.895 | 10.0 |
| mild(0.5) | 0.9998 | 0.9991 | 10 | 5 | 0.21 | 5.0 |
| Main(1.0) | 1.0 | 1.0 | 10 | 5 | 0.0 | 0.0 |
| strong(2.0) | 0.9999 | 0.9991 | 10 | 5 | 0.095 | 1.0 |

## 判读标准
- Equal / no_decay / no_penalty 三个“关模块”组若 Spearman 仍 >0.95，说明核心排序不依赖该模块；
  其中 Equal 组（取消 section 影响）若仍高度一致，可正面化解 section 标注准确率偏低的质疑。
- Top-10 / Top-5 overlap 高且 max_rank_change 小 → 头部高价值论文稳定。
- 若某组 Spearman <0.9，需如实报告并结合 top3_changed_papers 说明哪些论文、为何变动。

## 设计说明（回应代码审核）
- 悬垂节点未做均匀再分配、年份缺失填 2020：均刻意与 run_experiments.py 主实验保持一致，
  以保证 Main 排序等同正文表 5；敏感性分析的目的是同一模型下换参数，而非构造更优模型。
- 本实验为排序稳定性分析，无分类标签，故无混淆矩阵；混淆矩阵属于功能分类 benchmark(SciCite/ACL-ARC)。