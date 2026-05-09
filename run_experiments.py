#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parent
RAW_DIRS = [ROOT]
for sibling in ROOT.parent.iterdir():
    if sibling.is_dir() and sibling not in RAW_DIRS:
        RAW_DIRS.append(sibling)
RESULTS_DIR = ROOT / "results"

QUERY_TEXT = "data pricing"
DAMPING = 0.85
TIME_BIAS = 5.0
DEFAULT_Q = 0.3
ETA_A = 1.0
ETA_C = 1.0
ETA_I = 1.0
LOW_CONF_THRESHOLD = 0.5
PRICE_BASELINE_DIVISOR = 2.0


SECTION_WEIGHT_MAP = {
    "methodology": 1.0,
    "method": 1.0,
    "results": 1.0,
    "result": 1.0,
    "discussion": 0.7,
    "conclusion": 0.5,
    "conclusions": 0.5,
    "introduction": 0.4,
    "background": 0.4,
    "other": 0.2,
    "unknown": 0.2,
}


def ensure_results_dir() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def find_file(filename: str) -> Optional[Path]:
    for base in RAW_DIRS:
        candidate = base / filename
        if candidate.exists():
            return candidate
    return None


def safe_read_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def clean_id(value: object) -> Optional[str]:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.split("/")[-1]


def parse_bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y"])


def extract_year_from_text(text: object) -> Optional[int]:
    if pd.isna(text):
        return None
    text = str(text)
    for token in text.replace("/", " ").replace(".", " ").replace("-", " ").split():
        if token.isdigit() and len(token) == 4:
            year = int(token)
            if 1900 <= year <= 2100:
                return year
    return None


def normalize_minmax(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)
    min_val = float(values.min())
    max_val = float(values.max())
    if max_val > min_val:
        return (values - min_val) / (max_val - min_val)
    return pd.Series(np.zeros(len(values)), index=values.index, dtype=float)


