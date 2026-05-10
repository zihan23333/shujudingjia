#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"

SECTION_WEIGHT_MAP = {
    "methodology": 1.0,
    "method": 1.0,
    "result": 1.0,
    "results": 1.0,
    "discussion": 0.7,
    "conclusion": 0.5,
    "conclusions": 0.5,
    "introduction": 0.4,
    "other": 0.2,
    "unknown": 0.2,
}

SENTIMENT_NUMERIC_MAP = {
    "positive": 1.0,
    "neutral": 0.0,
    "negative": -1.0,
}


def ensure_results_dir() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def markdown_table(df: pd.DataFrame) -> str:
    preview = df.copy().fillna("")
    for col in preview.columns:
        if pd.api.types.is_float_dtype(preview[col]):
            preview[col] = preview[col].map(lambda x: f"{x:.6f}" if pd.notna(x) else "")
    headers = [str(c) for c in preview.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in preview.iterrows():
        vals = [str(row[c]).replace("\n", " ").strip() for c in preview.columns]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def normalize_section_label(value: object) -> str:
    if pd.isna(value):
        return "Other"
    text = str(value).strip().lower()
    if not text:
        return "Other"
    if "method" in text:
        return "Methodology"
    if "result" in text:
        return "Result"
    if "discussion" in text:
        return "Discussion"
    if "conclusion" in text:
        return "Conclusion"
    if "introduction" in text:
        return "Introduction"
    return "Other"


def normalize_sentiment_label(value: object) -> str:
    if pd.isna(value):
        return "neutral"
    text = str(value).strip().lower()
    if text in {"positive", "neutral", "negative"}:
        return text
    try:
        score = float(text)
    except ValueError:
        return "neutral"
    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def map_section_weight(section_label: str) -> float:
    key = section_label.strip().lower()
    return SECTION_WEIGHT_MAP.get(key, SECTION_WEIGHT_MAP.get(key.replace(" ", "").lower(), 0.2))


def compute_semantic_quality(section_label: str, sentiment_label: str, relevance_value: float) -> float:
    w_sec = map_section_weight(section_label)
    sentiment_numeric = SENTIMENT_NUMERIC_MAP.get(sentiment_label, 0.0)
    w_sent = (sentiment_numeric + 1.0) / 2.0 if sentiment_numeric >= 0 else 0.01
    w_rel = float(relevance_value) ** 2
    return w_sec * w_sent * w_rel


def detect_repeated_prompt_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    groups = {
        "section": [c for c in df.columns if c.lower().startswith("llm_section_repeat_")],
        "sentiment": [c for c in df.columns if c.lower().startswith("llm_sentiment_repeat_")],
        "relevance": [c for c in df.columns if c.lower().startswith("llm_relevance_repeat_")],
    }
    return groups


def repeated_prompt_consistency(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    groups = detect_repeated_prompt_columns(df)
    if not any(groups.values()):
        return None

    rows = []
    if len(groups["section"]) >= 2:
        section_block = df[groups["section"]].applymap(normalize_section_label)
        agreement = (section_block.nunique(axis=1) == 1).mean()
        rows.append({"metric": "repeated_prompt_section_exact_agreement", "value": float(agreement)})

    if len(groups["sentiment"]) >= 2:
        sentiment_block = df[groups["sentiment"]].applymap(normalize_sentiment_label)
        agreement = (sentiment_block.nunique(axis=1) == 1).mean()
        rows.append({"metric": "repeated_prompt_sentiment_exact_agreement", "value": float(agreement)})

    if len(groups["relevance"]) >= 2:
        rel_block = df[groups["relevance"]].apply(pd.to_numeric, errors="coerce")
        row_std = rel_block.std(axis=1, ddof=0).mean()
        rows.append({"metric": "repeated_prompt_relevance_mean_std", "value": float(row_std)})

    return pd.DataFrame(rows) if rows else None


def first_existing_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for name in candidates:
        if name in df.columns:
            return name
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="sampled_contexts_for_human_annotation.csv")
    args = parser.parse_args()

    ensure_results_dir()
    input_path = ROOT / args.input
    if not input_path.exists():
        raise FileNotFoundError(f"Annotation file not found: {input_path}")

    df = pd.read_csv(input_path)
    repeated_df = repeated_prompt_consistency(df)

    llm_section_col = first_existing_column(df, ["LLM_edge_section", "LLM_section"])
    llm_sentiment_col = first_existing_column(df, ["LLM_edge_sentiment", "LLM_sentiment"])
    llm_relevance_col = first_existing_column(df, ["LLM_edge_relevance", "LLM_relevance"])
    human_section_col = first_existing_column(df, ["human_primary_section", "human_section"])
    human_sentiment_col = first_existing_column(df, ["human_sentiment"])
    human_relevance_col = first_existing_column(df, ["human_relevance"])

    required_human_cols = [human_section_col, human_sentiment_col, human_relevance_col]
    human_ready = all(col is not None for col in required_human_cols)
    if human_ready:
        mask = (
            df[human_section_col].notna()
            & df[human_sentiment_col].notna()
            & df[human_relevance_col].notna()
            & df[human_section_col].astype(str).str.strip().ne("")
            & df[human_sentiment_col].astype(str).str.strip().ne("")
            & df[human_relevance_col].astype(str).str.strip().ne("")
        )
    else:
        mask = pd.Series([False] * len(df))

    annotated = df[mask].copy()

    if len(annotated) == 0:
        summary_lines = [
            "# LLM Reliability Summary",
            "",
            "Human annotation is not complete yet, so edge-level reliability metrics were not computed.",
            "The analysis script has been prepared and will run once the following columns are filled:",
            "- `human_primary_section` (or `human_section` for backward compatibility)",
            "- `human_sentiment`",
            "- `human_relevance`",
        ]
        if repeated_df is not None:
            repeated_df.to_csv(RESULTS_DIR / "table_llm_reliability_repeated_prompt.csv", index=False, encoding="utf-8-sig")
            summary_lines.extend(
                [
                    "",
                    "Repeated prompting consistency fields were detected and summarized in:",
                    "- `results/table_llm_reliability_repeated_prompt.csv`",
                ]
            )
        (RESULTS_DIR / "llm_reliability_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
        return

    if llm_section_col is None or llm_sentiment_col is None or llm_relevance_col is None:
        raise ValueError("Missing required LLM columns. Expected edge-level or legacy LLM section/sentiment/relevance columns.")

    annotated["LLM_section_norm"] = annotated[llm_section_col].apply(normalize_section_label)
    annotated["human_section_norm"] = annotated[human_section_col].apply(normalize_section_label)

    annotated["LLM_sentiment_norm"] = annotated[llm_sentiment_col].apply(normalize_sentiment_label)
    annotated["human_sentiment_norm"] = annotated[human_sentiment_col].apply(normalize_sentiment_label)

    annotated["LLM_relevance_num"] = pd.to_numeric(annotated[llm_relevance_col], errors="coerce")
    annotated["human_relevance_num"] = pd.to_numeric(annotated[human_relevance_col], errors="coerce")
    annotated = annotated.dropna(subset=["LLM_relevance_num", "human_relevance_num"]).copy()

    annotated["q_human"] = annotated.apply(
        lambda row: compute_semantic_quality(row["human_section_norm"], row["human_sentiment_norm"], row["human_relevance_num"]),
        axis=1,
    )
    annotated["q_llm"] = annotated.apply(
        lambda row: compute_semantic_quality(row["LLM_section_norm"], row["LLM_sentiment_norm"], row["LLM_relevance_num"]),
        axis=1,
    )

    metrics = pd.DataFrame(
        [
            {"metric": "comparison_level", "value": "edge"},
            {"metric": "section_accuracy", "value": accuracy_score(annotated["human_section_norm"], annotated["LLM_section_norm"])},
            {"metric": "section_macro_f1", "value": f1_score(annotated["human_section_norm"], annotated["LLM_section_norm"], average="macro")},
            {"metric": "sentiment_accuracy", "value": accuracy_score(annotated["human_sentiment_norm"], annotated["LLM_sentiment_norm"])},
            {"metric": "sentiment_macro_f1", "value": f1_score(annotated["human_sentiment_norm"], annotated["LLM_sentiment_norm"], average="macro")},
            {"metric": "relevance_spearman", "value": spearmanr(annotated["human_relevance_num"], annotated["LLM_relevance_num"]).statistic},
            {"metric": "relevance_mae", "value": mean_absolute_error(annotated["human_relevance_num"], annotated["LLM_relevance_num"])},
            {"metric": "q_human_vs_q_llm_spearman", "value": spearmanr(annotated["q_human"], annotated["q_llm"]).statistic},
            {"metric": "annotated_sample_size", "value": float(len(annotated))},
        ]
    )

    metrics.to_csv(RESULTS_DIR / "table_llm_reliability.csv", index=False, encoding="utf-8-sig")
    (RESULTS_DIR / "table_llm_reliability.md").write_text(markdown_table(metrics), encoding="utf-8")

    summary_lines = [
        "# LLM Reliability Summary",
        "",
        f"- Comparison level: `edge`",
        f"- LLM section field: `{llm_section_col}`",
        f"- Human section field: `{human_section_col}`",
        f"- Annotated sample size: `{len(annotated)}`",
        f"- Section accuracy: `{metrics.loc[metrics['metric']=='section_accuracy','value'].iloc[0]:.4f}`",
        f"- Section macro-F1: `{metrics.loc[metrics['metric']=='section_macro_f1','value'].iloc[0]:.4f}`",
        f"- Sentiment accuracy: `{metrics.loc[metrics['metric']=='sentiment_accuracy','value'].iloc[0]:.4f}`",
        f"- Sentiment macro-F1: `{metrics.loc[metrics['metric']=='sentiment_macro_f1','value'].iloc[0]:.4f}`",
        f"- Relevance Spearman: `{metrics.loc[metrics['metric']=='relevance_spearman','value'].iloc[0]:.4f}`",
        f"- Relevance MAE: `{metrics.loc[metrics['metric']=='relevance_mae','value'].iloc[0]:.4f}`",
        f"- Spearman between `q_human` and `q_llm`: `{metrics.loc[metrics['metric']=='q_human_vs_q_llm_spearman','value'].iloc[0]:.4f}`",
        "",
        "## Metric table",
        "",
        markdown_table(metrics),
    ]

    if repeated_df is not None:
        repeated_df.to_csv(RESULTS_DIR / "table_llm_reliability_repeated_prompt.csv", index=False, encoding="utf-8-sig")
        summary_lines.extend(
            [
                "",
                "Repeated prompting consistency fields were also detected and summarized in:",
                "- `results/table_llm_reliability_repeated_prompt.csv`",
            ]
        )

    (RESULTS_DIR / "llm_reliability_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
