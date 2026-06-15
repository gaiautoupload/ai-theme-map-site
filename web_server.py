import json
import os
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer
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

class LLMWikiHTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/api/update_stock":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            code = query_params.get("code", [None])[0]
            
            if not code:
                self.send_error_json(400, "Missing required parameter 'code'")
                return
                
            try:
                updated_entry = self.update_stock_wiki(code)
                self.send_response_json(200, updated_entry)
            except Exception as e:
                self.send_error_json(500, f"Error updating stock: {str(e)}")
        elif parsed_url.path == "/api/update_macro":
            try:
                from generate_daily_report import generate_macro_analysis
                generate_macro_analysis()
                macro_file = Path("macro_ai_analysis.json")
                if macro_file.exists():
                    macro_data = json.loads(macro_file.read_text(encoding="utf-8"))
                    self.send_response_json(200, macro_data)
                else:
                    self.send_error_json(500, "macro_ai_analysis.json was not created.")
            except Exception as e:
                self.send_error_json(500, f"Error updating macro: {str(e)}")
        else:
            super().do_GET()

    def send_response_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def send_error_json(self, status_code, message):
        self.send_response_json(status_code, {"error": message})

    def update_stock_wiki(self, code: str) -> dict:
        # 1. Check registry
        if not REGISTRY_FILE.exists():
            raise FileNotFoundError("ticker_registry_tw.json not found")
        registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        
        if code not in registry:
            raise KeyError(f"Stock code {code} not found in registry")
            
        stock_info = registry[code]
        name = stock_info.get("name", "")
        industry = stock_info.get("industry", "未分類")
        market = stock_info.get("market", "")
        
        # 2. Perform live web search
        search_query = f"{code} {name} 主營產品 業務 轉型 營收"
        print(f"[Live Update] Searching web for: {search_query}")
        search_results = search(search_query)
        search_context = format_search_context(search_query, search_results)
        
        # 3. Call LLM to structure
        user_prompt = f"""
請為以下個股建立結構化 LLM Wiki 分析：
公司代號：{code}
公司名稱：{name}
產業分類：{industry}

【搜尋取得的最新背景資料與新聞摘要】
{search_context}
"""
        print(f"[Live Update] Requesting LLM structure for: {code} ({name})")
        llm_response = call_vllm_json(WIKI_STRUCTURE_SYSTEM_PROMPT, user_prompt)
        
        # 4. Load & Merge with existing stocks_wiki.json
        wiki_data = {}
        if WIKI_FILE.exists():
            try:
                wiki_data = json.loads(WIKI_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Warning: Failed to load existing wiki: {e}")
                
        # Get existing record to preserve themes/tier if core
        existing_record = wiki_data.get(code, {})
        themes = existing_record.get("themes", [])
        tier = existing_record.get("tier", "extended")
        
        # Structure the new record
        new_record = {
            "code": code,
            "name": name,
            "industry": industry,
            "market": market,
            "tier": tier,
            "themes": themes,
            "summary": llm_response.get("summary", f"提供 {industry} 相關產品與服務。"),
            "products": llm_response.get("products", [industry]),
            "details": llm_response.get("details", {})
        }
        
        wiki_data[code] = new_record
        WIKI_FILE.write_text(json.dumps(wiki_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[Live Update] Successfully updated {code} in stocks_wiki.json")
        
        return new_record

def run_server(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, LLMWikiHTTPHandler)
    print(f"Server started on http://localhost:{port}/")
    print("Use Ctrl+C to stop the server.")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
