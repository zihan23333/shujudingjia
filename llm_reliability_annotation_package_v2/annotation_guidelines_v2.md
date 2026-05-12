# 人工标注说明 v2

本次标注只针对新的 DeepSeek target-aligned semantic layer。每一行是一条论文到论文的 citation edge。请只评价当前 `cited_paper_title` 对应的 target cited paper。

## 标注原则

1. 阅读 `all_target_aligned_contexts` 中提供的全部目标对齐上下文。
2. 只评价当前 target cited paper 的语义作用，不评价 grouped / range 引用中的其他文献。
3. 如果是 grouped / range citation，需要根据当前 target 在该上下文中的作用判断。
4. 如果人工认为当前 context 仍未真正对准 target，请在 `human_alignment_check` 中填写 `ambiguous` 或 `wrong`。

## 需要填写的字段

- `human_alignment_check`
- `human_primary_section`
- `human_sentiment`
- `human_relevance`
- `annotation_note`

## 标签说明

- `human_alignment_check`：`correct / ambiguous / wrong`
- `human_primary_section`：`Introduction / Methodology / Result / Discussion / Conclusion / Other`
- `human_sentiment`：`positive / neutral / negative`
- `human_relevance`：`0 / 0.25 / 0.5 / 0.75 / 1.0`
- `annotation_note`：记录 mixed usage、target 对齐疑问或其他备注

Reliability analysis v2 只在 `human_alignment_check = correct` 的样本上计算。