def markdown_table(df: pd.DataFrame, max_rows: Optional[int] = None) -> str:
    if max_rows is not None:
        df = df.head(max_rows)
    preview = df.copy()
    for col in preview.columns:
        if pd.api.types.is_float_dtype(preview[col]):
            preview[col] = preview[col].map(lambda x: f"{x:.6f}" if pd.notna(x) else "")
    preview = preview.fillna("")
    headers = [str(col) for col in preview.columns]
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in preview.iterrows():
        cells = [str(row[col]).replace("\n", " ").strip() for col in preview.columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def save_csv_and_md(df: pd.DataFrame, csv_name: str, md_name: Optional[str] = None, max_rows: Optional[int] = None) -> None:
    df.to_csv(RESULTS_DIR / csv_name, index=False, encoding="utf-8-sig")
    if md_name:
        (RESULTS_DIR / md_name).write_text(markdown_table(df, max_rows=max_rows), encoding="utf-8")


def rank_map_from_scores(df: pd.DataFrame, score_col: str, ascending: bool = False) -> Dict[str, int]:
    ranked = (
        df[["paper_id", score_col]]
        .sort_values(score_col, ascending=ascending, kind="mergesort")
        .reset_index(drop=True)
    )
    ranked["rank"] = np.arange(1, len(ranked) + 1)
    return dict(zip(ranked["paper_id"], ranked["rank"]))


@dataclass
class LoadedData:
    papers: pd.DataFrame
    edges: pd.DataFrame
    contexts: pd.DataFrame
    llm: pd.DataFrame
    authorships: pd.DataFrame
    enhanced_edges: pd.DataFrame
    file_status: pd.DataFrame
    graphml_path: Optional[Path]


def load_data() -> LoadedData:
    candidate_files = [
        "all_connected_papers.csv",
        "all_network_edges.csv",
        "contexts.csv",
        "contexts_final.csv",
        "llm_results.csv",
        "weighted_edge_weights.csv",
        "weighted_pagerank_ranking.csv",
        "unweighted_pagerank_ranking.csv",
        "weighted_pagerank_ranking_with_penalty.csv",
        "ranking_comparison_detailed.csv",
        "weighted_edges_comparison.csv",
        "weighted_wtp_analysis.csv",
        "weighted_wtp_analysis_with_penalty.csv",
        "penalty_pricing_comparison.csv",
        "sensitivity_analysis.csv",
        "HIN_network.graphml",
        "authorships_network.csv",
        "enhanced_paper_edges.csv",
    ]
    file_status_rows = []
    for name in candidate_files:
        path = find_file(name)
        file_status_rows.append(
            {
                "file_name": name,
                "exists": path is not None,
                "resolved_path": str(path) if path else "",
            }
        )
    file_status = pd.DataFrame(file_status_rows)

    papers_path = find_file("all_connected_papers.csv")
    edges_path = find_file("all_network_edges.csv")
    contexts_path = find_file("contexts_final.csv") or find_file("contexts.csv")
    llm_path = find_file("llm_results.csv")
    authorships_path = find_file("authorships_network.csv")
    enhanced_path = find_file("enhanced_paper_edges.csv")
    graphml_path = find_file("HIN_network.graphml")

    missing = [
        name
        for name, path in [
            ("all_connected_papers.csv", papers_path),
            ("all_network_edges.csv", edges_path),
            ("llm_results.csv", llm_path),
        ]
        if path is None
    ]
    if missing:
        raise FileNotFoundError(f"Missing required files: {missing}")

    papers = safe_read_csv(papers_path)
    edges = safe_read_csv(edges_path)
    contexts = safe_read_csv(contexts_path) if contexts_path else pd.DataFrame()
    llm = safe_read_csv(llm_path)
    authorships = safe_read_csv(authorships_path) if authorships_path else pd.DataFrame()
    enhanced_edges = safe_read_csv(enhanced_path) if enhanced_path else pd.DataFrame()

    return LoadedData(
        papers=papers,
        edges=edges,
        contexts=contexts,
        llm=llm,
        authorships=authorships,
        enhanced_edges=enhanced_edges,
        file_status=file_status,
        graphml_path=graphml_path,
    )


def prepare_papers(df: pd.DataFrame) -> pd.DataFrame:
    papers = df.copy()
    id_col = next((c for c in papers.columns if c.lower() in ("openalex_id", "paper_id", "id")), papers.columns[0])
    papers = papers.rename(columns={id_col: "paper_raw_id"})
    papers["paper_id"] = papers["paper_raw_id"].apply(clean_id)
    title_col = next((c for c in papers.columns if c.lower() == "title"), None)
    papers["title"] = papers[title_col].fillna("").astype(str) if title_col else papers["paper_id"]
    doi_col = next((c for c in papers.columns if c.lower() == "doi"), None)
    papers["doi"] = papers[doi_col] if doi_col else ""
    year_col = next((c for c in papers.columns if "year" in c.lower()), None)
    if year_col:
        years = pd.to_numeric(papers[year_col], errors="coerce")
    else:
        years = pd.Series([np.nan] * len(papers), index=papers.index)
    papers["year"] = years.fillna(papers["doi"].apply(extract_year_from_text)).fillna(2020).astype(int)
    gc_col = next((c for c in papers.columns if c.lower() in ("global_citations", "citations", "citation_count")), None)
    papers["global_citations"] = pd.to_numeric(papers[gc_col], errors="coerce").fillna(0.0) if gc_col else 0.0
    core_col = next((c for c in papers.columns if c.lower() in ("is_core", "core", "iscore")), None)
    papers["is_core"] = parse_bool_series(papers[core_col]) if core_col else False
    papers["base_value"] = normalize_minmax(papers["global_citations"])
    if papers["base_value"].sum() == 0:
        papers["base_value"] = 1.0
    return papers


def prepare_edges(df: pd.DataFrame) -> pd.DataFrame:
    edges = df.copy()
    source_col = next((c for c in edges.columns if c.lower() == "source"), edges.columns[0])
    target_col = next((c for c in edges.columns if c.lower() == "target"), edges.columns[1])
    edges["source_raw_id"] = edges[source_col]
    edges["target_raw_id"] = edges[target_col]
    edges["source_id"] = edges["source_raw_id"].apply(clean_id)
    edges["target_id"] = edges["target_raw_id"].apply(clean_id)
    edges = edges.dropna(subset=["source_id", "target_id"]).copy()
    edges["edge_key"] = edges["source_id"] + "->" + edges["target_id"]
    return edges


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


def compute_semantic_weight(llm_df: pd.DataFrame, edge_df: pd.DataFrame) -> pd.DataFrame:
    llm = llm_df.copy()
    source_col = next((c for c in llm.columns if c.lower() == "source_id"), None)
    target_col = next((c for c in llm.columns if c.lower() == "target_id"), None)
    if source_col is None or target_col is None:
        raise ValueError("llm_results.csv is missing Source_ID or Target_ID")
    llm["source_id"] = llm[source_col].apply(clean_id)
    llm["target_id"] = llm[target_col].apply(clean_id)
    llm["edge_key"] = llm["source_id"] + "->" + llm["target_id"]

    llm["section"] = llm.get("LLM_Section", "").fillna("").astype(str)
    llm["sentiment"] = pd.to_numeric(llm.get("LLM_Sentiment", 0.0), errors="coerce").fillna(0.0)
    llm["relevance"] = pd.to_numeric(llm.get("LLM_Relevance", 0.0), errors="coerce").fillna(0.0)
    llm["confidence"] = pd.to_numeric(llm.get("Confidence", np.nan), errors="coerce")
    llm["w_sec"] = llm["section"].apply(map_section_weight)
    llm["w_sent"] = np.where(llm["sentiment"] >= 0, (llm["sentiment"] + 1.0) / 2.0, 0.01)
    llm["w_rel"] = llm["relevance"] ** 2
    llm["q_ij"] = llm["w_sec"] * llm["w_sent"] * llm["w_rel"]
    if "Weight_Combined" in llm.columns:
        llm["q_existing"] = pd.to_numeric(llm["Weight_Combined"], errors="coerce")
    else:
        llm["q_existing"] = np.nan

    dedup = (
        llm.sort_values(["edge_key", "q_ij"], ascending=[True, False])
        .drop_duplicates(subset=["edge_key"], keep="first")
        .copy()
    )

    merged = edge_df.merge(
        dedup[
            [
                "edge_key",
                "section",
                "sentiment",
                "relevance",
                "confidence",
                "w_sec",
                "w_sent",
                "w_rel",
                "q_ij",
            ]
        ],
        on="edge_key",
        how="left",
    )
    merged["has_llm_score"] = merged["q_ij"].notna()
    merged["q_ij"] = merged["q_ij"].fillna(DEFAULT_Q)
    return merged, dedup


def compute_relation_penalty(
    edge_df: pd.DataFrame,
    authorships_df: pd.DataFrame,
    enhanced_df: pd.DataFrame,
) -> pd.DataFrame:
    edges = edge_df.copy()

    if not enhanced_df.empty:
        enhanced = enhanced_df.copy()
        source_clean_col = next((c for c in enhanced.columns if c.lower() == "source_clean"), None)
        target_clean_col = next((c for c in enhanced.columns if c.lower() == "target_clean"), None)
        if source_clean_col and target_clean_col:
            enhanced["source_id"] = enhanced[source_clean_col].apply(clean_id)
            enhanced["target_id"] = enhanced[target_clean_col].apply(clean_id)
        else:
            enhanced["source_id"] = enhanced[next(c for c in enhanced.columns if c.lower() == "source")].apply(clean_id)
            enhanced["target_id"] = enhanced[next(c for c in enhanced.columns if c.lower() == "target")].apply(clean_id)
        shared_col = next((c for c in enhanced.columns if "shared_authors" in c.lower()), None)
        self_col = next((c for c in enhanced.columns if "author_self_cite" in c.lower()), None)
        enhanced["shared_authors_count"] = pd.to_numeric(enhanced.get(shared_col, 0), errors="coerce").fillna(0).astype(int)
        enhanced["is_author_self_cite"] = parse_bool_series(enhanced.get(self_col, False))
        penalty_map = enhanced[["source_id", "target_id", "shared_authors_count", "is_author_self_cite"]].drop_duplicates()
    else:
        if authorships_df.empty:
            penalty_map = pd.DataFrame(columns=["source_id", "target_id", "shared_authors_count", "is_author_self_cite"])
        else:
            authorships = authorships_df.copy()
            paper_col = next((c for c in authorships.columns if c.lower() in ("paper_id", "openalex_id")), authorships.columns[0])
            author_col = next((c for c in authorships.columns if c.lower() in ("author_id", "authorid")), authorships.columns[1])
            authorships["paper_id"] = authorships[paper_col].apply(clean_id)
            authorships["author_id"] = authorships[author_col].astype(str)
            author_sets = authorships.groupby("paper_id")["author_id"].apply(set).to_dict()
            rows = []
            for _, row in edges.iterrows():
                source_authors = author_sets.get(row["source_id"], set())
                target_authors = author_sets.get(row["target_id"], set())
                shared = len(source_authors & target_authors)
                rows.append(
                    {
                        "source_id": row["source_id"],
                        "target_id": row["target_id"],
                        "shared_authors_count": shared,
                        "is_author_self_cite": shared > 0,
                    }
                )
            penalty_map = pd.DataFrame(rows)

    penalty_map["edge_key"] = penalty_map["source_id"] + "->" + penalty_map["target_id"]
    edges = edges.merge(
        penalty_map[["edge_key", "shared_authors_count", "is_author_self_cite"]].drop_duplicates("edge_key"),
        on="edge_key",
        how="left",
    )
    edges["shared_authors_count"] = pd.to_numeric(edges["shared_authors_count"], errors="coerce").fillna(0).astype(int)
    edges["is_author_self_cite"] = parse_bool_series(edges["is_author_self_cite"].fillna(False))
    edges["rho_ij"] = 1.0 / (1.0 + ETA_A * edges["shared_authors_count"])
    return edges


def compute_extended_relation_features(edge_df: pd.DataFrame, authorships_df: pd.DataFrame) -> pd.DataFrame:
    edges = edge_df.copy()
    if authorships_df.empty:
        edges["team_collab_count"] = 0
        edges["shared_institutions_count"] = 0
        edges["rho_extended"] = edges["rho_ij"]
        return edges

    authorships = authorships_df.copy()
    paper_col = next((c for c in authorships.columns if c.lower() in ("paper_id", "openalex_id")), authorships.columns[0])
    author_col = next((c for c in authorships.columns if c.lower() in ("author_id", "authorid")), None)
    inst_col = next((c for c in authorships.columns if "institution_id" in c.lower()), None)

    authorships["paper_id"] = authorships[paper_col].apply(clean_id)
    if author_col:
        authorships["author_id"] = authorships[author_col].fillna("").astype(str).str.strip()
    else:
        authorships["author_id"] = ""
    if inst_col:
        authorships["institution_ids"] = authorships[inst_col].fillna("").astype(str)
    else:
        authorships["institution_ids"] = ""

    author_sets = authorships[authorships["author_id"] != ""].groupby("paper_id")["author_id"].apply(set).to_dict()
    institution_sets = (
        authorships.groupby("paper_id")["institution_ids"]
        .apply(
            lambda s: set(
                token.strip()
                for value in s
                for token in str(value).split("|")
                if token and token.strip()
            )
        )
        .to_dict()
    )

    # Build corpus-level coauthor graph to capture indirect team proximity.
    coauthor_neighbors: Dict[str, set] = {}
    for _, group in authorships[authorships["author_id"] != ""].groupby("paper_id"):
        authors = sorted(set(group["author_id"]))
        for i, src in enumerate(authors):
            coauthor_neighbors.setdefault(src, set())
            for dst in authors[i + 1:]:
                coauthor_neighbors.setdefault(dst, set())
                coauthor_neighbors[src].add(dst)
                coauthor_neighbors[dst].add(src)

    team_counts = []
    inst_counts = []
    for _, row in edges.iterrows():
        src_authors = author_sets.get(row["source_id"], set())
        tgt_authors = author_sets.get(row["target_id"], set())
        src_inst = institution_sets.get(row["source_id"], set())
        tgt_inst = institution_sets.get(row["target_id"], set())

        shared_authors = src_authors & tgt_authors
        team_count = 0
        for a in src_authors:
            for b in tgt_authors:
                if a == b:
                    continue
                if b in coauthor_neighbors.get(a, set()):
                    team_count += 1
        team_count = max(0, team_count - len(shared_authors))
        inst_count = len(src_inst & tgt_inst)
        team_counts.append(team_count)
        inst_counts.append(inst_count)

    edges["team_collab_count"] = team_counts
    edges["shared_institutions_count"] = inst_counts
    edges["rho_extended"] = 1.0 / (
        1.0
        + ETA_A * edges["shared_authors_count"]
        + ETA_C * edges["team_collab_count"]
        + ETA_I * edges["shared_institutions_count"]
    )
    return edges


def compute_temporal_decay(edge_df: pd.DataFrame, paper_year_map: Dict[str, int]) -> pd.DataFrame:
    edges = edge_df.copy()
    source_year = edges["source_id"].map(paper_year_map).fillna(2020).astype(int)
    target_year = edges["target_id"].map(paper_year_map).fillna(2020).astype(int)
    edges["delta_t"] = (source_year - target_year).clip(lower=0)
    edges["tau_ij"] = TIME_BIAS / (TIME_BIAS + edges["delta_t"].astype(float))
    return edges


def build_graph(papers: pd.DataFrame, edges: pd.DataFrame, weight_col: Optional[str] = None) -> nx.DiGraph:
    graph = nx.DiGraph()
    for _, row in papers.iterrows():
        graph.add_node(row["paper_id"], title=row["title"])
    for _, row in edges.iterrows():
        weight = float(row[weight_col]) if weight_col else 1.0
        graph.add_edge(row["source_id"], row["target_id"], weight=weight)
    return graph


def run_weighted_pagerank(
    papers: pd.DataFrame,
    edges: pd.DataFrame,
    raw_weight_col: Optional[str],
    score_name: str,
) -> pd.DataFrame:
    work = edges.copy()
    if raw_weight_col is None:
        work["normalized_weight"] = 1.0
    else:
        work["raw_weight"] = pd.to_numeric(work[raw_weight_col], errors="coerce").fillna(0.0)
        out_sum = work.groupby("source_id")["raw_weight"].transform("sum")
        work["normalized_weight"] = np.where(out_sum > 0, work["raw_weight"] / out_sum, 0.0)

    base_map = dict(zip(papers["paper_id"], papers["base_value"].astype(float)))
    scores = {pid: float(base_map.get(pid, 0.0)) for pid in papers["paper_id"]}
    incoming = work.groupby("target_id")[["source_id", "normalized_weight"]].apply(
        lambda g: list(zip(g["source_id"], g["normalized_weight"]))
    ).to_dict()

    for _ in range(200):
        max_diff = 0.0
        new_scores = {}
        for pid in papers["paper_id"]:
            total = sum(scores.get(src, 0.0) * wt for src, wt in incoming.get(pid, []))
            value = (1.0 - DAMPING) * base_map.get(pid, 0.0) + DAMPING * total
            new_scores[pid] = value
            max_diff = max(max_diff, abs(value - scores[pid]))
        scores = new_scores
        if max_diff < 1e-10:
            break

    result = papers[["paper_id", "title", "global_citations", "is_core"]].copy()
    result[score_name] = result["paper_id"].map(scores).fillna(0.0)
    result[f"{score_name}_rank"] = (
        result[score_name].rank(method="min", ascending=False).astype(int)
    )
    return result.sort_values(score_name, ascending=False).reset_index(drop=True)


def compute_citation_count_ranking(papers: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    result = papers[["paper_id", "title", "global_citations", "is_core"]].copy()
    indegree = edges.groupby("target_id").size().to_dict()
    outdegree = edges.groupby("source_id").size().to_dict()
    result["in_degree"] = result["paper_id"].map(indegree).fillna(0).astype(int)
    result["out_degree"] = result["paper_id"].map(outdegree).fillna(0).astype(int)
    result["citation_count"] = result["global_citations"]
    result["citation_count_rank"] = result["citation_count"].rank(method="min", ascending=False).astype(int)
    result["in_degree_rank"] = result["in_degree"].rank(method="min", ascending=False).astype(int)
    return result.sort_values(["citation_count", "in_degree"], ascending=False).reset_index(drop=True)


def compute_rank_metrics(
    left_df: pd.DataFrame,
    left_col: str,
    right_df: pd.DataFrame,
    right_col: str,
    label: str,
) -> Dict[str, float]:
    merged = (
        left_df[["paper_id", left_col]]
        .rename(columns={left_col: "left_score"})
        .merge(
            right_df[["paper_id", right_col]].rename(columns={right_col: "right_score"}),
            on="paper_id",
            how="inner",
        )
    )
    rank_left = merged["left_score"].rank(method="average", ascending=False)
    rank_right = merged["right_score"].rank(method="average", ascending=False)
    spearman = spearmanr(merged["left_score"], merged["right_score"]).statistic

    top5_left = set(merged.nlargest(5, "left_score")["paper_id"])
    top5_right = set(merged.nlargest(5, "right_score")["paper_id"])
    top10_left = set(merged.nlargest(10, "left_score")["paper_id"])
    top10_right = set(merged.nlargest(10, "right_score")["paper_id"])

    rank_delta = (rank_left - rank_right).abs()
    return {
        "comparison": label,
        "spearman": float(spearman) if pd.notna(spearman) else float("nan"),
        "top5_overlap": len(top5_left & top5_right),
        "top10_overlap": len(top10_left & top10_right),
        "avg_rank_change": float(rank_delta.mean()),
        "max_rank_change": float(rank_delta.max()),
    }


def compute_text_similarity(texts: pd.Series, query: str) -> pd.Series:
    corpus = texts.fillna("").astype(str)
    vectorizer = TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, matrix)[0]
    return pd.Series(scores, index=texts.index)


def pricing_function(value_norm: pd.Series, similarity: pd.Series, alpha: float, beta: float) -> Tuple[pd.Series, pd.Series]:
    demand_component = 0.2 * similarity + 0.8 * value_norm * similarity
    wtp = alpha * value_norm + beta * demand_component
    price = (wtp / PRICE_BASELINE_DIVISOR) * (0.3 + 0.7 * value_norm)
    return wtp, price


def run_pricing(
    full_scores: pd.DataFrame,
    scenario_name: str = "Base Case",
    alpha: float = 1.0,
    beta: float = 10.0,
) -> pd.DataFrame:
    df = full_scores[["paper_id", "title", "full_model_score"]].copy()
    df["value_norm"] = normalize_minmax(df["full_model_score"])
    df["query_similarity"] = compute_text_similarity(df["title"], QUERY_TEXT)
    df["WTP"], df["price"] = pricing_function(df["value_norm"], df["query_similarity"], alpha=alpha, beta=beta)
    df["price_rank"] = df["price"].rank(method="min", ascending=False).astype(int)
    df["scenario"] = scenario_name
    return df.sort_values("price", ascending=False).reset_index(drop=True)


def save_figure(fig: plt.Figure, filename: str) -> None:
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / filename, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_degree_distribution(edges: pd.DataFrame, papers: pd.DataFrame) -> None:
    indegree = papers["paper_id"].map(edges.groupby("target_id").size()).fillna(0).astype(int)
    outdegree = papers["paper_id"].map(edges.groupby("source_id").size()).fillna(0).astype(int)
    fig, ax = plt.subplots(figsize=(8, 5))
    bins = np.arange(0, max(indegree.max(), outdegree.max()) + 2) - 0.5
    ax.hist(indegree, bins=bins, alpha=0.7, label="In-degree")
    ax.hist(outdegree, bins=bins, alpha=0.5, label="Out-degree")
    ax.set_xlabel("Degree")
    ax.set_ylabel("Number of papers")
    ax.set_title("Degree distribution of the citation network")
    ax.legend()
    save_figure(fig, "fig_degree_distribution.png")


def plot_rank_change(rank_changes: pd.DataFrame, filename: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    plot_df = rank_changes.sort_values("baseline_rank")
    ax.bar(np.arange(len(plot_df)), plot_df["rank_change"], color=np.where(plot_df["rank_change"] > 0, "#c0392b", "#2980b9"))
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Papers ordered by baseline rank")
    ax.set_ylabel("Rank change (positive means lower rank)")
    ax.set_title(title)
    save_figure(fig, filename)


def plot_hist(series: pd.Series, filename: str, title: str, xlabel: str, bins: int = 20) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(pd.to_numeric(series, errors="coerce").dropna(), bins=bins, color="#2f7ed8", alpha=0.8)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frequency")
    save_figure(fig, filename)


def plot_bar(series: pd.Series, filename: str, title: str, xlabel: str, ylabel: str = "Count") -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    counts = series.value_counts(dropna=False)
    counts.plot(kind="bar", ax=ax, color="#27ae60")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35)
    save_figure(fig, filename)


def plot_value_similarity_price(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(df["value_norm"], df["query_similarity"], c=df["price"], cmap="viridis", s=60, alpha=0.85)
    ax.set_xlabel("Normalized article value")
    ax.set_ylabel("Query similarity")
    ax.set_title("Value, similarity, and personalized price")
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Price")
    save_figure(fig, "fig_value_similarity_price_scatter.png")


def run_experiments() -> None:
    ensure_results_dir()
    loaded = load_data()
    loaded.file_status.to_csv(RESULTS_DIR / "input_file_status.csv", index=False, encoding="utf-8-sig")

    papers = prepare_papers(loaded.papers)
    edges = prepare_edges(loaded.edges)
    edges, llm_unique = compute_semantic_weight(loaded.llm, edges)
    edges = compute_relation_penalty(edges, loaded.authorships, loaded.enhanced_edges)
    edges = compute_extended_relation_features(edges, loaded.authorships)
    year_map = dict(zip(papers["paper_id"], papers["year"]))
    edges = compute_temporal_decay(edges, year_map)

    edges["w_structure"] = 1.0
    edges["w_semantic"] = edges["q_ij"]
    edges["w_semantic_temporal"] = edges["q_ij"] * edges["tau_ij"]
    edges["w_semantic_relation"] = edges["q_ij"] * edges["rho_ij"]
    edges["w_full"] = edges["q_ij"] * edges["tau_ij"] * edges["rho_ij"]
    edges["w_full_extended"] = edges["q_ij"] * edges["tau_ij"] * edges["rho_extended"]

    citation_rank = compute_citation_count_ranking(papers, edges)
    unweighted_rank = run_weighted_pagerank(papers, edges, None, "unweighted_pagerank")
    semantic_rank = run_weighted_pagerank(papers, edges, "w_semantic", "semantic_pagerank")
    semantic_temporal_rank = run_weighted_pagerank(papers, edges, "w_semantic_temporal", "semantic_temporal_pagerank")
    semantic_relation_rank = run_weighted_pagerank(papers, edges, "w_semantic_relation", "semantic_relation_pagerank")
    full_rank = run_weighted_pagerank(papers, edges, "w_full", "full_model_score")
    full_extended_rank = run_weighted_pagerank(papers, edges, "w_full_extended", "full_extended_score")

    # Experiment 1
    graph = build_graph(papers, edges)
    weak_components = list(nx.weakly_connected_components(graph))
    largest_component_size = max((len(c) for c in weak_components), default=0)
    indegree = dict(graph.in_degree())
    outdegree = dict(graph.out_degree())
    isolate_count = sum(1 for node in graph.nodes if indegree.get(node, 0) == 0 and outdegree.get(node, 0) == 0)
    hin_total_edges = ""
    hin_citation_edges = ""
    if loaded.graphml_path and loaded.graphml_path.exists():
        try:
            G_hin = nx.read_graphml(loaded.graphml_path)
            hin_total_edges = G_hin.number_of_edges()
            hin_citation_edges = sum(
                1
                for _, _, d in G_hin.edges(data=True)
                if (d.get("type") or d.get("edge_type") or d.get("relation") or "") == "cites"
            )
        except Exception:
            hin_total_edges = ""
            hin_citation_edges = ""

    dataset_stats = pd.DataFrame(
        [
            ["paper_nodes", len(papers)],
            ["citation_edges", len(edges)],
            ["heterogeneous_total_edges", hin_total_edges],
            ["heterogeneous_citation_edges", hin_citation_edges],
            ["largest_weak_component_nodes", largest_component_size],
            ["average_in_degree", round(np.mean(list(indegree.values())), 6)],
            ["average_out_degree", round(np.mean(list(outdegree.values())), 6)],
            ["max_in_degree", max(indegree.values()) if indegree else 0],
            ["max_out_degree", max(outdegree.values()) if outdegree else 0],
            ["network_density", round(nx.density(graph), 8)],
            ["has_isolates", "Yes" if isolate_count > 0 else "No"],
            ["isolate_count", isolate_count],
            ["core_paper_count", int(papers["is_core"].sum())],
            ["llm_scored_edges", int(edges["has_llm_score"].sum())],
            ["unscored_edges", int((~edges["has_llm_score"]).sum())],
            ["self_citation_edges", int(edges["is_author_self_cite"].sum())],
            ["self_citation_ratio", round(float(edges["is_author_self_cite"].mean()), 6)],
            ["average_shared_authors", round(float(edges["shared_authors_count"].mean()), 6)],
        ],
        columns=["metric", "value"],
    )
    save_csv_and_md(dataset_stats, "table_dataset_statistics.csv", "table_dataset_statistics.md")
    plot_degree_distribution(edges, papers)

    # Experiment 2
    ranking_all = papers[["paper_id", "title"]].copy()
    ranking_all = ranking_all.merge(citation_rank[["paper_id", "citation_count", "in_degree", "citation_count_rank"]], on="paper_id", how="left")
    ranking_all = ranking_all.merge(unweighted_rank[["paper_id", "unweighted_pagerank", "unweighted_pagerank_rank"]], on="paper_id", how="left")
    ranking_all = ranking_all.merge(semantic_rank[["paper_id", "semantic_pagerank", "semantic_pagerank_rank"]], on="paper_id", how="left")
    ranking_all = ranking_all.merge(semantic_temporal_rank[["paper_id", "semantic_temporal_pagerank", "semantic_temporal_pagerank_rank"]], on="paper_id", how="left")
    ranking_all = ranking_all.merge(full_rank[["paper_id", "full_model_score", "full_model_score_rank"]], on="paper_id", how="left")
    ranking_top30 = ranking_all.sort_values("full_model_score_rank").head(30).copy()
    save_csv_and_md(ranking_top30, "table_ranking_comparison.csv", "table_ranking_comparison.md", max_rows=30)

    # Experiment 3
    rank_corr_rows = [
        compute_rank_metrics(full_rank, "full_model_score", unweighted_rank, "unweighted_pagerank", "Full vs Unweighted PageRank"),
        compute_rank_metrics(full_rank, "full_model_score", citation_rank.rename(columns={"citation_count": "citation_count_metric"}), "citation_count_metric", "Full vs Citation Count"),
        compute_rank_metrics(semantic_temporal_rank, "semantic_temporal_pagerank", semantic_rank, "semantic_pagerank", "Semantic-Temporal vs Semantic"),
        compute_rank_metrics(full_rank, "full_model_score", semantic_temporal_rank, "semantic_temporal_pagerank", "Full vs Semantic-Temporal"),
    ]
    rank_corr_df = pd.DataFrame(rank_corr_rows)
    save_csv_and_md(rank_corr_df, "table_rank_correlation.csv")

    topk_overlap_df = rank_corr_df[["comparison", "top5_overlap", "top10_overlap"]].copy()
    save_csv_and_md(topk_overlap_df, "table_topk_overlap.csv")

    baseline_compare = full_rank[["paper_id", "title", "full_model_score", "full_model_score_rank"]].merge(
        unweighted_rank[["paper_id", "unweighted_pagerank", "unweighted_pagerank_rank"]],
        on="paper_id",
        how="left",
    )
    baseline_compare["rank_change"] = baseline_compare["full_model_score_rank"] - baseline_compare["unweighted_pagerank_rank"]
    baseline_compare["abs_rank_change"] = baseline_compare["rank_change"].abs()
    baseline_compare["baseline_rank"] = baseline_compare["unweighted_pagerank_rank"]
    rank_change_table = baseline_compare.sort_values("abs_rank_change", ascending=False)
    save_csv_and_md(rank_change_table, "table_rank_changes.csv")
    plot_rank_change(rank_change_table, "fig_rank_change_full_vs_baseline.png", "Full model rank change relative to unweighted PageRank")

    # Experiment 4
    ablation_frames = []
    for label, df_model, score_col in [
        ("structure_only", unweighted_rank, "unweighted_pagerank"),
        ("semantic_only", semantic_rank, "semantic_pagerank"),
        ("semantic_temporal", semantic_temporal_rank, "semantic_temporal_pagerank"),
        ("semantic_relation", semantic_relation_rank, "semantic_relation_pagerank"),
        ("full_model", full_rank, "full_model_score"),
    ]:
        temp = df_model[["paper_id", "title", score_col]].copy()
        temp["model"] = label
        temp["rank"] = temp[score_col].rank(method="min", ascending=False).astype(int)
        temp = temp.rename(columns={score_col: "score"})
        ablation_frames.append(temp)
    ablation_rankings = pd.concat(ablation_frames, ignore_index=True)
    save_csv_and_md(ablation_rankings, "table_ablation_rankings.csv")

    ablation_summary_rows = []
    for label, df_model, score_col in [
        ("structure_only", unweighted_rank, "unweighted_pagerank"),
        ("semantic_only", semantic_rank, "semantic_pagerank"),
        ("semantic_temporal", semantic_temporal_rank, "semantic_temporal_pagerank"),
        ("semantic_relation", semantic_relation_rank, "semantic_relation_pagerank"),
        ("full_model", full_rank, "full_model_score"),
    ]:
        metrics = compute_rank_metrics(full_rank, "full_model_score", df_model, score_col, label)
        ablation_summary_rows.append(metrics)
    ablation_summary = pd.DataFrame(ablation_summary_rows)
    save_csv_and_md(ablation_summary, "table_ablation_summary.csv")

    # Experiment 5
    self_cite_stats = pd.DataFrame(
        [
            ["self_citation_edges", int(edges["is_author_self_cite"].sum())],
            ["self_citation_ratio", round(float(edges["is_author_self_cite"].mean()), 6)],
            ["penalized_edges", int((edges["rho_ij"] < 1.0).sum())],
            ["penalized_source_papers", int(edges.loc[edges["rho_ij"] < 1.0, "source_id"].nunique())],
            ["mean_shared_authors_all_edges", round(float(edges["shared_authors_count"].mean()), 6)],
            ["mean_shared_authors_penalized_edges", round(float(edges.loc[edges["rho_ij"] < 1.0, "shared_authors_count"].mean()), 6) if (edges["rho_ij"] < 1.0).any() else 0.0],
        ],
        columns=["metric", "value"],
    )
    save_csv_and_md(self_cite_stats, "table_self_citation_statistics.csv")

    penalty_compare = semantic_temporal_rank[["paper_id", "title", "semantic_temporal_pagerank", "semantic_temporal_pagerank_rank"]].merge(
        full_rank[["paper_id", "full_model_score", "full_model_score_rank"]],
        on="paper_id",
        how="left",
    )
    penalty_compare = penalty_compare.merge(
        edges.groupby("source_id").agg(
            self_citation_edges=("is_author_self_cite", "sum"),
            avg_shared_authors=("shared_authors_count", "mean"),
        ).reset_index().rename(columns={"source_id": "paper_id"}),
        on="paper_id",
        how="left",
    )
    penalty_compare["self_citation_edges"] = penalty_compare["self_citation_edges"].fillna(0).astype(int)
    penalty_compare["avg_shared_authors"] = penalty_compare["avg_shared_authors"].fillna(0.0)
    penalty_compare["rank_change_due_to_penalty"] = penalty_compare["full_model_score_rank"] - penalty_compare["semantic_temporal_pagerank_rank"]
    penalty_compare["score_change_due_to_penalty"] = penalty_compare["full_model_score"] - penalty_compare["semantic_temporal_pagerank"]
    save_csv_and_md(
        penalty_compare.sort_values("rank_change_due_to_penalty", ascending=False),
        "table_penalty_rank_changes.csv",
    )
    save_csv_and_md(
        penalty_compare.sort_values("score_change_due_to_penalty"),
        "table_penalty_score_changes.csv",
    )
    plot_rank_change(
        penalty_compare.rename(columns={"semantic_temporal_pagerank_rank": "baseline_rank", "rank_change_due_to_penalty": "rank_change"}),
        "fig_penalty_rank_change.png",
        "Rank change after applying relation penalty",
    )
    plot_hist(edges["shared_authors_count"], "fig_common_author_distribution.png", "Distribution of shared author counts", "Shared author count", bins=max(int(edges["shared_authors_count"].max()) + 1, 5))

    # Experiment 6
    llm_stats = pd.DataFrame(
        [
            ["scored_edges", len(llm_unique)],
            ["mean_sentiment", round(float(llm_unique["sentiment"].mean()), 6)],
            ["mean_relevance", round(float(llm_unique["relevance"].mean()), 6)],
            ["mean_confidence", round(float(llm_unique["confidence"].mean()), 6)],
            ["low_confidence_ratio", round(float((llm_unique["confidence"] < LOW_CONF_THRESHOLD).mean()), 6)],
            ["mean_q", round(float(llm_unique["q_ij"].mean()), 6)],
            ["median_q", round(float(llm_unique["q_ij"].median()), 6)],
            ["relevance_full_weight_corr", round(float(pd.Series(llm_unique["relevance"]).corr(pd.Series(llm_unique["q_ij"]))), 6)],
        ],
        columns=["metric", "value"],
    )
    save_csv_and_md(llm_stats, "table_llm_semantic_statistics.csv")

    section_analysis = llm_unique.groupby("section", dropna=False).agg(
        edge_count=("edge_key", "count"),
        mean_q=("q_ij", "mean"),
        mean_sentiment=("sentiment", "mean"),
        mean_relevance=("relevance", "mean"),
        mean_confidence=("confidence", "mean"),
    ).reset_index().sort_values("edge_count", ascending=False)
    save_csv_and_md(section_analysis, "table_section_weight_analysis.csv")

    plot_bar(llm_unique["section"].replace("", "Unknown"), "fig_section_distribution.png", "LLM section distribution", "Section")
    plot_hist(llm_unique["sentiment"], "fig_sentiment_distribution.png", "LLM sentiment distribution", "Sentiment score")
    plot_hist(llm_unique["relevance"], "fig_relevance_distribution.png", "LLM relevance distribution", "Relevance score")
    plot_hist(llm_unique["confidence"], "fig_confidence_distribution.png", "LLM confidence distribution", "Confidence")
    plot_hist(llm_unique["q_ij"], "fig_semantic_quality_distribution.png", "Semantic quality distribution", "q_ij")

    # Experiment 7
    confidence_rows = []
    for eps in [0.3, 0.5, 0.7]:
        conf_edges = edges.copy()
        conf_factor = np.where(
            conf_edges["has_llm_score"],
            eps + (1.0 - eps) * conf_edges["confidence"].fillna(0.0),
            1.0,
        )
        conf_edges["w_conf_variant"] = conf_edges["w_full"] * conf_factor
        conf_rank = run_weighted_pagerank(papers, conf_edges, "w_conf_variant", "confidence_variant_score")
        metrics = compute_rank_metrics(full_rank, "full_model_score", conf_rank, "confidence_variant_score", f"epsilon={eps}")
        metrics["epsilon"] = eps
        confidence_rows.append(metrics)
    confidence_df = pd.DataFrame(confidence_rows)[["epsilon", "spearman", "top5_overlap", "top10_overlap", "avg_rank_change", "max_rank_change"]]
    save_csv_and_md(confidence_df, "table_confidence_variant.csv")

    # Extended robustness: add team and institution relation penalties without changing the main model.
    extended_metrics = compute_rank_metrics(full_rank, "full_model_score", full_extended_rank, "full_extended_score", "Extended relation robustness")
    extended_stats = pd.DataFrame(
        [
            {
                "comparison": extended_metrics["comparison"],
                "spearman": extended_metrics["spearman"],
                "top5_overlap": extended_metrics["top5_overlap"],
                "top10_overlap": extended_metrics["top10_overlap"],
                "avg_rank_change": extended_metrics["avg_rank_change"],
                "max_rank_change": extended_metrics["max_rank_change"],
                "penalized_edges_main": int((edges["rho_ij"] < 1.0).sum()),
                "penalized_edges_extended": int((edges["rho_extended"] < 1.0).sum()),
                "edges_with_team_collab": int((edges["team_collab_count"] > 0).sum()),
                "edges_with_shared_institutions": int((edges["shared_institutions_count"] > 0).sum()),
            }
        ]
    )
    save_csv_and_md(extended_stats, "table_extended_relation_robustness.csv")

    # Paper-ready combined Table 3
    table3_rows = []
    for _, row in ablation_summary.iterrows():
        table3_rows.append(
            {
                "section": "Ablation",
                "model_or_variant": row["comparison"],
                "spearman": row["spearman"],
                "top5_overlap": row["top5_overlap"],
                "top10_overlap": row["top10_overlap"],
                "avg_rank_change": row["avg_rank_change"],
                "max_rank_change": row["max_rank_change"],
                "notes": "",
            }
        )
    ext_row = extended_stats.iloc[0]
    table3_rows.append(
        {
            "section": "Extended robustness",
            "model_or_variant": "team_and_institution_relations",
            "spearman": ext_row["spearman"],
            "top5_overlap": ext_row["top5_overlap"],
            "top10_overlap": ext_row["top10_overlap"],
            "avg_rank_change": ext_row["avg_rank_change"],
            "max_rank_change": ext_row["max_rank_change"],
            "notes": f"main penalized edges={int(ext_row['penalized_edges_main'])}; extended penalized edges={int(ext_row['penalized_edges_extended'])}",
        }
    )
    for _, row in confidence_df.iterrows():
        table3_rows.append(
            {
                "section": "Confidence robustness",
                "model_or_variant": f"confidence_epsilon_{row['epsilon']}",
                "spearman": row["spearman"],
                "top5_overlap": row["top5_overlap"],
                "top10_overlap": row["top10_overlap"],
                "avg_rank_change": row["avg_rank_change"],
                "max_rank_change": row["max_rank_change"],
                "notes": "",
            }
        )
    table3_combined = pd.DataFrame(table3_rows)
    save_csv_and_md(
        table3_combined,
        "table3_ablation_and_robustness.csv",
        "table3_ablation_and_robustness.md",
    )

    # Experiment 8
    pricing_df = run_pricing(full_rank, "Base Case", alpha=1.0, beta=10.0)
    pricing_joined = pricing_df.copy()
    save_csv_and_md(
        pricing_joined[["paper_id", "title", "full_model_score", "query_similarity", "WTP", "price", "price_rank"]],
        "table_pricing_results.csv",
    )
    save_csv_and_md(
        pricing_joined[["paper_id", "title", "full_model_score", "query_similarity", "WTP", "price", "price_rank"]].head(20),
        "table_top_priced_papers.csv",
    )
    plot_value_similarity_price(pricing_df)
    plot_hist(pricing_df["price"], "fig_price_distribution.png", "Price distribution", "Price")

    # Experiment 9
    pricing_scenarios = [
        ("Conservative", 1.0, 5.0),
        ("Base Case", 1.0, 10.0),
        ("Aggressive", 1.0, 15.0),
        ("Quality Priority", 1.5, 8.0),
        ("Similarity Priority", 0.5, 12.0),
    ]
    scenario_tables = []
    base_prices = None
    for name, alpha, beta in pricing_scenarios:
        scenario_df = run_pricing(full_rank, name, alpha=alpha, beta=beta)
        scenario_tables.append(scenario_df)
        if name == "Base Case":
            base_prices = scenario_df[["paper_id", "price", "price_rank"]].rename(columns={"price": "base_price", "price_rank": "base_rank"})

    price_all = pd.concat(scenario_tables, ignore_index=True)
    sensitivity_rows = []
    for name, alpha, beta in pricing_scenarios:
        current = price_all[price_all["scenario"] == name][["paper_id", "price", "price_rank"]].merge(base_prices, on="paper_id", how="left")
        current["price_change"] = current["price"] - current["base_price"]
        current["rank_change"] = (current["price_rank"] - current["base_rank"]).abs()
        base_order = current.sort_values("base_rank")
        current_order = current.sort_values("price_rank")
        sensitivity_rows.append(
            {
                "scenario": name,
                "alpha": alpha,
                "beta": beta,
                "top5_overlap": len(set(base_order.head(5)["paper_id"]) & set(current_order.head(5)["paper_id"])),
                "avg_price_change": float(current["price_change"].abs().mean()),
                "max_price_change": float(current["price_change"].abs().max()),
                "avg_rank_change": float(current["rank_change"].mean()),
                "max_rank_change": float(current["rank_change"].max()),
            }
        )
    pricing_sensitivity_df = pd.DataFrame(sensitivity_rows)
    save_csv_and_md(pricing_sensitivity_df, "table_pricing_sensitivity.csv")

    top5_stability_rows = []
    base_top5 = set(price_all[price_all["scenario"] == "Base Case"].nsmallest(5, "price_rank")["paper_id"])
    for name, _, _ in pricing_scenarios:
        current_top5 = set(price_all[price_all["scenario"] == name].nsmallest(5, "price_rank")["paper_id"])
        top5_stability_rows.append(
            {
                "scenario": name,
                "top5_overlap_with_base": len(base_top5 & current_top5),
                "top5_papers": "; ".join(price_all[price_all["scenario"] == name].nsmallest(5, "price_rank")["paper_id"]),
            }
        )
    top5_stability_df = pd.DataFrame(top5_stability_rows)
    save_csv_and_md(top5_stability_df, "table_top5_price_stability.csv")

    # Paper-ready combined Table 5
    top_pricing_main = pricing_joined[
        ["paper_id", "title", "full_model_score", "query_similarity", "WTP", "price", "price_rank"]
    ].head(10).copy()
    top_pricing_main["section"] = "Top priced papers"
    top_pricing_main["scenario"] = "Base Case"
    top_pricing_main["top5_overlap"] = np.nan
    top_pricing_main["avg_price_change"] = np.nan
    top_pricing_main["max_price_change"] = np.nan
    top_pricing_main["avg_rank_change"] = np.nan
    top_pricing_main["max_rank_change"] = np.nan

    pricing_sens_part = pricing_sensitivity_df.copy()
    pricing_sens_part["section"] = "Pricing sensitivity"
    pricing_sens_part["paper_id"] = ""
    pricing_sens_part["title"] = ""
    pricing_sens_part["full_model_score"] = np.nan
    pricing_sens_part["query_similarity"] = np.nan
    pricing_sens_part["WTP"] = np.nan
    pricing_sens_part["price"] = np.nan
    pricing_sens_part["price_rank"] = np.nan

    table5_combined = pd.concat(
        [
            top_pricing_main[
                [
                    "section",
                    "scenario",
                    "paper_id",
                    "title",
                    "full_model_score",
                    "query_similarity",
                    "WTP",
                    "price",
                    "price_rank",
                    "top5_overlap",
                    "avg_price_change",
                    "max_price_change",
                    "avg_rank_change",
                    "max_rank_change",
                ]
            ],
            pricing_sens_part[
                [
                    "section",
                    "scenario",
                    "paper_id",
                    "title",
                    "full_model_score",
                    "query_similarity",
                    "WTP",
                    "price",
                    "price_rank",
                    "top5_overlap",
                    "avg_price_change",
                    "max_price_change",
                    "avg_rank_change",
                    "max_rank_change",
                ]
            ],
        ],
        ignore_index=True,
    )
    save_csv_and_md(
        table5_combined,
        "table5_pricing_main_and_sensitivity.csv",
        "table5_pricing_main_and_sensitivity.md",
    )

    # Experiment 10
    full_vs_unweighted = full_rank[["paper_id", "full_model_score_rank"]].merge(
        unweighted_rank[["paper_id", "unweighted_pagerank_rank"]],
        on="paper_id",
        how="left",
    )
    case_base = pricing_joined.merge(
        full_vs_unweighted,
        on="paper_id",
        how="left",
    ).merge(
        penalty_compare[["paper_id", "self_citation_edges", "rank_change_due_to_penalty", "score_change_due_to_penalty"]],
        on="paper_id",
        how="left",
    )
    case_base["self_citation_edges"] = case_base["self_citation_edges"].fillna(0).astype(int)
    case_base["rank_change_due_to_penalty"] = case_base["rank_change_due_to_penalty"].fillna(0).astype(int)
    case_base["score_change_due_to_penalty"] = case_base["score_change_due_to_penalty"].fillna(0.0)
    llm_edge_mean = edges.groupby("target_id").agg(
        mean_q=("q_ij", "mean"),
        mean_tau=("tau_ij", "mean"),
    ).reset_index().rename(columns={"target_id": "paper_id"})
    case_base = case_base.merge(llm_edge_mean, on="paper_id", how="left")
    case_base["mean_q"] = case_base["mean_q"].fillna(DEFAULT_Q)
    case_base["mean_tau"] = case_base["mean_tau"].fillna(1.0)

    high_value_threshold = case_base["full_model_score"].quantile(0.75)
    low_sim_threshold = case_base["query_similarity"].quantile(0.25)
    med_value_low = case_base["full_model_score"].quantile(0.35)
    med_value_high = case_base["full_model_score"].quantile(0.65)
    high_sim_threshold = case_base["query_similarity"].quantile(0.75)

    case_rows = []

    def add_case_rows(df_subset: pd.DataFrame, case_type: str, limit: int) -> None:
        for _, row in df_subset.head(limit).iterrows():
            explanation_bits = []
            if row["mean_q"] > case_base["mean_q"].median():
                explanation_bits.append("LLM语义质量较高")
            else:
                explanation_bits.append("LLM语义质量一般")
            if row["mean_tau"] < case_base["mean_tau"].median():
                explanation_bits.append("时间衰减较明显")
            else:
                explanation_bits.append("时间衰减较弱")
            if row["self_citation_edges"] > 0:
                explanation_bits.append(f"存在{row['self_citation_edges']}条自引/团队互引边")
            else:
                explanation_bits.append("未观察到自引边")
            case_rows.append(
                {
                    "case_type": case_type,
                    "paper_id": row["paper_id"],
                    "title": row["title"],
                    "unweighted_rank": int(row["unweighted_pagerank_rank"]),
                    "full_model_rank": int(row["full_model_score_rank"]),
                    "self_citation_edges": int(row["self_citation_edges"]),
                    "mean_semantic_quality": round(float(row["mean_q"]), 6),
                    "mean_temporal_decay": round(float(row["mean_tau"]), 6),
                    "query_similarity": round(float(row["query_similarity"]), 6),
                    "price": round(float(row["price"]), 6),
                    "reason": "；".join(explanation_bits),
                }
            )

    add_case_rows(case_base.sort_values("full_model_score_rank"), "Top-3 full model papers", 3)
    add_case_rows(case_base.sort_values("rank_change_due_to_penalty", ascending=False), "Largest rank drops after penalty", 3)
    add_case_rows(case_base[(case_base["full_model_score"] >= high_value_threshold) & (case_base["query_similarity"] <= low_sim_threshold)].sort_values("query_similarity"), "High value but low similarity", 3)
    add_case_rows(case_base[(case_base["full_model_score"].between(med_value_low, med_value_high)) & (case_base["query_similarity"] >= high_sim_threshold)].sort_values("query_similarity", ascending=False), "Medium value but high similarity", 3)
    add_case_rows(case_base[case_base["self_citation_edges"] > 0].sort_values("self_citation_edges", ascending=False), "Papers with multiple self-citation edges", 3)

    case_study_df = pd.DataFrame(case_rows).drop_duplicates(subset=["case_type", "paper_id"])
    save_csv_and_md(case_study_df, "table_case_study.csv")

    # Summary markdown
    summary_lines = [
        "# Experiment Summary",
        "",
        "## Input status",
        markdown_table(loaded.file_status),
        "",
        "## Dataset statistics",
        markdown_table(dataset_stats),
        "",
        "## Ranking consistency",
        markdown_table(rank_corr_df),
        "",
        "## Ablation summary",
        markdown_table(ablation_summary),
        "",
        "## Confidence-aware variant",
        markdown_table(confidence_df),
        "",
        "## Extended relation robustness",
        markdown_table(extended_stats),
        "",
        "## Pricing sensitivity",
        markdown_table(pricing_sensitivity_df),
    ]
    (RESULTS_DIR / "experiment_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")


if __name__ == "__main__":
    run_experiments()
