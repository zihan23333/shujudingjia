# -*- coding: utf-8 -*-
"""
=======================================================================================
Task 6.3: Self-Citation Penalty & Weighted PageRank Recalculation

Flow:
1. Read enhanced_paper_edges.csv (contains self-citation flags)
2. Read llm_results.csv (contains original λ_ji = Weight_Combined)
3. Compute penalty factor penalty_ji:
   - If is_author_self_cite=True, use continuous penalty: penalty = 1 / (1 + shared_authors_count)
   - Otherwise penalty = 1.0
4. Compute final weight: λ_ji_final = λ_ji × penalty_ji
5. Rerun weighted PageRank to compute new Q(i)
6. Compare ranking changes before and after penalty

=======================================================================================
"""

import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import spearmanr
import re
import sys
import io
from collections import defaultdict

# Set UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# =====================================================================
# [1] 工具函数
# =====================================================================

def extract_clean_id(url_or_id):
    """从 URL 中提取 clean ID (如 W123456)"""
    if pd.isna(url_or_id) or str(url_or_id).strip() == "":
        return None
    return str(url_or_id).split('/')[-1].strip()

def normalize_series(series):
    """Min-Max 归一化"""
    values = pd.to_numeric(series, errors='coerce').fillna(0.0)
    min_val = values.min()
    max_val = values.max()
    if max_val > min_val:
        return (values - min_val) / (max_val - min_val)
    return pd.Series(np.zeros(len(values)), index=values.index)

# =====================================================================
# [2] 主程序
# =====================================================================

print("=" * 90)
print("Step 3-5: Self-Citation Penalty + Weighted PageRank Recalculation")
print("=" * 90)

# --- 读取所需数据 ---
try:
    # 跨文件夹读取数据
    enhanced_edges = pd.read_csv("enhanced_paper_edges.csv")
    
    # 从原始工作目录读取 llm_results
    llm_results = pd.read_csv("../数据定价/llm_results.csv")
    all_papers = pd.read_csv("../数据定价/all_connected_papers.csv")
    all_edges = pd.read_csv("../数据定价/all_network_edges.csv")
    
    print(f"[OK] Loaded {len(enhanced_edges)} enhanced edges")
    print(f"[OK] Loaded {len(llm_results)} LLM scoring records")
    print(f"[OK] Loaded {len(all_papers)} papers and {len(all_edges)} edges")
except FileNotFoundError as e:
    print(f"[ERROR] File loading failed: {e}")
    exit(1)

# =====================================================================
# [3] 第三步：计算自引用惩罚因子
# =====================================================================
print("\n[Step 3] Computing self-citation penalty factors...")

# 建立映射字典：(Source_CleanID, Target_CleanID) -> 自引用信息
self_cite_features = {}
for _, row in enhanced_edges.iterrows():
    s_clean = row['Source_Clean']
    t_clean = row['Target_Clean']
    is_author_self_cite = row['is_author_self_cite']
    shared_authors_count = row['shared_authors_count']
    
    # 键为清洁ID对
    key = (s_clean, t_clean)
    
    # 计算惩罚因子：用连续的形式
    # 如果有共同作者，penalty = 1 / (1 + |共同作者数|)
    # 否则 penalty = 1.0
    if is_author_self_cite and shared_authors_count > 0:
        penalty = 1.0 / (1.0 + shared_authors_count)
    else:
        penalty = 1.0
    
    self_cite_features[key] = {
        'is_author_self_cite': is_author_self_cite,
        'shared_authors_count': shared_authors_count,
        'penalty': penalty
    }

print(f"   Generated penalty features for {len(self_cite_features)} edges")
self_cite_count = sum(1 for v in self_cite_features.values() if v['is_author_self_cite'])
print(f"   Found {self_cite_count} self-citation edges (penalty < 1.0)")

# =====================================================================
# [4] 第四步：将惩罚因子融入 λ
# =====================================================================
print("\n[Step 4] Fusing penalty factor into citation quality λ...")

# 清洁化 llm_results 和 all_edges
llm_results['Source_ID'] = llm_results['Source_ID'].apply(extract_clean_id)
llm_results['Target_ID'] = llm_results['Target_ID'].apply(extract_clean_id)
all_edges['Source'] = all_edges['Source'].apply(extract_clean_id)
all_edges['Target'] = all_edges['Target'].apply(extract_clean_id)

