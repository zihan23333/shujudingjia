# 人工标注说明（edge-level）

每一行代表一条论文到论文的 citation edge。

`citation_context` / `all_citation_contexts` 字段中，可能包含该被引论文在施引论文中出现的一个或多个引用上下文。标注者应阅读该字段中提供的**所有上下文**，并给出一个**边级标签**，而不是只看其中某一次引用。

如果不同上下文对应不同的引用功能，那么：

- `human_primary_section` 以**最具实质性**的一次引用为准
- `human_relevance` 以这条 citation edge 的**整体实质性使用强度**为准
- `human_sentiment` 以最主要、最实质性的引用语气为准
- `annotation_note` 可以记录是否存在多个上下文、是否出现 mixed usage

## 需要填写的字段

- `human_primary_section`
- `human_sentiment`
- `human_relevance`
- `annotation_note`（可选但推荐填写）

## 标注步骤

1. 查看 `sample_id`
2. 打开对应原文 PDF：
   - 位于 `sample_pdfs_by_sample_id/`
   - 文件名格式如 `S001__xxx.pdf`
3. 阅读该行的 `all_citation_contexts`
4. 在原文中定位相关引用位置
5. 综合所有上下文后，给出一个 edge-level 标签

## section 标注类别

从以下类别中选择一个：

- `Introduction`
- `Methodology`
- `Result`
- `Discussion`
- `Conclusion`
- `Other`

判断原则：

- `Introduction`：主要用于背景介绍、问题引入、文献铺垫
- `Methodology`：主要用于方法设计、模型定义、算法实现、实验设置、数据处理
- `Result`：主要用于结果比较、实验结果解释
- `Discussion`：主要用于讨论、分析、局限性说明
- `Conclusion`：主要出现在结论、总结、展望部分
- `Other`：无法明确归入以上类别，或没有清晰主导 section

注意：

- 若多个上下文的功能不同，`human_primary_section` 以**最具实质性的一次引用**为准
- 不要对多个 section 做简单平均

## sentiment 标注类别

- `positive`
- `neutral`
- `negative`

判断原则：

- `positive`：明确采用、认可、依赖、扩展该工作
- `neutral`：客观提及、背景介绍、无明显褒贬
- `negative`：明确指出缺陷、局限、反驳或否定

若不同上下文的语气不同，优先以最主要、最实质性的引用语气为准。

## relevance 标注档位

- `0`：无关或错误匹配
- `0.25`：弱背景性提及
- `0.5`：主题相关但非核心依赖
- `0.75`：明确用于方法、比较或论证
- `1.0`：核心方法、数据、模型或结论依赖

判断原则：

- 仅作顺带引用、罗列式背景介绍：通常为 `0` 到 `0.25`
- 主题相关但非核心支撑：通常为 `0.5`
- 用于方法、对比、论证：通常为 `0.75`
- 构成关键基础或核心依赖：通常为 `1.0`

若存在多个上下文，`human_relevance` 应基于该 citation edge 的整体实质性使用判断，但优先参考最具实质性的一次引用，而不是对所有上下文做简单平均。

## 与 LLM 字段的关系

以下列仅作为参考，不要求人工去迎合：

- `LLM_edge_section`
- `LLM_edge_sentiment`
- `LLM_edge_relevance`
- `LLM_edge_confidence`
- `LLM_edge_q`

人工标注应以：

- `all_citation_contexts`
- 原文 PDF

为主要依据。

## 当前数据口径说明

当前 `llm_results.csv` 的检查结果表明：

- 每条 citation edge 只有一条 LLM 记录
- 当前是 `single-context per edge`

因此当前样本中的 `all_citation_contexts` 大多数等于单一上下文。

后续如果同一 edge 存在多个抽取上下文，仍然沿用本说明中的 edge-level 标注规则：标注者阅读所有上下文，再给出一个边级标签。
