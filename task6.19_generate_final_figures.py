#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def save_dual(fig: plt.Figure, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES / f"{stem}.png", dpi=220, bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
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


def title_short(text: str, n: int = 20) -> str:
    text = str(text).strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def load_inputs() -> Dict[str, pd.DataFrame]:
    return {
        "ranking": pd.read_csv(RESULTS / "ranking_scores_final.csv", encoding="utf-8-sig"),
        "top30": pd.read_csv(RESULTS / "table_top30_ranking_final.csv", encoding="utf-8-sig"),
        "future_main": pd.read_csv(RESULTS / "table_future_citation_validation_core_final.csv", encoding="utf-8-sig"),
        "future_robust": pd.read_csv(RESULTS / "table_future_citation_validation_core_cutoff2021_final.csv", encoding="utf-8-sig"),
        "pricing": pd.read_csv(RESULTS / "table_pricing_results_final.csv", encoding="utf-8-sig"),
        "top_priced": pd.read_csv(RESULTS / "table_top_priced_papers_final.csv", encoding="utf-8-sig"),
        "reliability": pd.read_csv(RESULTS / "table_llm_reliability_final.csv", encoding="utf-8-sig"),
        "semantic": pd.read_csv(ROOT / "semantic_edge_weights_final.csv", encoding="utf-8-sig"),
        "rep": pd.read_excel(ROOT / "annotation_package_final" / "representative" / "sampled_contexts_for_human_annotation_representative_final.xlsx"),
    }


def draw_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(13, 4.8))
    ax.axis("off")
    blue = "#6e8ea6"
    gray = "#d9e1e8"
    textc = "#1f2a33"
    steps = [
        "OpenAlex / PDF / 元数据",
        "主题学术网络构建",
        "目标对齐引用上下文重建",
        "DeepSeek 语义评分",
        "语义质量 $q_{ij}$",
        "$q_{ij}\\times \\tau_{ij}\\times \\rho_{ij}$",
        "Full model 文章级价值",
        "价值 + 查询相似度",
        "个性化价格",
    ]
    xs = np.linspace(0.03, 0.93, len(steps))
    y = 0.5
    w = 0.09
    h = 0.22
    for i, (x, label) in enumerate(zip(xs, steps)):
        rect = Rectangle((x - w / 2, y - h / 2), w, h, facecolor=gray if i not in [0, 3, 6, 8] else "#c9d7e3", edgecolor=blue, linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center", fontsize=10.5, color=textc, wrap=True)
        if i < len(steps) - 1:
            arr = FancyArrowPatch((x + w / 2, y), (xs[i + 1] - w / 2, y), arrowstyle="-|>", mutation_scale=12, linewidth=1.1, color=blue)
            ax.add_patch(arr)
    ax.text(0.5, 0.9, "基于目标对齐语义融合的文章级价值评估与个性化定价流程", ha="center", va="center", fontsize=13, color=textc, fontweight="bold")
    save_dual(fig, "fig_method_pipeline_final")


def draw_funnel() -> None:
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    ax.axis("off")
    total = 204
    scored = 113
    fallback = 91
    widths = [1.0, scored / total, fallback / total]
    labels = [
        f"全部 citation edges\n{total}",
        f"DeepSeek target-aligned 评分边\n{scored}",
        f"default fallback 边\n{fallback}",
    ]
    colors = ["#cfd8df", "#7f9db1", "#a7b4be"]
    ys = [0.78, 0.5, 0.22]
    height = 0.16
    for w, y, label, color in zip(widths, ys, labels, colors):
        left = 0.5 - w / 2
        rect = Rectangle((left, y - height / 2), w, height, facecolor=color, edgecolor="#4f6777", linewidth=1.2)
        ax.add_patch(rect)
        ax.text(0.5, y, label, ha="center", va="center", fontsize=11)
    ax.text(0.5, 0.95, "target-aligned 语义层覆盖漏斗", ha="center", va="center", fontsize=13, fontweight="bold")
    ax.text(0.5, 0.04, "语义覆盖率 = 113 / 204 = 55.39%", ha="center", va="center", fontsize=10)
    save_dual(fig, "fig_semantic_coverage_funnel_final")


def draw_future_validation(df_main: pd.DataFrame, df_robust: pd.DataFrame) -> None:
    mapping = [
        ("Citation Count", "Citation Count"),
        ("Unweighted PageRank", "Unweighted PageRank"),
        ("Time-aware PageRank", "Time-aware PageRank"),
        ("Full model final", "Full model"),
    ]
    methods = [m[1] for m in mapping]
    main_vals_s = [float(df_main.loc[df_main["Method"] == m[0], "Spearman"].iloc[0]) for m in mapping]
    robust_vals_s = [float(df_robust.loc[df_robust["Method"] == m[0], "Spearman"].iloc[0]) for m in mapping]
    main_vals_n = [float(df_main.loc[df_main["Method"] == m[0], "NDCG@10"].iloc[0]) for m in mapping]
    robust_vals_n = [float(df_robust.loc[df_robust["Method"] == m[0], "NDCG@10"].iloc[0]) for m in mapping]
    x = np.arange(len(methods))
    bw = 0.34

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.bar(x - bw / 2, main_vals_s, bw, label="cutoff=2020 / future=2021-2024", color="#7f9db1")
    ax.bar(x + bw / 2, robust_vals_s, bw, label="cutoff=2021 / future=2022-2024", color="#c2ccd4")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=18)
    ax.set_ylabel("Spearman")
    ax.set_title("Future citation validation: Spearman 对比")
    ax.legend(frameon=False, fontsize=9)
    full_idx = methods.index("Full model")
    ax.annotate("0.1707", (x[full_idx] - bw / 2, main_vals_s[full_idx]), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=9)
    ax.annotate("0.1355", (x[full_idx] + bw / 2, robust_vals_s[full_idx]), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=9)
    save_dual(fig, "fig_future_validation_spearman_final")

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.bar(x - bw / 2, main_vals_n, bw, label="cutoff=2020 / future=2021-2024", color="#7f9db1")
    ax.bar(x + bw / 2, robust_vals_n, bw, label="cutoff=2021 / future=2022-2024", color="#c2ccd4")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=18)
    ax.set_ylabel("NDCG@10")
    ax.set_title("Future citation validation: NDCG@10 对比")
    ax.legend(frameon=False, fontsize=9)
    save_dual(fig, "fig_future_validation_ndcg_final")


