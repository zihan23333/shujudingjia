#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
INPUT_CONTEXTS = ROOT / "target_aligned_contexts_v22.csv"
INPUT_V21 = ROOT / "llm_results_target_aligned_v2.csv"
OUTPUT_V22 = ROOT / "llm_results_target_aligned_v22.csv"
SCORABLE = {"high_confidence", "grouped", "range"}
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
- num_mentions: {num_mentions}
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
        num_mentions=row["num_mentions"],
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
    parser.add_argument("--input-v21", type=str, default=str(INPUT_V21))
    parser.add_argument("--output", type=str, default=str(OUTPUT_V22))
    parser.add_argument("--api-key", type=str, default=os.environ.get("DEEPSEEK_API_KEY", ""))
    args = parser.parse_args()

    input_contexts = Path(args.input_contexts)
    input_v21 = Path(args.input_v21)
    output = Path(args.output)
    if not input_contexts.exists():
        raise FileNotFoundError(input_contexts)
    if not input_v21.exists():
        raise FileNotFoundError(input_v21)

    contexts = pd.read_csv(input_contexts)
    v21 = pd.read_csv(input_v21)
    v21_ids = set(v21["edge_id"].astype(str))
    scorable = contexts[contexts["alignment_status"].isin(SCORABLE)].copy()
    new_edges = scorable[~scorable["edge_id"].astype(str).isin(v21_ids)].copy()

    reused = v21.copy()
    reused["backend"] = "DeepSeek"
    reused["version"] = "v2.2"
    reused["source"] = "reused_v21"
    if "scoring_backend" not in reused.columns:
        reused["scoring_backend"] = "deepseek:deepseek-chat"

    if new_edges.empty:
        reused.to_csv(output, index=False, encoding="utf-8-sig")
        print(f"No newly accepted rescue edges found. Reused v2.1 scores only: {len(reused)} rows.")
        return

    if not args.api_key:
        raise RuntimeError("DeepSeek API key is required to score newly accepted rescue edges.")

    rows = []
    for _, row in new_edges.iterrows():
        prompt = build_prompt(row)
        parsed = call_deepseek(prompt, args.api_key)
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
                "alignment_status": row["alignment_status"],
                "target_reference_marker": row["target_reference_marker"],
                "num_mentions": row["num_mentions"],
                "section": section,
                "sentiment": sentiment,
                "relevance": relevance,
                "confidence": confidence,
                "q_ij": compute_q(section, sentiment, relevance),
                "raw_llm_response": parsed.get("raw_llm_response", ""),
                "scoring_backend": f"deepseek:{MODEL}",
                "backend": "DeepSeek",
                "version": "v2.2",
                "source": "newly_scored_v22",
            }
        )

    new_df = pd.DataFrame(rows)
    combined = pd.concat([reused, new_df], ignore_index=True)
    combined.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"Wrote v2.2 LLM results with {len(combined)} rows, including {len(new_df)} newly scored rescue edges.")


if __name__ == "__main__":
    main()
