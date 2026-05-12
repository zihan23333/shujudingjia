#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from scipy.stats import kendalltau, spearmanr
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
REP_DEFAULT = ROOT / "sampled_contexts_for_human_annotation_representative_final.xlsx"
HARD_DEFAULT = ROOT / "sampled_contexts_for_human_annotation_hardcase_final.xlsx"

SECTION_WEIGHT_MAP = {
    "methodology": 1.0,
    "result": 1.0,
    "discussion": 0.7,
    "conclusion": 0.5,
    "introduction": 0.4,
    "other": 0.2,
}


def normalize_section(value: object) -> str:
    text = str(value).strip().lower()
    if "method" in text:
        return "Methodology"
    if "result" in text:
        return "Result"
    if "discussion" in text:
        return "Discussion"
    if "conclusion" in text:
        return "Conclusion"
    if "introduction" in text or "related" in text or "background" in text:
        return "Introduction"
    return "Other"


def normalize_sentiment(value: object) -> str:
    text = str(value).strip().lower()
    if text in {"positive", "neutral", "negative"}:
        return text
    try:
        v = float(text)
    except Exception:
        return "neutral"
    return "positive" if v > 0 else ("negative" if v < 0 else "neutral")


def compute_q(section: str, sentiment: str, relevance: float) -> float:
    w_sec = SECTION_WEIGHT_MAP.get(section.lower(), 0.2)
    sent_num = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}[sentiment]
    w_sent = (sent_num + 1.0) / 2.0 if sent_num >= 0 else 0.01
    return w_sec * w_sent * (float(relevance) ** 2)


def markdown_table(df: pd.DataFrame) -> str:
    preview = df.fillna("").copy()
    lines = [
        "| " + " | ".join(str(c) for c in preview.columns) + " |",
        "| " + " | ".join(["---"] * len(preview.columns)) + " |",
    ]
    for _, row in preview.iterrows():
        vals = []
        for col in preview.columns:
            val = row[col]
            if isinstance(val, float):
                vals.append(f"{val:.6f}")
            else:
                vals.append(str(val).replace("\n", " ").strip())
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def load_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path)
    return pd.read_csv(path, encoding="utf-8-sig")


def write_not_completed(name_csv: str, name_md: str, name_summary: str) -> None:
    msg = "Human annotation not completed. Reliability metrics are not computed."
    (RESULTS_DIR / name_summary).write_text(msg, encoding="utf-8")
    pd.DataFrame([{"status": msg}]).to_csv(RESULTS_DIR / name_csv, index=False, encoding="utf-8-sig")
    (RESULTS_DIR / name_md).write_text(markdown_table(pd.DataFrame([{"status": msg}])), encoding="utf-8")


