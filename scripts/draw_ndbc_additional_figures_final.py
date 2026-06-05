from pathlib import Path
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"

FONT_CN = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
FONT_CN_BOLD = FontProperties(fname=r"C:\Windows\Fonts\msyhbd.ttc")


def short_title(title: str, limit: int = 20) -> str:
    if len(title) <= limit:
        return title
    return title[: limit - 3] + "..."


def save_fig(fig, png_name: str, pdf_name: str | None = None):
    png_path = FIGURES / png_name
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    if pdf_name:
        fig.savefig(FIGURES / pdf_name, bbox_inches="tight")
    plt.close(fig)


def draw_semantic_layer_flow():
    fig, ax = plt.subplots(figsize=(12.4, 8.2), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(x, y, w, h, title, body="", title_size=18, body_size=13):
        rect = Rectangle((x, y), w, h, linewidth=1.8, edgecolor="black", facecolor="white")
        ax.add_patch(rect)
        ax.text(x + 0.25, y + h - 0.38, title, ha="left", va="top",
                fontproperties=FONT_CN_BOLD, fontsize=title_size, color="black")
        if body:
            ax.text(x + 0.25, y + h - 1.18, body, ha="left", va="top",
                    fontproperties=FONT_CN, fontsize=body_size, color="black", linespacing=1.45)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                     arrowstyle="-|>", mutation_scale=18,
                                     linewidth=1.8, color="black"))

    left_x = 0.85
    w = 4.45
    h = 1.08
    ys = [8.45, 6.95, 5.45, 3.95, 2.45]
    titles = [
        "204 条论文层 citation edges",
        "reference entry matching",
        "citation marker localization",
        "target-aligned context extraction",
        "113 条 DeepSeek 语义边",
    ]
    bodies = [
        "语义层构建起点",
        "匹配目标被引论文",
        "定位目标引用标记",
        "抽取目标对齐上下文",
        "正式 DeepSeek 语义边",
    ]
    for y, t, b in zip(ys, titles, bodies):
        box(left_x, y, w, h, t, b, title_size=16, body_size=11.6)

    for i in range(len(ys) - 1):
        arrow(left_x + w / 2, ys[i], left_x + w / 2, ys[i + 1] + h)

    fallback_box = (8.15, 4.7, 6.55, 3.55)
    box(*fallback_box, "91 条 default fallback 边",
        "统一采用默认 q = 0.3，不复用旧 llm_results.csv。\n\n"
        "典型原因：\n"
        "• PDF / text unavailable\n"
        "• reference parsing failure\n"
        "• citation marker not found\n"
        "• ambiguous grouped citation\n"
        "• context-target mismatch risk",
        title_size=16, body_size=12.0)
    arrow(left_x + w, ys[3] + h / 2, fallback_box[0], 6.0)

    ax.text(8.0, 0.55,
            "保守语义层策略：优先保证 target-context alignment 可靠性，而不是盲目追求更高覆盖率",
            ha="center", va="center", fontproperties=FONT_CN_BOLD, fontsize=14, color="black")

    save_fig(fig, "fig_target_aligned_semantic_layer_flow_final.png",
             "fig_target_aligned_semantic_layer_flow_final.pdf")


def draw_future_validation_spearman():
    core_2020 = pd.read_csv(RESULTS / "table_future_citation_validation_core_final.csv")
    core_2021 = pd.read_csv(RESULTS / "table_future_citation_validation_core_cutoff2021_final.csv")
    wanted = ["Citation Count", "Unweighted PageRank", "Time-aware PageRank", "Full model final"]
    map_2020 = dict(zip(core_2020["Method"], core_2020["Spearman"]))
    map_2021 = dict(zip(core_2021["Method"], core_2021["Spearman"]))
    vals_2020 = [float(map_2020[m]) for m in wanted]
    vals_2021 = [float(map_2021[m]) for m in wanted]

    fig, ax = plt.subplots(figsize=(10.6, 6.4), dpi=300)
    x = np.arange(len(wanted))
    width = 0.34
    colors = ["#6C8FB3", "#B9C7D8"]
    bars1 = ax.bar(x - width / 2, vals_2020, width, color=colors[0], edgecolor="black", linewidth=0.8,
                   label="cutoff=2020 / future=2021–2024")
    bars2 = ax.bar(x + width / 2, vals_2021, width, color=colors[1], edgecolor="black", linewidth=0.8,
                   label="cutoff=2021 / future=2022–2024")

    ax.axhline(0, color="black", linewidth=0.9)
    ax.set_ylabel("Spearman", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(["Citation\nCount", "Unweighted\nPageRank", "Time-aware\nPageRank", "Full\nmodel"],
                       fontsize=11)
    ax.set_ylim(-0.14, 0.26)
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.4)
    ax.legend(frameon=False, fontsize=10, loc="upper left")

    for bars in [bars1, bars2]:
        for bar in bars:
            h = bar.get_height()
            y = h + 0.008 if h >= 0 else h - 0.03
            ax.text(bar.get_x() + bar.get_width() / 2, y, f"{h:.4f}",
                    ha="center", va="bottom" if h >= 0 else "top", fontsize=9)

    # emphasize Full model
    ax.annotate("Full = 0.1707", xy=(x[-1] - width / 2, vals_2020[-1]),
                xytext=(x[-1] - 0.75, 0.225),
                arrowprops=dict(arrowstyle="-", lw=0.8, color="gray"),
                fontsize=10, color="black")
    ax.annotate("Full = 0.1355", xy=(x[-1] + width / 2, vals_2021[-1]),
                xytext=(x[-1] - 0.55, 0.195),
                arrowprops=dict(arrowstyle="-", lw=0.8, color="gray"),
                fontsize=10, color="black")

    save_fig(fig, "fig_future_validation_spearman_final.png",
             "fig_future_validation_spearman_final.pdf")


