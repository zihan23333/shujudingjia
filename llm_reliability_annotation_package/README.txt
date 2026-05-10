LLM 评分可靠性人工标注包

当前这套标注材料已经统一为 edge-level 口径。

也就是说：
- 一行样本 = 一条 citation edge
- 不是一行对应一次引用 mention
- 如果未来同一 edge 有多个引用上下文，会合并到 `all_citation_contexts`

当前推荐使用顺序

1. `sampled_contexts_for_human_annotation.xlsx`
   这是当前最推荐的标注文件。
   里面已经包含：
   - `sample_id`
   - `edge_id`
   - `all_citation_contexts`
   - `num_mentions`
   - `LLM_edge_section`
   - `LLM_edge_sentiment`
   - `LLM_edge_relevance`
   - `LLM_edge_confidence`
   - `LLM_edge_q`
   - `human_primary_section`
   - `human_sentiment`
   - `human_relevance`

2. `annotation_guidelines.md`
   中文标注说明。

3. `sample_pdfs_by_sample_id/`
   这里存放每条样本对应的原文 PDF。
   文件名格式如：
   - `S001__xxx.pdf`
   - `S002__xxx.pdf`

4. `sample_to_source_pdf_mapping.csv`
   样本编号和原文 PDF 的映射表。

如何标注 section

- 先打开 Excel 表
- 根据 `sample_id` 去 `sample_pdfs_by_sample_id/` 找对应原文
- 阅读 `all_citation_contexts`
- 结合原文里该被引论文的引用位置
- 按“最强实质性引用”填写 `human_primary_section`

人工需要填写的列

- `human_primary_section`
- `human_sentiment`
- `human_relevance`

当前数据口径说明

- 当前 `llm_results.csv` 中共有 123 条 LLM 记录
- 对应 123 条唯一 citation edges
- 多 instance edge 数为 0
- 因此当前属于 `single-context per edge`

如果后续同一 edge 出现多条 LLM instance，主口径仍然是 edge-level，只是会对 instance 做聚合后再比较人工结果。
