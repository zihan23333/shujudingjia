from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"

FONT_CN = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
FONT_CN_BOLD = FontProperties(fname=r"C:\Windows\Fonts\msyhbd.ttc")


def short_title(text: str, limit: int = 18) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def save(fig, png: str, pdf: str):
    fig.savefig(FIGURES / png, dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / pdf, bbox_inches="tight")
    plt.close(fig)


def fig1_pipeline():
    img = Image.new("RGB", (2400, 760), "white")
    draw = ImageDraw.Draw(img)
    title_font = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 42)
    body_font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 24)
    small_font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 20)

    boxes = [
        ("异构学术图构建", "papers, authors, institutions\ncitation network as propagation backbone"),
        ("目标对齐引用上下文重建", "target-aligned citation contexts\nfor each citation edge"),
        ("LLM-based semantic annotation", "section, relevance, sentiment\nas edge-level evidence"),
        ("语义—时间—关系加权边构造", "w_ij = q_ij · t_ij · r_ij"),
        ("加权文章级价值传播", "Full model article-level value"),
        ("需求感知价格生成", "value + query similarity\n→ personalized price"),
    ]

    x0 = 60
    y = 180
    w = 330
    h = 190
    gap = 45
    centers = []
    for i, (title, body) in enumerate(boxes):
        x = x0 + i * (w + gap)
        draw.rectangle([x, y, x + w, y + h], outline="black", width=4)
        draw.text((x + 18, y + 18), title, fill="black", font=title_font if i == 0 else ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 34))
        yy = y + 88
        for line in body.split("\n"):
            draw.text((x + 18, yy), line, fill="black", font=body_font)
            yy += 34
        centers.append((x + w, y + h // 2, x + w + gap, y + h // 2))

    for x1, y1, x2, y2 in centers[:-1]:
        draw.line((x1, y1, x2 - 18, y2), fill="black", width=5)
        draw.polygon([(x2, y2), (x2 - 22, y2 - 12), (x2 - 22, y2 + 12)], fill="black")

    caption = "edge-level evidence  →  weighted citation propagation  →  demand-aware service pricing"
    draw.rectangle([120, 520, 2280, 600], outline="black", width=3)
    draw.text((230, 547), caption, fill="black", font=small_font)

    img.save(FIGURES / "fig_framework_target_aligned_valuation_final.png", dpi=(300, 300))
    img.save(FIGURES / "fig_framework_target_aligned_valuation_final.pdf", resolution=300.0)


def fig2_semantic_flow():
    img = Image.new("RGB", (2200, 1260), "white")
    draw = ImageDraw.Draw(img)
    title_font = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 34)
    body_font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 24)
    bottom_font = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 28)

    left_x, left_w, box_h = 90, 680, 150
    ys = [60, 260, 460, 660, 860]
    items = [
        ("204 citation edges", ["semantic layer construction start"]),
        ("reference entry matching", ["match target cited paper"]),
        ("citation marker localization", ["locate target marker"]),
        ("target-aligned context extraction", ["extract aligned citation contexts"]),
        ("113 target-aligned semantic edges", ["formal semantic layer"]),
    ]

    def box(x, y, w, h, title, lines):
        draw.rectangle([x, y, x + w, y + h], outline="black", width=4)
        draw.text((x + 22, y + 24), title, fill="black", font=title_font)
        yy = y + 104
        for line in lines:
            draw.text((x + 22, yy), line, fill="black", font=body_font)
            yy += 32

    def down(x, y1, y2):
        draw.line((x, y1, x, y2), fill="black", width=5)
        draw.polygon([(x, y2), (x - 14, y2 - 24), (x + 14, y2 - 24)], fill="black")

    def right(x1, y, x2):
        draw.line((x1, y, x2, y), fill="black", width=5)
        draw.polygon([(x2, y), (x2 - 24, y - 14), (x2 - 24, y + 14)], fill="black")

    for (title, lines), y in zip(items, ys):
        box(left_x, y, left_w, box_h, title, lines)
    cx = left_x + left_w // 2
    for i in range(len(ys) - 1):
        down(cx, ys[i] + box_h, ys[i + 1] - 14)

    rx, ry, rw, rh = 1120, 250, 930, 500
    box(
        rx,
        ry,
        rw,
        rh,
        "91 default fallback edges",
        [
            "default q = 0.3; old llm_results.csv not reused.",
            "",
            "Typical reasons:",
            "• PDF / text unavailable",
            "• reference parsing failure",
            "• citation marker not found",
            "• ambiguous grouped citation",
            "• context-target mismatch risk",
        ],
    )
    right(left_x + left_w, ys[3] + box_h // 2, rx - 18)

    draw.rectangle([90, 1130, 2060, 1208], outline="black", width=3)
    draw.text((130, 1153), "Conservative strategy: prioritize target-context alignment reliability over higher semantic coverage",
              fill="black", font=bottom_font)

    img.save(FIGURES / "fig_target_aligned_semantic_layer_flow_final.png", dpi=(300, 300))
    img.save(FIGURES / "fig_target_aligned_semantic_layer_flow_final.pdf", resolution=300.0)


def fig3_future_validation():
    d1 = pd.read_csv(RESULTS / "table_future_citation_validation_core_final.csv")
    d2 = pd.read_csv(RESULTS / "table_future_citation_validation_core_cutoff2021_final.csv")
    methods = ["Citation Count", "Unweighted PageRank", "Time-aware PageRank", "Full model final"]
    m1 = dict(zip(d1["Method"], d1["Spearman"]))
    m2 = dict(zip(d2["Method"], d2["Spearman"]))
    y1 = [float(m1[m]) for m in methods]
    y2 = [float(m2[m]) for m in methods]

    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
    })
    fig, ax = plt.subplots(figsize=(10.8, 6.8), dpi=300)
    x = np.arange(len(methods))
    width = 0.34
    c1, c2 = "#C8C8C8", "#C0392B"
    bars1 = ax.bar(x - width/2, y1, width, color=c1, edgecolor="black", linewidth=0.8, label="cutoff=2020 / future=2021–2024")
    bars2 = ax.bar(x + width/2, y2, width, color=c2, edgecolor="white", linewidth=0.8, hatch="//", label="cutoff=2021 / future=2022–2024")
    ax.axhline(0, color="black", linewidth=0.9)
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
    ax.set_ylabel("Spearman", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(["Citation\nCount", "Unweighted\nPageRank", "Time-aware\nPageRank", "Full\nmodel"], fontsize=11)
    ax.set_ylim(-0.14, 0.26)
    ax.legend(frameon=True, facecolor="white", edgecolor="#CCCCCC", fontsize=10, loc="upper left")
    for bars in (bars1, bars2):
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width()/2, h + 0.008 if h >= 0 else h - 0.03, f"{h:.4f}",
                    ha="center", va="bottom" if h >= 0 else "top", fontsize=9)
    save(fig, "fig_future_validation_spearman_final.png", "fig_future_validation_spearman_final.pdf")