# 建立原始权重字典
llm_map_original = {}
for _, row in llm_results.iterrows():
    s_clean = row['Source_ID']
    t_clean = row['Target_ID']
    weight_combined = float(row['Weight_Combined'])
    key = (s_clean, t_clean)
    llm_map_original[key] = weight_combined

print(f"   Built original λ dictionary for {len(llm_map_original)} edges")

# 计算带惩罚的新 λ
llm_map_penalized = {}
for (s_clean, t_clean), lambda_original in llm_map_original.items():
    penalty = self_cite_features.get((s_clean, t_clean), {}).get('penalty', 1.0)
    lambda_penalized = lambda_original * penalty
    llm_map_penalized[(s_clean, t_clean)] = lambda_penalized

# 统计权重变化
weight_changes = []
for key in llm_map_original.keys():
    orig = llm_map_original[key]
    pena = llm_map_penalized[key]
    if pena != orig:
        weight_changes.append((key, orig, pena, (orig - pena) / orig * 100))

print(f"   {len(weight_changes)} edges weights adjusted (self-citation detected)")
if weight_changes:
    avg_reduction = np.mean([w[3] for w in weight_changes])
    max_reduction = np.max([w[3] for w in weight_changes])
    print(f"   Average weight reduction: {avg_reduction:.2f}%")
    print(f"   Max weight reduction: {max_reduction:.2f}%")

# =====================================================================
# [5] 第五步：重新运行加权 PageRank
# =====================================================================
print("\n[Step 5] Rerunning weighted PageRank (using penalized λ)...")

# 获取核心论文集合
core_papers = set(all_papers[all_papers['Is_Core'] == True]['OpenAlex_ID'].apply(extract_clean_id))

# 参数配置（与原始 task4 一致）
DAMPING_FACTOR = 0.85
TIMELINESS_BIAS = 5.0
MAX_ITER = 200
TOL = 1e-9
UNSCORED_PENALTY_WEIGHT = 0.3

# Prepare papers data
papers = all_papers.copy()
papers['OpenAlex_ID'] = papers['OpenAlex_ID'].apply(extract_clean_id)
title_dict = dict(zip(papers['OpenAlex_ID'], papers['Title']))

# Use default year 2020 for all papers (year info not available in this CSV)
year_dict = {pid: 2020 for pid in papers['OpenAlex_ID']}

# --- Computing time-decay weights (time_decay factor) ---
print("   Step 1: Computing time-decay weights...")
raw_weights_penalized = []
for _, row in all_edges.iterrows():
    u = row['Source']
    v = row['Target']
    
    # Use penalized lambda
    quality_weight = llm_map_penalized.get((u, v), UNSCORED_PENALTY_WEIGHT)
    
    # Time decay calculation
    y_j = year_dict.get(u, 2020)
    y_i = year_dict.get(v, 2020)
    year_diff = max(0, y_j - y_i)
    time_decay = 1.0 / (year_diff + 1.0 + TIMELINESS_BIAS)
    
    raw_weights_penalized.append(float(quality_weight) * time_decay)

all_edges['Raw_Weight_Penalized'] = raw_weights_penalized

# --- Normalize weights (w_ji) ---
print("   Step 2: Normalizing weights (w_ji)...")
sum_raw = all_edges.groupby('Source')['Raw_Weight_Penalized'].transform('sum')
all_edges['w_ji_penalized'] = all_edges['Raw_Weight_Penalized'] / sum_raw.replace({0.0: 1.0})

# --- Computing F(i): intrinsic quality using Global_Citations ---
print("   Step 3: Computing intrinsic quality F(i)...")
papers['F'] = normalize_series(papers['Global_Citations'].fillna(1.0))
F = dict(zip(papers['OpenAlex_ID'], papers['F']))

# --- Build reverse citation list ---
print("   Step 4: Building reverse citation graph...")
citing_map = defaultdict(list)
for _, row in all_edges.iterrows():
    citing_map[row['Target']].append((row['Source'], row['w_ji_penalized']))

# --- Iterative computation of Q(i) using PageRank formula ---
print(f"   Step 5: Iterating Q(i) (max {MAX_ITER} iterations, tolerance {TOL})...")
Q_penalized = {pid: float(F.get(pid, 1.0)) for pid in papers['OpenAlex_ID']}

