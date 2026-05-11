#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parent
INPUT_PATH = ROOT / "target_aligned_contexts.csv"
OUTPUT_PATH = ROOT / "llm_results_target_aligned_v2.csv"
RESULTS_DIR = ROOT / "results"

SCORABLE_STATUSES = {"high_confidence", "grouped", "range"}
API_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

SECTION_WEIGHT_MAP = {
    "Introduction": 0.4,
    "Methodology": 1.0,
    "Result": 1.0,
    "Discussion": 0.7,
    "Conclusion": 0.5,
    "Other": 0.2,
}


PROMPT_TEMPLATE = """You are scoring one paper-to-paper citation edge.

Task:
Evaluate only the semantic contribution of the CURRENT target cited paper inside the provided target-aligned citation contexts.
Do NOT evaluate other papers that may appear in grouped or range citations.

Input fields:
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

Return strict JSON with:
{{
  "section": "Introduction|Methodology|Result|Discussion|Conclusion|Other",
  "sentiment": <number in [-1,1]>,
  "relevance": <number in [0,1]>,
  "confidence": <number in [0,1]>
}}

Guidelines:
- section should reflect the most substantive use of the CURRENT target paper.
- sentiment should capture the citation stance toward the CURRENT target paper only.
- relevance should reflect how substantively the CURRENT target paper is used.
- confidence is quality control only and must not be used in the main weight formula.
"""


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def normalize_section(section: object) -> str:
    if pd.isna(section):
        return "Other"
    text = str(section).strip().lower()
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


def compute_q(section: str, sentiment: float, relevance: float) -> float:
    w_sec = SECTION_WEIGHT_MAP.get(section, 0.2)
    w_sent = (sentiment + 1.0) / 2.0 if sentiment >= 0 else 0.01
    w_rel = relevance ** 2
    return w_sec * w_sent * w_rel


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


def try_call_openai(prompt: str) -> Optional[Dict[str, object]]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    payload = {
        "model": API_MODEL,
        "input": prompt,
        "text": {"format": {"type": "json_object"}},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        text = ""
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text += content.get("text", "")
        if not text:
            return None
        parsed = json.loads(text)
        parsed["raw_llm_response"] = text
        parsed["scoring_backend"] = f"openai:{API_MODEL}"
        return parsed
    except Exception:
        return None


NEGATIVE_CUES = [
    "however",
    "limitation",
    "limitations",
    "problem",
    "drawback",
    "challenge",
    "insufficient",
    "fails",
    "failed",
    "suffers",
]
POSITIVE_CUES = [
    "propose",
    "proposed",
    "use",
    "used",
    "adopt",
    "adopted",
    "extend",
    "follow",
    "based on",
    "framework",
    "method",
    "model",
    "pricing mechanism",
]
RESULT_CUES = ["experiment", "evaluation", "result", "results", "performance", "compare", "comparison"]
DISCUSSION_CUES = ["discussion", "implication", "limitation", "future work"]
INTRO_CUES = ["background", "related work", "survey", "introduction"]
CONCLUSION_CUES = ["conclusion", "concluding", "in summary", "we conclude"]


def fallback_section(text: str) -> str:
    lower = text.lower()
    if any(cue in lower for cue in CONCLUSION_CUES):
        return "Conclusion"
    if any(cue in lower for cue in DISCUSSION_CUES):
        return "Discussion"
    if any(cue in lower for cue in RESULT_CUES):
        return "Result"
    if any(cue in lower for cue in ["algorithm", "mechanism", "model", "framework", "query", "method"]):
        return "Methodology"
    if any(cue in lower for cue in INTRO_CUES):
        return "Introduction"
    return "Other"


def fallback_sentiment(text: str, alignment_status: str) -> float:
    lower = text.lower()
    neg = sum(cue in lower for cue in NEGATIVE_CUES)
    pos = sum(cue in lower for cue in POSITIVE_CUES)
    if neg > pos:
        return -0.45
    if pos > 0:
        return 0.35 if alignment_status == "high_confidence" else 0.2
    return 0.0


def fallback_relevance(section: str, text: str, num_mentions: int, alignment_status: str) -> float:
    lower = text.lower()
    score = 0.45
    if section == "Methodology":
        score = 0.82
    elif section == "Result":
        score = 0.76
    elif section == "Discussion":
        score = 0.62
    elif section == "Introduction":
        score = 0.38
    elif section == "Conclusion":
        score = 0.48

    if "compare" in lower or "baseline" in lower or "using" in lower or "based on" in lower:
        score += 0.08
    if num_mentions and num_mentions >= 2:
        score += 0.05
    if alignment_status in {"grouped", "range"}:
        score -= 0.08
    return clamp(score, 0.1, 0.95)


def fallback_confidence(alignment_status: str, num_mentions: int) -> float:
    base = {"high_confidence": 0.82, "grouped": 0.68, "range": 0.63}.get(alignment_status, 0.55)
    if num_mentions and num_mentions >= 2:
        base += 0.04
    return clamp(base, 0.0, 0.95)


def local_fallback_score(row: pd.Series) -> Dict[str, object]:
    text = str(row["all_target_aligned_contexts"])
    section = fallback_section(text)
    sentiment = fallback_sentiment(text, str(row["alignment_status"]))
    relevance = fallback_relevance(section, text, int(row.get("num_mentions", 0) or 0), str(row["alignment_status"]))
    confidence = fallback_confidence(str(row["alignment_status"]), int(row.get("num_mentions", 0) or 0))
    return {
        "section": section,
        "sentiment": float(sentiment),
        "relevance": float(relevance),
        "confidence": float(confidence),
        "raw_llm_response": json.dumps(
            {
                "backend": "offline_rule_based_fallback",
                "section": section,
                "sentiment": sentiment,
                "relevance": relevance,
                "confidence": confidence,
            },
            ensure_ascii=False,
        ),
        "scoring_backend": "offline_rule_based_fallback",
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT_PATH)
    candidates = df[df["alignment_status"].isin(SCORABLE_STATUSES)].copy().reset_index(drop=True)

    rows: List[Dict[str, object]] = []
    used_api = 0
    used_fallback = 0
    for _, row in candidates.iterrows():
        prompt = build_prompt(row)
        result = try_call_openai(prompt)
        if result is None:
            result = local_fallback_score(row)
            used_fallback += 1
        else:
            used_api += 1

        section = normalize_section(result.get("section"))
        sentiment = clamp(float(result.get("sentiment", 0.0)), -1.0, 1.0)
        relevance = clamp(float(result.get("relevance", 0.0)), 0.0, 1.0)
        confidence = clamp(float(result.get("confidence", 0.0)), 0.0, 1.0)
        q_ij = compute_q(section, sentiment, relevance)

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
                "q_ij": q_ij,
                "raw_llm_response": result.get("raw_llm_response", ""),
                "scoring_backend": result.get("scoring_backend", "unknown"),
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    summary = pd.DataFrame(
        [
            {"metric": "candidate_edges_to_score", "value": int(len(candidates))},
            {"metric": "used_openai_api_count", "value": int(used_api)},
            {"metric": "used_offline_fallback_count", "value": int(used_fallback)},
        ]
    )
    summary.to_csv(RESULTS_DIR / "table_llm_target_aligned_v2_backend_summary.csv", index=False, encoding="utf-8-sig")
    print(f"wrote {len(out)} scored edges to {OUTPUT_PATH}")
    print(f"used_api={used_api} used_fallback={used_fallback}")


if __name__ == "__main__":
    main()