def infer_main_reason(row: pd.Series, semantic: pd.DataFrame, title_sim_map: Dict[str, float]) -> str:
    pid = row["paper_id"]
    incoming = semantic[semantic["target_id"] == pid].copy()
    if incoming.empty:
        return ""
    scored_in = incoming[incoming["has_llm_score"] == True]
    mean_q = float(scored_in["q_ij"].mean()) if not scored_in.empty else np.nan
    mean_rho = float(incoming["rho_ij"].mean()) if "rho_ij" in incoming.columns else np.nan
    sim = float(title_sim_map.get(pid, np.nan))
    if row["rank_change_vs_pagerank"] < 0 and pd.notna(mean_rho) and mean_rho < 0.95:
        return "relation penalty"
    if row["rank_change_vs_citation"] > 10 and pd.notna(mean_q) and mean_q >= 0.18:
        return "low citation count but high semantic value"
    if row["rank_change_vs_citation"] > 5 and pd.notna(sim) and sim >= 0.30:
        return "strong topic relevance"
    if row["rank_change_vs_citation"] < -10 and (pd.isna(sim) or sim < 0.20):
        return "high citation count but weaker semantic relevance"
    if pd.notna(mean_q) and mean_q >= 0.18:
        return "high semantic quality"
    return ""


def draw_rank_shifts(ranking: pd.DataFrame, semantic: pd.DataFrame) -> None:
    # lightweight title-sim proxy from existing pricing table if present not needed here
    pricing = pd.read_csv(RESULTS / "table_pricing_results_final.csv", encoding="utf-8-sig")
    title_sim_map = dict(zip(pricing["paper_id"], pricing["query_similarity"]))

    df = ranking.copy()
    df["rank_change_vs_citation"] = df["citation_count_rank"] - df["full_model_score_final_rank"]
    df["rank_change_vs_pagerank"] = df["unweighted_pagerank_score_rank"] - df["full_model_score_final_rank"]
    df["abs_change_vs_citation"] = df["rank_change_vs_citation"].abs()
    df["abs_change_vs_pagerank"] = df["rank_change_vs_pagerank"].abs()
    df["title_short"] = df["title"].apply(title_short)
    df["main_reason"] = df.apply(lambda r: infer_main_reason(r, semantic, title_sim_map), axis=1)
    out = df[
        [
            "title",
            "citation_count_rank",
            "unweighted_pagerank_score_rank",
            "full_model_score_final_rank",
            "rank_change_vs_citation",
            "rank_change_vs_pagerank",
            "main_reason",
        ]
    ].rename(
        columns={
            "title": "paper_title",
            "unweighted_pagerank_score_rank": "unweighted_pagerank_rank",
            "full_model_score_final_rank": "full_model_rank",
        }
    )
    out.to_csv(RESULTS / "table_value_revaluation_cases_final.csv", index=False, encoding="utf-8-sig")
    md = markdown_table(out, max_rows=30)
    (RESULTS / "table_value_revaluation_cases_final.md").write_text(md, encoding="utf-8")

    for baseline_col, delta_col, stem, title in [
        ("citation_count_rank", "rank_change_vs_citation", "fig_rank_shift_citation_to_full_final", "Citation Count 到 Full model 的排名变化"),
        ("unweighted_pagerank_score_rank", "rank_change_vs_pagerank", "fig_rank_shift_pagerank_to_full_final", "Unweighted PageRank 到 Full model 的排名变化"),
    ]:
        top = df.sort_values(delta_col, key=lambda s: s.abs(), ascending=False).head(10).copy()
        top = top.sort_values(delta_col)
        fig, ax = plt.subplots(figsize=(10.8, 5.8))
        y = np.arange(len(top))
        ax.hlines(y, top[baseline_col], top["full_model_score_final_rank"], color="#b0bcc5", linewidth=1.2)
        ax.scatter(top[baseline_col], y, color="#cfd7dd", s=52, label="baseline", zorder=3)
        ax.scatter(top["full_model_score_final_rank"], y, color="#587488", s=52, label="full", zorder=4)
        for yi, (_, row) in enumerate(top.iterrows()):
            ax.text(
                max(row[baseline_col], row["full_model_score_final_rank"]) + 1.0,
                yi,
                f"{row['title_short']}  {int(row[baseline_col])}->{int(row['full_model_score_final_rank'])}  Δ{int(row[delta_col])}",
                va="center",
                fontsize=8.2,
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.82),
            )
        ax.set_yticks([])
        ax.set_xlabel("排名（越小越靠前）")
        ax.set_title(title)
        ax.invert_xaxis()
        ax.legend(frameon=False, loc="lower right")
        save_dual(fig, stem)


