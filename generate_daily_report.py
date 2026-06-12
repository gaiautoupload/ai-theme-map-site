import json
import os
import datetime
from pathlib import Path
import requests

from search_provider import search, format_search_context

# Environmental settings
VLLM_URL = os.getenv("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
MODEL_NAME = os.getenv("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")
TIMEOUT_SECONDS = int(os.getenv("MAP_TIMEOUT_SECONDS", "240"))

REPORT_FILE = Path("market_reports.json")

SYSTEM_PROMPT = """
你是一個台股大盤與全球宏觀市場策略分析師。
你的任務是閱讀今日的最新市場搜尋資訊，產出一份結構化的「每日投研大局觀」報告。

請產出符合以下格式的 JSON 物件：
{
  "title": "大標題（例如：技術分析的ABC波修正 季線附近為另次買點）",
  "taiex_summary": "加權指數與大盤研判摘要（描述近期高低點、多空趨勢、月線支撐、籌碼等，字數約 150-200 字，口吻專業扎實）",
  "global_status": [
    {
      "name": "指數名稱（例如：那斯達克）",
      "peak": "近期高點描述（例如：6/1日27,190點）",
      "desc": "近期走勢與支撐（例如：到季線反彈）"
    }
  ],
  "abc_wave_analysis": {
    "intro": "技術分析導言（描述追價買盤、洗盤起伏、多頭信心等，字數約 100 字）",
    "analysis": "ABC 波段具體推演列表（請用繁體中文 Markdown 格式撰寫多行。列出 A波修正、B波反彈、C波修正、季線支撐等具體推演區間）"
  },
  "fundamentals": {
    "gdp_growth": "GDP 成長率預測與評估描述",
    "earnings_growth": "企業獲利成長率預估描述",
    "ai_industry": "AI 產業基建與泡沫化研判描述",
    "summary": "基本面總結（字數約 100 字）"
  },
  "operation_advice": "具體操作建議與風險控管（例如：B波洗盤區間與季線買點評估、槓桿風險控制，字數約 120 字）",
  "thematic_categories": [
    {
      "category_name": "今日時序焦點題材名稱（例如：太空低軌衛星）",
      "highlight": "該題材近期催化劑或焦點亮點說明",
      "stocks": [
        {
          "code": "股票代碼（如 3491）",
          "name": "股票名稱（如 昇達科）",
          "role": "該股在題材中的關鍵技術角色或利基點"
        }
      ]
    }
  ]
}

請務必遵守：
1. 只能輸出合法 JSON 格式，不要包含額外說明文字或 Markdown 標籤。
2. 內容一律使用繁體中文。
3. 焦點題材 thematic_categories 中，應包含 2-3 個今日最熱門的焦點題材，每個題材列出 3-5 檔代表性個股。
"""

def extract_json_object(text: str) -> dict:
    cleaned = text.strip()
    start = cleaned.find('{')
    if start == -1:
        raise ValueError("找不到 JSON 起點")
    depth = 0
    in_string = False
    escape = False
    end = -1
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
    if end == -1:
        raise ValueError("JSON 結尾不完整")
    return json.loads(cleaned[start:end])

VLLM_ALIVE = None

def check_vllm_alive() -> bool:
    global VLLM_ALIVE
    if VLLM_ALIVE is not None:
        return VLLM_ALIVE
    print("正在檢測 vLLM 伺服器連線狀態...")
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
        }
        res = requests.post(
            VLLM_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=5
        )
        VLLM_ALIVE = (res.status_code == 200)
    except Exception:
        VLLM_ALIVE = False
    print(f"vLLM 伺服器連線檢測結果：{'可用' if VLLM_ALIVE else '不可用'}")
    return VLLM_ALIVE

def call_vllm_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000, temperature: float = 0.35) -> dict:
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
    return extract_json_object(content)

def generate_report():
    if not check_vllm_alive():
        raise RuntimeError("vLLM 伺服器未啟用或不可用，跳過每日大盤投研日報生成。")
    print("正在搜集今日市場與大盤數據...")
    queries = [
        "台股 大盤 技術分析 收盤",
        "那斯達克 費半 走勢 季線 支撐",
        "台灣 經濟成長率 企業盈餘 總經"
    ]
    
    search_context_parts = []
    for q in queries:
        try:
            print(f"搜尋：{q}")
            res = search(q)
            if res:
                search_context_parts.append(format_search_context(q, res))
        except Exception as e:
            print(f"搜尋失敗：{q}", e)
            
    search_context = "\n\n".join(search_context_parts)
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    user_prompt = f"""
【今日日期】: {today_str}
【實時搜尋資料】:
{search_context}

請根據上述搜集到的資訊，撰寫一份今日 ({today_str}) 的「每日投研大局觀」報告。
注意：必須包含加權指數研判、技術分析 ABC 波推演、美股主要指數近況、總體經濟/盈餘，以及 2-3 個當天有熱度且能對應台股概念股的「今日時序焦點題材」。
"""
    
    print("正在呼叫 LLM 進行大盤分析與報告生成...")
    report_data = call_vllm_json(SYSTEM_PROMPT, user_prompt)
    
    # Add ID and Date
    report_data["id"] = f"report-{today_str.replace('-', '')}"
    report_data["date"] = today_str
    
    # Load existing reports
    existing_reports = []
    if REPORT_FILE.exists():
        try:
            with open(REPORT_FILE, "r", encoding="utf-8") as f:
                existing_reports = json.load(f)
        except Exception as e:
            print("讀取既有報告失敗，建立新檔案", e)
            
    # Remove duplicate date if exists
    existing_reports = [r for r in existing_reports if r.get("date") != today_str]
    
    # Prepend new report to the top (newest first)
    existing_reports.insert(0, report_data)
    
    # Save back to file
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_reports, f, indent=2, ensure_ascii=False)
        
    print(f"今日投研日報生成完成！已儲存至 {REPORT_FILE}")

if __name__ == "__main__":
    generate_report()
