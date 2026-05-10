#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"

DEFAULT_Q = 0.3
TIME_BIAS = 5.0
ETA_A = 0.5

SECTION_WEIGHT_MAP = {
    "methodology": 1.0,
    "method": 1.0,
    "result": 1.0,
    "results": 1.0,
    "discussion": 0.7,
    "conclusion": 0.5,
    "conclusions": 0.5,
    "introduction": 0.4,
    "other": 0.2,
    "unknown": 0.2,
    "related work": 0.2,
}


def clean_id(value: object) -> Optional[str]:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.split("/")[-1]


def parse_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y"])


def ensure_results_dir() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def markdown_table(df: pd.DataFrame) -> str:
    preview = df.copy().fillna("")
    for col in preview.columns:
        if pd.api.types.is_float_dtype(preview[col]):
            preview[col] = preview[col].map(lambda x: f"{x:.6f}" if pd.notna(x) else "")
    headers = [str(c) for c in preview.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in preview.iterrows():
        vals = [str(row[c]).replace("\n", " ").strip() for c in preview.columns]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def detect_files(cutoff_year: int) -> Dict[str, Optional[Path]]:
    paths = {
        "all_connected_papers.csv": ROOT / "all_connected_papers.csv",
        "enhanced_paper_edges.csv": ROOT / "enhanced_paper_edges.csv",
        "node_publication_years.csv": ROOT / "node_publication_years.csv",
        "llm_results.csv": ROOT / "llm_results.csv",
        "future_ground_truth.csv": ROOT / "future_ground_truth.csv",
        f"future_ground_truth_{cutoff_year}_cutoff.csv": ROOT / f"future_ground_truth_{cutoff_year}_cutoff.csv",
        f"historical_edges_until_{cutoff_year}.csv": ROOT / f"historical_edges_until_{cutoff_year}.csv",
        f"historical_llm_until_{cutoff_year}.csv": ROOT / f"historical_llm_until_{cutoff_year}.csv",
        "future_ground_truth_all_papers.csv": ROOT / "future_ground_truth_all_papers.csv",
        "ranking_comparison_detailed.csv": ROOT / "ranking_comparison_detailed.csv",
        "weighted_pagerank_ranking_with_penalty.csv": ROOT / "weighted_pagerank_ranking_with_penalty.csv",
        "weighted_pagerank_ranking.csv": ROOT / "weighted_pagerank_ranking.csv",
    }
    return {name: path if path.exists() else None for name, path in paths.items()}


def load_required_data(file_map: Dict[str, Optional[Path]], cutoff_year: int) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = [
        "all_connected_papers.csv",
        "enhanced_paper_edges.csv",
        "node_publication_years.csv",
        "llm_results.csv",
    ]
    missing = [name for name in required if file_map[name] is None]
    future_path = file_map.get(f"future_ground_truth_{cutoff_year}_cutoff.csv") or file_map.get("future_ground_truth.csv")
    hist_edges_path = file_map.get(f"historical_edges_until_{cutoff_year}.csv")
    hist_llm_path = file_map.get(f"historical_llm_until_{cutoff_year}.csv")
    if future_path is None:
        missing.append("future_ground_truth.csv / future_ground_truth_{cutoff}_cutoff.csv")
    if hist_edges_path is None:
        missing.append(f"historical_edges_until_{cutoff_year}.csv")
    if hist_llm_path is None:
        missing.append(f"historical_llm_until_{cutoff_year}.csv")
    if missing:
        raise FileNotFoundError("Missing required files: " + ", ".join(missing))

    papers = pd.read_csv(file_map["all_connected_papers.csv"])
    edges = pd.read_csv(file_map["enhanced_paper_edges.csv"])
    years = pd.read_csv(file_map["node_publication_years.csv"])
    llm = pd.read_csv(file_map["llm_results.csv"])
    future = pd.read_csv(future_path)
    hist_edges = pd.read_csv(hist_edges_path)
    hist_llm = pd.read_csv(hist_llm_path)
    return papers, edges, years, llm, future, hist_edges, hist_llm


def map_section_weight(section: object) -> float:
    if pd.isna(section):
        return SECTION_WEIGHT_MAP["unknown"]
    text = str(section).strip().lower()
    if not text:
        return SECTION_WEIGHT_MAP["unknown"]
    for key, value in SECTION_WEIGHT_MAP.items():
        if key in text:
            return value
    return SECTION_WEIGHT_MAP["other"]


def prepare_papers(papers_df: pd.DataFrame, years_df: pd.DataFrame, cutoff_year: int) -> pd.DataFrame:
    papers = papers_df.copy()
    papers["paper_id"] = papers["OpenAlex_ID"].apply(clean_id)
    papers["title"] = papers["Title"].fillna("").astype(str)
    papers["is_core"] = parse_bool(papers["Is_Core"])

    years = years_df.copy()
    years["paper_id"] = years["Clean_ID"].apply(clean_id)
    years["publication_year"] = pd.to_numeric(years["Publication_Year"], errors="coerce")
    papers = papers.merge(years[["paper_id", "publication_year"]], on="paper_id", how="left")
    papers = papers.dropna(subset=["publication_year"]).copy()
    papers["publication_year"] = papers["publication_year"].astype(int)
    return papers[papers["publication_year"] <= cutoff_year].copy()


def prepare_historical_edges(hist_edges_df: pd.DataFrame, valid_nodes: set) -> pd.DataFrame:
    edges = hist_edges_df.copy()
    edges["source_id"] = edges["Source_Clean"].apply(clean_id)
    edges["target_id"] = edges["Target_Clean"].apply(clean_id)
    edges = edges[
        edges["source_id"].isin(valid_nodes) & edges["target_id"].isin(valid_nodes)
    ].copy()
    edges["shared_authors_count"] = pd.to_numeric(edges["shared_authors_count"], errors="coerce").fillna(0).astype(int)
    edges["rho_ij"] = 1.0 / (1.0 + ETA_A * edges["shared_authors_count"])
    return edges


def prepare_historical_llm(hist_llm_df: pd.DataFrame, valid_edge_keys: set) -> pd.DataFrame:
    llm = hist_llm_df.copy()
    llm["source_id"] = llm["Source_ID"].apply(clean_id)
    llm["target_id"] = llm["Target_ID"].apply(clean_id)
    llm["edge_key"] = llm["source_id"] + "->" + llm["target_id"]
    llm = llm[llm["edge_key"].isin(valid_edge_keys)].copy()
    llm["section"] = llm["LLM_Section"].fillna("").astype(str)
    llm["sentiment"] = pd.to_numeric(llm["LLM_Sentiment"], errors="coerce").fillna(0.0)
    llm["relevance"] = pd.to_numeric(llm["LLM_Relevance"], errors="coerce").fillna(0.0)
    llm["confidence"] = pd.to_numeric(llm["Confidence"], errors="coerce")
    llm["w_sec"] = llm["section"].apply(map_section_weight)
    llm["w_sent"] = np.where(llm["sentiment"] >= 0, (llm["sentiment"] + 1.0) / 2.0, 0.01)
    llm["w_rel"] = llm["relevance"] ** 2
    llm["q_ij"] = llm["w_sec"] * llm["w_sent"] * llm["w_rel"]
    llm = llm.sort_values(["edge_key", "q_ij"], ascending=[True, False]).drop_duplicates("edge_key", keep="first")
    return llm


def attach_edge_weights(edges: pd.DataFrame, llm_hist: pd.DataFrame, year_map: Dict[str, int]) -> pd.DataFrame:
    work = edges.copy()
    work["edge_key"] = work["source_id"] + "->" + work["target_id"]
    llm_map = dict(zip(llm_hist["edge_key"], llm_hist["q_ij"]))
    work["q_ij"] = work["edge_key"].map(llm_map).fillna(DEFAULT_Q)
    work["has_llm"] = work["edge_key"].isin(llm_map)
    work["source_year"] = work["source_id"].map(year_map).fillna(2020).astype(int)
    work["target_year"] = work["target_id"].map(year_map).fillna(2020).astype(int)
    work["delta_t"] = (work["source_year"] - work["target_year"]).clip(lower=0)
    work["tau_ij"] = TIME_BIAS / (TIME_BIAS + work["delta_t"].astype(float))
    work["w_time"] = work["tau_ij"]
    work["w_semantic"] = work["q_ij"]
    work["w_semantic_temporal"] = work["q_ij"] * work["tau_ij"]
    work["w_full"] = work["q_ij"] * work["tau_ij"] * work["rho_ij"]
    return work


def run_pagerank(nodes: List[str], edges: pd.DataFrame, weight_col: Optional[str]) -> Dict[str, float]:
    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    if weight_col is None:
        for _, row in edges.iterrows():
            graph.add_edge(row["source_id"], row["target_id"], weight=1.0)
    else:
        for _, row in edges.iterrows():
            graph.add_edge(row["source_id"], row["target_id"], weight=float(row[weight_col]))
    return nx.pagerank(graph, alpha=0.85, weight="weight")


def ndcg_at_k(pred_order: List[str], true_rel_map: Dict[str, float], k: int = 10) -> float:
    pred_top = pred_order[:k]
    dcg = 0.0
    for i, pid in enumerate(pred_top, start=1):
        rel = float(true_rel_map.get(pid, 0.0))
        dcg += rel / np.log2(i + 1)

    ideal_top = sorted(true_rel_map.items(), key=lambda x: x[1], reverse=True)[:k]
    idcg = 0.0
    for i, (_, rel) in enumerate(ideal_top, start=1):
        idcg += float(rel) / np.log2(i + 1)

    if idcg == 0:
        return 0.0
    return dcg / idcg


def precision_at_k(pred_order: List[str], future_topk: set, k: int = 10) -> float:
    return len(set(pred_order[:k]) & future_topk) / float(k)


def topk_overlap(pred_order: List[str], future_topk: set, k: int = 10) -> int:
    return len(set(pred_order[:k]) & future_topk)


def rank_desc(series: pd.Series) -> pd.Series:
    return series.rank(method="min", ascending=False).astype(int)


def build_validation_table(df: pd.DataFrame) -> pd.DataFrame:
    future_top10 = set(df.sort_values("future_citations_2021_2024", ascending=False).head(10)["paper_id"])
    rel_map = dict(zip(df["paper_id"], df["future_citations_2021_2024"]))
    rows = []
    method_map = [
        ("Citation Count", "citation_count_score"),
        ("Unweighted PageRank", "unweighted_pagerank_score"),
        ("Time-aware PageRank", "time_aware_pagerank_score"),
        ("Semantic-weighted PageRank", "semantic_pagerank_score"),
        ("Semantic-temporal PageRank", "semantic_temporal_score"),
        ("Full model", "full_model_score"),
    ]
    for method_name, col in method_map:
        sub = df[["paper_id", col, "future_citations_2021_2024"]].copy()
        spearman = spearmanr(sub[col], sub["future_citations_2021_2024"]).statistic
        kendall = kendalltau(sub[col], sub["future_citations_2021_2024"]).statistic
        pred_order = sub.sort_values(col, ascending=False)["paper_id"].tolist()
        rows.append(
            {
                "Method": method_name,
                "Spearman": float(spearman) if pd.notna(spearman) else np.nan,
                "Kendall": float(kendall) if pd.notna(kendall) else np.nan,
                "NDCG@10": ndcg_at_k(pred_order, rel_map, 10),
                "Precision@10": precision_at_k(pred_order, future_top10, 10),
                "Top-10 overlap": topk_overlap(pred_order, future_top10, 10),
            }
        )
    return pd.DataFrame(rows)


def save_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_comparison_table(table_df: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    methods = table_df["Method"].tolist()

    axes[0].bar(methods, table_df["Spearman"], color="#2f7ed8")
    axes[0].set_title("Spearman")
    axes[0].set_ylim(min(0.0, float(table_df["Spearman"].min()) * 1.15), max(0.1, float(table_df["Spearman"].max()) * 1.15))
    axes[0].tick_params(axis="x", rotation=35)

    axes[1].bar(methods, table_df["NDCG@10"], color="#27ae60")
    axes[1].set_title("NDCG@10")
    axes[1].set_ylim(0, max(0.1, float(table_df["NDCG@10"].max()) * 1.15))
    axes[1].tick_params(axis="x", rotation=35)
    save_figure(fig, out_path)


def plot_scatter(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.scatter(df["full_model_score"], df["future_citations_2021_2024"], color="#2f7ed8", alpha=0.8, s=55)
    ax.set_xlabel("Full model score")
    ax.set_ylabel("Future citations (2021-2024)")
    ax.set_title("Full model score vs. future citations")

    label_titles = {
        "TUBE",
        "Query-based data pricing",
        "Nonrivalry and the Economics of Data",
        "Too Much Data: Prices and Inefficiencies in Data Markets",
    }
    for _, row in df.iterrows():
        if row["title"] in label_titles:
            ax.annotate(
                row["title"],
                (row["full_model_score"], row["future_citations_2021_2024"]),
                xytext=(6, 6),
                textcoords="offset points",
                fontsize=8,
            )
    save_figure(fig, out_path)


def write_summary(
    table_df: pd.DataFrame,
    score_df: pd.DataFrame,
    out_path: Path,
    cutoff_year: int,
    future_start: int,
    future_end: int,
    target: str,
    total_labels: int,
    hist_edge_count: int,
    hist_llm_count: int,
    nonzero_future_count: int,
) -> None:
    best_spearman = table_df.sort_values("Spearman", ascending=False).iloc[0]
    best_ndcg = table_df.sort_values("NDCG@10", ascending=False).iloc[0]

    full_row = table_df[table_df["Method"] == "Full model"].iloc[0]
    cc_row = table_df[table_df["Method"] == "Citation Count"].iloc[0]
    uw_row = table_df[table_df["Method"] == "Unweighted PageRank"].iloc[0]
    time_row = table_df[table_df["Method"] == "Time-aware PageRank"].iloc[0]

    full_beats_cc = full_row["Spearman"] > cc_row["Spearman"]
    full_beats_uw = full_row["Spearman"] > uw_row["Spearman"]
    full_beats_time = full_row["Spearman"] > time_row["Spearman"]

    lines = [
        "# Future Citation Validation Summary",
        "",
        f"- Validation type: `{target}-paper future citation validation`",
        f"- Cutoff year: `{cutoff_year}`",
        f"- Future citation window: `{future_start}-{future_end}`",
        f"- Number of papers with future citation labels = `{total_labels}`",
        f"- Number of target papers evaluated = `{len(score_df)}`",
        f"- Number of target papers with nonzero future citations = `{nonzero_future_count}`",
        f"- Number of historical edges before cutoff = `{hist_edge_count}`",
        f"- Number of LLM-scored historical edges before cutoff = `{hist_llm_count}`",
        f"- Relation penalty parameter `eta_a = {ETA_A}` and time decay parameter `b = {TIME_BIAS}`",
        "",
        "## Main findings",
        "",
        f"- Highest Spearman: `{best_spearman['Method']}` ({best_spearman['Spearman']:.4f})",
        f"- Highest NDCG@10: `{best_ndcg['Method']}` ({best_ndcg['NDCG@10']:.4f})",
        f"- Full model vs Citation Count: `{'better' if full_beats_cc else 'not better'}` in Spearman ({full_row['Spearman']:.4f} vs {cc_row['Spearman']:.4f})",
        f"- Full model vs Unweighted PageRank: `{'better' if full_beats_uw else 'not better'}` in Spearman ({full_row['Spearman']:.4f} vs {uw_row['Spearman']:.4f})",
        f"- Full model vs Time-aware PageRank: `{'better' if full_beats_time else 'not better'}` in Spearman ({full_row['Spearman']:.4f} vs {time_row['Spearman']:.4f})",
        "",
        "## Interpretation",
        "",
    ]

    if best_spearman["Method"] != "Full model" or best_ndcg["Method"] != "Full model":
        lines.extend(
            [
                "The Full model is not necessarily the best on every future-citation metric.",
                "Possible reasons include the small core-paper sample, the fact that future citations are influenced by topic popularity and paper age, and the fact that future citations are only an external proxy rather than a direct measure of article-level scholarly value.",
            ]
        )
    else:
        lines.append(
            "The Full model achieves the best overall alignment with future citation impact, suggesting that semantic, temporal, and relation-aware fusion improves the forward validity of article-level value scores."
        )

    lines.extend(
        [
            "",
            "## Metric table",
            "",
            markdown_table(table_df),
            "",
            "All model scores were computed from cutoff-year historical information only, without using future-window citations, future-window LLM scores, or future-window citing papers.",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cutoff-year", type=int, default=2020)
    parser.add_argument("--future-start", type=int, default=2021)
    parser.add_argument("--future-end", type=int, default=2024)
    parser.add_argument("--target", type=str, default="core", choices=["core", "all"])
    args = parser.parse_args()

    ensure_results_dir()
    file_map = detect_files(args.cutoff_year)
    missing_optional = [name for name, path in file_map.items() if path is None]
    if missing_optional:
        print("Missing optional files or alternatives not found:")
        for name in missing_optional:
            print(f"  - {name}")

    papers_df, _, years_df, _, future_df, hist_edges_df, hist_llm_df = load_required_data(file_map, args.cutoff_year)

    papers_hist = prepare_papers(papers_df, years_df, args.cutoff_year)
    valid_nodes = set(papers_hist["paper_id"])
    hist_edges = prepare_historical_edges(hist_edges_df, valid_nodes)
    valid_edge_keys = set(hist_edges["source_id"] + "->" + hist_edges["target_id"])
    hist_llm = prepare_historical_llm(hist_llm_df, valid_edge_keys)
    year_map = dict(zip(papers_hist["paper_id"], papers_hist["publication_year"]))
    hist_edges = attach_edge_weights(hist_edges, hist_llm, year_map)

    future = future_df.copy()
    future["paper_id"] = future["Clean_ID"].apply(clean_id)
    future["future_citations_2021_2024"] = pd.to_numeric(future["Future_Citations"], errors="coerce").fillna(0.0)
    future["is_core"] = parse_bool(future["Is_Core"])

    total_labels = len(future)
    if args.target == "core":
        target_df = future[future["is_core"]].copy()
    else:
        all_gt_path = file_map.get("future_ground_truth_all_papers.csv")
        if all_gt_path is not None:
            target_df = pd.read_csv(all_gt_path)
            target_df["paper_id"] = target_df["Clean_ID"].apply(clean_id)
            target_df["future_citations_2021_2024"] = pd.to_numeric(target_df["Future_Citations"], errors="coerce").fillna(0.0)
        else:
            target_df = future.copy()

    target_df = target_df[target_df["paper_id"].isin(valid_nodes)].copy()
    target_df = target_df.merge(
        papers_hist[["paper_id", "title", "publication_year"]],
        on="paper_id",
        how="left",
    )

    print(f"Number of total papers loaded: {len(papers_df)}")
    print(f"Number of papers with future labels: {total_labels}")
    print(f"Future citation window: {args.future_start}-{args.future_end}")
    print(f"Cutoff year: {args.cutoff_year}")
    print(f"Number of historical edges before cutoff: {len(hist_edges)}")
    print(f"Number of LLM-scored historical edges before cutoff: {len(hist_llm)}")
    print(f"Number of target papers evaluated: {len(target_df)}")
    print(f"Number of target papers with nonzero future citations: {(target_df['future_citations_2021_2024'] > 0).sum()}")
    if args.cutoff_year == 2020 and len(hist_edges) < 110:
        print("Warning: historical network may be too sparse under cutoff=2020.")

    nodes = papers_hist["paper_id"].tolist()
    citation_count_map = hist_edges.groupby("target_id").size().to_dict()
    pr_unweighted = run_pagerank(nodes, hist_edges, None)
    pr_time = run_pagerank(nodes, hist_edges, "w_time")
    pr_semantic = run_pagerank(nodes, hist_edges, "w_semantic")
    pr_semantic_temporal = run_pagerank(nodes, hist_edges, "w_semantic_temporal")
    pr_full = run_pagerank(nodes, hist_edges, "w_full")

    scores = target_df[["paper_id", "title", "publication_year", "future_citations_2021_2024"]].copy()
    scores["citation_count_score"] = scores["paper_id"].map(citation_count_map).fillna(0.0)
    scores["unweighted_pagerank_score"] = scores["paper_id"].map(pr_unweighted).fillna(0.0)
    scores["time_aware_pagerank_score"] = scores["paper_id"].map(pr_time).fillna(0.0)
    scores["semantic_pagerank_score"] = scores["paper_id"].map(pr_semantic).fillna(0.0)
    scores["semantic_temporal_score"] = scores["paper_id"].map(pr_semantic_temporal).fillna(0.0)
    scores["full_model_score"] = scores["paper_id"].map(pr_full).fillna(0.0)

    scores["citation_count_rank"] = rank_desc(scores["citation_count_score"])
    scores["unweighted_pagerank_rank"] = rank_desc(scores["unweighted_pagerank_score"])
    scores["time_aware_pagerank_rank"] = rank_desc(scores["time_aware_pagerank_score"])
    scores["semantic_pagerank_rank"] = rank_desc(scores["semantic_pagerank_score"])
    scores["semantic_temporal_rank"] = rank_desc(scores["semantic_temporal_score"])
    scores["full_model_rank"] = rank_desc(scores["full_model_score"])
    scores["future_citation_rank"] = rank_desc(scores["future_citations_2021_2024"])
    scores = scores.sort_values("future_citation_rank").reset_index(drop=True)

    table_df = build_validation_table(scores)

    scores_file = RESULTS_DIR / ("future_validation_scores_core.csv" if args.target == "core" else "future_validation_scores_all.csv")
    table_csv = RESULTS_DIR / ("table_future_citation_validation_core.csv" if args.target == "core" else "table_future_citation_validation_all.csv")
    table_md = RESULTS_DIR / ("table_future_citation_validation_core.md" if args.target == "core" else "table_future_citation_validation_all.md")
    fig_comp = RESULTS_DIR / ("fig_future_validation_comparison.png" if args.target == "core" else "fig_future_validation_comparison_all.png")
    fig_scatter = RESULTS_DIR / ("fig_full_model_vs_future_citations.png" if args.target == "core" else "fig_full_model_vs_future_citations_all.png")

    scores.to_csv(scores_file, index=False, encoding="utf-8-sig")
    table_df.to_csv(table_csv, index=False, encoding="utf-8-sig")
    table_md.write_text(markdown_table(table_df), encoding="utf-8")
    plot_comparison_table(table_df, fig_comp)
    plot_scatter(scores, fig_scatter)

    write_summary(
        table_df,
        scores,
        RESULTS_DIR / "future_validation_summary.md",
        args.cutoff_year,
        args.future_start,
        args.future_end,
        args.target,
        total_labels,
        len(hist_edges),
        len(hist_llm),
        int((scores["future_citations_2021_2024"] > 0).sum()),
    )


if __name__ == "__main__":
    main()
