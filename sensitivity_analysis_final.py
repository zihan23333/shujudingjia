#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
阶段 2：参数稳健性 / 敏感性分析  （最终版）
================================================================================

完全复刻 run_experiments.py 的真实公式（代码真实设定，非论文公式）：
  q_ij    = w_sec(section) * w_sent(sentiment) * w_rel(relevance)
            w_sent = (s+1)/2 if s>=0 else 0.01 ;  w_rel = rel^2
            无 LLM 分边 q = DEFAULT_Q = 0.3
  tau_ij  = TIME_BIAS / (TIME_BIAS + Δt) ,  Δt = max(0, year_src - year_tgt)
  rho_ij  = 1 / (1 + ETA_A * shared_authors_count)
  w_full  = q_ij * tau_ij * rho_ij  ，按 source 出边归一化
  传播     V(j) = (1-d)*B(j) + d * Σ_i V(i)*ŵ_ij  ，d=0.85，B=归一化Global_Citations
            200 轮迭代，收敛阈值 1e-10

设计原则（回应代码审核）：
  - 悬垂节点不做额外处理、年份缺失填 2020：刻意与 run_experiments.py 一致，
    确保 Main 排序 == 正文主实验排序（自检 Spearman 应=1.0）。敏感性分析的目的
    是“同一模型下换参数”，不是构造更优模型，故不在此修改传播逻辑。
  - 混淆矩阵不在本实验：那是功能分类 benchmark(SciCite/ACL-ARC)的交付物；
    参数敏感性是排序稳定性分析，无分类标签，无混淆矩阵。

三组敏感性（每组只改一个参数，其余固定为 Main）：
  组1 section 权重：Main / Equal / Conservative / Theory-strong / Theory-strong-fixed
  组2 时间衰减 TIME_BIAS：∞(无衰减) / 2 / 5(Main) / 8 / 15
  组3 关系惩罚 ETA_A：0 / 0.5 / 1.0(Main) / 2.0

输入文件（与本脚本同目录）：
  semantic_edge_weights_final.csv   edge_id/source_id/target_id/section/sentiment/
                                    relevance/shared_authors_count/q_ij/
                                    has_llm_score/w_full_final
  all_connected_papers.csv          OpenAlex_ID/Title/Global_Citations/Is_Core
  node_publication_years.csv        Clean_ID/Publication_Year

输出（results/ 目录）：
  sens_section.csv / sens_time.csv / sens_relation.csv   三组敏感性表
  sens_main_ranking.csv                                  Main 基准排序（复核用）
  sens_rank_change_cases.csv                             各变体排名变动最大的论文
  sens_summary.md                                        汇总 + 判读

依赖：pip install pandas numpy scipy
================================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
EDGE_PATH = ROOT / "semantic_edge_weights_final.csv"
PAPER_PATH = ROOT / "all_connected_papers.csv"
YEAR_PATH = ROOT / "node_publication_years.csv"

# ---- 代码真实常量（来自 run_experiments.py）----
DAMPING = 0.85
DEFAULT_Q = 0.3
MAIN_TIME_BIAS = 5.0
MAIN_ETA_A = 1.0
MAX_ITER = 200
TOL = 1e-10
FILL_YEAR = 2020  # 与 run_experiments.py 一致

# Main section 权重（代码真实设定）
MAIN_SECTION_WEIGHTS = {
    "methodology": 1.0, "method": 1.0,
    "results": 1.0, "result": 1.0,
    "discussion": 0.7,
    "conclusion": 0.5, "conclusions": 0.5,
    "introduction": 0.4, "background": 0.4,
    "other": 0.2, "unknown": 0.2,
}

# ---- 组1：五组 section 权重 ----
# Theory-strong       = 论文原版（Other=1.0，含“低质量边被拉升”的混合效应，代表论文公式）
# Theory-strong-fixed = 仅改已识别章节权重，Other/Unknown 保持与 Main 一致(0.2)，纯区分度对照
SECTION_VARIANTS = {
    "Main": MAIN_SECTION_WEIGHTS,
    "Equal": {k: 1.0 for k in MAIN_SECTION_WEIGHTS},
    "Conservative": {
        "methodology": 1.0, "method": 1.0, "results": 1.0, "result": 1.0,
        "discussion": 0.85, "conclusion": 0.75, "conclusions": 0.75,
        "introduction": 0.7, "background": 0.7, "other": 0.6, "unknown": 0.6,
    },
    "Theory-strong": {
        "methodology": 1.20, "method": 1.20, "results": 1.15, "result": 1.15,
        "discussion": 1.05, "conclusion": 1.00, "conclusions": 1.00,
        "introduction": 0.90, "background": 0.90, "other": 1.00, "unknown": 1.00,
    },
    "Theory-strong-fixed": {
        "methodology": 1.20, "method": 1.20, "results": 1.15, "result": 1.15,
        "discussion": 1.05, "conclusion": 1.00, "conclusions": 1.00,
        "introduction": 0.90, "background": 0.90, "other": 0.2, "unknown": 0.2,
    },
}

