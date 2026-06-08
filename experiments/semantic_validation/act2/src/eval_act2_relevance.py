"""Evaluate ACT2 relevance predictions against influence labels."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]
INPUT_PATH = PROJECT_ROOT / "results" / "semantic_validation" / "act2" / "act2_relevance_predictions.csv"
OUTPUT_DIR = PROJECT_ROOT / "results" / "semantic_validation" / "act2"
LOG_PATH = OUTPUT_DIR / "run_log.md"


def append_log(lines: list[str]) -> None:
    """Append markdown log lines to the ACT2 run log."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## eval_act2_relevance.py - {timestamp}\n\n")
        for line in lines:
            handle.write(f"- {line}\n")


def normalize_parse_failed(series: pd.Series) -> pd.Series:
    """Convert mixed parse_failed values to boolean."""
    normalized = series.astype(str).str.strip().str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    )
    return normalized.fillna(False)


def normalize_influence_label(value: object) -> float:
    """Robustly map ACT2 influence labels to binary values."""
    if pd.isna(value):
        return np.nan

    label = str(value).strip().lower()
    if label in {"1", "1.0", "true", "yes", "influential", "important"}:
        return 1
    if label in {
        "0",
        "0.0",
        "false",
        "no",
        "incidental",
        "non-influential",
        "non_influential",
        "not influential",
    }:
        return 0
    try:
        numeric_value = float(label)
        if numeric_value == 1.0:
            return 1
        if numeric_value == 0.0:
            return 0
    except Exception:
        pass
    return np.nan


