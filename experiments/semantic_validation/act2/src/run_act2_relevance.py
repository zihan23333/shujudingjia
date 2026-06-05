"""Run ACT2 relevance scoring with an OpenAI-compatible LLM."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from llm_client import call_llm_json


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_INPUT = PROJECT_ROOT / "experiments" / "semantic_validation" / "act2" / "data" / "act2_processed.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "results" / "semantic_validation" / "act2" / "act2_relevance_predictions.csv"
PROMPT_PATH = PROJECT_ROOT / "experiments" / "semantic_validation" / "act2" / "prompts" / "act2_relevance_prompt.txt"
LOG_PATH = PROJECT_ROOT / "results" / "semantic_validation" / "act2" / "run_log.md"
REQUIRED_COLUMNS = ["sample_id", "citation_context", "citation_influence_label"]
OUTPUT_COLUMNS = [
    "sample_id",
    "citation_context",
    "citation_influence_label",
    "prompt_text",
    "relevance",
    "reason",
    "raw_response",
    "parse_failed",
    "error",
]


def append_log(lines: list[str]) -> None:
    """Append markdown log lines to the ACT2 run log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## run_act2_relevance.py - {timestamp}\n\n")
        for line in lines:
            handle.write(f"- {line}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ACT2 relevance prediction with LLMs.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input processed ACT2 CSV.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output prediction CSV.")
    parser.add_argument("--limit", type=int, default=None, help="Optional number of samples to score.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed used when sampling with --limit.")
    return parser.parse_args()


def load_existing_sample_ids(output_path: Path) -> set[str]:
    """Read already completed sample IDs for resume support."""
    if not output_path.exists():
        return set()

    existing = pd.read_csv(output_path, dtype={"sample_id": str})
    if "sample_id" not in existing.columns:
        raise ValueError(f"Existing output file is missing sample_id: {output_path}")
    return set(existing["sample_id"].dropna().astype(str))


def validate_columns(dataframe: pd.DataFrame, required_columns: list[str], file_path: Path) -> None:
    """Ensure all required columns are present before scoring."""
    missing_columns = [column for column in required_columns if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(
            f"Input file {file_path} is missing required columns: {', '.join(missing_columns)}"
        )


def validate_prediction(result: dict) -> tuple[float | None, str, bool, str]:
    """Validate parsed LLM output and normalize prediction fields."""
    if result.get("parse_failed", False):
        return None, "", True, str(result.get("error", "Unknown parse failure."))

    relevance = result.get("relevance")
    reason = str(result.get("reason", "")).strip()

    try:
        relevance_value = float(relevance)
    except Exception as exc:
        return None, reason, True, f"Invalid relevance value: {relevance!r}. {exc}"

    if not 0.0 <= relevance_value <= 1.0:
        return None, reason, True, f"Relevance out of range [0, 1]: {relevance_value}"

    if not reason:
        return relevance_value, "", False, ""

    return relevance_value, reason, False, ""


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_PATH}")

    dataframe = pd.read_csv(input_path, dtype={"sample_id": str})
    validate_columns(dataframe, REQUIRED_COLUMNS, input_path)

    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("--limit must be a positive integer when provided.")
        sample_size = min(args.limit, len(dataframe))
        dataframe = dataframe.sample(n=sample_size, random_state=args.seed).copy()

    existing_sample_ids = load_existing_sample_ids(output_path)
    remaining = dataframe.loc[~dataframe["sample_id"].astype(str).isin(existing_sample_ids)].copy()

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8").strip()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Total selected rows: {len(dataframe)}")
    print(f"Already completed rows: {len(dataframe) - len(remaining)}")
    print(f"Rows to process now: {len(remaining)}")

    append_log(
        [
            f"Input file: `{input_path}`",
            f"Output file: `{output_path}`",
            f"Prompt file: `{PROMPT_PATH}`",
            f"Selected rows before resume filter: {len(dataframe)}",
            f"Already completed sample_ids: {len(existing_sample_ids)}",
            f"Rows to process this run: {len(remaining)}",
            f"Sampling limit: {args.limit}",
            f"Sampling seed: {args.seed}",
        ]
    )

    if remaining.empty:
        print("No remaining rows to process. Resume check skipped all selected sample_ids.")
        return

    buffer: list[dict] = []
    for row in tqdm(remaining.itertuples(index=False), total=len(remaining), desc="Scoring ACT2"):
        citation_context = str(row.citation_context).strip()
        final_prompt = f"{prompt_template}\n\ncitation_context:\n{citation_context}"
        result_record = {
            "sample_id": str(row.sample_id),
            "citation_context": citation_context,
            "citation_influence_label": row.citation_influence_label,
            "prompt_text": final_prompt,
            "relevance": None,
            "reason": "",
            "raw_response": "",
            "parse_failed": True,
            "error": "",
        }

        try:
            llm_result = call_llm_json(
                system_prompt=prompt_template,
                user_prompt=f"citation_context:\n{citation_context}",
            )
            relevance, reason, parse_failed, validation_error = validate_prediction(llm_result)
            result_record["relevance"] = relevance
            result_record["reason"] = reason
            result_record["raw_response"] = llm_result.get("raw_response", "")
            result_record["parse_failed"] = parse_failed
            result_record["error"] = validation_error or str(llm_result.get("error", ""))
        except Exception as exc:
            result_record["error"] = f"Unexpected row-level error: {exc}"

        buffer.append(result_record)

        if len(buffer) >= 20:
            batch = pd.DataFrame(buffer, columns=OUTPUT_COLUMNS)
            batch.to_csv(
                output_path,
                mode="a",
                index=False,
                header=not output_path.exists(),
                encoding="utf-8-sig",
            )
            buffer.clear()

    if buffer:
        batch = pd.DataFrame(buffer, columns=OUTPUT_COLUMNS)
        batch.to_csv(
            output_path,
            mode="a",
            index=False,
            header=not output_path.exists(),
            encoding="utf-8-sig",
        )

    append_log(
        [
            f"Completed rows written in this run: {len(remaining)}",
            f"Output file updated: `{output_path}`",
        ]
    )
    print(f"Predictions saved to: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        append_log([f"Error: {exc}"])
        raise
