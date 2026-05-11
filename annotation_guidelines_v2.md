# 人工标注说明 v2

本次标注只针对新的 target-aligned semantic layer。

每一行是一条论文—论文 citation edge。请只评价当前 `cited_paper_title` 对应的 target cited paper。

## 标注原则

1. 阅读 `all_target_aligned_contexts`
2. 只评价当前 target cited paper 的语义作用
3. 若是 grouped / range citation，需要根据当前 target 在该上下文中的作用判断，而不是泛化到整个引用组
4. 如果人工认为该 context 仍未真正对准 target，请在 `human_alignment_check` 中填写 `wrong_or_ambiguous`

## 需要填写的字段

- `human_primary_section`
- `human_sentiment`
- `human_relevance`
- `human_alignment_check`
- `annotation_note`

## human_alignment_check 取值

- `correct`
- `wrong_or_ambiguous`

Reliability analysis v2 只在 `human_alignment_check = correct` 的样本上计算。
