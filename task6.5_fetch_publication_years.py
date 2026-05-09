import pandas as pd
import requests
import time
from tqdm import tqdm

# =====================================================================
# [1] 核心配置区
# =====================================================================
INPUT_FILE = "all_connected_papers.csv"
OUTPUT_FILE = "node_publication_years.csv"

# 你的 OpenAlex 礼貌池邮箱（与 task6.1 保持一致）
YOUR_EMAIL = "x768466345@gmail.com"  
CHUNK_SIZE = 50 # 每次请求打包的 ID 数量
# =====================================================================

def clean_id(url_or_id):
    """清洗工具：剥离 'https://openalex.org/' 前缀，仅保留纯 ID 字符串"""
    if pd.isna(url_or_id) or not str(url_or_id).strip():
        return None
    return str(url_or_id).split('/')[-1].strip()

def fetch_publication_years():
    print("==================================================")
    print("⏳ 任务启动：获取所有节点的精确发表年份 (Time Anchors)")
    print("==================================================")

    # 1. 读取节点数据
    try:
        df_papers = pd.read_csv(INPUT_FILE)
        raw_ids = df_papers['OpenAlex_ID'].dropna().unique().tolist()
        clean_ids = [clean_id(pid) for pid in raw_ids if clean_id(pid)]
        print(f"📄 成功加载 {len(clean_ids)} 个唯一论文 ID，准备分批请求...")
    except FileNotFoundError:
        print(f"❌ 找不到文件 {INPUT_FILE}，请检查路径。")
        return

    # 2. 对 ID 进行分块打包
    chunks = [clean_ids[i:i + CHUNK_SIZE] for i in range(0, len(clean_ids), CHUNK_SIZE)]
    
    extracted_data = []
    
    # 3. 带着进度条遍历批次请求 OpenAlex
    print("\n🚀 正在向 OpenAlex 发起批量请求提取年份...")
    for chunk in tqdm(chunks, desc="获取进度", unit="批次"):
        filter_str = "openalex:" + "|".join(chunk)
        
        url = "https://api.openalex.org/works"
        # 使用 select 参数减少数据传输量，只要我们需要的那几个字段，速度极快
        params = {
            "filter": filter_str,
            "mailto": YOUR_EMAIL,
            "per-page": CHUNK_SIZE,
            "select": "id,title,publication_year" 
        }
        
        try:
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                works = data.get("results", [])
                
                for work in works:
                    paper_id = clean_id(work.get("id"))
                    pub_year = work.get("publication_year")
                    title = work.get("title")
                    
                    extracted_data.append({
                        "Clean_ID": paper_id,
                        "Publication_Year": pub_year,
                        "Title": title
                    })
            else:
                print(f"\n⚠️ 请求异常: 状态码 {response.status_code}。")
                
        except Exception as e:
            print(f"\n❌ 网络/解析错误: {e}。")
            
        # 频率锁，遵守 API 规范
        time.sleep(0.15) 
        
    # 4. 保存结果
    if extracted_data:
        df_out = pd.DataFrame(extracted_data)
        
        # 筛查是否有缺失年份的论文
        missing_years = df_out['Publication_Year'].isna().sum()
        
        df_out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        
        print("\n==================================================")
        print("🎉 年份数据获取成功！")
        print(f"📊 共获取了 {len(df_out)} 篇论文的精确年份。")
        if missing_years > 0:
            print(f"⚠️ 注意: 有 {missing_years} 篇论文 API 未返回年份，建议后续填充为默认值或丢弃。")
        print(f"📁 结果已保存至: {OUTPUT_FILE}")
        print("==================================================")
    else:
        print("\n⚠️ 未获取到任何数据。")

if __name__ == "__main__":
    fetch_publication_years()