# ---- 组2：TIME_BIAS 档位（None = 无衰减 tau≡1）----
TIME_BIAS_VARIANTS = {"no_decay": None, "strong(2)": 2.0, "Main(5)": 5.0,
                      "weak(8)": 8.0, "veryweak(15)": 15.0}

# ---- 组3：ETA_A 档位 ----
ETA_A_VARIANTS = {"no_penalty(0)": 0.0, "mild(0.5)": 0.5,
                  "Main(1.0)": 1.0, "strong(2.0)": 2.0}


# ===========================================================================
# 工具函数
# ===========================================================================
def to_bool(series: pd.Series) -> pd.Series:
    """稳健布尔转换：兼容 True/False / "true"/"false" / 1/0。"""
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y"])


def map_section_weight(section: object, weight_map: Dict[str, float]) -> float:
    """复刻 run_experiments.map_section_weight：子串匹配，命中第一个 key。"""
    if pd.isna(section):
        return weight_map.get("unknown", 0.2)
    text = str(section).strip().lower()
    if not text:
        return weight_map.get("unknown", 0.2)
    for key, value in weight_map.items():
        if key in text:
            return value
    return weight_map.get("other", 0.2)


def compute_q(edges: pd.DataFrame, weight_map: Dict[str, float]) -> pd.Series:
    """q = w_sec * w_sent * w_rel；无 LLM 分边用 DEFAULT_Q。"""
    w_sec = edges["section"].apply(lambda s: map_section_weight(s, weight_map))
    sent = pd.to_numeric(edges["sentiment"], errors="coerce").fillna(0.0)
    w_sent = np.where(sent >= 0, (sent + 1.0) / 2.0, 0.01)
    rel = pd.to_numeric(edges["relevance"], errors="coerce").fillna(0.0)
    w_rel = rel ** 2
    q = pd.Series(w_sec.values * w_sent * w_rel.values, index=edges.index)
    q = q.where(edges["has_llm_score_bool"], DEFAULT_Q)
    return q


def compute_tau(delta_t: pd.Series, time_bias: Optional[float]) -> pd.Series:
    """tau = TIME_BIAS/(TIME_BIAS+Δt)；time_bias=None 表示无衰减(tau≡1)。"""
    if time_bias is None:
        return pd.Series(1.0, index=delta_t.index)
    return time_bias / (time_bias + delta_t.astype(float))


def compute_rho(shared: pd.Series, eta_a: float) -> pd.Series:
    """rho = 1/(1+eta_a*shared_authors)。"""
    return 1.0 / (1.0 + eta_a * shared.astype(float))


def run_weighted_pagerank(papers: pd.DataFrame, edges: pd.DataFrame,
                          weight_col: str) -> pd.Series:
    """
    复刻 run_experiments.run_weighted_pagerank。返回 paper_id -> score。
    注意：悬垂节点不做均匀再分配 —— 刻意与 run_experiments.py 一致。
    """
    work = edges.copy()
    work["raw_weight"] = pd.to_numeric(work[weight_col], errors="coerce").fillna(0.0)
    out_sum = work.groupby("source_id")["raw_weight"].transform("sum")
    work["norm_weight"] = np.where(out_sum > 0, work["raw_weight"] / out_sum, 0.0)

    base_map = dict(zip(papers["paper_id"], papers["base_value"].astype(float)))
    scores = {pid: float(base_map.get(pid, 0.0)) for pid in papers["paper_id"]}

    incoming: Dict[str, List] = {}
    for _, r in work.iterrows():
        incoming.setdefault(r["target_id"], []).append((r["source_id"], r["norm_weight"]))

    for _ in range(MAX_ITER):
        max_diff = 0.0
        new_scores = {}
        for pid in papers["paper_id"]:
            total = sum(scores.get(src, 0.0) * wt for src, wt in incoming.get(pid, []))
            val = (1.0 - DAMPING) * base_map.get(pid, 0.0) + DAMPING * total
            new_scores[pid] = val
            max_diff = max(max_diff, abs(val - scores[pid]))
        scores = new_scores
        if max_diff < TOL:
            break
    return pd.Series(scores)


