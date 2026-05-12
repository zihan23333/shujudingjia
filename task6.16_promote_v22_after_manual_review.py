#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
V21_PATH = ROOT / "target_aligned_contexts.csv"
V22_CANDIDATE_PATH = ROOT / "target_aligned_contexts_v22_candidate.csv"
DEFAULT_REVIEW_PATH = ROOT / "rescued_edges_for_manual_review_v22.xlsx"
OUTPUT_PATH = ROOT / "target_aligned_contexts_v22.csv"
RESULTS_DIR = ROOT / "results"

SCORABLE = {"exact", "high_confidence", "grouped", "range"}
VALID_HUMAN = {"correct", "ambiguous", "wrong"}


def markdown_table(df: pd.DataFrame) -> str:
    show = df.fillna("")
    lines = [
        "| " + " | ".join(map(str, show.columns)) + " |",
        "| " + " | ".join(["---"] * len(show.columns)) + " |",
    ]
    for _, row in show.iterrows():
        vals = []
        for value in row:
            if isinstance(value, float):
                vals.append(f"{value:.6f}")
            else:
                vals.append(str(value).replace("\n", " ").strip())
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def load_review(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def normalize_status(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value or "").strip().lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-file", type=str, default=str(DEFAULT_REVIEW_PATH))
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    v21 = pd.read_csv(V21_PATH)
    v22_candidate = pd.read_csv(V22_CANDIDATE_PATH)
    review_path = Path(args.review_file)
    if not review_path.exists():
        raise FileNotFoundError(review_path)
    review = load_review(review_path)

    required_cols = {
        "edge_id",
        "human_alignment_status",
        "human_reference_marker_confirmed",
        "human_note",
    }
    missing = sorted(required_cols - set(review.columns))
    if missing:
        raise ValueError(f"Review file is missing required columns: {missing}")

    review["human_alignment_status_norm"] = review["human_alignment_status"].apply(normalize_status)
    blanks = review["human_alignment_status_norm"].eq("")
    invalid = ~review["human_alignment_status_norm"].isin(VALID_HUMAN) & ~blanks
    if invalid.any():
        bad = review.loc[invalid, ["edge_id", "human_alignment_status"]]
        raise ValueError(f"Invalid human_alignment_status values found:\n{bad}")
    if blanks.any():
        pending = int(blanks.sum())
        print(f"Pending manual review: {pending} rows still have empty human_alignment_status. Formal v2.2 will not be generated.")
        return

    rescued = v22_candidate.merge(
        v21[["edge_id", "alignment_status"]].rename(columns={"alignment_status": "old_alignment_status"}),
        on="edge_id",
        how="left",
    )
    rescued = rescued[
        (rescued["old_alignment_status"].isin(["failed", "ambiguous"]) | rescued["old_alignment_status"].isna())
        & rescued["alignment_status"].isin(["high_confidence", "grouped", "range"])
    ].copy()

    review = rescued[["edge_id"]].merge(review, on="edge_id", how="left")
    if review["human_alignment_status_norm"].eq("").any():
        pending = int(review["human_alignment_status_norm"].eq("").sum())
        print(f"Pending manual review: {pending} rescued rows are still empty after merge. Formal v2.2 will not be generated.")
        return

    accepted = review[review["human_alignment_status_norm"] == "correct"]["edge_id"].tolist()
    reject_amb = review[review["human_alignment_status_norm"] == "ambiguous"]["edge_id"].tolist()
    reject_wrong = review[review["human_alignment_status_norm"] == "wrong"]["edge_id"].tolist()

    final_v22 = v21.copy()
    candidate_map = v22_candidate.set_index("edge_id").to_dict(orient="index")
    review_map = review.set_index("edge_id").to_dict(orient="index")

    for edge_id in accepted:
        if edge_id not in candidate_map:
            continue
        candidate_row = candidate_map[edge_id].copy()
        human_row = review_map[edge_id]
        marker_confirmed = str(human_row.get("human_reference_marker_confirmed", "") or "").strip()
        note = str(candidate_row.get("alignment_note", "") or "")
        if marker_confirmed:
            candidate_row["target_reference_marker"] = marker_confirmed
            note = (note + " | human_reference_marker_confirmed=" + marker_confirmed).strip(" |")
        human_note = str(human_row.get("human_note", "") or "").strip()
        if human_note:
            note = (note + " | human_note=" + human_note).strip(" |")
        candidate_row["alignment_note"] = note
        for col, value in candidate_row.items():
            final_v22.loc[final_v22["edge_id"] == edge_id, col] = value

    final_v22.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    final_scored = int(final_v22["alignment_status"].isin(SCORABLE).sum())
    summary = pd.DataFrame(
        [
            {"metric": "candidate_rescued_edges", "value": int(len(rescued))},
            {"metric": "manually_accepted_edges", "value": int(len(accepted))},
            {"metric": "rejected_ambiguous_edges", "value": int(len(reject_amb))},
            {"metric": "rejected_wrong_edges", "value": int(len(reject_wrong))},
            {"metric": "final_target_aligned_edges", "value": final_scored},
            {"metric": "final_coverage_ratio", "value": final_scored / max(1, len(final_v22))},
        ]
    )
    summary.to_csv(RESULTS_DIR / "table_v22_manual_promotion_summary.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# v2.2 Manual Promotion Summary",
        "",
        markdown_table(summary),
        "",
        f"- Review source: `{review_path.name}`",
        f"- Formal v2.2 file written to `{OUTPUT_PATH.name}`.",
        "- Only rows with `human_alignment_status = correct` are promoted from the candidate alignment layer.",
        "- Rows marked `ambiguous` or `wrong` stay on the original v2.1 alignment status and later fall back to default semantic weight if still unscored.",
    ]
    (RESULTS_DIR / "v22_manual_promotion_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote formal v2.2 alignment file: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
