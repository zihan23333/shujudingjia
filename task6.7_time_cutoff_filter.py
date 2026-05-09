import pandas as pd

# =====================================================================
# [1] 配置区
# =====================================================================
CUTOFF_YEAR = 2021

EDGES_FILE = "enhanced_paper_edges.csv"
YEARS_FILE = "node_publication_years.csv"
LLM_FILE = "llm_results.csv"  # 你的原始大模型打分文件

OUTPUT_HIST_EDGES = f"historical_edges_until_{CUTOFF_YEAR}.csv"
OUTPUT_HIST_LLM = f"historical_llm_until_{CUTOFF_YEAR}.csv"
# =====================================================================

def clean_id(url_or_id):
    if pd.isna(url_or_id) or not str(url_or_id).strip():
        return None
    return str(url_or_id).split('/')[-1].strip()

def run_time_cutoff():
    print("==================================================")
    print(f"🔪 任务启动：执行 {CUTOFF_YEAR} 年时间截断 (防止 Data Leakage)")
    print("==================================================")

    # 1. 加载时间锚点字典
    try:
        df_years = pd.read_csv(YEARS_FILE)
        # 过滤掉没有年份的异常节点
        df_years = df_years.dropna(subset=['Publication_Year'])
        year_dict = dict(zip(df_years['Clean_ID'], df_years['Publication_Year']))
        print(f"✅ 成功加载 {len(year_dict)} 个节点的时间锚点。")
    except Exception as e:
        print(f"❌ 读取年份文件失败: {e}")
        return

    # 2. 处理网络边 (Citation Edges)
    try:
        df_edges = pd.read_csv(EDGES_FILE)
        total_edges_before = len(df_edges)
        
        # 映射施引论文(Source)的发表年份
        df_edges['Citing_Year'] = df_edges['Source_Clean'].map(year_dict)
        
        # 剔除找不到年份的边
        df_edges = df_edges.dropna(subset=['Citing_Year'])
        df_edges['Citing_Year'] = df_edges['Citing_Year'].astype(int)
        
        # 执行截断！
        df_edges_hist = df_edges[df_edges['Citing_Year'] <= CUTOFF_YEAR]
        df_edges_future = df_edges[df_edges['Citing_Year'] > CUTOFF_YEAR]
        
        hist_edges_count = len(df_edges_hist)
        leakage_edges_count = len(df_edges_future)
        
        # 保存纯净的历史边
        df_edges_hist.to_csv(OUTPUT_HIST_EDGES, index=False, encoding='utf-8-sig')
        
    except Exception as e:
        print(f"❌ 处理网络边失败: {e}")
        return

    # 3. 处理 LLM 语义评分表
    try:
        df_llm = pd.read_csv(LLM_FILE)
        total_llm_before = len(df_llm)
        
        # 提取 Source Clean ID 并映射年份
        df_llm['Source_Clean'] = df_llm['Source_ID'].apply(clean_id)
        df_llm['Citing_Year'] = df_llm['Source_Clean'].map(year_dict)
        df_llm = df_llm.dropna(subset=['Citing_Year'])
        df_llm['Citing_Year'] = df_llm['Citing_Year'].astype(int)
        
        # 执行截断！
        df_llm_hist = df_llm[df_llm['Citing_Year'] <= CUTOFF_YEAR]
        df_llm_future = df_llm[df_llm['Citing_Year'] > CUTOFF_YEAR]
        
        hist_llm_count = len(df_llm_hist)
        leakage_llm_count = len(df_llm_future)
        
        # 保存纯净的历史 LLM 分数
        df_llm_hist.to_csv(OUTPUT_HIST_LLM, index=False, encoding='utf-8-sig')
        
    except Exception as e:
        print(f"❌ 处理 LLM 文件失败: {e}")
        return

    # 4. 打印诊断战报
    print("\n📊 【防泄露诊断报告】")
    print("-" * 50)
    print(f"🔗 全量引用边总数: {total_edges_before}")
    print(f"   🟢 <= {CUTOFF_YEAR} 的历史边 (留用): {hist_edges_count}")
    print(f"   🔴 >  {CUTOFF_YEAR} 的未来边 (剔除): {leakage_edges_count}")
    print(f"   ⚠️ 历史网络存活率: {hist_edges_count/total_edges_before*100:.1f}%\n")
    
    print(f"🤖 全量 LLM 评分边数: {total_llm_before}")
    print(f"   🟢 <= {CUTOFF_YEAR} 的历史评分 (留用): {hist_llm_count}")
    print(f"   🔴 >  {CUTOFF_YEAR} 的未来评分 (剔除): {leakage_llm_count}")
    print("-" * 50)
    print(f"💾 数据已清洗并保存至:\n  1. {OUTPUT_HIST_EDGES}\n  2. {OUTPUT_HIST_LLM}")
    print("==================================================")
    print("🎉 完美消除 Future Leakage！现在你可以用这两份文件去算历史 PageRank 了。")

if __name__ == "__main__":
    run_time_cutoff()