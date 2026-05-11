# Rebuilt Context Alignment Summary

The old `llm_results.csv` should no longer be treated as the main semantic input without alignment filtering.

## Aggregate counts

| metric | value |
| --- | --- |
| total_citation_edges | 204.000000 |
| exact_count | 0.000000 |
| high_confidence_count | 63.000000 |
| grouped_count | 14.000000 |
| range_count | 1.000000 |
| ambiguous_count | 10.000000 |
| failed_count | 116.000000 |
| alignment_success_ratio | 0.382353 |

## Source papers with most failed alignments

| source_id | citing_paper_title | failed_alignments |
| --- | --- | --- |
| W2123954539 | Microeconomic Evidence on Price-Setting | 4 |
| W4281293246 | Business model archetypes for data marketplaces in the automotive industry | 4 |
| W2920282816 | Pricing for Revenue Maximization in IoT Data Markets: An Information Design Perspective | 4 |
| W4312395603 | Shaping future low-carbon energy and transportation systems: Digital technologies and applications | 4 |
| W2996741051 | Dynamic Pricing for Revenue Maximization in Mobile Social Data Market With Network Effects | 3 |
| W4289544372 | The value of data in digital-based business models: Measurement and economic policy implications | 3 |
| W4360991875 | The Economics of Digital Privacy | 3 |
| W2180742472 | Smart data pricing | 3 |
| W4323644227 | A Survey of Data Pricing for Data Marketplaces | 3 |
| W2919782326 | Making Big Money from Small Sensors: Trading Time-Series Data under Pufferfish Privacy | 2 |

## Interpretation

Alignment statuses `exact` and `high_confidence` are the most suitable candidates for retained semantic scores.
Statuses `grouped`, `range`, and `ambiguous` indicate that the target paper may be present but the local citation form is not clean enough for direct target-specific semantic reuse.
Status `failed` means the source PDF or target-specific numbered reference link could not be established confidently.