for iteration in range(MAX_ITER):
    max_diff = 0.0
    new_Q = {}
    for pid in papers['OpenAlex_ID']:
        incoming = citing_map.get(pid, [])
        total = sum(weight * Q_penalized.get(source, 0.0) for source, weight in incoming)
        new_value = (1 - DAMPING_FACTOR) * F.get(pid, 1.0) + DAMPING_FACTOR * total
        new_Q[pid] = new_value
        max_diff = max(max_diff, abs(new_value - Q_penalized[pid]))
    Q_penalized = new_Q
    if max_diff < TOL:
        break

print(f"   [OK] Iteration complete: {iteration + 1} rounds, max change {max_diff:.2e}")

# =====================================================================
# [6] 对比分析和排名
# =====================================================================
print("\n[Comparison] Ranking changes before and after penalty...")

# Original PageRank (no penalty)
print("   Step A: Computing original PageRank (no penalty)...")
raw_weights_original = []
for _, row in all_edges.iterrows():
    u = row['Source']
    v = row['Target']
    quality_weight = llm_map_original.get((u, v), UNSCORED_PENALTY_WEIGHT)
    y_j = year_dict.get(u, 2020)
    y_i = year_dict.get(v, 2020)
    year_diff = max(0, y_j - y_i)
    time_decay = 1.0 / (year_diff + 1.0 + TIMELINESS_BIAS)
    raw_weights_original.append(float(quality_weight) * time_decay)

all_edges['Raw_Weight_Original'] = raw_weights_original
sum_raw_orig = all_edges.groupby('Source')['Raw_Weight_Original'].transform('sum')
all_edges['w_ji_original'] = all_edges['Raw_Weight_Original'] / sum_raw_orig.replace({0.0: 1.0})

# Build original citing_map for baseline PageRank
citing_map_orig = defaultdict(list)
for _, row in all_edges.iterrows():
    citing_map_orig[row['Target']].append((row['Source'], row['w_ji_original']))

Q_original = {pid: float(F.get(pid, 1.0)) for pid in papers['OpenAlex_ID']}
for iteration in range(MAX_ITER):
    max_diff = 0.0
    new_Q = {}
    for pid in papers['OpenAlex_ID']:
        incoming = citing_map_orig.get(pid, [])
        total = sum(weight * Q_original.get(source, 0.0) for source, weight in incoming)
        new_value = (1 - DAMPING_FACTOR) * F.get(pid, 1.0) + DAMPING_FACTOR * total
        new_Q[pid] = new_value
        max_diff = max(max_diff, abs(new_value - Q_original[pid]))
    Q_original = new_Q
    if max_diff < TOL:
        break

print(f"   [OK] Original PageRank computed")

# 仅针对核心论文进行排名
sorted_original = sorted(
    [(pid, Q_original.get(pid, 0.0)) for pid in core_papers],
    key=lambda x: x[1],
    reverse=True
)
sorted_penalized = sorted(
    [(pid, Q_penalized.get(pid, 0.0)) for pid in core_papers],
    key=lambda x: x[1],
    reverse=True
)

# 计算 Spearman 相关系数
cores_list = list(core_papers)
scores_orig = [Q_original.get(pid, 0.0) for pid in cores_list]
scores_pena = [Q_penalized.get(pid, 0.0) for pid in cores_list]
spearman_corr, _ = spearmanr(scores_orig, scores_pena)

print(f"\n   Spearman rank correlation (original vs penalized): {spearman_corr:.4f}")
print(f"   (Close to 1.0 = minor changes; close to 0 = major changes)")

# =====================================================================
# [7] 输出文件
# =====================================================================
print("\n[Output] Generating result files...")

# 7.1 加罚边表
edges_output = all_edges[[
    'Source', 'Target', 'Raw_Weight_Original', 'w_ji_original',
    'Raw_Weight_Penalized', 'w_ji_penalized'
]].copy()
edges_output.to_csv("weighted_edges_comparison.csv", index=False, encoding='utf-8-sig')
print(f"   weighted_edges_comparison.csv (edge weight comparison)")

# 7.2 加罚前排名
df_original = pd.DataFrame([
    [pid, score, title_dict.get(pid, 'Unknown'), False]
    for pid, score in sorted_original
], columns=['OpenAlex_ID', 'Q_Score_Original', 'Title', 'Affected_by_Penalty'])
df_original['Rank_Original'] = range(1, len(df_original) + 1)