def compute_reason(row):
    if row["full_model_rank"] > row["unweighted_pagerank_rank"] + 6:
        return "relation penalty"
    if row["citation_count_rank"] - row["full_model_rank"] >= 12:
        return "low citation count but high semantic value"
    if row["full_model_rank"] - row["citation_count_rank"] >= 12:
        return "high citation count but weaker semantic relevance"
    if row["unweighted_pagerank_rank"] - row["full_model_rank"] >= 8:
        return "high semantic quality"
    return ""


def draw_reranking_and_table():
    df = pd.read_csv(RESULTS / "ranking_scores_final.csv")
    df["full_model_rank"] = df["full_model_score_final_rank"]
    df["unweighted_pagerank_rank"] = df["unweighted_pagerank_score_rank"]
    df["rank_change_vs_citation"] = df["citation_count_rank"] - df["full_model_rank"]
    df["rank_change_vs_pagerank"] = df["unweighted_pagerank_rank"] - df["full_model_rank"]
    df["title_short"] = df["title"].apply(lambda s: short_title(s, 20))
    df["main_reason"] = df.apply(compute_reason, axis=1)

    top_case = df.assign(max_abs_change=np.maximum(df["rank_change_vs_citation"].abs(),
                                                   df["rank_change_vs_pagerank"].abs()))
    top_case = top_case.sort_values(["max_abs_change", "full_model_rank"], ascending=[False, True]).head(15)
    table_cols = ["title", "citation_count_rank", "unweighted_pagerank_rank", "full_model_rank",
                  "rank_change_vs_citation", "rank_change_vs_pagerank", "main_reason"]
    table_df = top_case[table_cols].rename(columns={"title": "paper_title"})
    table_df.to_csv(
        RESULTS / "table_value_revaluation_cases_final.csv", index=False, encoding="utf-8-sig"
    )
    headers = list(table_df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in table_df.iterrows():
        vals = [str(row[h]).replace("\n", " ") for h in headers]
        lines.append("| " + " | ".join(vals) + " |")
    (RESULTS / "table_value_revaluation_cases_final.md").write_text("\n".join(lines), encoding="utf-8")

    top_cit = df.assign(abs_change=df["rank_change_vs_citation"].abs()).sort_values(
        ["abs_change", "full_model_rank"], ascending=[False, True]
    ).head(6).sort_values("citation_count_rank")
    top_pr = df.assign(abs_change=df["rank_change_vs_pagerank"].abs()).sort_values(
        ["abs_change", "full_model_rank"], ascending=[False, True]
    ).head(6).sort_values("unweighted_pagerank_rank")

    fig, axes = plt.subplots(1, 2, figsize=(14.4, 7.0), dpi=300, sharey=False)

    def slope_panel(ax, subset, left_col, left_label, title):
        y = np.arange(len(subset))
        ax.set_xlim(0, 1)
        max_rank = max(int(subset[left_col].max()), int(subset["full_model_rank"].max())) + 3
        ax.set_ylim(max_rank, 0)
        ax.axis("off")
        ax.text(0.15, 0.98, left_label, transform=ax.transAxes, ha="center", va="top",
                fontproperties=FONT_CN_BOLD, fontsize=13)
        ax.text(0.85, 0.98, "Full model", transform=ax.transAxes, ha="center", va="top",
                fontproperties=FONT_CN_BOLD, fontsize=13)
        ax.text(0.5, 1.06, title, transform=ax.transAxes, ha="center", va="bottom",
                fontproperties=FONT_CN_BOLD, fontsize=15)
        for _, row in subset.iterrows():
            x1, x2 = 0.18, 0.82
            y1 = row[left_col]
            y2 = row["full_model_rank"]
            improved = y2 < y1
            color = "#5078A0" if improved else "#A36A5A"
            ax.plot([x1, x2], [y1, y2], color=color, linewidth=1.8, alpha=0.85)
            ax.scatter([x1, x2], [y1, y2], s=28, color=color, zorder=3)
            delta = int(y1 - y2)
            label = f"{short_title(row['title'], 14)}  {int(y1)}→{int(y2)}  Δ{delta:+d}"
            ax.text(0.5, (y1 + y2) / 2, label, ha="center", va="center", fontsize=9.0,
                    bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.82))

    slope_panel(axes[0], top_cit, "citation_count_rank", "Citation Count", "传统计数与 Full model 的价值重估")
    slope_panel(axes[1], top_pr, "unweighted_pagerank_rank", "Unweighted PR", "经典传播与 Full model 的价值重估")

    save_fig(fig, "fig_article_value_reranking_final.png", "fig_article_value_reranking_final.pdf")


def main():
    draw_semantic_layer_flow()
    draw_future_validation_spearman()
    draw_reranking_and_table()


if __name__ == "__main__":
    main()
