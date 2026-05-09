import pandas as pd
import networkx as nx
from collections import defaultdict
import os

# =====================================================================
# [1] 工具函数：数据清洗
# =====================================================================
def clean_id(url_or_id):
    """
    清洗传入的 ID：
    如果是带有 URL 的 (如 https://openalex.org/W123)，剥离前缀仅保留 W123。
    如果是纯 ID，直接返回。
    """
    if pd.isna(url_or_id) or str(url_or_id).strip() == "":
        return None
    # 取 URL 的最后一部分
    return str(url_or_id).split('/')[-1].strip()

# =====================================================================
# [2] 核心主程序
# =====================================================================
def build_information_fusion_hin():
    print("==================================================")
    print("🕸️ 开始构建 Information Fusion 异构信息网络 (HIN)")
    print("==================================================")

    # --- 1. 读取数据 ---
    try:
        edges_df = pd.read_csv("all_network_edges.csv")
        authorships_df = pd.read_csv("authorships_network.csv")
        print(f"📄 成功加载 {len(edges_df)} 条同构引用边，{len(authorships_df)} 条异构关系记录。")
    except FileNotFoundError as e:
        print(f"❌ 找不到文件: {e}")
        return

    # --- 2. 构建超高速哈希字典 (O(1) 查询) ---
    print("\n⚡ 正在构建哈希索引字典，用于加速自引检测...")
    paper_to_authors = defaultdict(set)
    paper_to_insts = defaultdict(set)

    # --- 3. 初始化有向图 ---
    HIN = nx.DiGraph()

    # --- 4. 载入异构关系：处理作者与机构 ---
    print("🧠 正在融合 [论文-作者-机构] 异构拓扑特征...")
    
    # 清洗 authorships 数据集中的空作者
    authorships_df = authorships_df.dropna(subset=['Author_ID'])

    for _, row in authorships_df.iterrows():
        # 获取清洗后的纯 ID
        p_raw = clean_id(row['Paper_ID'])
        a_raw = clean_id(row['Author_ID'])
        if not p_raw or not a_raw: 
            continue

        # 加上规范前缀
        p_node = f"P_{p_raw}"
        a_node = f"A_{a_raw}"

        # 1. 建立作者和论文节点
        HIN.add_node(p_node, node_type="paper")
        HIN.add_node(a_node, node_type="author", name=str(row['Author_Name']))

        # 2. 建立 P -> A 撰写边
        HIN.add_edge(p_node, a_node, 
                     edge_type="written_by",
                     author_position=str(row['Author_Position']),
                     is_corresponding=bool(row['Is_Corresponding']))
        
        # 记录哈希字典，方便后续算交集
        paper_to_authors[p_raw].add(a_raw)

        # 3. 处理机构信息 (可能存在多个，以 '|' 分隔)
        inst_str = str(row['Institution_IDs'])
        if inst_str and inst_str.lower() not in ['none', 'nan']:
            inst_list = [i.strip() for i in inst_str.split('|') if i.strip()]
            for i_raw in inst_list:
                i_node = f"I_{i_raw}"
                
                # 建立机构节点
                HIN.add_node(i_node, node_type="institution")
                
                # 建立 A -> I 隶属边
                HIN.add_edge(a_node, i_node, edge_type="affiliated_with")
                
                # 记录哈希字典，将机构也映射到论文上（说明该论文挂靠了此机构）
                paper_to_insts[p_raw].add(i_raw)

    # --- 5. 载入同构关系：处理论文引用并计算“学术裙带惩罚特征” ---
    print("\n🔍 正在处理 [论文-论文] 引用网络，并提取自引惩罚特征...")
    
    enhanced_edges_data = []

    for _, row in edges_df.iterrows():
        # 清洗 Source 和 Target
        s_raw = clean_id(row['Source'])
        t_raw = clean_id(row['Target'])
        if not s_raw or not t_raw: 
            continue

        s_node = f"P_{s_raw}"
        t_node = f"P_{t_raw}"

        # 确保节点在图中存在（防止有些论文没有作者信息）
        HIN.add_node(s_node, node_type="paper")
        HIN.add_node(t_node, node_type="paper")

        # 🚀 核心逻辑：利用哈希集合的高速交集运算 (Intersection)
        s_authors = paper_to_authors[s_raw]
        t_authors = paper_to_authors[t_raw]
        shared_authors = s_authors.intersection(t_authors)

        s_insts = paper_to_insts[s_raw]
        t_insts = paper_to_insts[t_raw]
        shared_insts = s_insts.intersection(t_insts)

        # 计算附加属性 (转成标准的 Python 布尔和整型，防止 GraphML 导出报错)
        is_auth_self_cite = bool(len(shared_authors) > 0)
        is_inst_self_cite = bool(len(shared_insts) > 0)
        shared_auth_count = int(len(shared_authors))

        # 建立 P -> P 引用边
        HIN.add_edge(s_node, t_node, 
                     edge_type="cites",
                     is_author_self_cite=is_auth_self_cite,
                     is_inst_self_cite=is_inst_self_cite,
                     shared_authors_count=shared_auth_count)

        # 收集增强后的边信息，留给后续 PageRank 使用
        enhanced_edges_data.append({
            "Source": row['Source'],  # 保留原始带有URL的ID方便溯源
            "Target": row['Target'],
            "Source_Clean": s_raw,
            "Target_Clean": t_raw,
            "is_author_self_cite": is_auth_self_cite,
            "is_inst_self_cite": is_inst_self_cite,
            "shared_authors_count": shared_auth_count
        })

    # --- 6. 数据导出与统计 ---
    print("\n💾 正在导出异构信息网络与增强特征...")
    
    # 导出为 GraphML (可直接导入 Gephi 渲染图谱)
    graphml_path = "HIN_network.graphml"
    nx.write_graphml(HIN, graphml_path)

    # 导出包含惩罚特征的增强型边列表
    enhanced_csv_path = "enhanced_paper_edges.csv"
    df_enhanced = pd.DataFrame(enhanced_edges_data)
    df_enhanced.to_csv(enhanced_csv_path, index=False, encoding="utf-8-sig")

    # 统计信息
    nodes_count = HIN.number_of_nodes()
    edges_count = HIN.number_of_edges()
    self_cites = df_enhanced['is_author_self_cite'].sum()
    inst_cites = df_enhanced['is_inst_self_cite'].sum()

    print("==================================================")
    print("🎉 异构网络构建大功告成！")
    print(f"📍 图谱总节点数 : {nodes_count}")
    print(f"📍 图谱总连边数 : {edges_count}")
    print(f"🚨 发现作者自引 : {self_cites} 条")
    print(f"🚨 发现机构互引 : {inst_cites} 条")
    print("--------------------------------------------------")
    print(f"📁 异构网络图谱已保存至: {graphml_path}")
    print(f"📁 惩罚特征边表已保存至: {enhanced_csv_path} (供后续 PageRank 降权使用)")
    print("==================================================")

if __name__ == "__main__":
    build_information_fusion_hin()