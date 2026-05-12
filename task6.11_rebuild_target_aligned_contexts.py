#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

from run_experiments import (
    RESULTS_DIR,
    compute_relation_penalty,
    compute_semantic_weight,
    compute_temporal_decay,
    prepare_edges,
    prepare_papers,
    run_weighted_pagerank,
    save_csv_and_md,
)


ROOT = Path(__file__).resolve().parent
PDF_ROOTS = [
    Path(r"C:\Users\76846\Desktop\new\pdfs"),  # 改成你的实际路径
    ROOT / "llm_reliability_annotation_package" / "source_pdfs_for_section_check",
]
TARGET_ALIGNED_PATH = ROOT / "target_aligned_contexts.csv"
FILTERED_LLM_PATH = ROOT / "llm_results_filtered.csv"

DEFAULT_Q = 0.3
KEEP_ALIGNMENT_STATUSES = {"exact", "high_confidence"}


def clean_id(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return text.split("/")[-1]


def normalize_text(text: object) -> str:
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def safe_read_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def markdown_table(df: pd.DataFrame, max_rows: Optional[int] = None) -> str:
    preview = df.copy()
    if max_rows is not None:
        preview = preview.head(max_rows)
    preview = preview.fillna("")
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


def parse_year(value: object) -> Optional[int]:
    if pd.isna(value):
        return None
    if isinstance(value, (int, np.integer)):
        year = int(value)
        return year if 1900 <= year <= 2100 else None
    text = str(value)
    match = re.search(r"(19|20)\d{2}", text)
    return int(match.group(0)) if match else None


def load_first_author_map(authorships: pd.DataFrame) -> Dict[str, str]:
    if authorships.empty:
        return {}
    df = authorships.copy()
    paper_col = next((c for c in df.columns if c.lower() in ("paper_id", "openalex_id")), df.columns[0])
    name_col = next((c for c in df.columns if "author_name" in c.lower()), None)
    pos_col = next((c for c in df.columns if "author_position" in c.lower()), None)
    if name_col is None:
        return {}
    df["paper_id"] = df[paper_col].apply(clean_id)
    df["author_name"] = df[name_col].fillna("").astype(str)
    if pos_col:
        first = df[df[pos_col].astype(str).str.lower() == "first"].copy()
        if not first.empty:
            return dict(zip(first["paper_id"], first["author_name"]))
    return (
        df[df["author_name"] != ""]
        .groupby("paper_id", as_index=False)
        .first()[["paper_id", "author_name"]]
        .set_index("paper_id")["author_name"]
        .to_dict()
    )


def build_pdf_path_map(papers: pd.DataFrame) -> Dict[str, Path]:
    title_map = {row.paper_id: row.title for row in papers.itertuples()}
    path_map: Dict[str, Path] = {}
    pdf_files: List[Path] = []
    for root in PDF_ROOTS:
        if root.exists():
            pdf_files.extend(sorted(root.glob("*.pdf")))
    indexed = {p.name: p for p in pdf_files}
    for pid, title in title_map.items():
        source_name = f"Source_{pid}.pdf"
        if source_name in indexed:
            path_map[pid] = indexed[source_name]
            continue
        title_norm = normalize_text(title)
        best_path = None
        best_score = 0.0
        for path in pdf_files:
            name_norm = normalize_text(path.stem)
            if not name_norm:
                continue
            score = SequenceMatcher(None, title_norm, name_norm).ratio()
            if title_norm and title_norm in name_norm:
                score += 0.25
            if score > best_score:
                best_score = score
                best_path = path
        if best_path is not None and best_score >= 0.55:
            path_map[pid] = best_path
    return path_map


PDF_TEXT_CACHE: Dict[Path, str] = {}


def extract_pdf_text(path: Path) -> str:
    if path in PDF_TEXT_CACHE:
        return PDF_TEXT_CACHE[path]
    try:
        reader = PdfReader(str(path))
        text_parts = []
        for page in reader.pages:
            try:
                text_parts.append(page.extract_text() or "")
            except Exception:
                text_parts.append("")
        text = "\n".join(text_parts)
    except Exception:
        text = ""
    PDF_TEXT_CACHE[path] = text
    return text


def split_body_and_references(full_text: str) -> Tuple[str, str]:
    if not full_text:
        return "", ""
    candidates = [
        r"\nreferences\b",
        r"\nbibliography\b",
        r"\nreference\s*\n",
    ]
    idx = -1
    lowered = full_text.lower()
    for pattern in candidates:
        match = re.search(pattern, lowered)
        if match:
            idx = max(idx, match.start())
    if idx == -1:
        return full_text, ""
    return full_text[:idx], full_text[idx:]


@dataclass
class ReferenceEntry:
    marker: str
    marker_number: Optional[int]
    entry_text: str


def parse_reference_entries(ref_text: str) -> List[ReferenceEntry]:
    if not ref_text:
        return []
    entries: List[ReferenceEntry] = []

    bracket_pattern = re.compile(r"(?ms)(?:^|\n)\s*\[(\d{1,3})\]\s*(.*?)(?=(?:\n\s*\[\d{1,3}\]\s)|\Z)")
    dot_pattern = re.compile(r"(?ms)(?:^|\n)\s*(\d{1,3})\.\s*(.*?)(?=(?:\n\s*\d{1,3}\.\s)|\Z)")

    for pattern, marker_style in ((bracket_pattern, "[{}]"), (dot_pattern, "{}")):
        matches = list(pattern.finditer(ref_text))
        if len(matches) >= 3:
            for match in matches:
                num = int(match.group(1))
                entry = re.sub(r"\s+", " ", match.group(2)).strip()
                if entry:
                    entries.append(ReferenceEntry(marker_style.format(num), num, entry))
            break
    return entries


def title_similarity(a: str, b: str) -> float:
    na = normalize_text(a)
    nb = normalize_text(b)
    if not na or not nb:
        return 0.0
    ratio = SequenceMatcher(None, na, nb).ratio()
    a_tokens = set(na.split())
    b_tokens = set(nb.split())
    jaccard = len(a_tokens & b_tokens) / max(1, len(a_tokens | b_tokens))
    if na in nb or nb in na:
        return max(ratio, 0.95)
    return 0.65 * ratio + 0.35 * jaccard


def match_reference_entry(
    entries: List[ReferenceEntry],
    target_title: str,
    target_doi: str,
    target_year: Optional[int],
    target_first_author: str,
) -> Tuple[Optional[ReferenceEntry], str, float]:
    if not entries:
        return None, "no_reference_entries", 0.0

    target_doi_norm = normalize_text(target_doi).replace(" ", "")
    target_title_norm = normalize_text(target_title)
    first_author_norm = normalize_text(target_first_author).split(" ")[0] if target_first_author else ""

    best_entry = None
    best_method = "failed"
    best_score = 0.0

    for entry in entries:
        entry_norm = normalize_text(entry.entry_text)
        entry_doi_match = re.search(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", entry.entry_text.lower())
        entry_doi = entry_doi_match.group(0) if entry_doi_match else ""
        if target_doi_norm and entry_doi and target_doi_norm in entry_doi.replace(" ", ""):
            return entry, "doi_exact", 1.0

        sim = title_similarity(target_title, entry.entry_text)
        author_hit = bool(first_author_norm and first_author_norm in entry_norm)
        year_hit = bool(target_year and re.search(rf"\b{target_year}\b", entry.entry_text))

        method = "failed"
        score = sim
        if target_title_norm and target_title_norm in entry_norm:
            method = "title_exact"
            score = max(score, 0.97)
        elif sim >= 0.85:
            method = "title_fuzzy_high"
        elif sim >= 0.72 and author_hit and year_hit:
            method = "author_year_title_fuzzy"
            score = max(score, 0.78)
        elif sim >= 0.68 and author_hit:
            method = "author_title_fuzzy"
            score = max(score, 0.72)

        if score > best_score:
            best_entry = entry
            best_method = method
            best_score = score

    return best_entry, best_method, float(best_score)


def sentence_boundaries(text: str) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    start = 0
    for match in re.finditer(r"(?<=[.!?])\s+|\n{2,}", text):
        end = match.start()
        chunk = text[start:end].strip()
        if chunk:
            spans.append((start, end))
        start = match.end()
    if start < len(text):
        chunk = text[start:].strip()
        if chunk:
            spans.append((start, len(text)))
    return spans


def expand_range_token(token: str) -> Iterable[int]:
    token = token.strip()
    if not token:
        return []
    token = token.replace("–", "-").replace("—", "-")
    if "-" in token:
        left, right = token.split("-", 1)
        if left.strip().isdigit() and right.strip().isdigit():
            lnum, rnum = int(left), int(right)
            if lnum <= rnum and rnum - lnum <= 20:
                return range(lnum, rnum + 1)
    if token.isdigit():
        return [int(token)]
    return []


def extract_target_mentions(body_text: str, marker_number: Optional[int]) -> Tuple[List[str], List[str]]:
    if not body_text or marker_number is None:
        return [], []

    sentence_spans = sentence_boundaries(body_text)
    if not sentence_spans:
        return [], []

    mentions: List[str] = []
    context_types: List[str] = []

    for match in re.finditer(r"\[([^\]]+)\]", body_text):
        inside = match.group(1)
        nums = []
        for token in re.split(r"[,\s;]+", inside):
            nums.extend(list(expand_range_token(token)))
        if marker_number not in nums:
            continue

        sent_idx = None
        for idx, (start, end) in enumerate(sentence_spans):
            if start <= match.start() <= end:
                sent_idx = idx
                break
        if sent_idx is None:
            continue

        window_ids = range(max(0, sent_idx - 1), min(len(sentence_spans), sent_idx + 2))
        window = " ".join(body_text[sentence_spans[i][0]:sentence_spans[i][1]].strip() for i in window_ids)
        window = re.sub(r"\s+", " ", window).strip()
        mentions.append(window)

        token_text = inside.replace("–", "-").replace("—", "-")
        if "," in token_text or ";" in token_text:
            context_types.append("grouped")
        elif "-" in token_text:
            context_types.append("range")
        else:
            context_types.append("exact")

    dedup_mentions = []
    dedup_types = []
    seen = set()
    for mention, ctype in zip(mentions, context_types):
        if mention not in seen:
            dedup_mentions.append(mention)
            dedup_types.append(ctype)
            seen.add(mention)
    return dedup_mentions, dedup_types


def classify_alignment_status(method: str, score: float, context_types: List[str], num_mentions: int) -> Tuple[str, str]:
    if method == "doi_exact" and num_mentions > 0:
        if "range" in context_types:
            return "range", "Reference entry matched by DOI; citation marker appears in a range citation."
        if "grouped" in context_types:
            return "grouped", "Reference entry matched by DOI; citation marker appears in a grouped citation."
        return "exact", "Reference entry matched by DOI and target-specific citation marker was found in body text."
    if method in {"title_exact", "title_fuzzy_high"} and score >= 0.85 and num_mentions > 0:
        if "range" in context_types:
            return "range", "Reference entry matched with high title confidence; marker appears in a range citation."
        if "grouped" in context_types:
            return "grouped", "Reference entry matched with high title confidence; marker appears in a grouped citation."
        return "high_confidence", "Reference entry matched with high title confidence and target marker was found."
    if method in {"author_year_title_fuzzy", "author_title_fuzzy"} and num_mentions > 0:
        return "ambiguous", "Reference entry matched fuzzily, but confidence is not high enough for direct semantic reuse."
    if method == "failed" or score == 0:
        return "failed", "Target paper could not be matched confidently to a numbered reference entry."
    if num_mentions == 0:
        return "ambiguous", "Reference entry matched, but the target marker was not found in the citing body text."
    return "ambiguous", "Alignment requires manual inspection."


def rebuild_target_aligned_contexts() -> Tuple[pd.DataFrame, pd.DataFrame]:
    papers = prepare_papers(safe_read_csv(ROOT / "all_connected_papers.csv"))
    edges_raw = safe_read_csv(ROOT / "enhanced_paper_edges.csv")
    authorships = safe_read_csv(ROOT / "authorships_network.csv") if (ROOT / "authorships_network.csv").exists() else pd.DataFrame()
    edges = prepare_edges(edges_raw)

    title_map = dict(zip(papers["paper_id"], papers["title"]))
    year_map = dict(zip(papers["paper_id"], papers["year"]))
    doi_map = dict(zip(papers["paper_id"], papers["doi"]))
    first_author_map = load_first_author_map(authorships)
    pdf_map = build_pdf_path_map(papers)

    rows: List[Dict[str, object]] = []
    for _, edge in edges.iterrows():
        source_id = edge["source_id"]
        target_id = edge["target_id"]
        edge_id = f"{source_id}->{target_id}"

        source_pdf = pdf_map.get(source_id)
        if source_pdf is None:
            rows.append(
                {
                    "edge_id": edge_id,
                    "source_id": source_id,
                    "target_id": target_id,
                    "citing_paper_title": title_map.get(source_id, ""),
                    "cited_paper_title": title_map.get(target_id, ""),
                    "citing_year": year_map.get(source_id),
                    "cited_year": year_map.get(target_id),
                    "target_reference_marker": "",
                    "target_reference_entry": "",
                    "reference_match_method": "pdf_missing",
                    "reference_match_score": 0.0,
                    "num_mentions": 0,
                    "all_target_aligned_contexts": "",
                    "context_type": "",
                    "alignment_status": "failed",
                    "alignment_note": "Source paper PDF not found locally.",
                }
            )
            continue

        full_text = extract_pdf_text(source_pdf)
        body_text, refs_text = split_body_and_references(full_text)
        entries = parse_reference_entries(refs_text)

        ref_entry, match_method, match_score = match_reference_entry(
            entries=entries,
            target_title=title_map.get(target_id, ""),
            target_doi=doi_map.get(target_id, ""),
            target_year=parse_year(year_map.get(target_id)),
            target_first_author=first_author_map.get(target_id, ""),
        )

        marker = ref_entry.marker if ref_entry else ""
        marker_number = ref_entry.marker_number if ref_entry else None
        mentions, context_types = extract_target_mentions(body_text, marker_number)
        context_type = "mixed" if len(set(context_types)) > 1 else (context_types[0] if context_types else "")
        status, note = classify_alignment_status(match_method, match_score, context_types, len(mentions))

        rows.append(
            {
                "edge_id": edge_id,
                "source_id": source_id,
                "target_id": target_id,
                "citing_paper_title": title_map.get(source_id, ""),
                "cited_paper_title": title_map.get(target_id, ""),
                "citing_year": year_map.get(source_id),
                "cited_year": year_map.get(target_id),
                "target_reference_marker": marker,
                "target_reference_entry": ref_entry.entry_text if ref_entry else "",
                "reference_match_method": match_method,
                "reference_match_score": float(match_score),
                "num_mentions": len(mentions),
                "all_target_aligned_contexts": "\n\n... [another target-aligned mention] ...\n\n".join(mentions),
                "context_type": context_type,
                "alignment_status": status,
                "alignment_note": note,
            }
        )

    aligned = pd.DataFrame(rows)
# 改成
    aligned.to_csv(TARGET_ALIGNED_PATH, index=False, encoding="utf-8-sig", escapechar="\\")
    summary = pd.DataFrame(
        [
            {"metric": "total_citation_edges", "value": int(len(aligned))},
            {"metric": "exact_count", "value": int((aligned["alignment_status"] == "exact").sum())},
            {"metric": "high_confidence_count", "value": int((aligned["alignment_status"] == "high_confidence").sum())},
            {"metric": "grouped_count", "value": int((aligned["alignment_status"] == "grouped").sum())},
            {"metric": "range_count", "value": int((aligned["alignment_status"] == "range").sum())},
            {"metric": "ambiguous_count", "value": int((aligned["alignment_status"] == "ambiguous").sum())},
            {"metric": "failed_count", "value": int((aligned["alignment_status"] == "failed").sum())},
            {
                "metric": "alignment_success_ratio",
                "value": float(aligned["alignment_status"].isin(["exact", "high_confidence", "grouped", "range"]).mean()),
            },
        ]
    )
    return aligned, summary


def rebuild_filtered_llm_and_rankings(aligned: pd.DataFrame) -> None:
    llm = safe_read_csv(ROOT / "llm_results.csv")
    llm["source_id"] = llm["Source_ID"].apply(clean_id)
    llm["target_id"] = llm["Target_ID"].apply(clean_id)
    llm["edge_id"] = llm["source_id"] + "->" + llm["target_id"]

    merged = llm.merge(
        aligned[["edge_id", "alignment_status", "reference_match_method", "reference_match_score", "num_mentions"]],
        on="edge_id",
        how="left",
    )
    merged["use_filtered_semantic_score"] = merged["alignment_status"].isin(KEEP_ALIGNMENT_STATUSES)
    merged["filtered_weight_combined"] = np.where(
        merged["use_filtered_semantic_score"],
        pd.to_numeric(merged["Weight_Combined"], errors="coerce").fillna(DEFAULT_Q),
        DEFAULT_Q,
    )
    merged["filtered_q_mode"] = np.where(merged["use_filtered_semantic_score"], "keep_original", "fallback_default")
    merged.to_csv(FILTERED_LLM_PATH, index=False, encoding="utf-8-sig")

    papers = prepare_papers(safe_read_csv(ROOT / "all_connected_papers.csv"))
    edges = prepare_edges(safe_read_csv(ROOT / "enhanced_paper_edges.csv"))
    authorships = safe_read_csv(ROOT / "authorships_network.csv") if (ROOT / "authorships_network.csv").exists() else pd.DataFrame()
    enhanced = safe_read_csv(ROOT / "enhanced_paper_edges.csv")

    filtered_keep = merged[merged["use_filtered_semantic_score"]].copy()
    semantic_edges, _ = compute_semantic_weight(filtered_keep, edges)
    for col in ["shared_authors_count", "is_author_self_cite", "rho_ij"]:
        if col in semantic_edges.columns:
            semantic_edges = semantic_edges.drop(columns=[col])
    semantic_edges = compute_relation_penalty(semantic_edges, authorships, enhanced)
    semantic_edges = compute_temporal_decay(semantic_edges, dict(zip(papers["paper_id"], papers["year"])))
    semantic_edges["semantic_only_weight"] = semantic_edges["q_ij"]
    semantic_edges["semantic_temporal_weight"] = semantic_edges["q_ij"] * semantic_edges["tau_ij"]
    semantic_edges["full_model_weight_filtered"] = semantic_edges["q_ij"] * semantic_edges["tau_ij"] * semantic_edges["rho_ij"]

    semantic_only = run_weighted_pagerank(papers, semantic_edges, "semantic_only_weight", "semantic_only_filtered_score")
    semantic_temporal = run_weighted_pagerank(papers, semantic_edges, "semantic_temporal_weight", "semantic_temporal_filtered_score")
    full_model = run_weighted_pagerank(papers, semantic_edges, "full_model_weight_filtered", "full_model_filtered_score")

    merged_rank = (
        papers[["paper_id", "title"]]
        .merge(semantic_only[["paper_id", "semantic_only_filtered_score", "semantic_only_filtered_score_rank"]], on="paper_id", how="left")
        .merge(semantic_temporal[["paper_id", "semantic_temporal_filtered_score", "semantic_temporal_filtered_score_rank"]], on="paper_id", how="left")
        .merge(full_model[["paper_id", "full_model_filtered_score", "full_model_filtered_score_rank"]], on="paper_id", how="left")
        .sort_values("full_model_filtered_score", ascending=False)
        .reset_index(drop=True)
    )
    save_csv_and_md(
        merged_rank,
        "table_filtered_semantic_rankings.csv",
        "table_filtered_semantic_rankings.md",
        max_rows=30,
    )

    llm_filter_summary = pd.DataFrame(
        [
            {"metric": "total_llm_edges", "value": int(len(merged))},
            {"metric": "kept_original_semantic_edges", "value": int(merged["use_filtered_semantic_score"].sum())},
            {"metric": "fallback_default_edges", "value": int((~merged["use_filtered_semantic_score"]).sum())},
            {"metric": "kept_ratio", "value": float(merged["use_filtered_semantic_score"].mean())},
        ]
    )
    save_csv_and_md(
        llm_filter_summary,
        "table_filtered_semantic_summary.csv",
        "table_filtered_semantic_summary.md",
    )


def write_alignment_summary(aligned: pd.DataFrame, summary: pd.DataFrame) -> None:
    failed_by_source = (
        aligned[aligned["alignment_status"] == "failed"]
        .groupby(["source_id", "citing_paper_title"], as_index=False)
        .size()
        .rename(columns={"size": "failed_alignments"})
        .sort_values("failed_alignments", ascending=False)
    )
    save_csv_and_md(
        summary,
        "table_rebuilt_context_alignment_summary.csv",
        None,
    )
    failed_by_source.to_csv(RESULTS_DIR / "table_alignment_failed_by_source.csv", index=False, encoding="utf-8-sig")

    lines = [
        "# Rebuilt Context Alignment Summary",
        "",
        "The old `llm_results.csv` should no longer be treated as the main semantic input without alignment filtering.",
        "",
        "## Aggregate counts",
        "",
        markdown_table(summary),
        "",
        "## Source papers with most failed alignments",
        "",
        markdown_table(failed_by_source, max_rows=10) if not failed_by_source.empty else "No failed alignments.",
        "",
        "## Interpretation",
        "",
        "Alignment statuses `exact` and `high_confidence` are the most suitable candidates for retained semantic scores.",
        "Statuses `grouped`, `range`, and `ambiguous` indicate that the target paper may be present but the local citation form is not clean enough for direct target-specific semantic reuse.",
        "Status `failed` means the source PDF or target-specific numbered reference link could not be established confidently.",
    ]
    (RESULTS_DIR / "rebuilt_context_alignment_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    aligned, summary = rebuild_target_aligned_contexts()
    write_alignment_summary(aligned, summary)
    rebuild_filtered_llm_and_rankings(aligned)
    print("target_aligned_contexts.csv written:", TARGET_ALIGNED_PATH)
    print("alignment summary written:", RESULTS_DIR / "rebuilt_context_alignment_summary.md")
    print("llm_results_filtered.csv written:", FILTERED_LLM_PATH)


if __name__ == "__main__":
    main()
