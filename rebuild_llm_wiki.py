import json
import os
import re
import time
import datetime
from pathlib import Path
import requests

# 設定
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
4. 【重要安全機制】：如果輸入的背景資料/新聞內容是空的，代表網路搜尋未找到該公司的最新特定消息。在此情況下，你必須根據其官方產業分類【{industry}】產出最基本、保守的傳統產品描述（例如：電子通路就寫電子零組件代理經銷；化學類就寫基本化學材料生產加工；電機機械就寫機械加工與設備組裝）。絕對不要虛構任何「精密醫療器材」、「居家生物科技」、「高頻寬記憶體轉型」等完全沒有依據的事蹟！
"""

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
        print(f"    [Warning] 獲取新聞內文失敗 (ID {news_id}): {e}")
    return ""

def search_cnyes_context(code: str, name: str) -> str:
    query = f"{code} {name}"
    url = f"https://api.cnyes.com/media/api/v1/search?q={requests.utils.quote(query)}&limit=5"
    context_parts = []
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            items = res.json().get("items", {}).get("data", [])
            fetched = 0
            for item in items:
                news_id = item.get("newsId")
                title = item.get("title")
                if not news_id:
                    continue
                text = fetch_cnyes_article_text(news_id)
                if text:
                    context_parts.append(f"新聞標題：{title}\n新聞內容：\n{text}")
                    fetched += 1
                if fetched >= 2:
                    break
    except Exception as e:
        print(f"    [Warning] 搜尋 API 失敗: {e}")
    return "\n\n".join(context_parts)

def call_vllm_json(system_prompt: str, user_prompt: str, max_tokens: int = 3000, temperature: float = 0.2) -> dict:
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

def main():
    print("=== 全市場個股 LLM Wiki 大盤整引擎啟動 ===")
    
    if not REGISTRY_FILE.exists():
        print(f"錯誤：找不到 {REGISTRY_FILE}，請先執行 build_ticker_registry.py")
        return
        
    registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    
    wiki_data = {}
    if WIKI_FILE.exists():
        try:
            wiki_data = json.loads(WIKI_FILE.read_text(encoding="utf-8"))
            print(f"載入現有 Wiki 檔案，共計 {len(wiki_data)} 檔個股。")
        except Exception as e:
            print(f"讀取現有 Wiki 失敗，將重新建立：{e}")

    # 找出核心個股 (Tier 1)，優先排序
    maps_repo = {}
    if MAPS_REPO_FILE.exists():
        try:
            maps_repo = json.loads(MAPS_REPO_FILE.read_text(encoding="utf-8"))
        except:
            pass
            
    core_codes = set()
    for map_val in maps_repo.values():
        for s in map_val.get("stocks", []):
            code = s.get("code") or s.get("id")
            if code:
                core_codes.add(code)
                
    # 決定處理清單 (排除今天已經更新過的個股，方便中斷後重啟)
    today_str = datetime.date.today().isoformat()
    
    to_process = []
    for code, info in registry.items():
        name = info.get("name", "")
        industry = info.get("industry", "未分類")
        market = info.get("market", "")
        
        # 檢查是否今天已經更新過
        existing = wiki_data.get(code, {})
        if existing.get("updated_at") == today_str and "details" in existing and existing["details"]:
            # 已更新過，跳過
            continue
            
        to_process.append({
            "code": code,
            "name": name,
            "industry": industry,
            "market": market,
            "is_core": code in core_codes
        })
        
    # 優先處理核心 (Tier 1) 股票，接著是其他股票
    to_process.sort(key=lambda x: (not x["is_core"], x["code"]))
    
    total = len(to_process)
    print(f"今天需要處理/更新的個股總數: {total} 檔 (核心個股優先)")
    if total == 0:
        print("所有個股百科已是最新狀態，無需更新。")
        return
        
    success = 0
    start_time = time.time()
    
    for idx, item in enumerate(to_process, 1):
        code = item["code"]
        name = item["name"]
        industry = item["industry"]
        market = item["market"]
        
        print(f"\n[{idx}/{total}] 正在盤整 {code} ({name}) - 核心: {item['is_core']} - 產業: {industry}")
        
        # 1. 取得真實新聞脈絡
        context = search_cnyes_context(code, name)
        
        if not context:
            print("  -> 鉅亨網未找到近期報導，將套用安全 Fallback 機制")
            
        # 2. 呼叫 vLLM 生成結構化資料
        system_prompt = WIKI_STRUCTURE_SYSTEM_PROMPT.replace("{industry}", industry)
        user_prompt = f"""
請為以下個股建立精確的結構化 LLM Wiki 百科：
公司代碼：{code}
公司名稱：{name}
產業分類：{industry}

【搜尋背景新聞脈絡】
{context}
"""
        try:
            llm_response = call_vllm_json(system_prompt, user_prompt)
            
            # 3. 整合至 wiki_data
            existing_record = wiki_data.get(code, {})
            wiki_data[code] = {
                "code": code,
                "name": name,
                "industry": industry,
                "market": market,
                "tier": "core" if item["is_core"] else "extended",
                "themes": existing_record.get("themes", []),
                "summary": llm_response.get("summary", f"提供 {industry} 相關產品與服務。"),
                "products": llm_response.get("products", [industry]),
                "details": llm_response.get("details", {}),
                "updated_at": today_str
            }
            success += 1
            print(f"  -> 盤整成功: {wiki_data[code]['summary']}")
            
            # 每 5 檔自動寫入存檔
            if success % 5 == 0:
                WIKI_FILE.write_text(json.dumps(wiki_data, ensure_ascii=False, indent=2), encoding="utf-8")
                elapsed = time.time() - start_time
                speed = elapsed / idx
                rem_time = speed * (total - idx)
                print(f"  [Progress] 累計成功 {success} 檔，已即時存檔。預估剩餘時間: {rem_time/60:.1f} 分鐘")
                
        except Exception as e:
            print(f"  [Error] 盤整失敗: {e}")
            
        # 延遲 1 秒，防止過度頻繁請求
        time.sleep(1.0)
        
    # 最終存檔
    WIKI_FILE.write_text(json.dumps(wiki_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== 百科全書盤整完成！共成功更新 {success} 檔 ===")

if __name__ == "__main__":
    main()
