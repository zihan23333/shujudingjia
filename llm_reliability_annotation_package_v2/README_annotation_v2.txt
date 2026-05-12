LLM reliability annotation package v2

优先使用：
- sampled_contexts_for_human_annotation_v2.xlsx
- annotation_guidelines_v2.md

说明：
- 本包只针对 DeepSeek target-aligned semantic layer v2.1
- 标注者只评价当前 target cited paper
- 如果认为上下文仍未对准 target，请填写 human_alignment_check = ambiguous 或 wrong
- reliability 只在 human_alignment_check = correct 的样本上计算
- manual_check_needed = 1 的样本建议优先人工复核