def save_boxplot(influential_scores: pd.Series, incidental_scores: pd.Series, output_path: Path) -> None:
    """Draw ACT2 relevance distributions using matplotlib only."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(
        [incidental_scores.to_list(), influential_scores.to_list()],
        tick_labels=["incidental", "influential"],
        patch_artist=True,
        boxprops={"facecolor": "#9ecae1"},
        medianprops={"color": "#d62728", "linewidth": 2},
    )
    ax.set_ylabel("Relevance")
    ax.set_title("ACT2 relevance by citation influence label")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def save_placeholder_plot(message: str, output_path: Path) -> None:
    """Create a placeholder figure when boxplot data are unavailable."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis("off")
    ax.text(0.5, 0.5, message, ha="center", va="center", wrap=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def dataframe_to_markdown_lines(dataframe: pd.DataFrame) -> list[str]:
    """Render a simple markdown table without extra dependencies."""
    headers = list(dataframe.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in dataframe.iterrows():
        values = [str(row[column]) for column in headers]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Prediction file not found: {INPUT_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataframe = pd.read_csv(INPUT_PATH)
    if dataframe.empty:
        raise ValueError(f"Prediction file is empty: {INPUT_PATH}")
    required_columns = ["parse_failed", "relevance", "citation_influence_label"]
    missing_columns = [column for column in required_columns if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(
            "Prediction file is missing required columns: " + ", ".join(missing_columns)
        )

    dataframe["parse_failed"] = normalize_parse_failed(dataframe["parse_failed"])
    dataframe["gold_label"] = dataframe["citation_influence_label"].apply(normalize_influence_label)
    dataframe["relevance"] = pd.to_numeric(dataframe["relevance"], errors="coerce")

    parse_failed_removed = int(dataframe["parse_failed"].eq(True).sum())
    non_failed = dataframe.loc[~dataframe["parse_failed"]].copy()

    invalid_label_removed = int(non_failed["gold_label"].isna().sum())
    label_valid = non_failed.loc[non_failed["gold_label"].notna()].copy()

    invalid_relevance_removed = int(label_valid["relevance"].isna().sum())
    filtered = label_valid.loc[label_valid["relevance"].notna()].copy()
    filtered["gold_label"] = filtered["gold_label"].astype(int)

    influential_scores = filtered.loc[filtered["gold_label"] == 1, "relevance"]
    incidental_scores = filtered.loc[filtered["gold_label"] == 0, "relevance"]

    group_summary = pd.DataFrame(
        [
            {
                "group": "influential",
                "count": int(influential_scores.shape[0]),
                "mean": influential_scores.mean(),
                "median": influential_scores.median(),
                "std": influential_scores.std(ddof=1),
            },
            {
                "group": "incidental",
                "count": int(incidental_scores.shape[0]),
                "mean": incidental_scores.mean(),
                "median": incidental_scores.median(),
                "std": incidental_scores.std(ddof=1),
            },
        ]
    )
    group_summary_path = OUTPUT_DIR / "act2_group_summary.xlsx"
    group_summary.to_excel(group_summary_path, index=False)

    auc_rows: list[dict] = []
    metric_rows: list[dict] = []
    auc_error = ""
    auc_value = np.nan
    if filtered["gold_label"].nunique() < 2:
        auc_error = (
            "AUC cannot be computed because valid evaluation rows contain only one gold_label class."
        )
        auc_rows.append({"metric": "auc", "value": np.nan, "error": auc_error})
    else:
        auc_value = roc_auc_score(filtered["gold_label"], filtered["relevance"])
        binary_predictions = (filtered["relevance"] >= 0.5).astype(int)
        auc_rows.append({"metric": "auc", "value": auc_value, "error": ""})
        metric_rows.extend(
            [
                {"metric": "accuracy", "value": accuracy_score(filtered["gold_label"], binary_predictions)},
                {
                    "metric": "precision",
                    "value": precision_score(filtered["gold_label"], binary_predictions, zero_division=0),
                },
                {
                    "metric": "recall",
                    "value": recall_score(filtered["gold_label"], binary_predictions, zero_division=0),
                },
                {"metric": "f1", "value": f1_score(filtered["gold_label"], binary_predictions, zero_division=0)},
            ]
        )

    auc_result_path = OUTPUT_DIR / "act2_auc_result.xlsx"
    pd.DataFrame(auc_rows + metric_rows).to_excel(auc_result_path, index=False)

    mannwhitney_rows: list[dict] = []
    mannwhitney_error = ""
    mannwhitney_statistic = np.nan
    mannwhitney_p_value = np.nan
    if influential_scores.empty or incidental_scores.empty:
        mannwhitney_error = (
            "Mann-Whitney U test cannot be computed because one comparison group is empty."
        )
        mannwhitney_rows.append(
            {"statistic": np.nan, "p_value": np.nan, "alternative": "two-sided", "error": mannwhitney_error}
        )
    else:
        mannwhitney_statistic, mannwhitney_p_value = mannwhitneyu(
            influential_scores,
            incidental_scores,
            alternative="two-sided",
        )
        mannwhitney_rows.append(
            {
                "statistic": mannwhitney_statistic,
                "p_value": mannwhitney_p_value,
                "alternative": "two-sided",
                "error": "",
            }
        )

    mannwhitney_path = OUTPUT_DIR / "act2_mannwhitney_result.xlsx"
    pd.DataFrame(mannwhitney_rows).to_excel(mannwhitney_path, index=False)

    boxplot_path = OUTPUT_DIR / "act2_relevance_boxplot.png"
    if not influential_scores.empty and not incidental_scores.empty:
        save_boxplot(influential_scores, incidental_scores, boxplot_path)
    else:
        save_placeholder_plot(
            "Boxplot unavailable because one evaluation group is empty.",
            boxplot_path,
        )

    summary_lines = [
        "# ACT2 Relevance Evaluation",
        "",
        f"- Input file: `{INPUT_PATH}`",
        f"- Total predictions: {len(dataframe)}",
        f"- Parse-failed rows removed: {parse_failed_removed}",
        f"- Invalid label rows removed: {invalid_label_removed}",
        f"- Invalid relevance rows removed: {invalid_relevance_removed}",
        f"- Valid rows used in evaluation: {len(filtered)}",
        f"- Influential rows: {len(influential_scores)}",
        f"- Incidental rows: {len(incidental_scores)}",
    ]

    if auc_error:
        summary_lines.append(f"- AUC error: {auc_error}")
    else:
        summary_lines.append(f"- AUC: {auc_value:.6f}")
        for metric_row in metric_rows:
            summary_lines.append(f"- {metric_row['metric']}: {metric_row['value']:.6f}")

    if mannwhitney_error:
        summary_lines.append(f"- Mann-Whitney U error: {mannwhitney_error}")
    else:
        summary_lines.append(f"- Mann-Whitney U statistic: {mannwhitney_statistic:.6f}")
        summary_lines.append(f"- p value: {mannwhitney_p_value:.6g}")

    for row in group_summary.itertuples(index=False):
        summary_lines.append(
            f"- {row.group} mean={row.mean:.6f} median={row.median:.6f} std={row.std:.6f}"
        )

    summary_lines.extend(
        [
            "",
            "## Group Summary",
            "",
            *dataframe_to_markdown_lines(group_summary),
        ]
    )

    summary_path = OUTPUT_DIR / "act2_eval_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    append_log(
        [
            f"Input file: `{INPUT_PATH}`",
            f"Valid evaluation rows: {len(filtered)}",
            f"Summary file: `{summary_path}`",
            f"AUC workbook: `{auc_result_path}`",
            f"Mann-Whitney workbook: `{mannwhitney_path}`",
        ]
    )
    print(f"Saved evaluation summary to: {summary_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        append_log([f"Error: {exc}"])
        raise
