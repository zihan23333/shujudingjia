import pandas as pd
import requests
import time
from tqdm import tqdm

# =====================================================================
# [1] 核心配置区
# =====================================================================
INPUT_FILE = "all_connected_papers.csv"
OUTPUT_FILE = "future_ground_truth.csv"

# 你的 OpenAlex 礼貌池邮箱
YOUR_EMAIL = "x768466345@gmail.com"  
CHUNK_SIZE = 50 

# 🚨 关键参数：定义未来验证窗口 (假设 Cutoff 是 2020 年)
FUTURE_YEARS = [2021,2022, 2023, 2024]
# =====================================================================

def clean_id(url_or_id):
    if pd.isna(url_or_id) or not str(url_or_id).strip():
        return None
    return str(url_or_id).split('/')[-1].strip()

def fetch_future_ground_truth():
    print("==================================================")
    print("🎯 任务启动：获取核心论文的未来真实引用量 (Ground Truth)")
    print("==================================================")

    # 1. 仅提取 30 篇核心论文的 ID
    try:
        df_papers = pd.read_csv(INPUT_FILE)
        # 过滤出核心论文
        core_papers = df_papers[df_papers['Is_Core'] == True].copy()
        raw_ids = core_papers['OpenAlex_ID'].dropna().unique().tolist()
        clean_ids = [clean_id(pid) for pid in raw_ids if clean_id(pid)]
        print(f"📄 成功锁定 {len(clean_ids)} 篇核心论文，准备获取未来流水...")
    except FileNotFoundError:
        print(f"❌ 找不到文件 {INPUT_FILE}，请检查路径。")
        return

    chunks = [clean_ids[i:i + CHUNK_SIZE] for i in range(0, len(clean_ids), CHUNK_SIZE)]
    extracted_data = []
    
    print(f"🚀 正在拉取 {FUTURE_YEARS} 年份区间的真实引用数据...")
    for chunk in tqdm(chunks, desc="获取进度", unit="批次"):
        filter_str = "openalex:" + "|".join(chunk)
        url = "https://api.openalex.org/works"
        
        # select=id,title,counts_by_year 让返回数据极简，速度极快
        params = {
            "filter": filter_str,
            "mailto": YOUR_EMAIL,
            "per-page": CHUNK_SIZE,
            "select": "id,title,counts_by_year" 
        }
        
        try:
            response = requests.get(url, params=params, timeout=20)
            if response.status_code == 200:
                works = response.json().get("results", [])
                
                for work in works:
                    paper_id = clean_id(work.get("id"))
                    title = work.get("title")
                    counts_by_year = work.get("counts_by_year", [])
                    
                    # 统计在未来窗口期内的新增引用量
                    future_cit_sum = 0
                    for year_data in counts_by_year:
                        if year_data.get('year') in FUTURE_YEARS:
                            future_cit_sum += year_data.get('cited_by_count', 0)
                            
                    extracted_data.append({
                        "Clean_ID": paper_id,
                        "Title": title,
                        "Future_Citations": future_cit_sum
                    })
            else:
                print(f"\\n⚠️ 请求异常: 状态码 {response.status_code}。")
        except Exception as e:
            print(f"\\n❌ 网络/解析错误: {e}。")
            
        time.sleep(0.15) 
        
    # 4. 保存结果并按引用量倒序排列
    if extracted_data:
        df_out = pd.DataFrame(extracted_data)
        # 按照未来真实引用量排个序，方便你直观看看谁是未来的“真神”
        df_out = df_out.sort_values(by="Future_Citations", ascending=False)
        df_out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        
        print("\n==================================================")
        print("🎉 Ground Truth 数据获取成功！")
        print(f"📊 记录了 {len(df_out)} 篇核心论文在 2022-2025 年的新增总引用。")
        print(f"📁 结果已保存至: {OUTPUT_FILE}")
        print("==================================================")

if __name__ == "__main__":
    fetch_future_ground_truth()