def draw_reliability_scatter(rep: pd.DataFrame, rel_table: pd.DataFrame) -> None:
    work = rep.copy()
    for col in ["human_alignment_check", "human_primary_section", "human_sentiment", "human_relevance"]:
        work[col] = work[col].fillna("").astype(str).str.strip()
    work["human_alignment_check_norm"] = work["human_alignment_check"].str.lower().replace({"wrong": "wrong_or_ambiguous"})
    valid = work[
        (work["human_alignment_check_norm"] == "correct")
        & work["human_primary_section"].ne("")
        & work["human_sentiment"].ne("")
        & work["human_relevance"].ne("")
    ].copy()

    section_map = {"methodology": 1.0, "result": 1.0, "discussion": 0.7, "conclusion": 0.5, "introduction": 0.4, "other": 0.2}
    def norm_sec(v: str) -> str:
        t = str(v).strip().lower()
        if "method" in t:
            return "methodology"
        if "result" in t:
            return "result"
        if "discussion" in t:
            return "discussion"
        if "conclusion" in t:
            return "conclusion"
        if "introduction" in t or "related" in t or "background" in t:
            return "introduction"
        return "other"
    def norm_sent(v: str) -> str:
        t = str(v).strip().lower()
        if t in {"positive", "neutral", "negative"}:
            return t
        return "neutral"
    valid["human_relevance_num"] = pd.to_numeric(valid["human_relevance"], errors="coerce")
    valid["LLM_relevance_num"] = pd.to_numeric(valid["LLM_relevance"], errors="coerce")
    valid["LLM_q_num"] = pd.to_numeric(valid["LLM_q"], errors="coerce")
    valid["human_q"] = valid.apply(
        lambda r: section_map[norm_sec(r["human_primary_section"])]
        * ((({"positive": 1.0, "neutral": 0.0, "negative": -1.0}[norm_sent(r["human_sentiment"])] + 1) / 2)
           if norm_sent(r["human_sentiment"]) != "negative" else 0.01)
        * (float(r["human_relevance_num"]) ** 2),
        axis=1,
    )
    valid = valid.dropna(subset=["human_relevance_num", "LLM_relevance_num", "human_q", "LLM_q_num"]).copy()

    rel_s = float(rel_table.loc[rel_table["metric"] == "relevance_spearman", "value"].iloc[0])
    rel_mae = float(rel_table.loc[rel_table["metric"] == "relevance_mae", "value"].iloc[0])
    q_s = float(rel_table.loc[rel_table["metric"] == "human_q_vs_LLM_q_spearman", "value"].iloc[0])
    q_k = float(rel_table.loc[rel_table["metric"] == "human_q_vs_LLM_q_kendall", "value"].iloc[0])

    rng = np.random.default_rng(42)
    jx = valid["LLM_relevance_num"] + rng.normal(0, 0.012, len(valid))
    jy = valid["human_relevance_num"] + rng.normal(0, 0.012, len(valid))
    fig, ax = plt.subplots(figsize=(6.6, 5.4))
    ax.scatter(jx, jy, color="#6d8797", alpha=0.75, s=42)
    ax.plot([0, 1], [0, 1], color="#c2ccd4", linestyle="--", linewidth=1)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("LLM relevance")
    ax.set_ylabel("human relevance")
    ax.set_title("LLM 与人工 relevance 一致性")
    ax.text(0.03, 0.95, f"Spearman = {rel_s:.4f}\nMAE = {rel_mae:.4f}", transform=ax.transAxes, va="top", fontsize=10)
    save_dual(fig, "fig_llm_relevance_human_scatter_final")

    jx = valid["LLM_q_num"] + rng.normal(0, 0.006, len(valid))
    jy = valid["human_q"] + rng.normal(0, 0.006, len(valid))
    lim = max(valid["LLM_q_num"].max(), valid["human_q"].max()) * 1.05
    fig, ax = plt.subplots(figsize=(6.6, 5.4))
    ax.scatter(jx, jy, color="#6d8797", alpha=0.75, s=42)
    ax.plot([0, lim], [0, lim], color="#c2ccd4", linestyle="--", linewidth=1)
    ax.set_xlim(-0.01, lim)
    ax.set_ylim(-0.01, lim)
    ax.set_xlabel("LLM q")
    ax.set_ylabel("human q")
    ax.set_title("LLM 与人工语义质量一致性")
    ax.text(0.03, 0.95, f"Spearman = {q_s:.4f}\nKendall = {q_k:.4f}", transform=ax.transAxes, va="top", fontsize=10)
    save_dual(fig, "fig_llm_q_human_q_scatter_final")


