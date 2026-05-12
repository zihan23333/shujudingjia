# DeepSeek v2.1 Sentiment Audit

- Total DeepSeek-scored edges: `91`
- Negative sentiment count: `0`
- Neutral exact-zero count: `18`
- Positive sentiment count: `73`
- Cue-audit matched edges: `48`
- Cue-audit rows needing manual check: `48`

The absence of negative sentiment predictions should be treated as a limitation of the current DeepSeek semantic layer. The no-sentiment robustness check is therefore used to verify whether sentiment materially changes the downstream ranking conclusions.

## Overall distribution

| group_type | group_value | sentiment_bucket | count | ratio |
| --- | --- | --- | --- | --- |
| overall | all | negative | 0 | 0.000000 |
| overall | all | neutral | 18 | 0.197802 |
| overall | all | positive | 73 | 0.802198 |
| overall_metric | sentiment_eq_0 | neutral_exact_zero | 18 | 0.197802 |
| overall_metric | sentiment_gt_0 | positive_numeric | 73 | 0.802198 |
| overall_metric | sentiment_lt_0 | negative_numeric | 0 | 0.000000 |

## Distribution by section

| group_value | sentiment_bucket | count | ratio |
| --- | --- | --- | --- |
| Conclusion | negative | 0 | 0.000000 |
| Conclusion | neutral | 1 | 1.000000 |
| Conclusion | positive | 0 | 0.000000 |
| Discussion | negative | 0 | 0.000000 |
| Discussion | neutral | 1 | 0.142857 |
| Discussion | positive | 6 | 0.857143 |
| Introduction | negative | 0 | 0.000000 |
| Introduction | neutral | 13 | 0.351351 |
| Introduction | positive | 24 | 0.648649 |
| Methodology | negative | 0 | 0.000000 |
| Methodology | neutral | 2 | 0.051282 |
| Methodology | positive | 37 | 0.948718 |
| Other | negative | 0 | 0.000000 |
| Other | neutral | 0 | 0.000000 |
| Other | positive | 2 | 1.000000 |
| Result | negative | 0 | 0.000000 |
| Result | neutral | 1 | 0.200000 |
| Result | positive | 4 | 0.800000 |

## Distribution by relevance bucket

| group_value | sentiment_bucket | count | ratio |
| --- | --- | --- | --- |
| low | negative | 0 | 0.000000 |
| low | neutral | 14 | 0.538462 |
| low | positive | 12 | 0.461538 |
| mid | negative | 0 | 0.000000 |
| mid | neutral | 4 | 0.067797 |
| mid | positive | 55 | 0.932203 |
| high | negative | 0 | 0.000000 |
| high | neutral | 0 | 0.000000 |
| high | positive | 6 | 1.000000 |