def fig4_reranking():
    df = pd.read_csv(RESULTS / "ranking_scores_final.csv")
    df["full_rank"] = df["full_model_score_final_rank"]
    df["delta_cit"] = df["citation_count_rank"] - df["full_rank"]
    df["delta_pr"] = df["unweighted_pagerank_score_rank"] - df["full_rank"]

    top_c = df.assign(abs_change=df["delta_cit"].abs()).sort_values(["abs_change", "full_rank"], ascending=[False, True]).head(5)
    top_p = df.assign(abs_change=df["delta_pr"].abs()).sort_values(["abs_change", "full_rank"], ascending=[False, True]).head(5)

    fig, axes = plt.subplots(1, 2, figsize=(13.8, 6.8), dpi=300)

    def panel(ax, subset, left_col, subtitle):
        ax.set_xlim(0, 1)
        max_rank = max(int(subset[left_col].max()), int(subset["full_rank"].max())) + 4
        ax.set_ylim(max_rank, 0)
        ax.axis("off")
        ax.text(0.16, 0.98, subtitle, transform=ax.transAxes, ha="center", va="top", fontsize=12, fontweight="bold")
        ax.text(0.84, 0.98, "Full model", transform=ax.transAxes, ha="center", va="top", fontsize=12, fontweight="bold")
        for _, r in subset.iterrows():
            x1, x2 = 0.20, 0.80
            y1, y2 = r[left_col], r["full_rank"]
            color = "#547DA7" if y2 < y1 else "#A66F60"
            ax.plot([x1, x2], [y1, y2], color=color, linewidth=2.0, alpha=0.92)
            ax.scatter([x1, x2], [y1, y2], s=36, color=color, zorder=3)
            delta = int(y1 - y2)
            label = f"{short_title(r['title'], 16)}  {int(y1)}→{int(y2)}  Δ{delta:+d}"
            ax.text(0.5, (y1 + y2) / 2, label, ha="center", va="center", fontsize=9.5,
                    bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none", alpha=0.86))

    panel(axes[0], top_c.sort_values("citation_count_rank"), "citation_count_rank", "(a) Citation Count vs Full model")
    panel(axes[1], top_p.sort_values("unweighted_pagerank_score_rank"), "unweighted_pagerank_score_rank", "(b) Unweighted PageRank vs Full model")
    fig.suptitle("Ranking shifts from baseline indicators to the full model", fontsize=18, fontweight="bold", y=0.98)
    save(fig, "fig_article_value_reranking_final.png", "fig_article_value_reranking_final.pdf")


def fig5_pricing():
    pricing = pd.read_csv(RESULTS / "table_pricing_results_final.csv")
    top = pd.read_csv(RESULTS / "table_top_priced_papers_final.csv")
    col_map = {c.lower(): c for c in pricing.columns}
    value_col = col_map.get("full_model_normalized_value") or col_map.get("normalized_value") or col_map.get("value_normalized")
    if value_col is None:
        # derive min-max from full model score
        score_col = col_map.get("full_model_score_final") or col_map.get("full_model_score") or col_map.get("full_model_score_v2")
        vals = pricing[score_col].astype(float)
        pricing["_norm_value_"] = (vals - vals.min()) / (vals.max() - vals.min() + 1e-12)
        value_col = "_norm_value_"
    sim_col = col_map.get("query_similarity")
    price_col = col_map.get("price")
    title_col = col_map.get("title")

    top_names = [
        "TUBE",
        "Query-based data pricing",
        "Too Much Data: Prices and Inefficiencies in Data Markets",
        "Smart data pricing",
        "A survey of smart data pricing",
    ]

    fig, axes = plt.subplots(2, 1, figsize=(10.2, 11.4), dpi=300, gridspec_kw={"height_ratios": [2.2, 1.5]})

    ax = axes[0]
    sc = ax.scatter(pricing[value_col], pricing[sim_col], c=pricing[price_col], s=50 + 900 * pricing[price_col], cmap="Greys", alpha=0.82, edgecolors="#777777", linewidths=0.5)
    for name in top_names:
        hit = pricing[pricing[title_col] == name]
        if len(hit):
            r = hit.iloc[0]
            ax.annotate(short_title(name, 22), (r[value_col], r[sim_col]),
                        xytext=(8, 8), textcoords="offset points", fontsize=10,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    ax.set_xlabel("Full model normalized value", fontsize=12)
    ax.set_ylabel("query similarity", fontsize=12)
    ax.text(0.01, 1.03, "(a)", transform=ax.transAxes, fontsize=13, fontweight="bold")
    cbar = fig.colorbar(sc, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("price", fontsize=11)

    ax2 = axes[1]
    top_plot = top.head(10).copy()
    ax2.bar(np.arange(len(top_plot)), top_plot[price_col], color="#8FA7BF", edgecolor="black", linewidth=0.7)
    ax2.set_xticks(np.arange(len(top_plot)))
    ax2.set_xticklabels([short_title(t, 16) for t in top_plot[title_col]], rotation=24, ha="right", fontsize=10)
    ax2.set_ylabel("price", fontsize=12)
    ax2.text(0.01, 1.03, "(b)", transform=ax2.transAxes, fontsize=13, fontweight="bold")
    ax2.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.35)

    fig.tight_layout()
    save(fig, "fig_personalized_pricing_results_final.png", "fig_personalized_pricing_results_final.pdf")


def main():
    fig1_pipeline()
    fig2_semantic_flow()
    fig3_future_validation()
    fig4_reranking()
    fig5_pricing()


if __name__ == "__main__":
    main()
