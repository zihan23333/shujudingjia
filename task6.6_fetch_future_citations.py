import pandas as pd
import requests
import time
from tqdm import tqdm
import urllib3

# 禁用因忽略 SSL 校验而产生的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================================
# [1] 核心配置区
# =====================================================================
INPUT_FILE = "all_connected_papers.csv"

OUTPUT_FILE_2020_CUTOFF = "future_ground_truth_2020_cutoff.csv"
OUTPUT_FILE_2021_CUTOFF = "future_ground_truth_2021_cutoff.csv"

YOUR_EMAIL = "x768466345@gmail.com"  
# 【修改1】将批次调小，防止 URL 过长导致代理断开
CHUNK_SIZE = 30 

FUTURE_YEARS_2020 = [2021, 2022, 2023, 2024, 2025]
FUTURE_YEARS_2021 = [2022, 2023, 2024, 2025]
# =====================================================================

def clean_id(url_or_id):
    if pd.isna(url_or_id) or not str(url_or_id).strip():
        return None
    return str(url_or_id).split('/')[-1].strip()

def fetch_future_ground_truth():
    print("==================================================")
    print("🎯 任务启动：双线获取全量 105 篇论文的未来真实引用量 (抗干扰版)")
    print("==================================================")

    try:
        df_papers = pd.read_csv(INPUT_FILE)
        df_papers['Clean_ID'] = df_papers['OpenAlex_ID'].apply(clean_id)
        is_core_dict = dict(zip(df_papers['Clean_ID'], df_papers['Is_Core']))
        
        raw_ids = df_papers['OpenAlex_ID'].dropna().unique().tolist()
        clean_ids = [clean_id(pid) for pid in raw_ids if clean_id(pid)]
        print(f"📄 成功锁定全网 {len(clean_ids)} 篇论文...")
    except FileNotFoundError:
        print(f"❌ 找不到文件 {INPUT_FILE}")
        return

    chunks = [clean_ids[i:i + CHUNK_SIZE] for i in range(0, len(clean_ids), CHUNK_SIZE)]
    extracted_data_2020 = []
    extracted_data_2021 = []
    
    print(f"🚀 正在拉取 API 数据...")
    for chunk in tqdm(chunks, desc="获取进度", unit="批次"):
        filter_str = "openalex:" + "|".join(chunk)
        url = "https://api.openalex.org/works"
        
        params = {
            "filter": filter_str,
            "mailto": YOUR_EMAIL,
            "per-page": CHUNK_SIZE,
            "select": "id,title,counts_by_year" 
        }
        
        # 【修改2】加入最大重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 【修改3】加入 verify=False，无视 SSL 代理拦截错误
                response = requests.get(url, params=params, timeout=30, verify=False)
                
                if response.status_code == 200:
                    works = response.json().get("results", [])
                    
                    for work in works:
                        paper_id = clean_id(work.get("id"))
                        title = work.get("title")
                        counts_by_year = work.get("counts_by_year", [])
                        
                        future_cit_sum_2020 = 0
                        future_cit_sum_2021 = 0
                        
                        for year_data in counts_by_year:
                            year = year_data.get('year')
                            count = year_data.get('cited_by_count', 0)
                            
                            if year in FUTURE_YEARS_2020:
                                future_cit_sum_2020 += count
                            if year in FUTURE_YEARS_2021:
                                future_cit_sum_2021 += count
                                
                        is_core_flag = is_core_dict.get(paper_id, False)
                                
                        extracted_data_2020.append({
                            "Clean_ID": paper_id,
                            "Title": title,
                            "Future_Citations": future_cit_sum_2020,
                            "Is_Core": is_core_flag
                        })
                        extracted_data_2021.append({
                            "Clean_ID": paper_id,
                            "Title": title,
                            "Future_Citations": future_cit_sum_2021,
                            "Is_Core": is_core_flag
                        })
                    
                    # 成功后跳出重试循环
                    break 
                else:
                    print(f"\n⚠️ 请求异常: 状态码 {response.status_code}")
                    if attempt < max_retries - 1: time.sleep(2)
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    # 报错后等待 2 秒再次重试
                    time.sleep(2)
                else:
                    print(f"\n❌ 第 {attempt+1} 次重试依然失败: {e}")
            
        time.sleep(0.2) 
        
    if extracted_data_2020 and extracted_data_2021:
        df_out_2020 = pd.DataFrame(extracted_data_2020).sort_values(by="Future_Citations", ascending=False)
        df_out_2020.to_csv(OUTPUT_FILE_2020_CUTOFF, index=False, encoding="utf-8-sig")
        
        df_out_2021 = pd.DataFrame(extracted_data_2021).sort_values(by="Future_Citations", ascending=False)
        df_out_2021.to_csv(OUTPUT_FILE_2021_CUTOFF, index=False, encoding="utf-8-sig")
        
        print("\n==================================================")
        print("🎉 双线 Ground Truth 数据获取成功！")
        print(f"✅ 2020版 实际获取数据量: {len(df_out_2020)} 篇")
        print(f"✅ 2021版 实际获取数据量: {len(df_out_2021)} 篇")
        print("==================================================")

if __name__ == "__main__":
    fetch_future_ground_truth()