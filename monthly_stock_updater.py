import os
import sys
import json
import datetime
import subprocess
from pathlib import Path
import requests

from search_provider import search, format_search_context

# VLLM Configuration
VLLM_URL = os.getenv("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
MODEL_NAME = os.getenv("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")
TIMEOUT_SECONDS = int(os.getenv("MAP_TIMEOUT_SECONDS", "240"))

REGISTRY_FILE = Path("ticker_registry_tw.json")
WIKI_FILE = Path("stocks_wiki.json")

WIKI_STRUCTURE_SYSTEM_PROMPT = """
你是一個台股產業鏈研究分析師與估值專家。你的任務是閱讀某家公司的搜尋與背景資訊，透過 "LLM Wiki" 技術，為這家公司建立高度結構化的產業與技術分析 Profile。

請務必根據所提供的最新新聞、公司結構與主營業務脈絡，產出符合以下格式的 JSON 物件：
{
  "summary": "業務精華（15-30字，描述核心地位與近期轉型）",
  "products": ["核心產品1", "核心產品2", "核心產品3"],
  "details": {
    "pureLevel": 4.5, // 題材純度分數 (0.0 到 5.0 的浮點數，依據該公司題材業務營收佔比或關鍵性)
    "barrierLevel": 4.0, // 核心技術壁壘 (0.0 到 5.0 的浮點數，依據專利、客戶黏性、Switching cost 或認證門檻)
    "ai_revenue_exposure": "營收佔比估算 (例如 '10-15%' 或 '主要以傳統伺服器為主，AI 佔比 <5%')",
    "gross_margin_impact": "毛利率走勢與結構影響 (例如 '受惠高毛利產品放量，預期毛利率提升 2-3%')",
    "pricing_power": "定價權評估 (例如 '高，因屬獨家供應商' 或 '中，市場競爭者眾')",
    "value_capture_score": 85, // 價值捕獲得分 (0 到 100 的整數)
    "substitution_risk": "替代風險評估 (例如 '低，認證期長達 2 年' 或 '中，面臨陸廠殺價競爭')",
    "commercialization_phase": "營收放量與商用時程 (例如 '已開始量產出貨' 或 '樣品送樣驗證中，預期 2027 放量')",
    "pros": "聯網核心競爭優勢與正面因素 (簡明一句話)",
    "cons": "投資潛在風險與負面因素 (簡明一句話)",
    "catalyst": "關鍵催化劑事件 (簡明一句話)"
  }
}

請務必遵守：
1. 只能輸出合法 JSON 格式，不要包含 markdown 標籤或額外說明文字。
2. 內容一律使用繁體中文。
3. 估值與評分需合理客觀，符合台灣上市櫃公司實際情況。
"""

def call_vllm_json(system_prompt: str, user_prompt: str, max_tokens: int = 3000, temperature: float = 0.3) -> dict:
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

def update_single_stock(code, name, industry, market, existing_record):
    search_query = f"{code} {name} 主營產品 業務 轉型 營收"
    print(f"-> Searching web for: {search_query}")
    search_results = search(search_query)
    search_context = format_search_context(search_query, search_results)
    
    user_prompt = f"""
請為以下個股建立結構化 LLM Wiki 分析：
公司代號：{code}
公司名稱：{name}
產業分類：{industry}

【搜尋取得的最新背景資料與新聞摘要】
{search_context}
"""
    llm_response = call_vllm_json(WIKI_STRUCTURE_SYSTEM_PROMPT, user_prompt)
    
    themes = existing_record.get("themes", [])
    tier = existing_record.get("tier", "extended")
    
    new_record = {
        "code": code,
        "name": name,
        "industry": industry,
        "market": market,
        "tier": tier,
        "themes": themes,
        "summary": llm_response.get("summary", f"提供 {industry} 相關產品與服務。"),
        "products": llm_response.get("products", [industry]),
        "details": llm_response.get("details", {}),
        "updated_at": datetime.date.today().isoformat()
    }
    return new_record

def main():
    force_run = "--force" in sys.argv
    today = datetime.date.today()
    
    # 預設每個月 12 號執行，或者強制執行
    if not force_run and today.day != 12:
        print(f"今天日期是 {today}。非每個月的 12 號，略過更新。(可使用 --force 參數強制執行)")
        return
        
    print(f"=== 啟動每月全市場個股 LLM Wiki 更新排程 ===")
    
    if not REGISTRY_FILE.exists():
        print("錯誤：找不到 ticker_registry_tw.json")
        return
        
    registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    
    wiki_data = {}
    if WIKI_FILE.exists():
        try:
            wiki_data = json.loads(WIKI_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"讀取既存 wiki 失敗: {e}")
            
    to_update = []
    for code, entry in registry.items():
        existing = wiki_data.get(code, {})
        updated_at = existing.get("updated_at")
        
        needs_update = False
        if not updated_at:
            needs_update = True
        else:
            try:
                last_update = datetime.datetime.strptime(updated_at, "%Y-%m-%d").date()
                # 超過 25 天即需要更新
                if (today - last_update).days >= 25:
                    needs_update = True
            except Exception:
                needs_update = True
                
        if needs_update:
            to_update.append((code, entry))
            
    print(f"本月待更新個股數：{len(to_update)} / {len(registry)}")
    
    if not to_update:
        print("所有個股資訊皆為最新狀態，無需更新。")
        return
        
    success_count = 0
    fail_count = 0
    
    # 逐一更新並寫入檔案
    for idx, (code, entry) in enumerate(to_update, 1):
        name = entry.get("name", "")
        industry = entry.get("industry", "未分類")
        market = entry.get("market", "")
        print(f"[{idx}/{len(to_update)}] 正在更新 {code} ({name})...")
        
        try:
            existing_record = wiki_data.get(code, {})
            new_record = update_single_stock(code, name, industry, market, existing_record)
            wiki_data[code] = new_record
            success_count += 1
            
            # 每成功更新 5 檔，即時存檔防當機
            if success_count % 5 == 0:
                WIKI_FILE.write_text(json.dumps(wiki_data, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"-> 累計更新成功 {success_count} 檔，已即時存檔。")
        except Exception as e:
            print(f"-> 更新 {code} 失敗: {e}")
            fail_count += 1
            
    WIKI_FILE.write_text(json.dumps(wiki_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"=== 更新完成！成功: {success_count} 檔, 失敗: {fail_count} 檔 ===")
    
    # 執行 Git 提交與推送
    if success_count > 0:
        print("執行發布與 Git 推送...")
        try:
            subprocess.run([sys.executable, "publish_site.py"], check=True)
            print("發布完成並成功推送至 GitHub Pages！")
        except Exception as e:
            print(f"Git 推送失敗: {e}")

if __name__ == "__main__":
    main()