def analyze_representative(df: pd.DataFrame) -> None:
    required = ["human_alignment_check", "human_primary_section", "human_sentiment", "human_relevance"]
    if not all(col in df.columns for col in required):
        write_not_completed("table_llm_reliability_final.csv", "table_llm_reliability_final.md", "llm_reliability_summary_final.md")
        return
    mask = (
        df["human_alignment_check"].astype(str).str.strip().str.lower().eq("correct")
        & df["human_primary_section"].astype(str).str.strip().ne("")
        & df["human_sentiment"].astype(str).str.strip().ne("")
        & df["human_relevance"].astype(str).str.strip().ne("")
    )
    excluded = int((df["human_alignment_check"].astype(str).str.strip().str.lower() == "wrong_or_ambiguous").sum())
    sub = df[mask].copy()
    if sub.empty:
        write_not_completed("table_llm_reliability_final.csv", "table_llm_reliability_final.md", "llm_reliability_summary_final.md")
        return

    sub["LLM_section_norm"] = sub["LLM_section"].apply(normalize_section)
    sub["human_section_norm"] = sub["human_primary_section"].apply(normalize_section)
    sub["LLM_sentiment_norm"] = sub["LLM_sentiment"].apply(normalize_sentiment)
    sub["human_sentiment_norm"] = sub["human_sentiment"].apply(normalize_sentiment)
    sub["LLM_relevance_num"] = pd.to_numeric(sub["LLM_relevance"], errors="coerce")
    sub["human_relevance_num"] = pd.to_numeric(sub["human_relevance"], errors="coerce")
    sub = sub.dropna(subset=["LLM_relevance_num", "human_relevance_num"]).copy()
    if sub.empty:
        write_not_completed("table_llm_reliability_final.csv", "table_llm_reliability_final.md", "llm_reliability_summary_final.md")
        return
    sub["LLM_q_num"] = pd.to_numeric(sub["LLM_q"], errors="coerce")
    sub["human_q"] = sub.apply(lambda r: compute_q(r["human_section_norm"], r["human_sentiment_norm"], r["human_relevance_num"]), axis=1)

    metrics = pd.DataFrame(
        [
            {"metric": "section_accuracy", "value": accuracy_score(sub["human_section_norm"], sub["LLM_section_norm"])},
            {"metric": "section_macro_f1", "value": f1_score(sub["human_section_norm"], sub["LLM_section_norm"], average="macro")},
            {"metric": "sentiment_accuracy", "value": accuracy_score(sub["human_sentiment_norm"], sub["LLM_sentiment_norm"])},
            {"metric": "sentiment_macro_f1", "value": f1_score(sub["human_sentiment_norm"], sub["LLM_sentiment_norm"], average="macro")},
            {"metric": "relevance_spearman", "value": spearmanr(sub["human_relevance_num"], sub["LLM_relevance_num"]).statistic},
            {"metric": "relevance_mae", "value": mean_absolute_error(sub["human_relevance_num"], sub["LLM_relevance_num"])},
            {"metric": "human_q_vs_LLM_q_spearman", "value": spearmanr(sub["human_q"], sub["LLM_q_num"]).statistic},
            {"metric": "human_q_vs_LLM_q_kendall", "value": kendalltau(sub["human_q"], sub["LLM_q_num"]).statistic},
            {"metric": "valid_sample_count", "value": float(len(sub))},
            {"metric": "excluded_wrong_or_ambiguous_count", "value": float(excluded)},
        ]
    )
    metrics.to_csv(RESULTS_DIR / "table_llm_reliability_final.csv", index=False, encoding="utf-8-sig")
    (RESULTS_DIR / "table_llm_reliability_final.md").write_text(markdown_table(metrics), encoding="utf-8")
    (RESULTS_DIR / "llm_reliability_summary_final.md").write_text(
        "# LLM Reliability Summary Final\n\n" + markdown_table(metrics),
        encoding="utf-8",
    )


def analyze_hardcase(df: pd.DataFrame) -> None:
    if "human_alignment_check" not in df.columns:
        write_not_completed("table_llm_hardcase_audit_final.csv", "table_llm_hardcase_audit_final.md", "llm_hardcase_audit_summary_final.md")
        return
    for col in ["human_alignment_check", "human_primary_section", "human_sentiment", "human_relevance"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
    filled = df[
        df["human_alignment_check"].astype(str).str.strip().ne("")
        | df["human_primary_section"].astype(str).str.strip().ne("")
        | df["human_sentiment"].astype(str).str.strip().ne("")
        | df["human_relevance"].astype(str).str.strip().ne("")
    ].copy()
    if filled.empty:
        write_not_completed("table_llm_hardcase_audit_final.csv", "table_llm_hardcase_audit_final.md", "llm_hardcase_audit_summary_final.md")
        return

    table = pd.DataFrame(
        [
            {"metric": "annotated_hardcase_samples", "value": float(len(filled))},
            {"metric": "correct_alignment_count", "value": float((filled["human_alignment_check"].astype(str).str.strip().str.lower() == "correct").sum())},
            {"metric": "wrong_or_ambiguous_count", "value": float((filled["human_alignment_check"].astype(str).str.strip().str.lower() == "wrong_or_ambiguous").sum())},
            {"metric": "negative_sentiment_count", "value": float((filled["human_sentiment"].astype(str).str.strip().str.lower() == "negative").sum())},
            {"metric": "neutral_sentiment_count", "value": float((filled["human_sentiment"].astype(str).str.strip().str.lower() == "neutral").sum())},
            {"metric": "positive_sentiment_count", "value": float((filled["human_sentiment"].astype(str).str.strip().str.lower() == "positive").sum())},
        ]
    )
    table.to_csv(RESULTS_DIR / "table_llm_hardcase_audit_final.csv", index=False, encoding="utf-8-sig")
    (RESULTS_DIR / "table_llm_hardcase_audit_final.md").write_text(markdown_table(table), encoding="utf-8")
    (RESULTS_DIR / "llm_hardcase_audit_summary_final.md").write_text(
        "# LLM Hard-case Audit Summary Final\n\n" + markdown_table(table),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--representative", type=str, default=str(REP_DEFAULT))
    parser.add_argument("--hardcase", type=str, default=str(HARD_DEFAULT))
    args = parser.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rep = load_table(Path(args.representative))
    hard = load_table(Path(args.hardcase))
    analyze_representative(rep)
    analyze_hardcase(hard)


if __name__ == "__main__":
    main()
