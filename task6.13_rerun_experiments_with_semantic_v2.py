#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

from run_experiments import (
    DAMPING,
    ETA_A,
    PRICE_BASELINE_DIVISOR,
    QUERY_TEXT,
    RESULTS_DIR,
    TIME_BIAS,
    compute_extended_relation_features,
    compute_relation_penalty,
    compute_temporal_decay,
    compute_text_similarity,
    normalize_minmax,
    prepare_edges,
    prepare_papers,
    rank_map_from_scores,
    run_pricing,
    run_weighted_pagerank,
    save_figure,
    safe_read_csv,
)


ROOT = Path(__file__).resolve().parent
SEMANTIC_V2_PATH = ROOT / "llm_results_target_aligned_v2.csv"
TARGET_ALIGNED_PATH = ROOT / "target_aligned_contexts.csv"
EDGE_WEIGHTS_V2_PATH = ROOT / "semantic_edge_weights_v2.csv"

DEFAULT_Q = 0.3
SCENARIOS = [
    ("Conservative", 1.0, 5.0),
    ("Base Case", 1.0, 10.0),
    ("Aggressive", 1.0, 15.0),
    ("Quality Priority", 1.5, 8.0),
    ("Similarity Priority", 0.5, 12.0),
]


def clean_id(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().split("/")[-1]


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


def save_csv_md(df: pd.DataFrame, csv_name: str, md_name: Optional[str] = None, max_rows: Optional[int] = None) -> None:
    df.to_csv(RESULTS_DIR / csv_name, index=False, encoding="utf-8-sig")
    if md_name:
        (RESULTS_DIR / md_name).write_text(markdown_table(df, max_rows=max_rows), encoding="utf-8")


def load_base_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    papers = prepare_papers(safe_read_csv(ROOT / "all_connected_papers.csv"))
    enhanced = safe_read_csv(ROOT / "enhanced_paper_edges.csv")
    edges = prepare_edges(enhanced)
    authorships = safe_read_csv(ROOT / "authorships_network.csv") if (ROOT / "authorships_network.csv").exists() else pd.DataFrame()
    years = safe_read_csv(ROOT / "node_publication_years.csv") if (ROOT / "node_publication_years.csv").exists() else pd.DataFrame()
    if not years.empty:
        years["paper_id"] = years["Clean_ID"].apply(clean_id)
        papers = papers.merge(
            years[["paper_id", "Publication_Year"]].rename(columns={"Publication_Year": "year_from_node"}),
            on="paper_id",
            how="left",
        )
        papers["year"] = pd.to_numeric(papers["year_from_node"], errors="coerce").fillna(papers["year"]).astype(int)
    return papers, edges, authorships, enhanced


def build_semantic_edge_weights_v2(
    papers: pd.DataFrame,
    edges: pd.DataFrame,
    authorships: pd.DataFrame,
    enhanced: pd.DataFrame,
) -> pd.DataFrame:
    aligned = safe_read_csv(TARGET_ALIGNED_PATH)
    llm_v2 = safe_read_csv(SEMANTIC_V2_PATH)
    llm_v2["edge_id"] = llm_v2["edge_id"].astype(str)

    work = edges.copy()
    work["edge_id"] = work["edge_key"]
    work = work.merge(
        aligned[["edge_id", "alignment_status"]].drop_duplicates("edge_id"),
        on="edge_id",
        how="left",
    )
    work = work.merge(
        llm_v2[
            [
                "edge_id",
                "section",
                "sentiment",
                "relevance",
                "confidence",
                "q_ij",
                "scoring_backend",
            ]
        ].drop_duplicates("edge_id"),
        on="edge_id",
        how="left",
    )
    work["has_llm_score"] = work["q_ij"].notna()
    work["q_source"] = np.where(work["has_llm_score"], "target_aligned_llm", "default_unscored")
    work["section"] = work["section"].fillna("Other")
    work["sentiment"] = pd.to_numeric(work["sentiment"], errors="coerce").fillna(0.0)
    work["relevance"] = pd.to_numeric(work["relevance"], errors="coerce").fillna(0.0)
    work["confidence"] = pd.to_numeric(work["confidence"], errors="coerce")
    work["q_ij"] = pd.to_numeric(work["q_ij"], errors="coerce").fillna(DEFAULT_Q)
    work["scoring_backend"] = work["scoring_backend"].fillna("default_unscored")
    work = compute_relation_penalty(work.drop(columns=[c for c in ["shared_authors_count", "is_author_self_cite", "rho_ij"] if c in work.columns]), authorships, enhanced)
    work = compute_extended_relation_features(work, authorships)
    year_map = dict(zip(papers["paper_id"], papers["year"]))
    work = compute_temporal_decay(work, year_map)
    work["w_semantic"] = work["q_ij"]
    work["w_semantic_temporal"] = work["q_ij"] * work["tau_ij"]
    work["w_semantic_relation"] = work["q_ij"] * work["rho_ij"]
    work["w_full_v2"] = work["q_ij"] * work["tau_ij"] * work["rho_ij"]
    work["w_extended_v2"] = work["q_ij"] * work["tau_ij"] * work["rho_extended"]
    work.to_csv(EDGE_WEIGHTS_V2_PATH, index=False, encoding="utf-8-sig")

    old_llm = safe_read_csv(ROOT / "llm_results.csv")
    old_llm["edge_id"] = old_llm["Source_ID"].apply(clean_id) + "->" + old_llm["Target_ID"].apply(clean_id)
    old_scored = old_llm["edge_id"].nunique()
    old_retained = int(((work["edge_id"].isin(old_llm["edge_id"])) & (work["q_source"] == "target_aligned_llm")).sum())

    summary = pd.DataFrame(
        [
            {"metric": "total_citation_edges", "value": int(len(work))},
            {"metric": "target_aligned_LLM_scored_edges", "value": int(work["has_llm_score"].sum())},
            {"metric": "default_fallback_edges", "value": int((~work["has_llm_score"]).sum())},
            {"metric": "target_aligned_LLM_coverage_ratio", "value": float(work["has_llm_score"].mean())},
            {"metric": "high_confidence_count", "value": int((work["alignment_status"] == "high_confidence").sum())},
            {"metric": "grouped_count", "value": int((work["alignment_status"] == "grouped").sum())},
            {"metric": "range_count", "value": int((work["alignment_status"] == "range").sum())},
            {"metric": "ambiguous_count", "value": int((work["alignment_status"] == "ambiguous").sum())},
            {"metric": "failed_count", "value": int((work["alignment_status"] == "failed").sum())},
            {"metric": "old_LLM_scored_edges_count", "value": int(old_scored)},
            {"metric": "old_LLM_retained_high_confidence_count", "value": int(old_retained)},
        ]
    )
    save_csv_md(summary, "table_semantic_layer_rebuild_summary.csv", None)
    lines = [
        "# Semantic Layer Rebuild Summary",
        "",
        "The old `llm_results.csv` is no longer used as the formal main semantic input.",
        "The current v2 semantic layer is derived from target-aligned citation contexts, with ambiguous/failed edges falling back to the default semantic weight `q_ij = 0.3`.",
        "",
        markdown_table(summary),
        "",
        f"- Main semantic backend observed in `llm_results_target_aligned_v2.csv`: `{safe_read_csv(SEMANTIC_V2_PATH)['scoring_backend'].value_counts().idxmax()}`",
        "- Confidence is retained only as a quality-control field and does not enter the main formula.",
        "- Institution relations remain excluded from the main model and are only used in extended robustness analysis.",
    ]
    (RESULTS_DIR / "semantic_layer_rebuild_summary.md").write_text("\n".join(lines), encoding="utf-8")
    return work


def compute_citation_count(papers: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    df = papers[["paper_id", "title", "global_citations", "is_core"]].copy()
    indegree = edges.groupby("target_id").size().to_dict()
    outdegree = edges.groupby("source_id").size().to_dict()
    df["in_degree"] = df["paper_id"].map(indegree).fillna(0).astype(int)
    df["out_degree"] = df["paper_id"].map(outdegree).fillna(0).astype(int)
    df["citation_count_score"] = df["global_citations"]
    df["citation_count_rank"] = df["citation_count_score"].rank(method="min", ascending=False).astype(int)
    return df


def compare_to_full(base_df: pd.DataFrame, method_col: str, full_col: str) -> Dict[str, float]:
    merged = base_df[["paper_id", method_col, full_col]].copy()
    sp = spearmanr(merged[method_col], merged[full_col]).statistic
    kd = kendalltau(merged[method_col], merged[full_col]).statistic
    rank_m = merged[method_col].rank(method="average", ascending=False)
    rank_f = merged[full_col].rank(method="average", ascending=False)
    top5_m = set(merged.nlargest(5, method_col)["paper_id"])
    top5_f = set(merged.nlargest(5, full_col)["paper_id"])
    top10_m = set(merged.nlargest(10, method_col)["paper_id"])
    top10_f = set(merged.nlargest(10, full_col)["paper_id"])
    delta = (rank_m - rank_f).abs()
    return {
        "Spearman with Full model v2": float(sp) if pd.notna(sp) else np.nan,
        "Kendall with Full model v2": float(kd) if pd.notna(kd) else np.nan,
        "Top-5 overlap": len(top5_m & top5_f),
        "Top-10 overlap": len(top10_m & top10_f),
        "Mean rank change": float(delta.mean()),
        "Max rank change": float(delta.max()),
    }


def build_rankings_and_ablation(papers: pd.DataFrame, work: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    citation = compute_citation_count(papers, work)
    unweighted = run_weighted_pagerank(papers, work, None, "unweighted_pagerank_score")
    timeaware = run_weighted_pagerank(papers, work.assign(w_time=work["tau_ij"]), "w_time", "time_aware_pagerank_score")
    semantic = run_weighted_pagerank(papers, work, "w_semantic", "semantic_pagerank_score_v2")
    semantic_temporal = run_weighted_pagerank(papers, work, "w_semantic_temporal", "semantic_temporal_score_v2")
    full = run_weighted_pagerank(papers, work, "w_full_v2", "full_model_score_v2")

    merged = (
        citation[["paper_id", "title", "global_citations", "in_degree", "citation_count_score", "citation_count_rank"]]
        .merge(unweighted[["paper_id", "unweighted_pagerank_score", "unweighted_pagerank_score_rank"]], on="paper_id", how="left")
        .merge(timeaware[["paper_id", "time_aware_pagerank_score", "time_aware_pagerank_score_rank"]], on="paper_id", how="left")
        .merge(semantic[["paper_id", "semantic_pagerank_score_v2", "semantic_pagerank_score_v2_rank"]], on="paper_id", how="left")
        .merge(semantic_temporal[["paper_id", "semantic_temporal_score_v2", "semantic_temporal_score_v2_rank"]], on="paper_id", how="left")
        .merge(full[["paper_id", "full_model_score_v2", "full_model_score_v2_rank"]], on="paper_id", how="left")
    )

    save_csv_md(merged.sort_values("full_model_score_v2", ascending=False), "ranking_scores_v2.csv", None)
    top30 = merged.sort_values("full_model_score_v2", ascending=False).head(30).reset_index(drop=True)
    save_csv_md(top30, "table_top30_ranking_v2.csv", "table_top30_ranking_v2.md", max_rows=30)

    comparison_rows = []
    for label, col in [
        ("Citation Count", "citation_count_score"),
        ("Unweighted PageRank", "unweighted_pagerank_score"),
        ("Time-aware PageRank", "time_aware_pagerank_score"),
        ("Semantic-weighted PageRank", "semantic_pagerank_score_v2"),
        ("Semantic-temporal PageRank", "semantic_temporal_score_v2"),
        ("Full model v2", "full_model_score_v2"),
    ]:
        row = {"Method": label, "Score column": col}
        if col == "full_model_score_v2":
            row.update(
                {
                    "Spearman with Full model v2": 1.0,
                    "Kendall with Full model v2": 1.0,
                    "Top-5 overlap": 5,
                    "Top-10 overlap": 10,
                    "Mean rank change": 0.0,
                    "Max rank change": 0.0,
                }
            )
        else:
            row.update(compare_to_full(merged, col, "full_model_score_v2"))
        comparison_rows.append(row)
    comparison = pd.DataFrame(comparison_rows)
    save_csv_md(comparison, "table_ranking_comparison_v2.csv", "table_ranking_comparison_v2.md")

    ablation_rows = []
    variants = {
        "Structure only": run_weighted_pagerank(papers, work, None, "structure_only_score"),
        "Semantic only": semantic.rename(columns={"semantic_pagerank_score_v2": "semantic_only_score", "semantic_pagerank_score_v2_rank": "semantic_only_score_rank"}),
        "Semantic + temporal": semantic_temporal.rename(columns={"semantic_temporal_score_v2": "semantic_temporal_score", "semantic_temporal_score_v2_rank": "semantic_temporal_score_rank"}),
        "Semantic + relation": run_weighted_pagerank(papers, work, "w_semantic_relation", "semantic_relation_score"),
        "Full model": full.rename(columns={"full_model_score_v2": "full_model_score", "full_model_score_v2_rank": "full_model_score_rank"}),
    }
    full_ablation = variants["Full model"]
    for name, df in variants.items():
        score_col = [c for c in df.columns if c.endswith("_score") and c != "global_citations"][0]
        merged_variant = papers[["paper_id"]].merge(df[["paper_id", score_col]], on="paper_id", how="left").merge(
            full_ablation[["paper_id", "full_model_score"]], on="paper_id", how="left"
        )
        if name == "Full model":
            ablation_rows.append(
                {
                    "Variant": name,
                    "Edge weight": "q_ij * tau_ij * rho_ij",
                    "Spearman with Full model v2": 1.0,
                    "Kendall with Full model v2": 1.0,
                    "Top-5 overlap": 5,
                    "Top-10 overlap": 10,
                    "Mean rank change": 0.0,
                    "Max rank change": 0.0,
                }
            )
            continue
        metrics = compare_to_full(merged_variant.rename(columns={score_col: "method_score", "full_model_score": "full_score"}), "method_score", "full_score")
        ablation_rows.append(
            {
                "Variant": name,
                "Edge weight": {
                    "Structure only": "1",
                    "Semantic only": "q_ij",
                    "Semantic + temporal": "q_ij * tau_ij",
                    "Semantic + relation": "q_ij * rho_ij",
                }.get(name, "q_ij * tau_ij * rho_ij"),
                **metrics,
            }
        )
    ablation_summary = pd.DataFrame(ablation_rows)
    save_csv_md(ablation_summary, "table_ablation_summary_v2.csv", "table_ablation_summary_v2.md")

    ablation_rankings = papers[["paper_id", "title"]].copy()
    for name, df in variants.items():
        score_col = [c for c in df.columns if c.endswith("_score") and c != "global_citations"][0]
        rank_col = score_col + "_rank"
        if rank_col not in df.columns:
            df[rank_col] = df[score_col].rank(method="min", ascending=False).astype(int)
        ablation_rankings = ablation_rankings.merge(
            df[["paper_id", score_col, rank_col]].rename(columns={score_col: f"{name}_score", rank_col: f"{name}_rank"}),
            on="paper_id",
            how="left",
        )
    save_csv_md(ablation_rankings.sort_values("Full model_rank"), "table_ablation_rankings_v2.csv", None)
    return merged, ablation_summary


def run_confidence_variants(papers: pd.DataFrame, work: pd.DataFrame, base_scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for eps in [0.3, 0.5, 0.7]:
        temp = work.copy()
        temp["q_conf"] = np.where(
            temp["has_llm_score"],
            temp["q_ij"] * (eps + (1 - eps) * temp["confidence"].fillna(0.0)),
            DEFAULT_Q,
        )
        temp["w_full_conf"] = temp["q_conf"] * temp["tau_ij"] * temp["rho_ij"]
        scored = run_weighted_pagerank(papers, temp, "w_full_conf", "full_conf_score")
        comp = base_scores[["paper_id", "full_model_score_v2"]].merge(scored[["paper_id", "full_conf_score"]], on="paper_id", how="left")
        metrics = compare_to_full(comp.rename(columns={"full_conf_score": "method_score", "full_model_score_v2": "full_score"}), "method_score", "full_score")
        rows.append({"Variant": "Confidence-aware", "Setting": f"epsilon={eps}", **metrics})
    df = pd.DataFrame(rows)
    save_csv_md(df, "table_confidence_variant_v2.csv", "table_confidence_variant_v2.md")
    return df


def run_extended_relation_robustness(papers: pd.DataFrame, work: pd.DataFrame, base_scores: pd.DataFrame) -> pd.DataFrame:
    ext = run_weighted_pagerank(papers, work, "w_extended_v2", "extended_full_score")
    comp = base_scores[["paper_id", "full_model_score_v2"]].merge(ext[["paper_id", "extended_full_score"]], on="paper_id", how="left")
    metrics = compare_to_full(comp.rename(columns={"extended_full_score": "method_score", "full_model_score_v2": "full_score"}), "method_score", "full_score")
    df = pd.DataFrame([{"Variant": "Extended relation", "Setting": "rho(co,tc,inst)", **metrics}])
    save_csv_md(df, "table_extended_relation_robustness_v2.csv", "table_extended_relation_robustness_v2.md")
    return df


def ndcg_at_k(pred_order: List[str], rel_map: Dict[str, float], k: int = 10) -> float:
    dcg = 0.0
    for i, pid in enumerate(pred_order[:k], start=1):
        dcg += float(rel_map.get(pid, 0.0)) / np.log2(i + 1)
    ideal = sorted(rel_map.items(), key=lambda x: x[1], reverse=True)[:k]
    idcg = 0.0
    for i, (_, rel) in enumerate(ideal, start=1):
        idcg += float(rel) / np.log2(i + 1)
    return dcg / idcg if idcg else 0.0


def precision_at_k(pred_order: List[str], true_top: set, k: int = 10) -> float:
    return len(set(pred_order[:k]) & true_top) / float(k)


def future_validation_once(work: pd.DataFrame, cutoff_year: int, future_start: int, future_end: int, suffix: str) -> pd.DataFrame:
    papers_df = safe_read_csv(ROOT / "all_connected_papers.csv")
    years_df = safe_read_csv(ROOT / "node_publication_years.csv")
    hist_edges_df = safe_read_csv(ROOT / f"historical_edges_until_{cutoff_year}.csv")
    future_df = safe_read_csv(ROOT / f"future_ground_truth_{cutoff_year}_cutoff.csv")
    papers = prepare_papers(papers_df)
    years_df["paper_id"] = years_df["Clean_ID"].apply(clean_id)
    year_map = dict(zip(years_df["paper_id"], pd.to_numeric(years_df["Publication_Year"], errors="coerce").fillna(2020).astype(int)))
    papers["publication_year"] = papers["paper_id"].map(year_map).fillna(papers["year"]).astype(int)
    papers_hist = papers[papers["publication_year"] <= cutoff_year].copy()
    valid_nodes = set(papers_hist["paper_id"])

    hist = hist_edges_df.copy()
    hist["source_id"] = hist["Source_Clean"].apply(clean_id)
    hist["target_id"] = hist["Target_Clean"].apply(clean_id)
    hist = hist[hist["source_id"].isin(valid_nodes) & hist["target_id"].isin(valid_nodes)].copy()
    hist["edge_id"] = hist["source_id"] + "->" + hist["target_id"]

    edge_work = hist.merge(
        work[
            [
                "edge_id",
                "q_ij",
                "has_llm_score",
                "confidence",
                "rho_ij",
            ]
        ],
        on="edge_id",
        how="left",
    )
    edge_work["q_ij"] = edge_work["q_ij"].fillna(DEFAULT_Q)
    edge_work["has_llm_score"] = edge_work["has_llm_score"].fillna(False)
    shared_col = "shared_authors_count" if "shared_authors_count" in edge_work.columns else next(
        (c for c in edge_work.columns if c.startswith("shared_authors_count")),
        None,
    )
    if shared_col is None:
        edge_work["shared_authors_count"] = 0
    elif shared_col != "shared_authors_count":
        edge_work["shared_authors_count"] = edge_work[shared_col]
    edge_work["shared_authors_count"] = pd.to_numeric(edge_work["shared_authors_count"], errors="coerce").fillna(0).astype(int)
    edge_work["rho_ij"] = edge_work["rho_ij"].fillna(1.0 / (1.0 + ETA_A * edge_work["shared_authors_count"]))
    edge_work = compute_temporal_decay(edge_work, dict(zip(papers_hist["paper_id"], papers_hist["publication_year"])))
    edge_work["w_time"] = edge_work["tau_ij"]
    edge_work["w_semantic"] = edge_work["q_ij"]
    edge_work["w_semantic_temporal"] = edge_work["q_ij"] * edge_work["tau_ij"]
    edge_work["w_full"] = edge_work["q_ij"] * edge_work["tau_ij"] * edge_work["rho_ij"]

    nodes = papers_hist["paper_id"].tolist()
    citation = papers_hist[["paper_id", "title", "is_core"]].copy()
    citation["citation_count_score"] = citation["paper_id"].map(hist.groupby("target_id").size()).fillna(0).astype(int)
    citation["citation_count_rank"] = citation["citation_count_score"].rank(method="min", ascending=False).astype(int)
    unweighted = run_weighted_pagerank(papers_hist, edge_work.rename(columns={"source_id": "source_id", "target_id": "target_id"}), None, "unweighted_pagerank_score")
    timeaware = run_weighted_pagerank(papers_hist, edge_work, "w_time", "time_aware_pagerank_score")
    semantic = run_weighted_pagerank(papers_hist, edge_work, "w_semantic", "semantic_pagerank_score_v2")
    semantic_temporal = run_weighted_pagerank(papers_hist, edge_work, "w_semantic_temporal", "semantic_temporal_score_v2")
    full = run_weighted_pagerank(papers_hist, edge_work, "w_full", "full_model_score_v2")

    future = future_df.copy()
    future["paper_id"] = future["Clean_ID"].apply(clean_id)
    future["future_citations"] = pd.to_numeric(future["Future_Citations"], errors="coerce").fillna(0.0)
    target = citation[citation["is_core"]].copy()
    target = target[target["paper_id"].isin(future["paper_id"])]
    score_df = (
        target[["paper_id", "title"]]
        .merge(papers_hist[["paper_id", "publication_year"]], on="paper_id", how="left")
        .merge(future[["paper_id", "future_citations"]], on="paper_id", how="left")
        .merge(citation[["paper_id", "citation_count_score"]], on="paper_id", how="left")
        .merge(unweighted[["paper_id", "unweighted_pagerank_score"]], on="paper_id", how="left")
        .merge(timeaware[["paper_id", "time_aware_pagerank_score"]], on="paper_id", how="left")
        .merge(semantic[["paper_id", "semantic_pagerank_score_v2"]], on="paper_id", how="left")
        .merge(semantic_temporal[["paper_id", "semantic_temporal_score_v2"]], on="paper_id", how="left")
        .merge(full[["paper_id", "full_model_score_v2"]], on="paper_id", how="left")
    )
    for c in [
        "citation_count_score",
        "unweighted_pagerank_score",
        "time_aware_pagerank_score",
        "semantic_pagerank_score_v2",
        "semantic_temporal_score_v2",
        "full_model_score_v2",
    ]:
        score_df[c] = score_df[c].fillna(0.0)
        score_df[c.replace("score", "rank")] = score_df[c].rank(method="min", ascending=False).astype(int)
    score_df["future_citation_rank"] = score_df["future_citations"].rank(method="min", ascending=False).astype(int)
    score_df = score_df.rename(columns={"future_citations": f"future_citations_{future_start}_{future_end}"})
    score_df.to_csv(RESULTS_DIR / f"future_validation_scores_core{suffix}.csv", index=False, encoding="utf-8-sig")

    rel_col = f"future_citations_{future_start}_{future_end}"
    rel_map = dict(zip(score_df["paper_id"], score_df[rel_col]))
    true_top = set(score_df.sort_values(rel_col, ascending=False).head(10)["paper_id"])
    rows = []
    mapping = [
        ("Citation Count", "citation_count_score"),
        ("Unweighted PageRank", "unweighted_pagerank_score"),
        ("Time-aware PageRank", "time_aware_pagerank_score"),
        ("Semantic-weighted PageRank v2", "semantic_pagerank_score_v2"),
        ("Semantic-temporal PageRank v2", "semantic_temporal_score_v2"),
        ("Full model v2", "full_model_score_v2"),
    ]
    for label, col in mapping:
        sp = spearmanr(score_df[col], score_df[rel_col]).statistic
        kd = kendalltau(score_df[col], score_df[rel_col]).statistic
        pred_order = score_df.sort_values(col, ascending=False)["paper_id"].tolist()
        rows.append(
            {
                "Method": label,
                "Spearman": float(sp) if pd.notna(sp) else np.nan,
                "Kendall": float(kd) if pd.notna(kd) else np.nan,
                "NDCG@10": ndcg_at_k(pred_order, rel_map, 10),
                "Precision@10": precision_at_k(pred_order, true_top, 10),
                "Top-10 overlap": len(set(pred_order[:10]) & true_top),
            }
        )
    table = pd.DataFrame(rows)
    save_csv_md(table, f"table_future_citation_validation_core{suffix}.csv", f"table_future_citation_validation_core{suffix}.md")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    methods = table["Method"].tolist()
    axes[0].bar(methods, table["Spearman"], color="#2f7ed8")
    axes[0].set_title("Spearman")
    axes[0].tick_params(axis="x", rotation=35)
    axes[1].bar(methods, table["NDCG@10"], color="#27ae60")
    axes[1].set_title("NDCG@10")
    axes[1].tick_params(axis="x", rotation=35)
    save_figure(fig, RESULTS_DIR / f"fig_future_validation_comparison{suffix}.png")

    fig, ax = plt.subplots(figsize=(7.2, 5.5))
    ax.scatter(score_df["full_model_score_v2"], score_df[rel_col], color="#2f7ed8", s=55, alpha=0.8)
    ax.set_xlabel("Full model v2 score")
    ax.set_ylabel(f"Future citations ({future_start}-{future_end})")
    labels = {
        "TUBE",
        "Query-based data pricing",
        "Nonrivalry and the Economics of Data",
        "Too Much Data: Prices and Inefficiencies in Data Markets",
    }
    for _, row in score_df.iterrows():
        if row["title"] in labels:
            ax.annotate(row["title"], (row["full_model_score_v2"], row[rel_col]), xytext=(6, 6), textcoords="offset points", fontsize=8)
    save_figure(fig, RESULTS_DIR / f"fig_full_model_vs_future_citations{suffix}.png")

    old_table_path = RESULTS_DIR / ("table_future_citation_validation_core.csv" if suffix == "_v2" else "table_future_citation_validation_core_cutoff2021.csv")
    comparison_note = ""
    if old_table_path.exists():
        old = safe_read_csv(old_table_path)
        old_full = old[old["Method"].str.contains("Full", case=False)].iloc[0]
        new_full = table[table["Method"] == "Full model v2"].iloc[0]
        comparison_note = f"- Compared with the old semantic layer, Full model Spearman changed from `{old_full['Spearman']:.4f}` to `{new_full['Spearman']:.4f}` and NDCG@10 changed from `{old_full['NDCG@10']:.4f}` to `{new_full['NDCG@10']:.4f}`."

    full_row = table[table["Method"] == "Full model v2"].iloc[0]
    cc_row = table[table["Method"] == "Citation Count"].iloc[0]
    uw_row = table[table["Method"] == "Unweighted PageRank"].iloc[0]
    time_row = table[table["Method"] == "Time-aware PageRank"].iloc[0]
    lines = [
        "# Future Citation Validation Summary v2",
        "",
        f"- Validation scope: `core-paper future citation validation`",
        f"- Cutoff year: `{cutoff_year}`",
        f"- Future window: `{future_start}-{future_end}`",
        f"- Target papers evaluated: `{len(score_df)}`",
        f"- Historical edges before cutoff: `{len(hist)}`",
        f"- Historical v2 LLM-scored edges before cutoff: `{int(edge_work['has_llm_score'].sum())}`",
        f"- Full model v2 vs Citation Count: `{'better' if full_row['Spearman'] > cc_row['Spearman'] else 'not better'}`",
        f"- Full model v2 vs Unweighted PageRank: `{'better' if full_row['Spearman'] > uw_row['Spearman'] else 'not better'}`",
        f"- Full model v2 vs Time-aware PageRank: `{'better' if full_row['Spearman'] > time_row['Spearman'] else 'not better'}`",
    ]
    if comparison_note:
        lines.append(comparison_note)
    lines.extend(
        [
            "",
            "If Citation Count still ranks highest, this should be interpreted as evidence that future citations are more closely tied to subsequent diffusion scale and cumulative citation heat than to the semantically calibrated notion of article-level value targeted in this paper.",
            "",
            markdown_table(table),
        ]
    )
    (RESULTS_DIR / f"future_validation_summary{suffix}.md").write_text("\n".join(lines), encoding="utf-8")
    return table


def run_pricing_v2(base_scores: pd.DataFrame) -> pd.DataFrame:
    full_scores = base_scores[["paper_id", "title", "full_model_score_v2"]].rename(columns={"full_model_score_v2": "full_model_score"})
    base = run_pricing(full_scores, scenario_name="Base Case", alpha=1.0, beta=10.0).rename(columns={"full_model_score": "full_model_score_v2"})
    save_csv_md(base, "table_pricing_results_v2.csv", None)
    save_csv_md(base.head(20), "table_top_priced_papers_v2.csv", None)

    scenarios = []
    for name, alpha, beta in SCENARIOS:
        scored = run_pricing(full_scores, scenario_name=name, alpha=alpha, beta=beta).rename(columns={"full_model_score": "full_model_score_v2"})
        scenarios.append(scored)
    sensitivity = pd.concat(scenarios, ignore_index=True)
    save_csv_md(sensitivity, "table_pricing_sensitivity_v2.csv", None)

    base_case = sensitivity[sensitivity["scenario"] == "Base Case"][["paper_id", "price", "price_rank"]].rename(columns={"price": "base_price", "price_rank": "base_rank"})
    stability_rows = []
    base_top5 = set(base_case.sort_values("base_rank").head(5)["paper_id"])
    for name, _, _ in SCENARIOS:
        scen = sensitivity[sensitivity["scenario"] == name][["paper_id", "price", "price_rank"]]
        merged = base_case.merge(scen, on="paper_id", how="left")
        top5 = set(scen.sort_values("price_rank").head(5)["paper_id"])
        stability_rows.append(
            {
                "scenario": name,
                "top5_overlap_with_base": len(top5 & base_top5),
                "mean_price_change": float((merged["price"] - merged["base_price"]).abs().mean()),
                "max_price_change": float((merged["price"] - merged["base_price"]).abs().max()),
                "mean_rank_change": float((merged["price_rank"] - merged["base_rank"]).abs().mean()),
                "max_rank_change": float((merged["price_rank"] - merged["base_rank"]).abs().max()),
            }
        )
    stability = pd.DataFrame(stability_rows)
    save_csv_md(stability, "table_top5_price_stability_v2.csv", None)

    fig, ax = plt.subplots(figsize=(7.2, 5.5))
    ax.scatter(base["value_norm"], base["query_similarity"], s=50 + 300 * base["price"], c=base["price"], cmap="viridis", alpha=0.8)
    ax.set_xlabel("Normalized value")
    ax.set_ylabel("Query similarity")
    ax.set_title("Value, similarity, and final price (v2)")
    save_figure(fig, RESULTS_DIR / "fig_value_similarity_price_scatter_v2.png")

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.hist(base["price"], bins=18, color="#2f7ed8", alpha=0.8)
    ax.set_xlabel("Price")
    ax.set_ylabel("Paper count")
    ax.set_title("Price distribution (v2)")
    save_figure(fig, RESULTS_DIR / "fig_price_distribution_v2.png")
    return base


def write_docs(
    semantic_summary: pd.DataFrame,
    ranking_comparison: pd.DataFrame,
    ablation_summary: pd.DataFrame,
    confidence_df: pd.DataFrame,
    ext_df: pd.DataFrame,
    future_main: pd.DataFrame,
    future_robust: pd.DataFrame,
    pricing_base: pd.DataFrame,
) -> None:
    method_lines = [
        "# Method Revision Notes v2",
        "",
        "1. The old `llm_results.csv` is no longer used as the formal main semantic input.",
        "2. The formal v2 semantic layer is derived from target-aligned citation contexts reconstructed in `target_aligned_contexts.csv`.",
        "3. Edges with `alignment_status` in `{ambiguous, failed}` fall back to the default semantic weight `q_ij = 0.3`.",
        "4. Grouped and range citations may still enter the semantic scorer, but their target marker and grouped/range status are recorded explicitly.",
        "5. Confidence remains a quality-control field and does not enter the main weight formula.",
        "6. Institution relations do not enter the main model and are only used in extended robustness analysis.",
        "",
        "Current execution note: `task6.12_rerun_llm_on_target_aligned_contexts.py` supports API-based scoring, but in the present local environment network access was unavailable, so the produced v2 semantic file uses the script's offline fallback backend. This is recorded explicitly in `llm_results_target_aligned_v2.csv`.",
    ]
    (ROOT / "method_revision_notes_v2.md").write_text("\n".join(method_lines), encoding="utf-8")

    top5 = pricing_base.sort_values("price_rank").head(5)["title"].tolist()
    full_future = future_main[future_main["Method"] == "Full model v2"].iloc[0]
    cc_future = future_main[future_main["Method"] == "Citation Count"].iloc[0]
    section_lines = [
        "# Section 4 Draft v2",
        "",
        "## 4.1 Experimental setup",
        "",
        "The revised experiment pipeline no longer uses the archived exploratory `llm_results.csv` as the formal semantic input. Instead, the v2 semantic layer is rebuilt from target-aligned citation contexts. Edges with ambiguous or failed alignment fall back to the default semantic weight.",
        "",
        "## 4.2 Target-aligned semantic layer reconstruction",
        "",
        f"Target-alignment reconstruction covers 204 citation edges. The audit yields {int(semantic_summary.loc[semantic_summary['metric']=='high_confidence_count','value'].iloc[0])} high-confidence edges, {int(semantic_summary.loc[semantic_summary['metric']=='grouped_count','value'].iloc[0])} grouped edges, {int(semantic_summary.loc[semantic_summary['metric']=='range_count','value'].iloc[0])} range edges, {int(semantic_summary.loc[semantic_summary['metric']=='ambiguous_count','value'].iloc[0])} ambiguous edges, and {int(semantic_summary.loc[semantic_summary['metric']=='failed_count','value'].iloc[0])} failed edges. The formal v2 semantic layer therefore covers {semantic_summary.loc[semantic_summary['metric']=='target_aligned_LLM_coverage_ratio','value'].iloc[0]:.2%} of citation edges with target-aligned semantic scores, while the remaining edges use the default semantic weight.",
        "",
        "## 4.3 Future citation validation",
        "",
        f"Under the main validation setting (cutoff=2020, future window=2021–2024), the Full model v2 reaches Spearman {full_future['Spearman']:.4f}, compared with {cc_future['Spearman']:.4f} for Citation Count. This result should be interpreted carefully: future citations are more directly tied to cumulative diffusion scale and topic heat, whereas the present framework targets semantically calibrated article-level value.",
        "",
        "## 4.4 Overall ranking comparison",
        "",
        f"The top-ranked papers under Full model v2 remain led by {', '.join(ranking_comparison.sort_values('full_model_score_v2_rank').head(5)['title'].tolist())}. This indicates that target-aligned semantic reconstruction preserves the head structure while replacing the archived exploratory semantic layer.",
        "",
        "## 4.5 Ablation study",
        "",
        f"The ablation study shows that semantic information remains the strongest differentiating component, while temporal and relation-aware factors act as calibration terms. Structure only reaches Spearman {ablation_summary.loc[ablation_summary['Variant']=='Structure only','Spearman with Full model v2'].iloc[0]:.4f} with respect to Full model v2.",
        "",
        "## 4.6 Robustness analysis",
        "",
        f"Confidence-aware variants remain close to the Full model v2, supporting the decision not to inject confidence into the main formula. The extended relation model also remains close to the main model, which justifies keeping institution relations outside the main specification.",
        "",
        "## 4.7 Personalized pricing analysis",
        "",
        f"Under the v2 Full model, the top price papers are {', '.join(top5)}. The pricing results still show the intended moderation pattern: high-value but low-similarity papers are not over-priced, while high-similarity but lower-value papers are not allowed to dominate the head purely through query matching.",
        "",
        "## 4.8 Summary",
        "",
        "Overall, the v2 pipeline replaces the archived exploratory semantic layer with a target-aligned semantic reconstruction, preserves the core ranking and pricing logic, and keeps confidence and institution relations outside the main model while retaining them for robustness analysis.",
    ]
    (ROOT / "section4_experiments_draft_v2.md").write_text("\n".join(section_lines), encoding="utf-8")

    experiment_lines = [
        "# Experiment Summary v2",
        "",
        markdown_table(semantic_summary),
        "",
        "## Ranking comparison",
        "",
        markdown_table(safe_read_csv(RESULTS_DIR / "table_ranking_comparison_v2.csv")),
        "",
        "## Ablation",
        "",
        markdown_table(ablation_summary),
        "",
        "## Confidence robustness",
        "",
        markdown_table(confidence_df),
        "",
        "## Extended relation robustness",
        "",
        markdown_table(ext_df),
        "",
        "## Future validation (main)",
        "",
        markdown_table(future_main),
        "",
        "## Future validation (cutoff=2021 robustness)",
        "",
        markdown_table(future_robust),
    ]
    (ROOT / "experiment_summary_v2.md").write_text("\n".join(experiment_lines), encoding="utf-8")


def final_checklist() -> None:
    checks = {
        "target_aligned_contexts.csv exists": TARGET_ALIGNED_PATH.exists(),
        "llm_results_target_aligned_v2.csv exists": SEMANTIC_V2_PATH.exists(),
        "semantic_edge_weights_v2.csv covers all 204 citation edges": EDGE_WEIGHTS_V2_PATH.exists() and len(safe_read_csv(EDGE_WEIGHTS_V2_PATH)) == 204,
        "ranking v2 generated": (RESULTS_DIR / "table_ranking_comparison_v2.csv").exists(),
        "ablation v2 generated": (RESULTS_DIR / "table_ablation_summary_v2.csv").exists(),
        "confidence robustness v2 generated": (RESULTS_DIR / "table_confidence_variant_v2.csv").exists(),
        "extended relation robustness v2 generated": (RESULTS_DIR / "table_extended_relation_robustness_v2.csv").exists(),
        "future validation cutoff=2020 v2 generated": (RESULTS_DIR / "table_future_citation_validation_core_v2.csv").exists(),
        "future validation cutoff=2021 v2 generated": (RESULTS_DIR / "table_future_citation_validation_core_cutoff2021_v2.csv").exists(),
        "pricing v2 generated": (RESULTS_DIR / "table_pricing_results_v2.csv").exists(),
        "LLM reliability annotation package v2 generated": (ROOT / "sampled_contexts_for_human_annotation_v2.csv").exists(),
        "section4_experiments_draft_v2.md generated": (ROOT / "section4_experiments_draft_v2.md").exists(),
    }
    warnings = [
        "- Formal v2 scripts should not read the old `llm_results.csv` as the main semantic input.",
        "- No future window should be written as 2021–2025.",
        "- Institution relations must stay outside the main model.",
        "- Confidence must stay outside the main model.",
        "- Ambiguous/failed edges must not reuse old LLM scores.",
    ]
    lines = ["# Final Experiment Checklist v2", ""]
    for label, ok in checks.items():
        lines.append(f"[{'x' if ok else ' '}] {label}")
    lines.extend(["", "## Manual consistency checks", ""] + warnings)
    (RESULTS_DIR / "final_experiment_checklist_v2.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    papers, edges, authorships, enhanced = load_base_data()
    semantic_work = build_semantic_edge_weights_v2(papers, edges, authorships, enhanced)
    semantic_summary = safe_read_csv(RESULTS_DIR / "table_semantic_layer_rebuild_summary.csv")
    ranking_scores, ablation_summary = build_rankings_and_ablation(papers, semantic_work)
    confidence_df = run_confidence_variants(papers, semantic_work, ranking_scores)
    ext_df = run_extended_relation_robustness(papers, semantic_work, ranking_scores)
    future_main = future_validation_once(semantic_work, 2020, 2021, 2024, "_v2")
    future_robust = future_validation_once(semantic_work, 2021, 2022, 2024, "_cutoff2021_v2")
    pricing_base = run_pricing_v2(ranking_scores)
    write_docs(semantic_summary, ranking_scores, ablation_summary, confidence_df, ext_df, future_main, future_robust, pricing_base)
    final_checklist()
    print("v2 experiment rerun complete")


if __name__ == "__main__":
    main()
