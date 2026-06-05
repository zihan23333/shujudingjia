from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"


def short_title(text: str, limit: int = 16) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def main():
    df = pd.read_csv(RESULTS / "ranking_scores_final.csv")
    df["full_model_rank"] = df["full_model_score_final_rank"]
    df["rank_change_vs_citation"] = df["citation_count_rank"] - df["full_model_rank"]
    df["rank_change_vs_pagerank"] = df["unweighted_pagerank_score_rank"] - df["full_model_rank"]

    top_cit = (
        df.assign(abs_change=df["rank_change_vs_citation"].abs())
        .sort_values(["abs_change", "full_model_rank"], ascending=[False, True])
        .head(5)
        .sort_values("citation_count_rank")
    )
    top_pr = (
        df.assign(abs_change=df["rank_change_vs_pagerank"].abs())
        .sort_values(["abs_change", "full_model_rank"], ascending=[False, True])
        .head(5)
        .sort_values("unweighted_pagerank_score_rank")
    )

    fig, axes = plt.subplots(1, 2, figsize=(13.8, 6.6), dpi=300)

    def panel(ax, subset, left_col, left_label):
        ax.set_xlim(0, 1)
        max_rank = max(int(subset[left_col].max()), int(subset["full_model_rank"].max())) + 3
        ax.set_ylim(max_rank, 0)
        ax.axis("off")
        ax.text(0.16, 0.98, left_label, transform=ax.transAxes, ha="center", va="top",
                fontsize=13, fontweight="bold")
        ax.text(0.84, 0.98, "Full model", transform=ax.transAxes, ha="center", va="top",
                fontsize=13, fontweight="bold")
        for _, row in subset.iterrows():
            x1, x2 = 0.20, 0.80
            y1, y2 = row[left_col], row["full_model_rank"]
            improved = y2 < y1
            color = "#547DA7" if improved else "#A66F60"
            ax.plot([x1, x2], [y1, y2], color=color, linewidth=2.0, alpha=0.9)
            ax.scatter([x1, x2], [y1, y2], s=34, color=color, zorder=3)
            delta = int(y1 - y2)
            label = f"{short_title(row['title'])}  {int(y1)}→{int(y2)}  Δ{delta:+d}"
            ax.text(
                0.5,
                (y1 + y2) / 2,
                label,
                ha="center",
                va="center",
                fontsize=9.5,
                bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none", alpha=0.85),
            )

    panel(axes[0], top_cit, "citation_count_rank", "Citation Count")
    panel(axes[1], top_pr, "unweighted_pagerank_score_rank", "Unweighted PR")
    fig.suptitle("Ranking shifts from baseline indicators to the full model", fontsize=18, fontweight="bold", y=0.98)
    fig.savefig(FIGURES / "fig_article_value_reranking_final.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / "fig_article_value_reranking_final.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
