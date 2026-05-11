#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
INPUT_DEFAULT = ROOT / "sampled_contexts_for_human_annotation_v2.csv"

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=str(INPUT_DEFAULT))
    args = parser.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = Path(args.input)
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    required = ["human_primary_section", "human_sentiment", "human_relevance", "human_alignment_check"]
    if not all(col in df.columns for col in required):
        (RESULTS_DIR / "llm_reliability_summary_v2.md").write_text(
            "# LLM Reliability Summary v2\n\nHuman annotation file is missing required columns.",
            encoding="utf-8",
        )
        return

    mask = (
        df["human_alignment_check"].astype(str).str.strip().str.lower().eq("correct")
        & df["human_primary_section"].astype(str).str.strip().ne("")
        & df["human_sentiment"].astype(str).str.strip().ne("")
        & df["human_relevance"].astype(str).str.strip().ne("")
    )
    sub = df[mask].copy()
    if sub.empty:
        (RESULTS_DIR / "llm_reliability_summary_v2.md").write_text(
            "# LLM Reliability Summary v2\n\nHuman annotation is not complete yet, or no samples are marked `correct` under `human_alignment_check`.",
            encoding="utf-8",
        )
        return

    sub["LLM_section_norm"] = sub["LLM_section"].apply(normalize_section)
    sub["human_section_norm"] = sub["human_primary_section"].apply(normalize_section)
    sub["LLM_sentiment_norm"] = sub["LLM_sentiment"].apply(normalize_sentiment)
    sub["human_sentiment_norm"] = sub["human_sentiment"].apply(normalize_sentiment)
    sub["LLM_relevance_num"] = pd.to_numeric(sub["LLM_relevance"], errors="coerce")
    sub["human_relevance_num"] = pd.to_numeric(sub["human_relevance"], errors="coerce")
    sub = sub.dropna(subset=["LLM_relevance_num", "human_relevance_num"]).copy()
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
            {"metric": "annotated_correct_sample_size", "value": float(len(sub))},
        ]
    )
    metrics.to_csv(RESULTS_DIR / "table_llm_reliability_v2.csv", index=False, encoding="utf-8-sig")
    (RESULTS_DIR / "table_llm_reliability_v2.md").write_text(markdown_table(metrics), encoding="utf-8")
    lines = ["# LLM Reliability Summary v2", "", markdown_table(metrics)]
    (RESULTS_DIR / "llm_reliability_summary_v2.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
