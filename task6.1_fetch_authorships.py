import pandas as pd
import requests
import time
from tqdm import tqdm
import math

# =====================================================================
# [1] 核心配置区
# =====================================================================
INPUT_FILE = "all_connected_papers.csv"
OUTPUT_FILE = "authorships_network.csv"

# 🛑 务必替换为你自己的真实邮箱，以进入 OpenAlex 礼貌池（响应快10倍且不易被封）
YOUR_EMAIL = "x768466345@gmail.com"  

# OpenAlex 限制单个 filter 查询最多包含 50 个使用 '|' 分隔的 ID
CHUNK_SIZE = 50 
# =====================================================================

def clean_id(url_or_id):
    """
    清洗工具：剥离 'https://openalex.org/' 前缀，仅保留纯 ID 字符串
    """
    if pd.isna(url_or_id) or not str(url_or_id).strip():
        return None
    return str(url_or_id).split('/')[-1]

def fetch_authorships():
    print("==================================================")
    print("🌐 任务启动：OpenAlex 异构网络元数据批量获取")
    print("==================================================")

    # 1. 读取原数据，提取并清洗 ID
    try:
        df_papers = pd.read_csv(INPUT_FILE)
        raw_ids = df_papers['OpenAlex_ID'].dropna().unique().tolist()
        clean_ids = [clean_id(pid) for pid in raw_ids if clean_id(pid)]
        print(f"📄 成功读取 {len(clean_ids)} 个唯一论文 ID，准备分批请求 API...")
    except FileNotFoundError:
        print(f"❌ 找不到文件 {INPUT_FILE}，请检查路径。")
        return

    # 2. 分块处理 (Chunking)
    chunks = [clean_ids[i:i + CHUNK_SIZE] for i in range(0, len(clean_ids), CHUNK_SIZE)]
    
    extracted_data = []
    
    # 3. 带着进度条遍历批次
    print("\n🚀 正在向 OpenAlex 发起批量请求...")
    for chunk in tqdm(chunks, desc="获取进度", unit="批次"):
        # 拼接批量查询 filter，如 openalex:W123|W456|W789
        filter_str = "openalex:" + "|".join(chunk)
        
        url = "https://api.openalex.org/works"
        params = {
            "filter": filter_str,
            "mailto": YOUR_EMAIL,
            "per-page": CHUNK_SIZE  # 确保一页能装下整个 Chunk
        }
        
        try:
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                works = data.get("results", [])
                
                # 遍历返回的每一篇论文
                for work in works:
                    paper_id = clean_id(work.get("id"))
                    authorships = work.get("authorships", [])
                    
                    # 遍历该论文下的所有作者记录
                    for auth in authorships:
                        # 提取作者基本信息
                        author_info = auth.get("author", {})
                        author_id = clean_id(author_info.get("id"))
                        author_name = author_info.get("display_name")
                        
                        author_position = auth.get("author_position")
                        is_corresponding = auth.get("is_corresponding", False)
                        
                        # 提取挂靠机构信息
                        institutions = auth.get("institutions", [])
                        if institutions:
                            inst_ids = "|".join([clean_id(i.get("id")) for i in institutions if i.get("id")])
                            inst_names = "|".join([i.get("display_name", "") for i in institutions if i.get("display_name")])
                        else:
                            inst_ids = "None"
                            inst_names = "None"
                            
                        # 存入结果列表
                        extracted_data.append({
                            "Paper_ID": paper_id,
                            "Author_ID": author_id,
                            "Author_Name": author_name,
                            "Author_Position": author_position,
                            "Is_Corresponding": is_corresponding,
                            "Institution_IDs": inst_ids,
                            "Institution_Names": inst_names
                        })
            else:
                print(f"\n⚠️ 请求异常: 状态码 {response.status_code}. 跳过当前 {len(chunk)} 个 ID。")
                
        except Exception as e:
            print(f"\n❌ 网络/解析错误: {e}. 跳过当前批次，继续执行。")
            
        # 严格遵守限速规范 (礼貌池限制通常是 10 requests / second)
        time.sleep(0.15) 
        
    # 4. 数据落地
    if extracted_data:
        df_out = pd.DataFrame(extracted_data)
        df_out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        
        print("\n==================================================")
        print("🎉 数据获取成功！")
        print(f"📊 累计提取了 {len(df_out)} 条【作者-论文-机构】关系边。")
        print(f"📁 结果已保存至: {OUTPUT_FILE}")
        print("==================================================")
    else:
        print("\n⚠️ 未获取到任何数据。")

if __name__ == "__main__":
    fetch_authorships()