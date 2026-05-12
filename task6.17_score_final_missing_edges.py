#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
INPUT_CONTEXTS = ROOT / "target_aligned_contexts_final.csv"
INPUT_EXISTING = ROOT / "llm_results_target_aligned_v2.csv"
OUTPUT_FINAL = ROOT / "llm_results_target_aligned_final.csv"
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

SECTION_WEIGHT_MAP = {
    "Introduction": 0.4,
    "Methodology": 1.0,
    "Result": 1.0,
    "Discussion": 0.7,
    "Conclusion": 0.5,
    "Other": 0.2,
}

PROMPT_TEMPLATE = """You are scoring one target-aligned paper-to-paper citation edge.

Evaluate only the CURRENT target paper and ignore other papers that may appear in grouped or range citations.

Input:
- edge_id: {edge_id}
- source_id: {source_id}
- target_id: {target_id}
- citing_paper_title: {citing_paper_title}
- cited_paper_title: {cited_paper_title}
- target_reference_marker: {target_reference_marker}
- target_reference_entry: {target_reference_entry}
- alignment_status: {alignment_status}
- all_target_aligned_contexts:
{all_target_aligned_contexts}

Return strict JSON:
{{
  "section": "Introduction|Methodology|Result|Discussion|Conclusion|Other",
  "sentiment": <number in [-1,1]>,
  "relevance": <number in [0,1]>,
  "confidence": <number in [0,1]>
}}
"""


def normalize_section(section: object) -> str:
    text = str(section or "").strip().lower()
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


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def compute_q(section: str, sentiment: float, relevance: float) -> float:
    w_sec = SECTION_WEIGHT_MAP.get(section, 0.2)
    w_sent = (sentiment + 1.0) / 2.0 if sentiment >= 0 else 0.01
    return w_sec * w_sent * (float(relevance) ** 2)


def build_prompt(row: pd.Series) -> str:
    return PROMPT_TEMPLATE.format(
        edge_id=row["edge_id"],
        source_id=row["source_id"],
        target_id=row["target_id"],
        citing_paper_title=row["citing_paper_title"],
        cited_paper_title=row["cited_paper_title"],
        target_reference_marker=row["target_reference_marker"],
        target_reference_entry=row["target_reference_entry"],
        alignment_status=row["alignment_status"],
        all_target_aligned_contexts=row["all_target_aligned_contexts"],
    )


def call_deepseek(prompt: str, api_key: str) -> Dict[str, object]:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers=headers,
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    text = data.get("choices", [])[0].get("message", {}).get("content", "")
    parsed = json.loads(text)
    parsed["raw_llm_response"] = text
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-contexts", type=str, default=str(INPUT_CONTEXTS))
    parser.add_argument("--input-existing", type=str, default=str(INPUT_EXISTING))
    parser.add_argument("--output", type=str, default=str(OUTPUT_FINAL))
    parser.add_argument("--api-key", type=str, default=os.environ.get("DEEPSEEK_API_KEY", ""))
    args = parser.parse_args()

    contexts = pd.read_csv(args.input_contexts)
    existing = pd.read_csv(args.input_existing)

    existing_ids = set(existing["edge_id"].astype(str))
    missing = contexts[~contexts["edge_id"].astype(str).isin(existing_ids)].copy()

    reused = existing.copy()
    reused["backend"] = "DeepSeek"
    reused["score_source"] = "reused_existing"
    if "scoring_backend" not in reused.columns:
        reused["scoring_backend"] = f"deepseek:{MODEL}"

    if missing.empty:
        reused.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"No missing accepted edges. Reused {len(reused)} existing DeepSeek rows.")
        return

    if not args.api_key:
        raise RuntimeError(
            f"{len(missing)} accepted edges still need real DeepSeek scoring. "
            "Set DEEPSEEK_API_KEY or pass --api-key in a network-enabled environment."
        )

    rows = []
    for _, row in missing.iterrows():
        parsed = call_deepseek(build_prompt(row), args.api_key)
        section = normalize_section(parsed.get("section", "Other"))
        sentiment = clamp(float(parsed.get("sentiment", 0.0)), -1.0, 1.0)
        relevance = clamp(float(parsed.get("relevance", 0.0)), 0.0, 1.0)
        confidence = clamp(float(parsed.get("confidence", 0.0)), 0.0, 1.0)
        rows.append(
            {
                "edge_id": row["edge_id"],
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "citing_paper_title": row["citing_paper_title"],
                "cited_paper_title": row["cited_paper_title"],
                "target_reference_marker": row["target_reference_marker"],
                "alignment_status": row["alignment_status"],
                "section": section,
                "sentiment": sentiment,
                "relevance": relevance,
                "confidence": confidence,
                "q_ij": compute_q(section, sentiment, relevance),
                "raw_llm_response": parsed.get("raw_llm_response", ""),
                "backend": "DeepSeek",
                "score_source": "newly_scored_final",
                "scoring_backend": f"deepseek:{MODEL}",
            }
        )

    new_df = pd.DataFrame(rows)
    combined = pd.concat([reused, new_df], ignore_index=True)
    combined.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(
        f"Wrote final LLM results with {len(combined)} rows, "
        f"including {len(new_df)} newly scored accepted edges."
    )


if __name__ == "__main__":
    main()
