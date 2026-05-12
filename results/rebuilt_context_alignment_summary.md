# Rebuilt Context Alignment Summary

The old `llm_results.csv` should no longer be treated as the main semantic input without alignment filtering.

## Aggregate counts

| metric | value |
| --- | --- |
| total_citation_edges | 204.000000 |
| exact_count | 0.000000 |
| high_confidence_count | 73.000000 |
| grouped_count | 17.000000 |
| range_count | 1.000000 |
| ambiguous_count | 16.000000 |
| failed_count | 97.000000 |
| alignment_success_ratio | 0.446078 |

## Source papers with most failed alignments

| source_id | citing_paper_title | failed_alignments |
| --- | --- | --- |
| W4323644227 | A Survey of Data Pricing for Data Marketplaces | 8 |
| W2920282816 | Pricing for Revenue Maximization in IoT Data Markets: An Information Design Perspective | 4 |
| W4281293246 | Business model archetypes for data marketplaces in the automotive industry | 4 |
| W4312395603 | Shaping future low-carbon energy and transportation systems: Digital technologies and applications | 4 |
| W4360991875 | The Economics of Digital Privacy | 3 |
| W2011238498 | Accounting for Incomplete Pass-Through | 2 |
| W3084177365 | A Survey on Data Pricing: From Economics to Data Science | 2 |
| W3089176333 | Towards Query Pricing on Incomplete Data | 2 |
| W3008256197 | The Effect of Privacy Regulation on the Data Industry: Empirical Evidence from GDPR | 2 |
| W3117086259 | Fintech: what’s old, what’s new? | 2 |

## Interpretation

Alignment statuses `exact` and `high_confidence` are the most suitable candidates for retained semantic scores.
Statuses `grouped`, `range`, and `ambiguous` indicate that the target paper may be present but the local citation form is not clean enough for direct target-specific semantic reuse.
Status `failed` means the source PDF or target-specific numbered reference link could not be established confidently.