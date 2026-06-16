import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
import urllib3

urllib3.disable_warnings()

VLLM_URL = os.getenv("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
MODEL_NAME = os.getenv("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")
TIMEOUT_SECONDS = int(os.getenv("MAP_TIMEOUT_SECONDS", "240"))

EXPECTATIONS_FILE = Path("expectations_gap.json")
TICKER_REGISTRY_FILE = Path("ticker_registry_tw.json")

def load_ticker_registry():
    if not TICKER_REGISTRY_FILE.exists():
        print("警告：未找到 ticker_registry_tw.json，將不進行概念股代碼校正。")
        return {}
    try:
        reg = json.loads(TICKER_REGISTRY_FILE.read_text(encoding="utf-8"))
        name_map = {}
        for code, info in reg.items():
            name = info.get("name", "").strip()
            name_map[name] = code
            for alias in info.get("aliases", []):
                alias_clean = alias.strip()
                if alias_clean:
                    name_map[alias_clean] = code
        return name_map
    except Exception as e:
        print(f"載入 ticker registry 失敗: {e}")
        return {}

def correct_concept_stocks(stocks_list, name_map):
    if not name_map or not stocks_list:
        return stocks_list
    corrected = []
    for s in stocks_list:
        s_clean = s.strip()
        parts = s_clean.split()
        if len(parts) >= 2:
            code = parts[0]
            name = " ".join(parts[1:])
        else:
            code = ""
            name = s_clean
            
        name_clean = re.sub(r"<[^>]+>", "", name).strip()
        
        # 尋找匹配
        matched_code = name_map.get(name_clean)
        if not matched_code:
            # 模糊匹配
            for k, v in name_map.items():
                if name_clean in k or k in name_clean:
                    matched_code = v
                    name_clean = k
                    break
                    
        if matched_code:
            corrected.append(f"{matched_code} {name_clean}")
        else:
            corrected.append(s_clean)
    return list(dict.fromkeys(corrected)) # 去重


# 1. LLM Screen Prompt
SCREEN_SYSTEM_PROMPT = """
你是一個專業的台股高科技投研篩選專家。請從輸入的新聞標題列表中，篩選出「強烈暗示」或「明確提及」市場/法人預期落差（例如：價格調漲、漲幅超預期、法說會財測或毛利率優於市場預估、結構性大缺貨、產能嚴重不足、跌價低於預期）的項目。

請輸出 JSON 格式如下，返回符合條件的 newsId 列表：
{
  "matched_ids": [6500761, 6500399]
}

如果沒有任何標題符合條件，請輸出：
{
  "matched_ids": []
}

請務必只篩選與「產業數據反差/估值重估/供需失衡價格大幅波動」高度相關的標題。
"""

# 2. LLM Extraction Prompt
EXTRACT_SYSTEM_PROMPT = """
你是一個精準的台股與半導體產業鏈分析大師。你的任務是閱讀新聞全文，提取出「先前預期」與「最新數據/實質傳聞」之間的對比，並產出結構化的「預期差距」與「估值追夢空間」評估。

請輸出符合以下格式的 JSON 物件：
{
  "category": "產業分類（如：記憶體 (Memory)、被動元件 (Passive Components)、光通訊 (Optical)、先進半導體、面板等）",
  "target": "具體產品或對象（例如：KIOXIA NAND、Winbond Nor flash、DRAM 供給缺口、CoWoS 產能）",
  "market_expect": "市場/法人先前預期（描述具體預期數值或風向，字數在 15-30 字，如：市場預期 Q3 價格上漲 10% 以內、原預期傳統週期波動）",
  "real_data": "實質數據 / 最新傳聞（最新法說會公布或通路實質數據，字數在 15-30 字，如：過去一年價格暴漲六倍，PC端DRAM至2027年缺口15%）",
  "gap_space": "預期差距評估（計算差距或重估空間，如：+15% 額外供給缺口，價格重估彈性極大）",
  "concept_stocks": ["股票代碼 股票名稱，如 '2344 華邦電', '2337 旺宏'，必須是台股真實的關聯概念股"],
  "dream_rating": "追夢空間評估，如：'利多追價效應'、'利多估值重估'、'利空重擊估值'、'利空出盡空間'",
  "impact_direction": "影響方向（'bullish' 或 'bearish'）",
  "source": "新聞來源簡述，如：'鉅亨網：大摩預警記憶體結構性危機'"
}

要求：
1. 只能輸出合法 JSON，不要包含額外說明。
2. 內容一律使用繁體中文。
3. 如果該新聞無法提取出清晰的預期反差對比，請在 JSON 中返回 {"invalid": true}。
"""

def call_vllm_json(system_prompt: str, user_prompt: str, max_tokens: int = 2000, temperature: float = 0.2) -> dict:
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    response = requests.post(
        VLLM_URL,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()
    return json.loads(content)

def search_cnyes_news(query: str, limit: int = 15) -> list:
    url = f"https://api.cnyes.com/media/api/v1/search?q={requests.utils.quote(query)}&limit={limit}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("items", {}).get("data", [])
    except Exception as e:
        print(f"查詢 鉅亨網 API 失敗 ({query}): {e}")
    return []

def fetch_cnyes_article_text(news_id: int) -> str:
    url = f"https://news.cnyes.com/news/id/{news_id}"
    try:
        res = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            html = res.text
            paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html)
            cleaned = []
            for p in paragraphs:
                p_clean = re.sub(r"<[^>]+>", "", p).strip()
                if p_clean and "鉅亨網" not in p_clean and "下一篇" not in p_clean:
                    cleaned.append(p_clean)
            return "\n".join(cleaned)
    except Exception as e:
        print(f"獲取 鉅亨網 新聞全文失敗 (ID {news_id}): {e}")
    return ""

def normalize_category(cat):
    if not cat:
        return "其他題材"
    cat_clean = cat.strip()
    if "先進半導體" in cat_clean or "Advanced Semiconductor" in cat_clean:
        return "先進半導體 (Advanced Semiconductor)"
    if "記憶體" in cat_clean or "Memory" in cat_clean:
        return "記憶體 (Memory)"
    if "儲存" in cat_clean or "Storage" in cat_clean:
        return "儲存設備 (Storage)"
    if "光通訊" in cat_clean or "Optical" in cat_clean or "散熱" in cat_clean or "Thermal" in cat_clean:
        return "光通訊與散熱 (Optical & Thermal)"
    if "AI 基礎設施" in cat_clean or "AI Infrastructure" in cat_clean or "Infrastructure" in cat_clean:
        return "AI 基礎設施 (AI Infrastructure)"
    return cat_clean

def is_duplicate_target(t1, t2):
    t1_lower = t1.lower()
    t2_lower = t2.lower()
    
    # 1. Oracle / AI Cloud Infrastructure
    if any(kw in t1_lower for kw in ["oracle", "甲骨文", "gpu 運算需求", "雲端運算", "ai 雲端基礎設施"]) and \
       any(kw in t2_lower for kw in ["oracle", "甲骨文", "gpu 運算需求", "雲端運算", "ai 雲端基礎設施"]):
        return True
        
    # 2. Blackwell
    if any(kw in t1_lower for kw in ["blackwell", "輝達"]) and \
       any(kw in t2_lower for kw in ["blackwell", "輝達"]):
        return True
        
    # 3. DRAM/HBM Cycle
    if any(kw in t1_lower for kw in ["景氣循環", "hbm 估值", "dram 價格"]) and \
       any(kw in t2_lower for kw in ["景氣循環", "hbm 估值", "dram 價格"]):
        if not any(kw in t1_lower + t2_lower for kw in ["美光", "micron", "硬碟", "hdd", "nor flash", "ddr4", "nand"]):
            return True
            
    # 4. Micron
    if any(kw in t1_lower for kw in ["美光", "micron"]) and \
       any(kw in t2_lower for kw in ["美光", "micron"]):
        return True

    # 5. HDD
    if any(kw in t1_lower for kw in ["硬碟", "hdd"]) and \
       any(kw in t2_lower for kw in ["硬碟", "hdd"]):
        return True

    # 6. Nor Flash
    if "nor flash" in t1_lower and "nor flash" in t2_lower:
        return True

    # 7. DDR4
    if "ddr4" in t1_lower and "ddr4" in t2_lower:
        return True

    # 8. KIOXIA NAND
    if "kioxia" in t1_lower and "kioxia" in t2_lower:
        return True

    # 9. SKhynix
    if "skhynix" in t1_lower and "skhynix" in t2_lower:
        return True

    # 10. PLP
    if "plp" in t1_lower and "plp" in t2_lower:
        return True

    # 11. Photodiode / 光PD
    if any(kw in t1_lower for kw in ["光 pd", "photodiode", "鼎元"]) and \
       any(kw in t2_lower for kw in ["光 pd", "photodiode", "鼎元"]):
        return True

    # 12. CPO
    if "cpo" in t1_lower and "cpo" in t2_lower:
        if not any(kw in t1_lower + t2_lower for kw in ["鼎元", "光 pd"]):
            return True

    return t1_lower == t2_lower

def merge_gap_items(item1, item2):
    # Merge concept stocks
    stocks1 = item1.get("concept_stocks", [])
    stocks2 = item2.get("concept_stocks", [])
    merged_stocks = list(stocks1)
    for s in stocks2:
        if s not in merged_stocks:
            merged_stocks.append(s)
            
    # Choose longer/more descriptive fields
    real_data = item1.get("real_data", "")
    if len(item2.get("real_data", "")) > len(real_data):
        real_data = item2.get("real_data", "")
        
    market_expect = item1.get("market_expect", "")
    if len(item2.get("market_expect", "")) > len(market_expect):
        market_expect = item2.get("market_expect", "")
        
    gap_space = item1.get("gap_space", "")
    if len(item2.get("gap_space", "")) > len(gap_space):
        gap_space = item2.get("gap_space", "")
        
    # Standardize target name (prefer the cleaner one)
    target1 = item1.get("target", "")
    target2 = item2.get("target", "")
    target = target1
    # Prefer standardized names
    if "輝達 Blackwell" in target2 or len(target2) < len(target1) and "Blackwell" in target2:
        target = target2
    elif "AI 雲端基礎設施" in target2 and "甲骨文" in target2:
        target = target2
    elif "美光" in target2 and len(target2) < len(target1):
        target = target2

    merged = dict(item1)
    merged["concept_stocks"] = merged_stocks
    merged["real_data"] = real_data
    merged["market_expect"] = market_expect
    merged["gap_space"] = gap_space
    merged["target"] = target
    
    # Pick latest date
    date1 = item1.get("last_update", "")
    date2 = item2.get("last_update", "")
    if date2 > date1:
        merged["last_update"] = date2
        
    return merged

def main():
    print("=== 自動預期反差/追夢空間搜查引擎啟動 ===")

    # 1. 定義搜查的關鍵字
    search_keywords = [
        "記憶體 價格",
        "記憶體 漲價",
        "調漲 預估",
        "超預期",
        "被動元件 價格",
        "面板 價格",
        "半導體 缺貨",
        "法說會 價格",
        "DRAM 漲價",
        "NAND 漲價",
        "CoWoS 產能"
    ]

    # 2. 檢索最新新聞
    news_pool = {}
    cutoff_time = datetime.now() - timedelta(days=7) # 只拿最近 7 天的新聞

    print("正在鉅亨網檢索相關熱門產業報導...")
    for kw in search_keywords:
        items = search_cnyes_news(kw, limit=12)
        for item in items:
            news_id = item.get("newsId")
            publish_at = item.get("publishAt")
            title = item.get("title", "").strip()
            
            if not news_id or not title:
                continue
                
            # 時間過濾
            if publish_at:
                try:
                    pub_dt = datetime.fromtimestamp(int(publish_at))
                    if pub_dt < cutoff_time:
                        continue
                except:
                    pass

            news_pool[news_id] = {
                "newsId": news_id,
                "title": title,
                "publishAt": publish_at
            }
            
    print(f"符合時間條件的候選新聞總數: {len(news_pool)}")
    if not news_pool:
        print("今日無最新相關產業報導。")
        return

    # 3. 呼叫 LLM 進行快速標題篩選
    candidate_list = [{"newsId": nid, "title": info["title"]} for nid, info in news_pool.items()]
    # 如果候選太多，切成每 30 筆一個批次
    batch_size = 30
    matched_ids = []
    
    print("正在使用 LLM 進行標題預篩選...")
    for i in range(0, len(candidate_list), batch_size):
        batch = candidate_list[i:i+batch_size]
        user_prompt = f"請篩選以下新聞標題列表中，具有「市場預期與實質數據/傳聞落差」的報導：\n{json.dumps(batch, ensure_ascii=False, indent=2)}"
        try:
            res = call_vllm_json(SCREEN_SYSTEM_PROMPT, user_prompt)
            batch_matched = res.get("matched_ids", [])
            matched_ids.extend(batch_matched)
            print(f"批次 {i//batch_size + 1} 完成。篩選出：{batch_matched}")
        except Exception as e:
            print(f"篩選批次 {i//batch_size + 1} 失敗: {e}")
            
    matched_ids = list(set(matched_ids))
    print(f"LLM 預篩選出具有預期反差特徵的新聞數: {len(matched_ids)}")
    
    # 4. 抓取全文並進行 LLM 深度提取
    new_gaps = []
    for nid in matched_ids:
        # 轉換成整數或字串做一致性檢查，視 API 回傳型態而定。
        # 為了保險起見，我們同時做整數與字串的檢查。
        nid_key = int(nid) if str(nid).isdigit() else nid
        if nid_key not in news_pool:
            # 嘗試字串匹配
            nid_key = str(nid)
            if nid_key not in news_pool:
                print(f"警告：LLM 返回的新聞 ID {nid} 不在候選名單中，跳過。")
                continue
        
        print(f"\n正在處理新聞 ID {nid}...")
        title = news_pool[nid_key]["title"]
        print(f"標題: {title}")
        
        full_text = fetch_cnyes_article_text(nid)
        if not full_text:
            print("無法讀取全文，跳過。")
            continue
            
        user_prompt = f"新聞標題：{title}\n\n新聞全文內容：\n{full_text}"
        try:
            gap_data = call_vllm_json(EXTRACT_SYSTEM_PROMPT, user_prompt)
            if gap_data.get("invalid"):
                print("-> LLM 研判無法提取出有效的市場預期反差數據，跳過。")
                continue
                
            # 寫入更新時間與來源資訊
            pub_time = news_pool[nid_key].get("publishAt")
            if pub_time:
                date_str = datetime.fromtimestamp(int(pub_time)).strftime("%Y-%m-%d")
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
                
            gap_data["last_update"] = date_str
            # 類別標準化
            gap_data["category"] = normalize_category(gap_data.get("category", ""))
            # 如果 source 未指定，用標題
            if not gap_data.get("source"):
                gap_data["source"] = f"鉅亨網：{title[:15]}..."
                
            print(f"-> 成功提取預期反差事件: {gap_data['target']} ({gap_data['gap_space']})")
            new_gaps.append(gap_data)
        except Exception as e:
            print(f"-> 處理失敗: {e}")
            
    # 5. 載入並合併至現有的 expectations_gap.json
    existing_gaps = []
    if EXPECTATIONS_FILE.exists():
        try:
            existing_gaps = json.loads(EXPECTATIONS_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"讀取現有 expectations_gap.json 失敗: {e}")
            
    # 載入證券名冊做代碼校正
    name_map = load_ticker_registry()
            
    # 保留使用者最關心的手動輸入紀錄 (Nor Flash, DDR4, NAND, NAND/DRAM)
    initial_targets = {
        "Winbond Nor flash",
        "Winbond DDR4",
        "KIOXIA NAND",
        "SKhynix NAND/DRAM"
    }
    
    updated_count = 0
    added_count = 0
    
    # 只有當有新數據時才合併
    if new_gaps:
        for new_item in new_gaps:
            target = new_item.get("target")
            match_idx = -1
            for idx, ext in enumerate(existing_gaps):
                if is_duplicate_target(ext.get("target", ""), target):
                    match_idx = idx
                    break
                    
            if match_idx != -1:
                if existing_gaps[match_idx].get("target") in initial_targets:
                    print(f"保留核心初始手動項目：{target}，跳過自動覆蓋。")
                else:
                    existing_gaps[match_idx] = merge_gap_items(existing_gaps[match_idx], new_item)
                    print(f"合併/更新已有項目：{existing_gaps[match_idx]['target']}")
                    updated_count += 1
            else:
                existing_gaps.append(new_item)
                print(f"新增全新項目：{target}")
                added_count += 1
    else:
        print("\n今日無新提取到的預期反差數據，僅對既有項目進行代碼校對。")

    # 對所有項目進行概念股代碼與名稱校正以及類別標準化
    for gap in existing_gaps:
        gap["category"] = normalize_category(gap.get("category", ""))
        orig = gap.get("concept_stocks", [])
        corrected = correct_concept_stocks(orig, name_map)
        gap["concept_stocks"] = corrected
        if orig != corrected:
            print(f"校正 {gap.get('target')} 的概念股代碼：{orig} -> {corrected}")
            
    # 按照類別與 target 排序，使同類型的整理在一起
    existing_gaps.sort(key=lambda x: (x.get("category", ""), x.get("target", "")))
            
    # 存回檔案
    try:
        EXPECTATIONS_FILE.write_text(json.dumps(existing_gaps, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n存檔成功！共更新 {updated_count} 筆，新增 {added_count} 筆，並完成所有概念股代碼校對。")
    except Exception as e:
        print(f"寫入 expectations_gap.json 失敗: {e}")

if __name__ == "__main__":
    main()