# 7.3 加罚后排名
df_penalized = pd.DataFrame([
    [pid, score, title_dict.get(pid, 'Unknown'), 
     self_cite_features.get((pid, pid), {}).get('is_author_self_cite', False)]
    for pid, score in sorted_penalized
], columns=['OpenAlex_ID', 'Q_Score_Penalized', 'Title', 'Has_Self_Citation'])
df_penalized['Rank_Penalized'] = range(1, len(df_penalized) + 1)

# 7.4 合并两个排名表
comparison_df = df_original[['OpenAlex_ID', 'Q_Score_Original', 'Rank_Original', 'Title']].copy()
comparison_df = comparison_df.merge(
    df_penalized[['OpenAlex_ID', 'Q_Score_Penalized', 'Rank_Penalized', 'Has_Self_Citation']],
    on='OpenAlex_ID',
    how='left'
)
comparison_df['Rank_Change'] = comparison_df['Rank_Original'] - comparison_df['Rank_Penalized']
comparison_df['Score_Change_Percent'] = (
    (comparison_df['Q_Score_Penalized'] - comparison_df['Q_Score_Original']) / 
    comparison_df['Q_Score_Original'] * 100
).fillna(0)

comparison_df = comparison_df.sort_values('Rank_Penalized')
comparison_df.to_csv("ranking_comparison_detailed.csv", index=False, encoding='utf-8-sig')
print(f"   ranking_comparison_detailed.csv (detailed ranking comparison)")

# 7.5 新的加权 PageRank 结果
weighted_ranking = df_penalized[['OpenAlex_ID', 'Q_Score_Penalized', 'Title', 'Rank_Penalized']].copy()
weighted_ranking.columns = ['OpenAlex_ID', 'Q_Score', 'Title', 'Rank']
weighted_ranking.to_csv("weighted_pagerank_ranking_with_penalty.csv", index=False, encoding='utf-8-sig')
print(f"   weighted_pagerank_ranking_with_penalty.csv (final weighted ranking)")

# =====================================================================
# [8] 统计报告
# =====================================================================
print("\n" + "=" * 90)
print("STATISTICS SUMMARY")
print("=" * 90)

print("\n[Self-Citation Statistics]")
self_cite_edges = [v for v in self_cite_features.values() if v['is_author_self_cite']]
print(f"  Total self-citation edges: {len(self_cite_edges)}")
print(f"  Self-citation ratio: {len(self_cite_edges) / len(self_cite_features) * 100:.2f}%")

if self_cite_edges:
    shared_counts = [v['shared_authors_count'] for v in self_cite_edges]
    print(f"  Average shared authors: {np.mean(shared_counts):.2f}")
    print(f"  Max shared authors: {np.max(shared_counts)}")

print("\n[Weight Impact Analysis]")
print(f"  Adjusted edges: {len(weight_changes)}")
print(f"  Affected papers: {len(comparison_df[comparison_df['Rank_Change'] != 0])}")

# Top affected papers (largest rank drops)
top_affected = comparison_df.nlargest(5, 'Rank_Change')
if len(top_affected) > 0:
    print(f"\n  TOP 5 PAPERS WITH MOST RANKING CHANGE:")
    for idx, (_, row) in enumerate(top_affected.iterrows(), 1):
        print(f"     {idx}. {row['Title'][:50]}")
        print(f"        Rank: {row['Rank_Original']:.0f} -> {row['Rank_Penalized']:.0f} (delta: {row['Rank_Change']:.0f})")
        print(f"        Score: {row['Q_Score_Original']:.6f} -> {row['Q_Score_Penalized']:.6f} ({row['Score_Change_Percent']:.2f}%)")

# Stable rankings
stable = comparison_df[comparison_df['Rank_Change'] == 0]
print(f"\n  UNCHANGED PAPERS: {len(stable)}")

print("\n[Correlation Analysis]")
print(f"  Spearman rank correlation: {spearman_corr:.4f}")
print(f"    (1.0 = identical, 0.9+ = highly correlated, < 0.7 = significant change)")

print("\n" + "=" * 90)
print("DONE! All results saved to CSV files in current directory")
print("=" * 90)
