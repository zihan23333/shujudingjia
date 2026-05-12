# 人工评分说明（final）

本次人工评分面向正式 final 语义层，所有样本均来自 113 条 DeepSeek target-aligned citation edges。

## 1. human_alignment_check

先判断当前 `all_target_aligned_contexts` 是否确实对应当前 `cited_paper_title`：

- `correct`：上下文明确对应当前 cited paper；
- `wrong_or_ambiguous`：上下文无法确认对应 target，或明显对应其他文献。

只有 `human_alignment_check = correct` 的样本进入正式 reliability 计算。

## 2. human_primary_section

从以下类别中选择：

- `Introduction`
- `Methodology`
- `Result`
- `Discussion`
- `Conclusion`
- `Other`

若 grouped / range citation 中出现多个文献，只评价当前 target cited paper 在该 context 中的语义作用。

## 3. human_sentiment

取值：

- `positive`
- `neutral`
- `negative`

规则：

- `positive`：采用、扩展、支持、作为方法/数据/理论依据；
- `neutral`：背景介绍、一般相关工作、客观陈述；
- `negative`：批评、指出不足、反驳、作为 limitation 或 problem 的例子。

## 4. human_relevance

五档评分：

- `0`：无关或错误匹配
- `0.25`：弱背景性提及
- `0.5`：主题相关但非核心依赖
- `0.75`：明确用于方法、比较、论证或实验设计
- `1.0`：核心方法、数据、模型、结论或理论依赖

## 5. human_note

记录：

- 为什么判断为 `correct` / `wrong_or_ambiguous`
- 是否为 grouped citation
- 是否有转折或负面线索
- 是否需要查看 PDF 才能判断