def rank_metrics(main_scores: pd.Series, var_scores: pd.Series,
                 core_ids: set, titles: Dict[str, str]) -> dict:
    """对比某变体排序与 Main 排序，返回各指标 + 变动最大3篇。"""
    df = pd.DataFrame({"main": main_scores, "var": var_scores}).dropna()
    sp_all = spearmanr(df["main"], df["var"]).statistic
    core_df = df[df.index.isin(core_ids)]
    sp_core = spearmanr(core_df["main"], core_df["var"]).statistic if len(core_df) > 2 else np.nan
    rank_main = df["main"].rank(ascending=False, method="average")
    rank_var = df["var"].rank(ascending=False, method="average")
    delta = (rank_main - rank_var).abs()
    top10_m = set(df["main"].nlargest(10).index); top10_v = set(df["var"].nlargest(10).index)
    top5_m = set(df["main"].nlargest(5).index); top5_v = set(df["var"].nlargest(5).index)
    change = (rank_main - rank_var)
    biggest = change.abs().nlargest(3).index
    cases = [f"{titles.get(pid, pid)[:40]} (rank {int(rank_main[pid])}->{int(rank_var[pid])})"
             for pid in biggest]
    return {
        "Spearman_all": round(float(sp_all), 4) if pd.notna(sp_all) else np.nan,
        "Spearman_core": round(float(sp_core), 4) if pd.notna(sp_core) else np.nan,
        "Top10_overlap": len(top10_m & top10_v),
        "Top5_overlap": len(top5_m & top5_v),
        "avg_rank_change": round(float(delta.mean()), 3),
        "max_rank_change": round(float(delta.max()), 1),
        "top3_changed_papers": " ; ".join(cases),
    }


def validate_columns(df: pd.DataFrame, required: List[str], name: str) -> None:
    """输入列完整性校验，缺列时给出清晰报错。"""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"[{name}] 缺少必要列: {missing}\n现有列: {list(df.columns)}")


