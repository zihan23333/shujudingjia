"""Auxiliary ACT2 analysis for relation-sensitive citation patterns."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


PROJECT_ROOT = Path(__file__).resolve().parents[4]
INPUT_PATH = PROJECT_ROOT / "experiments" / "semantic_validation" / "act2" / "data" / "act2_processed.csv"
OUTPUT_DIR = PROJECT_ROOT / "results" / "semantic_validation" / "act2"
LOG_PATH = OUTPUT_DIR / "run_log.md"


def append_log(lines: list[str]) -> None:
    """Append markdown log lines to the ACT2 run log."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## analyze_act2_relation.py - {timestamp}\n\n")
        for line in lines:
            handle.write(f"- {line}\n")


def normalize_label(value: object) -> float:
    """Map citation influence labels to binary values."""
    if pd.isna(value):
        return np.nan

    label = str(value).strip().lower()
    mapping = {
        "0": 0,
        "1": 1,
        "incidental": 0,
        "influential": 1,
    }
    if label in mapping:
        return float(mapping[label])
    return np.nan


def write_placeholder_excel(path: Path, message: str) -> None:
    """Write a small workbook when a requested field is unavailable."""
    pd.DataFrame([{"message": message}]).to_excel(path, index=False)


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Processed ACT2 file not found: {INPUT_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataframe = pd.read_csv(INPUT_PATH)
    required_columns = ["citation_influence_label"]
    missing_columns = [column for column in required_columns if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(
            "Processed ACT2 file is missing required columns: " + ", ".join(missing_columns)
        )
    dataframe["label_binary"] = dataframe["citation_influence_label"].apply(normalize_label)
    dataframe = dataframe.dropna(subset=["label_binary"]).copy()
    dataframe["label_binary"] = dataframe["label_binary"].astype(int)

    summary_lines = [
        "# ACT2 Relation Support Summary",
        "",
        f"- Input file: `{INPUT_PATH}`",
        f"- Valid rows after label normalization: {len(dataframe)}",
        "",
        "This analysis can only provide indirect empirical support for treating relational citations separately.",
        "It cannot prove that the gamma penalty formula in the main paper is fully correct.",
        "",
    ]

    self_citation_path = OUTPUT_DIR / "self_citation_influence_crosstab.xlsx"
    if "self_citation" in dataframe.columns:
        self_citation_df = dataframe.copy()
        self_citation_df["self_citation"] = pd.to_numeric(
            self_citation_df["self_citation"], errors="coerce"
        )
        self_citation_df = self_citation_df.dropna(subset=["self_citation"])
        self_citation_df["self_citation"] = self_citation_df["self_citation"].astype(int)

        crosstab = pd.crosstab(
            self_citation_df["self_citation"],
            self_citation_df["label_binary"],
            dropna=False,
        )
        chi2_error = ""
        chi2_statistic = np.nan
        p_value = np.nan
        if crosstab.shape[0] >= 2 and crosstab.shape[1] >= 2:
            chi2_statistic, p_value, _, _ = chi2_contingency(crosstab)
        else:
            chi2_error = "Chi-square test could not be computed because the contingency table lacks both classes."

        self_summary = (
            self_citation_df.groupby("self_citation")["label_binary"]
            .agg(["count", "mean"])
            .reset_index()
            .rename(columns={"mean": "influential_ratio"})
        )
        with pd.ExcelWriter(self_citation_path) as writer:
            crosstab.reset_index().to_excel(writer, sheet_name="crosstab", index=False)
            self_summary.to_excel(writer, sheet_name="ratio_summary", index=False)
            pd.DataFrame(
                [
                    {
                        "chi2_statistic": chi2_statistic,
                        "p_value": p_value,
                        "error": chi2_error,
                    }
                ]
            ).to_excel(writer, sheet_name="chi_square", index=False)

        summary_lines.extend(
            [
                "## Self Citation",
                "",
                f"- Rows with usable self_citation: {len(self_citation_df)}",
                f"- Self-citation influential ratio summary saved to `{self_citation_path}`",
                f"- Chi-square statistic: {chi2_statistic if not np.isnan(chi2_statistic) else 'NA'}",
                f"- Chi-square p-value: {p_value if not np.isnan(p_value) else 'NA'}",
            ]
        )
        if chi2_error:
            summary_lines.append(f"- Chi-square note: {chi2_error}")
        for row in self_summary.itertuples(index=False):
            summary_lines.append(
                f"- self_citation={row.self_citation}: influential_ratio={row.influential_ratio:.6f} (n={row.count})"
            )
        summary_lines.append("")
    else:
        write_placeholder_excel(self_citation_path, "Field self_citation is not available in act2_processed.csv.")
        summary_lines.extend(
            [
                "## Self Citation",
                "",
                "- Field `self_citation` is not available. Placeholder workbook created instead.",
                "",
            ]
        )

    co_mentions_path = OUTPUT_DIR / "co_mentions_influence_bins.xlsx"
    if "co_mentions" in dataframe.columns:
        co_mentions_df = dataframe.copy()
        co_mentions_df["co_mentions"] = pd.to_numeric(
            co_mentions_df["co_mentions"], errors="coerce"
        )
        co_mentions_df = co_mentions_df.dropna(subset=["co_mentions"])
        co_mentions_df["co_mentions_bin"] = pd.cut(
            co_mentions_df["co_mentions"],
            bins=[-np.inf, 0, 1, 2, np.inf],
            labels=["0", "1", "2", "3+"],
        )
        binned_summary = (
            co_mentions_df.groupby("co_mentions_bin", observed=False)["label_binary"]
            .agg(["count", "mean"])
            .reset_index()
            .rename(columns={"mean": "influential_ratio"})
        )
        binned_summary.to_excel(co_mentions_path, index=False)
        summary_lines.extend(
            [
                "## Co-mentions",
                "",
                f"- Rows with usable co_mentions: {len(co_mentions_df)}",
                f"- Binned summary saved to `{co_mentions_path}`",
            ]
        )
        for row in binned_summary.itertuples(index=False):
            summary_lines.append(
                f"- co_mentions_bin={row.co_mentions_bin}: influential_ratio={row.influential_ratio:.6f} (n={row.count})"
            )
        summary_lines.append("")
    else:
        write_placeholder_excel(co_mentions_path, "Field co_mentions is not available in act2_processed.csv.")
        summary_lines.extend(
            [
                "## Co-mentions",
                "",
                "- Field `co_mentions` is not available. Placeholder workbook created instead.",
                "",
            ]
        )

    summary_path = OUTPUT_DIR / "relation_support_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    append_log(
        [
            f"Input file: `{INPUT_PATH}`",
            f"Summary file: `{summary_path}`",
            f"Self-citation workbook: `{self_citation_path}`",
            f"Co-mentions workbook: `{co_mentions_path}`",
        ]
    )
    print(f"Saved relation analysis summary to: {summary_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        append_log([f"Error: {exc}"])
        raise