def draw_pricing(pricing: pd.DataFrame) -> None:
    base = pricing[pricing["scenario"] == "Base Case"].copy().sort_values("price_rank")
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    sc = ax.scatter(base["value_norm"], base["query_similarity"], s=70 + 650 * base["price"], c=base["price"], cmap="Greys", alpha=0.78, edgecolors="#5d6d79", linewidths=0.4)
    ax.set_xlabel("Full model normalized value")
    ax.set_ylabel("query similarity")
    ax.set_title("价值、需求相关性与价格")
    top5 = base.head(5).copy()
    offsets = [(6, 6), (8, -12), (8, 8), (8, -14), (-72, 8)]
    for (_, row), (dx, dy) in zip(top5.iterrows(), offsets):
        ax.annotate(
            title_short(row["title"], 20),
            (row["value_norm"], row["query_similarity"]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=8.3,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.85),
            arrowprops=dict(arrowstyle="-", color="#8899a5", lw=0.6, alpha=0.8),
        )
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("price")
    save_dual(fig, "fig_value_similarity_price_scatter_final")

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.hist(base["price"], bins=18, color="#7f9db1", alpha=0.85, edgecolor="#4f6777")
    ax.set_xlabel("price")
    ax.set_ylabel("paper count")
    ax.set_title("最终价格分布")
    save_dual(fig, "fig_price_distribution_final")


