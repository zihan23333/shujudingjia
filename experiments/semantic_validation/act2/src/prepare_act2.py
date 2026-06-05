"""Prepare the ACT2 dataset for external semantic validation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[4]
INPUT_PATH = PROJECT_ROOT / "experiments" / "semantic_validation" / "act2" / "data" / "ACT2_dataset.tsv"
OUTPUT_PATH = PROJECT_ROOT / "experiments" / "semantic_validation" / "act2" / "data" / "act2_processed.csv"
LOG_PATH = PROJECT_ROOT / "results" / "semantic_validation" / "act2" / "run_log.md"
REQUIRED_COLUMNS = ["citation_context", "citation_influence_label"]


def append_log(lines: list[str]) -> None:
    """Append markdown log lines to the ACT2 run log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## prepare_act2.py - {timestamp}\n\n")
        for line in lines:
            handle.write(f"- {line}\n")


def main() -> None:
    print(f"Reading ACT2 dataset from: {INPUT_PATH}")
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    dataframe = pd.read_csv(INPUT_PATH, sep="\t")
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(
            "ACT2 dataset is missing required columns: " + ", ".join(missing_columns)
        )

    original_rows = len(dataframe)
    valid_mask = dataframe["citation_context"].fillna("").astype(str).str.strip().ne("")
    dropped_rows = int((~valid_mask).sum())
    dataframe = dataframe.loc[valid_mask].copy()
    dataframe["citation_context"] = dataframe["citation_context"].astype(str)

    dataframe.insert(
        0,
        "sample_id",
        [f"ACT2_{index:06d}" for index in range(1, len(dataframe) + 1)],
    )

    label_distribution = (
        dataframe["citation_influence_label"]
        .value_counts(dropna=False)
        .sort_index()
        .rename_axis("citation_influence_label")
        .reset_index(name="count")
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("Label distribution:")
    print(label_distribution.to_string(index=False))
    print(f"Saved processed ACT2 file to: {OUTPUT_PATH}")

    append_log(
        [
            f"Input file: `{INPUT_PATH}`",
            f"Output file: `{OUTPUT_PATH}`",
            f"Original rows: {original_rows}",
            f"Dropped rows with missing citation_context: {dropped_rows}",
            f"Remaining rows: {len(dataframe)}",
            "Required columns verified: " + ", ".join(REQUIRED_COLUMNS),
            "Label distribution:",
            *[
                f"  - {row['citation_influence_label']}: {row['count']}"
                for _, row in label_distribution.iterrows()
            ],
        ]
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        append_log([f"Error: {exc}"])
        raise