# ===========================================================================
# 主流程
# ===========================================================================
def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)

    # ---- 读数据 + 列校验 ----
    edges = pd.read_csv(EDGE_PATH)
    papers_raw = pd.read_csv(PAPER_PATH)
    years = pd.read_csv(YEAR_PATH)

    validate_columns(edges, ["edge_id", "source_id", "target_id", "section",
                             "sentiment", "relevance", "shared_authors_count",
                             "has_llm_score"], "semantic_edge_weights_final.csv")
    validate_columns(papers_raw, ["OpenAlex_ID", "Title", "Global_Citations", "Is_Core"],
                     "all_connected_papers.csv")
    validate_columns(years, ["Clean_ID", "Publication_Year"], "node_publication_years.csv")

    has_wfull = "w_full_final" in edges.columns  # 自检可选，缺列则跳过

    # 节点：clean id + base_value(归一化 Global_Citations)
    papers = papers_raw.copy()
    papers["paper_id"] = papers["OpenAlex_ID"].astype(str).str.split("/").str[-1]
    papers["title"] = papers["Title"].fillna("").astype(str)
    gc = pd.to_numeric(papers["Global_Citations"], errors="coerce").fillna(0.0)
    if gc.max() > gc.min():
        papers["base_value"] = (gc - gc.min()) / (gc.max() - gc.min())
    else:
        papers["base_value"] = 1.0
    if papers["base_value"].sum() == 0:
        papers["base_value"] = 1.0
    papers["is_core"] = to_bool(papers["Is_Core"])
    core_ids = set(papers.loc[papers["is_core"], "paper_id"])
    titles = dict(zip(papers["paper_id"], papers["title"]))

    # 边字段稳健化
    edges["has_llm_score_bool"] = to_bool(edges["has_llm_score"])
    edges["shared_authors_count"] = pd.to_numeric(edges["shared_authors_count"], errors="coerce").fillna(0).astype(int)

    # 年份映射 + Δt（缺失填 2020，并统计触发次数）
    year_map = dict(zip(years["Clean_ID"].astype(str), pd.to_numeric(years["Publication_Year"], errors="coerce")))
    src_year_raw = edges["source_id"].map(year_map)
    tgt_year_raw = edges["target_id"].map(year_map)
    n_year_fallback = int(src_year_raw.isna().sum() + tgt_year_raw.isna().sum())
    src_year = src_year_raw.fillna(FILL_YEAR)
    tgt_year = tgt_year_raw.fillna(FILL_YEAR)
    edges["delta_t"] = (src_year - tgt_year).clip(lower=0)

    # 重复边检查（仅提示，不影响）
    n_dup = int(edges.duplicated(subset=["source_id", "target_id"]).sum())

    print(f"边数={len(edges)}  论文数={len(papers)}  核心={len(core_ids)}")
    print(f"有LLM分边={int(edges['has_llm_score_bool'].sum())}  自引边={int((edges['shared_authors_count']>0).sum())}")
    print(f"年份缺失触发fallback(填{FILL_YEAR})的端点数={n_year_fallback}  重复边数={n_dup}\n")

    # ---- 计算 MAIN 排序（基准）----
    q_main = compute_q(edges, MAIN_SECTION_WEIGHTS)
    tau_main = compute_tau(edges["delta_t"], MAIN_TIME_BIAS)
    rho_main = compute_rho(edges["shared_authors_count"], MAIN_ETA_A)
    edges_main = edges.copy()
    edges_main["w_full"] = q_main * tau_main * rho_main
    main_scores = run_weighted_pagerank(papers, edges_main, "w_full")

    # ---- 自检（若文件含 w_full_final）----
    if has_wfull:
        ec = edges.copy()
        ec["w_file"] = pd.to_numeric(edges["w_full_final"], errors="coerce").fillna(0.0)
        check_scores = run_weighted_pagerank(papers, ec, "w_file")
        sp_check = spearmanr(main_scores, check_scores).statistic
        print(f"[自检] 重算Main vs 文件w_full_final 排序 Spearman = {sp_check:.4f} (应≈1.0)\n")
    else:
        sp_check = None
        print("[自检] 文件无 w_full_final 列，跳过自检。\n")

    # ---- 输出 Main 基准排序（复核用）----
    main_rank_df = (
        pd.DataFrame({"paper_id": main_scores.index, "main_score": main_scores.values})
        .merge(papers[["paper_id", "title", "is_core"]], on="paper_id", how="left")
        .sort_values("main_score", ascending=False)
        .reset_index(drop=True)
    )
    main_rank_df.insert(0, "rank", np.arange(1, len(main_rank_df) + 1))
    main_rank_df.to_csv(RESULTS / "sens_main_ranking.csv", index=False, encoding="utf-8-sig")

    # ============================================================
    # 组1：section 权重敏感性
    # ============================================================
    rows = []
    for name, wmap in SECTION_VARIANTS.items():
        q = compute_q(edges, wmap)
        e = edges.copy()
        e["w_full"] = q * tau_main * rho_main      # 只改 section
        sc = run_weighted_pagerank(papers, e, "w_full")
        rows.append({"variant": name, **rank_metrics(main_scores, sc, core_ids, titles)})
    sec_df = pd.DataFrame(rows)
    sec_df.to_csv(RESULTS / "sens_section.csv", index=False, encoding="utf-8-sig")
    print("=== 组1 section 权重敏感性 ===")
    print(sec_df[["variant", "Spearman_all", "Spearman_core", "Top10_overlap", "Top5_overlap", "max_rank_change"]].to_string(index=False), "\n")

    # ============================================================
    # 组2：时间衰减 TIME_BIAS 敏感性
    # ============================================================
    rows = []
    for name, tb in TIME_BIAS_VARIANTS.items():
        tau = compute_tau(edges["delta_t"], tb)
        e = edges.copy()
        e["w_full"] = q_main * tau * rho_main      # 只改 tau
        sc = run_weighted_pagerank(papers, e, "w_full")
        rows.append({"variant": name, **rank_metrics(main_scores, sc, core_ids, titles)})
    time_df = pd.DataFrame(rows)
    time_df.to_csv(RESULTS / "sens_time.csv", index=False, encoding="utf-8-sig")
    print("=== 组2 时间衰减 TIME_BIAS 敏感性 ===")
    print(time_df[["variant", "Spearman_all", "Spearman_core", "Top10_overlap", "Top5_overlap", "max_rank_change"]].to_string(index=False), "\n")

    # ============================================================
    # 组3：关系惩罚 ETA_A 敏感性
    # ============================================================
    rows = []
    for name, ea in ETA_A_VARIANTS.items():
        rho = compute_rho(edges["shared_authors_count"], ea)
        e = edges.copy()
        e["w_full"] = q_main * tau_main * rho      # 只改 rho
        sc = run_weighted_pagerank(papers, e, "w_full")
        rows.append({"variant": name, **rank_metrics(main_scores, sc, core_ids, titles)})
    rel_df = pd.DataFrame(rows)
    rel_df.to_csv(RESULTS / "sens_relation.csv", index=False, encoding="utf-8-sig")
    print("=== 组3 关系惩罚 ETA_A 敏感性 ===")
    print(rel_df[["variant", "Spearman_all", "Spearman_core", "Top10_overlap", "Top5_overlap", "max_rank_change"]].to_string(index=False), "\n")

    # ---- 案例汇总 ----
    cases = []
    for group, df in [("section", sec_df), ("time", time_df), ("relation", rel_df)]:
        for _, r in df.iterrows():
            if str(r["variant"]).startswith("Main"):
                continue
            cases.append({"group": group, "variant": r["variant"],
                          "top3_changed_papers": r["top3_changed_papers"]})
    pd.DataFrame(cases).to_csv(RESULTS / "sens_rank_change_cases.csv", index=False, encoding="utf-8-sig")

    # ---- 汇总 md ----
    def md(df):
        cols = ["variant", "Spearman_all", "Spearman_core", "Top10_overlap", "Top5_overlap", "avg_rank_change", "max_rank_change"]
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for _, r in df.iterrows():
            lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
        return "\n".join(lines)

    summary = [
        "# 参数敏感性分析汇总（基于代码真实设定 run_experiments.py）",
        "",
        f"- 边数 {len(edges)}，论文 {len(papers)}，核心论文 {len(core_ids)}",
        f"- 有 LLM 语义分的边 {int(edges['has_llm_score_bool'].sum())}，自引边 {int((edges['shared_authors_count']>0).sum())}",
        f"- 年份 fallback 端点数 {n_year_fallback}（填 {FILL_YEAR}）；重复边 {n_dup}",
        (f"- 自检：重算 Main vs 文件 w_full_final 排序 Spearman = {sp_check:.4f}（应≈1.0，验证重算公式与已存边权一致）"
         if sp_check is not None else "- 自检：文件无 w_full_final 列，已跳过"),
        "",
        "## 组1：section 位置权重",
        "（Theory-strong=论文原版含 Other=1.0 混合效应；Theory-strong-fixed=Other 保持 0.2 的纯区分度对照）",
        "", md(sec_df), "",
        "## 组2：时间衰减 TIME_BIAS（tau=TIME_BIAS/(TIME_BIAS+Δt)）", "", md(time_df), "",
        "## 组3：关系惩罚 ETA_A（rho=1/(1+ETA_A·shared)）", "", md(rel_df), "",
        "## 判读标准",
        "- Equal / no_decay / no_penalty 三个“关模块”组若 Spearman 仍 >0.95，说明核心排序不依赖该模块；",
        "  其中 Equal 组（取消 section 影响）若仍高度一致，可正面化解 section 标注准确率偏低的质疑。",
        "- Top-10 / Top-5 overlap 高且 max_rank_change 小 → 头部高价值论文稳定。",
        "- 若某组 Spearman <0.9，需如实报告并结合 top3_changed_papers 说明哪些论文、为何变动。",
        "",
        "## 设计说明（回应代码审核）",
        "- 悬垂节点未做均匀再分配、年份缺失填 2020：均刻意与 run_experiments.py 主实验保持一致，",
        "  以保证 Main 排序等同正文表 5；敏感性分析的目的是同一模型下换参数，而非构造更优模型。",
        "- 本实验为排序稳定性分析，无分类标签，故无混淆矩阵；混淆矩阵属于功能分类 benchmark(SciCite/ACL-ARC)。",
    ]
    (RESULTS / "sens_summary.md").write_text("\n".join(summary), encoding="utf-8")

    print(f"全部完成，结果写入 {RESULTS}/")
    print("  sens_section.csv / sens_time.csv / sens_relation.csv")
    print("  sens_main_ranking.csv / sens_rank_change_cases.csv / sens_summary.md")


if __name__ == "__main__":
    main()