def write_indexes() -> None:
    figure_rows = [
        ("fig_method_pipeline_final.png / .pdf", "4.1", "整体方法流程图", "final semantic layer + pricing pipeline", "正文"),
        ("fig_semantic_coverage_funnel_final.png / .pdf", "4.2", "语义层覆盖漏斗", "113/204 semantic coverage", "正文"),
        ("fig_future_validation_spearman_final.png / .pdf", "4.3", "Future validation Spearman 对比", "table_future_citation_validation_*_final.csv", "正文"),
        ("fig_future_validation_ndcg_final.png / .pdf", "4.3", "Future validation NDCG@10 对比", "table_future_citation_validation_*_final.csv", "正文"),
        ("fig_rank_shift_citation_to_full_final.png / .pdf", "4.4", "Citation Count 到 Full model 的排名变化", "ranking_scores_final.csv", "正文"),
        ("fig_rank_shift_pagerank_to_full_final.png / .pdf", "4.4", "Unweighted PageRank 到 Full model 的排名变化", "ranking_scores_final.csv", "正文"),
        ("fig_llm_relevance_human_scatter_final.png / .pdf", "LLM reliability", "LLM relevance 与人工 relevance 散点", "representative_final.xlsx + table_llm_reliability_final.csv", "正文/附录均可"),
        ("fig_llm_q_human_q_scatter_final.png / .pdf", "LLM reliability", "LLM q 与 human q 散点", "representative_final.xlsx + table_llm_reliability_final.csv", "正文/附录均可"),
        ("fig_value_similarity_price_scatter_final.png / .pdf", "4.7", "价值-相似度-价格散点", "table_pricing_results_final.csv", "正文"),
        ("fig_price_distribution_final.png / .pdf", "4.7", "价格分布图", "table_pricing_results_final.csv", "正文"),
    ]
    lines = ["# Figure Index Final", "", "| 文件名 | 论文小节 | 用途 | 数据来源 | 建议位置 |", "| --- | --- | --- | --- | --- |"]
    for row in figure_rows:
        lines.append("| " + " | ".join(row) + " |")
    (FIGURES / "figure_index_final.md").write_text("\n".join(lines), encoding="utf-8")

    artifact_rows = [
        ("fig_method_pipeline_final", "4.1", "方法流程概览", "final pipeline", "是"),
        ("fig_semantic_coverage_funnel_final", "4.2", "target-aligned 语义层覆盖情况", "semantic layer final", "是"),
        ("fig_future_validation_spearman_final", "4.3", "两个 cutoff 的 Spearman 对比", "future validation final", "是"),
        ("fig_future_validation_ndcg_final", "4.3", "两个 cutoff 的 NDCG@10 对比", "future validation final", "是"),
        ("fig_rank_shift_citation_to_full_final", "4.4", "价值重估案例图 1", "ranking_scores_final.csv", "是"),
        ("fig_rank_shift_pagerank_to_full_final", "4.4", "价值重估案例图 2", "ranking_scores_final.csv", "是"),
        ("table_value_revaluation_cases_final", "4.4", "价值重估案例表", "ranking_scores_final.csv + semantic_edge_weights_final.csv", "是"),
        ("fig_llm_relevance_human_scatter_final", "LLM reliability", "人工与 LLM relevance 一致性", "representative sample", "可放正文"),
        ("fig_llm_q_human_q_scatter_final", "LLM reliability", "人工与 LLM q 一致性", "representative sample", "可放正文"),
        ("fig_value_similarity_price_scatter_final", "4.7", "价值-需求-价格关系", "pricing final", "是"),
        ("fig_price_distribution_final", "4.7", "最终价格分布", "pricing final", "是"),
    ]
    lines = ["# Main Experiment Artifacts Final", "", "| 文件名 | 对应论文小节 | 用途 | 数据来源 | 是否建议放正文 |", "| --- | --- | --- | --- | --- |"]
    for row in artifact_rows:
        lines.append("| " + " | ".join(row) + " |")
    (RESULTS / "table_main_experiment_artifacts_final.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    data = load_inputs()
    draw_pipeline()
    draw_funnel()
    draw_future_validation(data["future_main"], data["future_robust"])
    draw_rank_shifts(data["ranking"], data["semantic"])
    draw_reliability_scatter(data["rep"], data["reliability"])
    draw_pricing(data["pricing"])
    write_indexes()
    print("final figures generated")


if __name__ == "__main__":
    main()
