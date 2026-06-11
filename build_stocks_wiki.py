import json
import os
from pathlib import Path
import requests

# 環境變數與設定
VLLM_URL = os.getenv("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
MODEL_NAME = os.getenv("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")
TIMEOUT_SECONDS = int(os.getenv("MAP_TIMEOUT_SECONDS", "240"))

REGISTRY_FILE = Path("ticker_registry_tw.json")
MAPS_REPO_FILE = Path("maps_repo.json")
WIKI_FILE = Path("stocks_wiki.json")

BATCH_SIZE = 50

SYSTEM_PROMPT = """
你是一個台股產業研究助理。請為輸入的上市櫃公司列表，產生每家公司的主營業務精華（15至30字，包含核心地位與近期轉型）與核心產品線。
請務必遵守以下要求：
1. 只能輸出合法 JSON 格式。
2. 業務精華必須是繁體中文，精準簡短。
3. 核心產品線為 2 ~ 4 個關鍵詞的陣列。
"""

def call_vllm_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000, temperature: float = 0.3) -> dict:
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

def build_batch_prompt(stocks_batch: list) -> str:
    input_lines = []
    for item in stocks_batch:
        input_lines.append(f"- {item['code']} ({item['name']}, 產業別: {item['industry']})")
    
    input_str = "\n".join(input_lines)
    return f"""
請為以下公司列表，產生對應的業務精華與主要產品線。

【公司列表】
{input_str}

【輸出 JSON 結構】
{{
  "公司代號1": {{
    "summary": "業務精華（15-30字）",
    "products": ["產品1", "產品2"]
  }},
  "公司代號2": {{
    "summary": "業務精華",
    "products": ["產品1", "產品2"]
  }}
}}
"""

def main():
    print("=== 開始建置/更新全市場個股 LLM Wiki ===")
    
    # 1. 載入資料源
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

    # 2. 載入現有 Wiki 快取
    wiki_data = {}
    if WIKI_FILE.exists():
        try:
            wiki_data = json.loads(WIKI_FILE.read_text(encoding="utf-8"))
            print(f"載入現有 Wiki 檔案，包含 {len(wiki_data)} 檔股票。")
        except Exception as e:
            print(f"讀取現有 Wiki 失敗，將重新生成：{e}")

    # 3. 收集 maps_repo (Tier 1) 中現有的所有個股資訊與關聯主題
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

    # 4. 對齊並分類
    to_generate = []
    
    for code, entry in registry.items():
        name = entry.get("name", "")
        industry = entry.get("industry", "未分類")
        market = entry.get("market", "")
        
        # 判斷是否為 Core 級 (出現在主題地圖中)
        is_core = code in theme_stock_map
        
        # 基礎結構
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
            wiki_data[code] = stock_wiki
        else:
            # Extended 級，檢查快取中是否已有 summary 與 products
            stock_wiki.setdefault("themes", [])
            stock_wiki.setdefault("details", {})
            if "summary" not in stock_wiki or "products" not in stock_wiki:
                to_generate.append({
                    "code": code,
                    "name": name,
                    "industry": industry
                })
            wiki_data[code] = stock_wiki

    # 5. 批次處理未生成的個股
    if to_generate:
        print(f"共有 {len(to_generate)} 檔新增或未生成的股票，將以每批 {BATCH_SIZE} 檔進行 AI 批次生成。")
        for i in range(0, len(to_generate), BATCH_SIZE):
            batch = to_generate[i:i+BATCH_SIZE]
            print(f"正在生成第 {i+1} ~ {i+len(batch)} 檔...")
            prompt = build_batch_prompt(batch)
            try:
                response_json = call_vllm_json(SYSTEM_PROMPT, prompt)
                # 寫入快取中
                for item in batch:
                    code = item["code"]
                    res = response_json.get(code, {})
                    if "summary" in res and "products" in res:
                        wiki_data[code]["summary"] = res["summary"]
                        wiki_data[code]["products"] = res["products"]
                    else:
                        wiki_data[code]["summary"] = f"提供 {item['industry']} 相關產品與服務。"
                        wiki_data[code]["products"] = [item["industry"]]
            except Exception as e:
                print(f"批次生成失敗 ({i}~{i+len(batch)}): {e}")
                # 填入保底資料避免卡死
                for item in batch:
                    code = item["code"]
                    wiki_data[code]["summary"] = wiki_data[code].get("summary") or f"提供 {item['industry']} 相關產品與服務。"
                    wiki_data[code]["products"] = wiki_data[code].get("products") or [item["industry"]]
            
            # 每次批次完存檔，避免中斷全毀
            WIKI_FILE.write_text(json.dumps(wiki_data, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print("所有個股快取完整，無需發起新的 AI 批次生成。")

    # 6. 最後存檔與總結
    WIKI_FILE.write_text(json.dumps(wiki_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"=== 個股 LLM Wiki 建置完成！共產出 {len(wiki_data)} 檔 Wiki 資料 ===")

if __name__ == "__main__":
    main()
