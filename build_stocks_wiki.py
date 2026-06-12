import json
import os
import datetime
from pathlib import Path
import requests

from search_provider import search, format_search_context

# 環境變數與設定
VLLM_URL = os.getenv("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
MODEL_NAME = os.getenv("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")
TIMEOUT_SECONDS = int(os.getenv("MAP_TIMEOUT_SECONDS", "240"))

REGISTRY_FILE = Path("ticker_registry_tw.json")
MAPS_REPO_FILE = Path("maps_repo.json")
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
    print("=== 開始建置/更新全市場個股 LLM Wiki (完全基於 Web Search) ===")
    
    if not REGISTRY_FILE.exists():
        print(f"錯誤：找不到 {REGISTRY_FILE}，請先執行 build_ticker_registry.py")
        return
    registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    
    maps_repo = {}
    if MAPS_REPO_FILE.exists():
        try:
            maps_repo = json.loads(MAPS_REPO_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"讀取 maps_repo 失敗：{e}")

    wiki_data = {}
    if WIKI_FILE.exists():
        try:
            wiki_data = json.loads(WIKI_FILE.read_text(encoding="utf-8"))
            print(f"載入現有 Wiki 檔案，包含 {len(wiki_data)} 檔股票。")
        except Exception as e:
            print(f"讀取現有 Wiki 失敗，將重新生成：{e}")

    # 1. 收集 maps_repo (Tier 1) 中現有的所有個股資訊與關聯主題
    theme_stock_map = {}
    for map_key, map_val in maps_repo.items():
        theme_title = map_val.get("title", "")
        stocks = map_val.get("stocks", [])
        for s in stocks:
            code = s.get("code") or s.get("id")
            if not code:
                continue
            if code not in theme_stock_map:
                theme_stock_map[code] = {
                    "themes": [],
                    "detail": s
                }
            if theme_title and theme_title not in theme_stock_map[code]["themes"]:
                theme_stock_map[code]["themes"].append(theme_title)

    # 2. 對齊與篩選需要生成/更新的個股
    to_generate = []
    
    for code, entry in registry.items():
        name = entry.get("name", "")
        industry = entry.get("industry", "未分類")
        market = entry.get("market", "")
        
        is_core = code in theme_stock_map
        stock_wiki = wiki_data.get(code, {})
        stock_wiki["code"] = code
        stock_wiki["name"] = name
        stock_wiki["industry"] = industry
        stock_wiki["market"] = market
        stock_wiki["tier"] = "core" if is_core else "extended"
        
        if is_core:
            # 整合 Core 級主題地圖的深度資料
            core_info = theme_stock_map[code]["detail"]
            stock_wiki["themes"] = theme_stock_map[code]["themes"]
            stock_wiki["summary"] = core_info.get("desc") or core_info.get("role") or stock_wiki.get("summary") or "Core 題材核心概念股。"
            stock_wiki["products"] = list(set(stock_wiki.get("products", []) + [core_info.get("sector", industry)]))
            stock_wiki["details"] = {
                "pureLevel": core_info.get("pureLevel"),
                "barrierLevel": core_info.get("barrierLevel"),
                "pros": core_info.get("pros"),
                "cons": core_info.get("cons"),
                "catalyst": core_info.get("catalyst"),
                "pricing_power": core_info.get("pricing_power"),
                "ai_revenue_exposure": core_info.get("ai_revenue_exposure"),
                "commercialization_phase": core_info.get("commercialization_phase")
            }
            stock_wiki["updated_at"] = stock_wiki.get("updated_at") or datetime.date.today().isoformat()
            wiki_data[code] = stock_wiki
        else:
            stock_wiki.setdefault("themes", [])
            stock_wiki.setdefault("details", {})
            # 如果沒有 updated_at，代表它是舊版無 Web Search 盲猜生成的資料，需要重新生成
            if "updated_at" not in stock_wiki:
                to_generate.append({
                    "code": code,
                    "name": name,
                    "industry": industry,
                    "market": market
                })
            wiki_data[code] = stock_wiki

    # 3. 逐一針對缺乏真實 Web Search 資料的個股進行更新
    if to_generate:
        print(f"共有 {len(to_generate)} 檔股票需要進行 Web Search + LLM 結構化生成。")
        success_count = 0
        
        for idx, item in enumerate(to_generate, 1):
            code = item["code"]
            name = item["name"]
            industry = item["industry"]
            market = item["market"]
            
            print(f"[{idx}/{len(to_generate)}] 正在分析 {code} ({name})...")
            try:
                existing_record = wiki_data.get(code, {})
                new_record = update_single_stock(code, name, industry, market, existing_record)
                wiki_data[code] = new_record
                success_count += 1
                
                # 每成功 5 檔寫入存檔
                if success_count % 5 == 0:
                    WIKI_FILE.write_text(json.dumps(wiki_data, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"-> 累計生成成功 {success_count} 檔，已即時存檔。")
            except Exception as e:
                print(f"-> 分析 {code} 失敗: {e}")
                # 保底資料
                wiki_data[code]["summary"] = wiki_data[code].get("summary") or f"提供 {industry} 相關產品與服務。"
                wiki_data[code]["products"] = wiki_data[code].get("products") or [industry]
                wiki_data[code]["updated_at"] = datetime.date.today().isoformat()
                
        WIKI_FILE.write_text(json.dumps(wiki_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"=== 生成完成！共成功更新 {success_count} 檔 ===")
    else:
        print("所有個股皆已具備 Web Search 動態分析快取，無需重新生成。")

if __name__ == "__main__":
    main()
