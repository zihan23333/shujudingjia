# ACT2 External Validation

## 1. Data location

Place the raw ACT2 file at:

```text
experiments/semantic_validation/act2/data/ACT2_dataset.tsv
```

## 2. Small-sample test run

```powershell
python experiments/semantic_validation/act2/src/prepare_act2.py
python experiments/semantic_validation/act2/src/run_act2_relevance.py --limit 500 --seed 42
python experiments/semantic_validation/act2/src/eval_act2_relevance.py
```

## 3. Full run

```powershell
python experiments/semantic_validation/act2/src/run_act2_relevance.py --seed 42
python experiments/semantic_validation/act2/src/eval_act2_relevance.py
python experiments/semantic_validation/act2/src/analyze_act2_relation.py
```

## 4. Interpretation guide

```text
AUC > 0.70: can be reported as a main external-validation result with strong consistency;
AUC 0.60-0.70: can be reported as moderate external consistency;
AUC 0.55-0.60: should only be used as limited supporting evidence;
AUC ~= 0.50: not recommended for the main paper; re-check the prompt or relevance definition.
```
