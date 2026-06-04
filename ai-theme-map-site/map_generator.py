import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

from search_provider import build_search_context_from_evidence, format_search_context, search

VLLM_URL = os.getenv("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
MODEL_NAME = os.getenv("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")
REPORT_FILE = os.getenv("MAP_REPORT_FILE", "report.txt")
REPO_FILE = os.getenv("MAP_REPO_FILE", "maps_repo.json")
TIMEOUT_SECONDS = int(os.getenv("MAP_TIMEOUT_SECONDS", "240"))
SEARCH_MODE = os.getenv("MAP_SEARCH_MODE", "local_only")
PIPELINE_MODE = os.getenv("MAP_PIPELINE_MODE", "multi_step")
MAX_TOKENS_PER_STEP = int(os.getenv("MAP_MAX_TOKENS_PER_STEP", "4000"))
EVIDENCE_DIR = Path(os.getenv("MAP_EVIDENCE_DIR", "evidence"))
TICKER_REGISTRY_FILE = Path(os.getenv("MAP_TICKER_REGISTRY", "ticker_registry_tw.json"))

BASE_SYSTEM_PROMPT = """
你是一個「自主進化投資主題地圖引擎」的核心研究代理。
你會根據主題種子，以及系統提供的搜尋上下文（若有），輸出高密度、可延展的投資主題地圖 JSON。

任務目標不是只列股票，而是建立一份可持續演化的主題地圖，讓後續系統能根據同一份資料：
1. 解釋技術教學
2. 呈現產業結構位置
3. 推演資金輪動與火勢變化
4. 擴充相關子主題

【共同硬性要求】
1. 嚴禁輸出 Markdown，只能輸出合法 JSON。
2. 股票代號與公司簡稱不得亂編；若不確定，寧可降低數量，也不要硬湊。
3. 內容必須使用繁體中文。
4. 生成內容要偏向研究工作台，而不是新聞摘要。
5. 若有提供搜尋上下文，請將其視為外部感知材料；若沒有，則以產業邏輯與供應鏈推理補足。
"""

FINAL_SCHEMA_PROMPT = """
【最終輸出 JSON 結構】
{
  "map_unique_id": {
    "title": "主題名稱",
    "date": "2026-05-26",
    "updated_at": "2026-05-26T00:00:00+08:00",
    "heat": "極度火熱 🔥",
    "heat_score": 88,
    "heat_drivers": ["驅動因子1", "驅動因子2"],
    "period": "設備建置期 / 材料驗證期 / 載板量產期",
    "desc": "主題核心摘要",
    "thesis": "一句話投資主論點",
    "icon": "cpu",
    "color": "from-cyan-500 to-indigo-600",
    "theme_tags": ["先進封裝", "玻璃基板", "CPO"],
    "trigger_events": ["可能觸發火勢上升的事件1", "事件2"],
    "risks": ["主要風險1", "主要風險2"],
    "watch_signals": ["觀察訊號1", "觀察訊號2"],
    "related_themes": ["相關主題1", "相關主題2"],
    "tech_lessons": [
      {
        "title": "技術教學標題",
        "subtitle": "技術位置或用途",
        "problem": "它在解決什麼問題",
        "mechanism": "原理或運作方式",
        "why_now": "為什麼現在重要",
        "desc": "整體教學摘要"
      }
    ],
    "market_size_tam": "2027E 約 450 億美元 / 若無可靠依據請寫 待補資料",
    "market_size_tam_source_type": "analyst_estimate / official / llm_inference / manual_review",
    "market_cagr": "2025-2028 CAGR 28% / 若無可靠依據請寫 待補資料",
    "market_cagr_source_type": "analyst_estimate / official / llm_inference / manual_review",
    "theme_stage": "概念期 / 驗證期 / 放量期 / 財報貢獻期",
    "why_now": "為什麼現在重要",
    "key_bottleneck": "核心瓶頸",
    "primary_value_capture": "哪一層最能賺到錢",
    "market_narrative": "從商業與產業角度描述題材演變",
    "evidence_confidence": "low / medium / high",
    "structure_layers": [
      {
        "name": "結構層名稱",
        "position": "在整體系統中的位置",
        "summary": "這一層的任務與關鍵價值",
        "key_points": ["重點1", "重點2"],
        "beneficiaries": ["受惠廠商類型1", "受惠廠商類型2"],
        "pricing_power": "high / medium / low",
        "margin_profile": "利潤率輪廓",
        "value_capture": "高 / 中 / 低",
        "entry_barrier": "進入門檻",
        "leader_type": "誰通常是這層贏家"
      }
    ],
    "capital_flow": [
      {
        "phase": "第一階段",
        "timeframe": "2025-2026",
        "focus": "資金聚焦在哪一層",
        "logic": "為什麼先炒這裡",
        "beneficiary_groups": ["設備", "加工"]
      }
    ],
    "timeline_phases": [
      {
        "phase": "設備建置期",
        "timeframe": "2025-2026",
        "summary": "這段時間市場在驗證什麼",
        "winners": ["設備廠", "加工廠"],
        "investment_phase": "概念期 / 驗證期 / 放量期 / 財報貢獻期",
        "revenue_meaning": "此階段對營收的意義",
        "watch_metric": "投資人該觀察什麼",
        "expected_market_focus": "市場此時最在意什麼"
      }
    ],
    "concepts": [{"title": "", "subtitle": "", "desc": ""}],
    "stocks": [
      {
        "id": "3037",
        "name": "公司簡稱",
        "code": "3037",
        "sector": "細分板塊分類",
        "sectorId": "carrier",
        "role": "關鍵角色",
        "timeframe": "驗證/放量時程",
        "pureLevel": 4.5,
        "barrierLevel": 4.0,
        "pros": "優勢",
        "cons": "風險",
        "catalyst": "催化劑",
        "desc": "背景分析",
        "ai_revenue_exposure": "2026E 15-25% / 若缺資料請寫 待補資料",
        "ai_revenue_exposure_source_type": "analyst_estimate / official / llm_inference / manual_review",
        "gross_margin_impact": "AI 升級是否帶動毛利率改善",
        "customer_concentration": "客戶集中度與依賴對象",
        "sole_supplier": false,
        "pricing_power": "high / medium / low",
        "value_capture_score": 4.2,
        "substitution_risk": "high / medium / low",
        "commercialization_phase": "2026 H1 驗證 / 2026 H2 放量",
        "capacity_share_hint": "產能或供應位置提示",
        "switching_cost": "high / medium / low",
        "revenue_visibility": "high / medium / low"
      }
    ],
    "sources": [
      {
        "type": "model-inference",
        "label": "本地 vLLM 推理",
        "note": "可選擇搭配搜尋上下文"
      }
    ]
  }
}
"""


def load_topic_seed() -> str | None:
    if not os.path.exists(REPORT_FILE):
        print(f"找不到發想檔案：{REPORT_FILE}")
        return None

    for encoding in ("utf-8", "cp950"):
        try:
            with open(REPORT_FILE, "r", encoding=encoding) as f:
                return f.read().strip()
        except Exception:
            continue

    print("無法讀取發想檔案")
    return None


def strip_markdown_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("\n", 1)[0] if "\n" in cleaned else cleaned
    return cleaned.strip()


def slugify_topic(text: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "_", text).strip("_")
    normalized = normalized[:48] if normalized else "map"
    return f"map_{normalized}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def default_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = strip_markdown_fence(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find('{')
        if start == -1:
            raise
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
            raise
        return json.loads(cleaned[start:end])


def call_vllm_json(system_prompt: str, user_prompt: str, max_tokens: int = MAX_TOKENS_PER_STEP, temperature: float = 0.2) -> Dict[str, Any]:
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
    result_data = response.json()
    raw_content = result_data["choices"][0]["message"]["content"].strip()
    try:
        return extract_json_object(raw_content)
    except Exception:
        with open("last_vllm_raw_output.txt", "w", encoding="utf-8") as f:
            f.write(raw_content)
        raise


def enrich_map(map_id: str, map_data: Dict[str, Any]) -> Dict[str, Any]:
    now_iso = datetime.now().astimezone().isoformat(timespec="seconds")
    enriched = dict(map_data)
    enriched.setdefault("updated_at", now_iso)
    enriched.setdefault("heat", "中度關注")
    enriched.setdefault("heat_score", 60)
    enriched.setdefault("heat_drivers", [])
    enriched.setdefault("period", "觀察期")
    enriched.setdefault("desc", "")
    enriched.setdefault("thesis", enriched.get("desc", "")[:120])
    enriched.setdefault("icon", "cpu")
    enriched.setdefault("color", "from-cyan-500 to-indigo-600")
    enriched.setdefault("theme_tags", [])
    enriched.setdefault("trigger_events", [])
    enriched.setdefault("risks", [])
    enriched.setdefault("watch_signals", [])
    enriched.setdefault("related_themes", [])
    enriched.setdefault("market_size_tam", "待補資料")
    enriched.setdefault("market_size_tam_source_type", "llm_inference")
    enriched.setdefault("market_cagr", "待補資料")
    enriched.setdefault("market_cagr_source_type", "llm_inference")
    enriched.setdefault("theme_stage", enriched.get("period", "觀察期"))
    enriched.setdefault("why_now", enriched.get("thesis", "待補資料"))
    enriched.setdefault("key_bottleneck", "待補資料")
    enriched.setdefault("primary_value_capture", "待補資料")
    enriched.setdefault("market_narrative", enriched.get("desc", ""))
    enriched.setdefault("evidence_confidence", "medium")
    enriched.setdefault("tech_lessons", [])
    enriched.setdefault("structure_layers", [])
    enriched.setdefault("capital_flow", [])
    enriched.setdefault("timeline_phases", [])
    enriched.setdefault("concepts", [])
    enriched.setdefault("stocks", [])
    enriched.setdefault("sources", [{"type": "model-inference", "label": "本地 vLLM 推理", "note": f"search_mode={SEARCH_MODE}; pipeline_mode={PIPELINE_MODE}"}])

    enriched["heat_drivers"] = default_list(enriched.get("heat_drivers"))
    enriched["theme_tags"] = default_list(enriched.get("theme_tags"))
    enriched["trigger_events"] = default_list(enriched.get("trigger_events"))
    enriched["risks"] = default_list(enriched.get("risks"))
    enriched["watch_signals"] = default_list(enriched.get("watch_signals"))
    enriched["related_themes"] = default_list(enriched.get("related_themes"))
    enriched["tech_lessons"] = default_list(enriched.get("tech_lessons"))
    enriched["structure_layers"] = default_list(enriched.get("structure_layers"))
    enriched["capital_flow"] = default_list(enriched.get("capital_flow"))
    enriched["timeline_phases"] = default_list(enriched.get("timeline_phases"))
    enriched["concepts"] = default_list(enriched.get("concepts"))
    enriched["stocks"] = default_list(enriched.get("stocks"))
    enriched["sources"] = default_list(enriched.get("sources"))

    if not enriched["concepts"] and enriched["tech_lessons"]:
        enriched["concepts"] = [
            {
                "title": x.get("title", "未命名概念"),
                "subtitle": x.get("subtitle", ""),
                "desc": x.get("desc", ""),
            }
            for x in enriched["tech_lessons"][:3]
        ]

    if not enriched["tech_lessons"] and enriched["concepts"]:
        enriched["tech_lessons"] = [
            {
                "title": c.get("title", "未命名技術"),
                "subtitle": c.get("subtitle", ""),
                "problem": c.get("desc", ""),
                "mechanism": c.get("desc", ""),
                "why_now": "與新一輪產業升級與資本支出有關",
                "desc": c.get("desc", ""),
            }
            for c in enriched["concepts"][:3]
        ]

    if not enriched["capital_flow"]:
        enriched["capital_flow"] = [
            {
                "phase": "第一階段",
                "timeframe": enriched.get("period", "觀察期"),
                "focus": "先反映最早能接單或最容易被市場理解的環節",
                "logic": "資金通常先從設備、加工或最純的題材股開始點火，再往材料與量產整合者擴散",
                "beneficiary_groups": sorted(list({s.get("sector", "未分類") for s in enriched["stocks"][:4]})),
            }
        ]

    if not enriched["timeline_phases"]:
        enriched["timeline_phases"] = [
            {
                "phase": "觀察與驗證期",
                "timeframe": enriched.get("period", "觀察期"),
                "summary": "重點在於技術是否進入客戶驗證、試產或小量導入。",
                "winners": [s.get("name", "") for s in enriched["stocks"][:3] if s.get("name")],
                "investment_phase": "驗證期",
                "revenue_meaning": "尚未大幅貢獻營收，以驗證與導入進度為主。",
                "watch_metric": "送樣、驗證、設計導入、初期接單",
                "expected_market_focus": "市場會先交易想像與卡位進度",
            }
        ]

    if not enriched["structure_layers"]:
        sectors = []
        seen = set()
        for stock in enriched["stocks"]:
            sec = stock.get("sector", "未分類")
            if sec not in seen:
                seen.add(sec)
                sectors.append(sec)
        enriched["structure_layers"] = [
            {
                "name": "供應鏈結構",
                "position": "由上游材料/設備延伸至中下游整合",
                "summary": "用供應鏈位置去理解誰先受惠、誰後受惠，而不是只看概念股名單。",
                "key_points": sectors[:5],
                "beneficiaries": sectors[:5],
                "pricing_power": "medium",
                "margin_profile": "待補資料",
                "value_capture": "中",
                "entry_barrier": "待補資料",
                "leader_type": "具規格、驗證與量產能力者",
            }
        ]

    for layer in enriched["structure_layers"]:
        if isinstance(layer, dict):
            layer.setdefault("pricing_power", "medium")
            layer.setdefault("margin_profile", "待補資料")
            layer.setdefault("value_capture", "中")
            layer.setdefault("entry_barrier", "待補資料")
            layer.setdefault("leader_type", "待補資料")

    for phase in enriched["timeline_phases"]:
        if isinstance(phase, dict):
            phase.setdefault("investment_phase", phase.get("phase", "驗證期"))
            phase.setdefault("revenue_meaning", "待補資料")
            phase.setdefault("watch_metric", "待補資料")
            phase.setdefault("expected_market_focus", "待補資料")

    for stock in enriched["stocks"]:
        if isinstance(stock, dict):
            stock.setdefault("ai_revenue_exposure", "待補資料")
            stock.setdefault("ai_revenue_exposure_source_type", "llm_inference")
            stock.setdefault("gross_margin_impact", "待補資料")
            stock.setdefault("customer_concentration", "待補資料")
            stock.setdefault("sole_supplier", False)
            stock.setdefault("pricing_power", "medium")
            stock.setdefault("value_capture_score", 0)
            stock.setdefault("substitution_risk", "medium")
            stock.setdefault("commercialization_phase", stock.get("timeframe", "待補資料"))
            stock.setdefault("capacity_share_hint", "待補資料")
            stock.setdefault("switching_cost", "medium")
            stock.setdefault("revenue_visibility", "medium")

    return enriched


def normalize_generated_map(payload: Dict[str, Any], topic_seed: str) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("模型輸出不是 JSON object")

    if len(payload) == 1:
        only_key = next(iter(payload.keys()))
        only_val = payload[only_key]
        if isinstance(only_val, dict) and "title" in only_val:
            return {only_key: enrich_map(only_key, only_val)}

    if "title" in payload:
        safe_id = slugify_topic(topic_seed)
        return {safe_id: enrich_map(safe_id, payload)}

    normalized = {}
    for key, value in payload.items():
        if isinstance(value, dict) and "title" in value:
            normalized[key] = enrich_map(key, value)

    if not normalized:
        raise ValueError("找不到合法地圖結構")

    return normalized


def validate_map_repository(repo: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    if not isinstance(repo, dict):
        return False, ["repository 必須是 dict"]

    required_root = ["title", "date", "heat", "period", "desc", "icon", "color", "concepts", "stocks"]
    for map_id, map_data in repo.items():
        if not isinstance(map_data, dict):
            errors.append(f"{map_id}: map data 必須是 object")
            continue
        for key in required_root:
            if key not in map_data:
                errors.append(f"{map_id}: 缺少欄位 {key}")
        if "concepts" in map_data and not isinstance(map_data["concepts"], list):
            errors.append(f"{map_id}: concepts 必須是 list")
        if "stocks" in map_data and not isinstance(map_data["stocks"], list):
            errors.append(f"{map_id}: stocks 必須是 list")
        if "heat_score" in map_data and not isinstance(map_data["heat_score"], int):
            errors.append(f"{map_id}: heat_score 必須是 int")
    return len(errors) == 0, errors


def load_repository() -> Dict[str, Any]:
    if not os.path.exists(REPO_FILE):
        return {}
    try:
        with open(REPO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            normalized = {}
            for key, value in data.items():
                if isinstance(value, dict) and "title" in value:
                    normalized[key] = enrich_map(key, value)
            return normalized
    except Exception as e:
        print(f"讀取既有數據庫失敗：{e}")
        return {}


def save_repository(repo_data: Dict[str, Any]) -> None:
    with open(REPO_FILE, "w", encoding="utf-8") as f:
        json.dump(repo_data, f, indent=2, ensure_ascii=False)


def load_ticker_registry() -> Dict[str, Any]:
    if not TICKER_REGISTRY_FILE.exists():
        return {}
    try:
        return json.loads(TICKER_REGISTRY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def normalize_name_for_match(name: str) -> str:
    value = str(name or "").strip()
    value = value.replace(" ", "")
    value = value.replace("股份有限公司", "")
    value = value.replace("有限公司", "")
    value = value.replace("電子", "")
    value = value.replace("科技", "")
    value = value.replace("控股", "")
    value = value.replace("-KY", "")
    value = value.replace("*", "")
    return value.lower()


def stock_matches_registry(stock: Dict[str, Any], registry_entry: Dict[str, Any]) -> bool:
    stock_name = normalize_name_for_match(stock.get("name", ""))
    candidate_names = [registry_entry.get("name", "")] + registry_entry.get("aliases", [])
    normalized_candidates = [normalize_name_for_match(x) for x in candidate_names if x]
    return stock_name in normalized_candidates if stock_name else False


def validate_stocks_with_registry(stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    registry = load_ticker_registry()
    if not registry:
        return stocks

    validated: List[Dict[str, Any]] = []
    seen_codes = set()
    for stock in stocks:
        if not isinstance(stock, dict):
            continue
        code = str(stock.get("code") or stock.get("id") or "").strip()
        if not code or code in seen_codes:
            continue
        entry = registry.get(code)
        if not isinstance(entry, dict):
            continue
        if not stock_matches_registry(stock, entry):
            continue
        normalized_stock = dict(stock)
        normalized_stock["id"] = code
        normalized_stock["code"] = code
        normalized_stock["name"] = entry.get("name", stock.get("name", ""))
        normalized_stock.setdefault("market", entry.get("market", ""))
        validated.append(normalized_stock)
        seen_codes.add(code)
    return validated


def extract_evidence_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    items: List[Dict[str, Any]] = []
    for bucket in ["official_sources", "global_news", "taiwan_finance_news", "youtube_sources", "analyst_sources", "community_sources", "other"]:
        rows = payload.get(bucket, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                item = dict(row)
                item.setdefault("bucket", bucket)
                items.append(item)
    return items


def extract_evidence_text(payload: Dict[str, Any]) -> str:
    parts: List[str] = []
    for item in extract_evidence_items(payload):
        for key in ["title", "snippet", "content", "source_name"]:
            value = str(item.get(key, "")).strip()
            if value:
                parts.append(value)
    return "\n".join(parts)


def stock_supported_by_evidence(stock: Dict[str, Any], evidence_text: str, registry_entry: Dict[str, Any]) -> bool:
    hay = normalize_name_for_match(evidence_text)
    if not hay:
        return False
    candidates = [stock.get("name", ""), registry_entry.get("name", "")] + registry_entry.get("aliases", [])
    for candidate in candidates:
        needle = normalize_name_for_match(candidate)
        if needle and needle in hay:
            return True
    return False


def collect_stock_source_refs(stock: Dict[str, Any], evidence_payload: Dict[str, Any], registry_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    candidates = [stock.get("name", ""), registry_entry.get("name", "")] + registry_entry.get("aliases", [])
    candidate_needles = [normalize_name_for_match(x) for x in candidates if normalize_name_for_match(x)]
    for item in extract_evidence_items(evidence_payload):
        blob = normalize_name_for_match(" ".join([
            str(item.get("title", "")),
            str(item.get("snippet", "")),
            str(item.get("content", "")),
            str(item.get("source_name", "")),
        ]))
        if not blob:
            continue
        if not any(needle in blob for needle in candidate_needles):
            continue
        source_name = item.get("source_name", "")
        title = item.get("title", "")
        analyst_name = ""
        if str(source_name).strip().lower() == "analyst":
            analyst_name = str(title).split("：")[-1].split("-")[0].strip() if str(title).strip() else ""
        refs.append({
            "source_type": item.get("bucket", item.get("source_group", "other")),
            "source_name": source_name,
            "title": title,
            "url": item.get("url", ""),
            "published_at": item.get("published_at", ""),
            "analyst_name": analyst_name,
        })
    return refs[:6]


def classify_stock_evidence_type(source_refs: List[Dict[str, Any]]) -> str:
    if not source_refs:
        return "inferred"
    direct_types = {"official_sources", "global_news", "taiwan_finance_news", "youtube_sources", "analyst_sources", "community_sources"}
    if any(ref.get("source_type") in direct_types for ref in source_refs):
        return "direct"
    return "inferred"


def pick_theme_expansion_candidates(topic_seed: str, registry: Dict[str, Any], existing_codes: set[str]) -> List[Dict[str, Any]]:
    rules = [
        {
            "match": ["cpo", "矽光子", "高速傳輸", "光通訊"],
            "keywords": ["光", "通訊", "網通", "光電", "電子", "科技"],
            "limit": 10,
        },
        {
            "match": ["電網", "重電", "能源"],
            "keywords": ["電", "能源", "機電", "重電", "工程", "工業"],
            "limit": 10,
        },
        {
            "match": ["國防", "無人", "軍工", "衛星"],
            "keywords": ["航太", "電機", "精密", "光電", "通訊", "電子", "工業"],
            "limit": 10,
        },
        {
            "match": ["封裝", "hbm", "散熱"],
            "keywords": ["電子", "半導體", "材料", "散熱", "電", "科技"],
            "limit": 10,
        },
        {
            "match": ["友岸", "東協", "製造重組", "china+1"],
            "keywords": ["工業", "機電", "電子", "科技", "物流", "電腦"],
            "limit": 10,
        },
    ]
    seed = topic_seed.lower()
    selected_rule = None
    for rule in rules:
        if any(token.lower() in seed for token in rule["match"]):
            selected_rule = rule
            break
    if not selected_rule:
        return []

    candidates: List[Dict[str, Any]] = []
    for code, entry in registry.items():
        if code in existing_codes or not isinstance(entry, dict):
            continue
        name = str(entry.get("name", ""))
        industry = str(entry.get("industry", ""))
        hay = f"{name} {industry} {' '.join(entry.get('aliases', []))}".lower()
        if any(keyword.lower() in hay for keyword in selected_rule["keywords"]):
            candidates.append({
                "id": code,
                "code": code,
                "name": name,
                "sector": industry or "延伸供應鏈",
                "sectorId": "extended",
                "role": "同主題供應鏈延伸受惠",
                "timeframe": "中期觀察",
                "pureLevel": 2.8,
                "barrierLevel": 2.6,
                "pros": "主題延伸受惠與族群聯動機會",
                "cons": "非直接證據股，需持續驗證",
                "catalyst": "主題擴散、族群輪動、訂單外溢",
                "desc": f"依主題 {topic_seed} 之供應鏈/族群關聯補入的延伸觀察股。",
                "market": entry.get("market", ""),
                "stock_tier": "extended",
                "evidence_type": "inferred",
                "sources": [],
            })
        if len(candidates) >= selected_rule["limit"]:
            break
    return candidates


def filter_stocks_by_evidence(stocks: List[Dict[str, Any]], evidence_payload: Dict[str, Any] | None, topic_seed: str = "") -> List[Dict[str, Any]]:
    registry = load_ticker_registry()
    if not registry:
        return stocks

    filtered: List[Dict[str, Any]] = []
    inferred: List[Dict[str, Any]] = []
    evidence_text = extract_evidence_text(evidence_payload or {})
    for stock in stocks:
        code = str(stock.get("code") or stock.get("id") or "").strip()
        entry = registry.get(code)
        if not isinstance(entry, dict):
            continue
        source_refs = collect_stock_source_refs(stock, evidence_payload or {}, entry)
        if source_refs:
            item = dict(stock)
            item["evidence_type"] = classify_stock_evidence_type(source_refs)
            item["sources"] = source_refs
            item["stock_tier"] = "core"
            filtered.append(item)
            continue
        item = dict(stock)
        item["evidence_type"] = "inferred"
        item["sources"] = []
        item["stock_tier"] = "extended" if evidence_text else item.get("stock_tier", "extended")
        inferred.append(item)

    merged = filtered + inferred
    existing_codes = {str(x.get("code") or x.get("id") or "").strip() for x in merged}
    if topic_seed and len(merged) < 12:
        merged.extend(pick_theme_expansion_candidates(topic_seed, registry, existing_codes))
    return merged[:18]


def slugify_evidence_name(text: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in text).strip("_")
    return safe[:80] or "theme"


def load_theme_evidence(topic_seed: str) -> Dict[str, Any] | None:
    path = EVIDENCE_DIR / f"theme_{slugify_evidence_name(topic_seed)}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_search_context(topic_seed: str) -> str:
    if SEARCH_MODE == "search_augmented":
        evidence_payload = load_theme_evidence(topic_seed)
        if evidence_payload:
            return build_search_context_from_evidence(topic_seed, evidence_payload)
        results = search(topic_seed)
        return format_search_context(topic_seed, results)
    return f"查詢主題：{topic_seed}\n目前沒有外部搜尋結果，請以既有知識與供應鏈推理完成分析。"


def generate_lessons(topic_seed: str, search_context: str) -> Dict[str, Any]:
    system_prompt = BASE_SYSTEM_PROMPT + "\n你現在只負責產出技術教學層。"
    user_prompt = f"""
請針對以下主題，只輸出教學層 JSON：
{{
  "tech_lessons": [
    {{"title": "", "subtitle": "", "problem": "", "mechanism": "", "why_now": "", "desc": ""}}
  ],
  "concepts": [
    {{"title": "", "subtitle": "", "desc": ""}}
  ]
}}

【主題種子】
{topic_seed}

【搜尋上下文】
{search_context}

要求：
1. 最多輸出 4 個教學模組。
2. 要講清楚技術在解決什麼問題，以及為何現在重要。
3. concepts 應為 tech_lessons 的濃縮版。
"""
    return call_vllm_json(system_prompt, user_prompt)


def generate_structure(topic_seed: str, search_context: str, lessons_data: Dict[str, Any]) -> Dict[str, Any]:
    system_prompt = BASE_SYSTEM_PROMPT + "\n你現在只負責產出結構分層與商用時程。"
    user_prompt = f"""
請針對以下主題，只輸出結構層與時程層 JSON：
{{
  "structure_layers": [
    {{"name": "", "position": "", "summary": "", "key_points": [""], "beneficiaries": [""]}}
  ],
  "timeline_phases": [
    {{"phase": "", "timeframe": "", "summary": "", "winners": [""]}}
  ]
}}

【主題種子】
{topic_seed}

【搜尋上下文】
{search_context}

【技術教學輸入】
{json.dumps(lessons_data, ensure_ascii=False)}

要求：
1. structure_layers 要有供應鏈位置感，不只是分類。
2. timeline_phases 要有驗證/導入/量產節奏。
3. 每個 structure layer 盡量補 pricing_power、margin_profile、value_capture、entry_barrier、leader_type。
4. 每個 timeline phase 盡量補 investment_phase、revenue_meaning、watch_metric、expected_market_focus。
5. 請偏向投資研究視角，不要只做技術教學。
"""
    return call_vllm_json(system_prompt, user_prompt)


def generate_capital_flow(topic_seed: str, search_context: str, lessons_data: Dict[str, Any], structure_data: Dict[str, Any]) -> Dict[str, Any]:
    system_prompt = BASE_SYSTEM_PROMPT + "\n你現在只負責產出資金流、火勢與觀察框架。"
    user_prompt = f"""
請針對以下主題，只輸出資金流與火勢推演 JSON：
{{
  "heat": "",
  "heat_score": 0,
  "heat_drivers": [""],
  "period": "",
  "thesis": "",
  "desc": "",
  "market_size_tam": "",
  "market_size_tam_source_type": "",
  "market_cagr": "",
  "market_cagr_source_type": "",
  "theme_stage": "",
  "why_now": "",
  "key_bottleneck": "",
  "primary_value_capture": "",
  "market_narrative": "",
  "evidence_confidence": "",
  "theme_tags": [""],
  "trigger_events": [""],
  "risks": [""],
  "watch_signals": [""],
  "related_themes": [""],
  "capital_flow": [
    {{"phase": "", "timeframe": "", "focus": "", "logic": "", "beneficiary_groups": [""]}}
  ]
}}

【主題種子】
{topic_seed}

【搜尋上下文】
{search_context}

【技術教學輸入】
{json.dumps(lessons_data, ensure_ascii=False)}

【結構輸入】
{json.dumps(structure_data, ensure_ascii=False)}

要求：
1. heat_score 必須是 0-100 的整數。
2. capital_flow 至少 3 段，講清楚資金為何先後移動。
3. thesis 要像投資主論點，不是摘要重寫。
4. 補 why_now、primary_value_capture、key_bottleneck、market_narrative。
5. 若 TAM / CAGR 缺乏可靠依據，可寫 待補資料，不可硬編假精準數字。
"""
    return call_vllm_json(system_prompt, user_prompt)


def generate_stocks(topic_seed: str, search_context: str, lessons_data: Dict[str, Any], structure_data: Dict[str, Any], capital_data: Dict[str, Any]) -> Dict[str, Any]:
    system_prompt = BASE_SYSTEM_PROMPT + "\n你現在只負責輸出概念股映射。若不確定股票，不可亂編。"
    user_prompt = f"""
請針對以下主題，只輸出股票映射 JSON：
{{
  "stocks": [
    {{
      "id": "3037",
      "name": "公司簡稱",
      "code": "3037",
      "sector": "細分板塊分類",
      "sectorId": "carrier",
      "role": "關鍵角色",
      "timeframe": "驗證/放量時程",
      "pureLevel": 4.5,
      "barrierLevel": 4.0,
      "pros": "優勢",
      "cons": "風險",
      "catalyst": "催化劑",
      "desc": "背景分析",
      "ai_revenue_exposure": "",
      "ai_revenue_exposure_source_type": "",
      "gross_margin_impact": "",
      "customer_concentration": "",
      "sole_supplier": false,
      "pricing_power": "",
      "value_capture_score": 0,
      "substitution_risk": "",
      "commercialization_phase": "",
      "capacity_share_hint": "",
      "switching_cost": "",
      "revenue_visibility": ""
    }}
  ]
}}

【主題種子】
{topic_seed}

【搜尋上下文】
{search_context}

【技術教學輸入】
{json.dumps(lessons_data, ensure_ascii=False)}

【結構輸入】
{json.dumps(structure_data, ensure_ascii=False)}

【資金流輸入】
{json.dumps(capital_data, ensure_ascii=False)}

要求：
1. 若股票代號或公司簡稱不確定，就不要列。
2. sector / sectorId 要有可用分類意義。
3. pureLevel、barrierLevel 為 0-5 數值。
4. 請盡量補 ai_revenue_exposure、gross_margin_impact、customer_concentration、pricing_power、substitution_risk、commercialization_phase、switching_cost、revenue_visibility。
5. 若缺乏可靠資料，請寫 待補資料 或 medium，不可編造精確數字。
6. 最多輸出 12 檔。
"""
    return call_vllm_json(system_prompt, user_prompt)


def merge_map(topic_seed: str, search_context: str, lessons_data: Dict[str, Any], structure_data: Dict[str, Any], capital_data: Dict[str, Any], stocks_data: Dict[str, Any]) -> Dict[str, Any]:
    map_id = slugify_topic(topic_seed)
    now = datetime.now().astimezone()
    final_map = {
        "title": capital_data.get("title") or topic_seed[:80],
        "date": now.strftime("%Y-%m-%d"),
        "updated_at": now.isoformat(timespec="seconds"),
        "heat": capital_data.get("heat", "中度關注"),
        "heat_score": int(capital_data.get("heat_score", 60)) if str(capital_data.get("heat_score", "")).isdigit() else 60,
        "heat_drivers": default_list(capital_data.get("heat_drivers")),
        "period": capital_data.get("period", "觀察期"),
        "desc": capital_data.get("desc", ""),
        "thesis": capital_data.get("thesis", ""),
        "market_size_tam": capital_data.get("market_size_tam", "待補資料"),
        "market_size_tam_source_type": capital_data.get("market_size_tam_source_type", "llm_inference"),
        "market_cagr": capital_data.get("market_cagr", "待補資料"),
        "market_cagr_source_type": capital_data.get("market_cagr_source_type", "llm_inference"),
        "theme_stage": capital_data.get("theme_stage", capital_data.get("period", "觀察期")),
        "why_now": capital_data.get("why_now", capital_data.get("thesis", "待補資料")),
        "key_bottleneck": capital_data.get("key_bottleneck", "待補資料"),
        "primary_value_capture": capital_data.get("primary_value_capture", "待補資料"),
        "market_narrative": capital_data.get("market_narrative", capital_data.get("desc", "")),
        "evidence_confidence": capital_data.get("evidence_confidence", "medium"),
        "icon": capital_data.get("icon", "cpu"),
        "color": capital_data.get("color", "from-cyan-500 to-indigo-600"),
        "theme_tags": default_list(capital_data.get("theme_tags")),
        "trigger_events": default_list(capital_data.get("trigger_events")),
        "risks": default_list(capital_data.get("risks")),
        "watch_signals": default_list(capital_data.get("watch_signals")),
        "related_themes": default_list(capital_data.get("related_themes")),
        "tech_lessons": default_list(lessons_data.get("tech_lessons")),
        "structure_layers": default_list(structure_data.get("structure_layers")),
        "capital_flow": default_list(capital_data.get("capital_flow")),
        "timeline_phases": default_list(structure_data.get("timeline_phases")),
        "concepts": default_list(lessons_data.get("concepts")),
        "stocks": filter_stocks_by_evidence(
            validate_stocks_with_registry(default_list(stocks_data.get("stocks"))),
            load_theme_evidence(topic_seed),
            topic_seed,
        )[:18],
        "sources": [
            {
                "type": "model-inference",
                "label": "本地 vLLM 多步推理",
                "note": f"search_mode={SEARCH_MODE}; pipeline_mode={PIPELINE_MODE}",
            },
            {
                "type": "context",
                "label": "search_context",
                "note": search_context[:500],
            },
        ],
    }
    return {map_id: final_map}


def build_user_prompt_single_step(topic_seed: str, search_context: str) -> str:
    return (
        "請根據以下主題，產出一份可持續演化的投資主題地圖。"
        "請優先吸收系統提供的搜尋上下文，再用產業邏輯、供應鏈拆解、技術教學與資金輪動推理補足。\n\n"
        f"{search_context}\n\n"
        "請務必完整填寫 tech_lessons、structure_layers、capital_flow、timeline_phases、stocks。\n\n"
        + FINAL_SCHEMA_PROMPT + f"\n\n【主題種子】\n{topic_seed}"
    )


def request_map_single_step(topic_seed: str, search_context: str) -> Dict[str, Any]:
    return call_vllm_json(BASE_SYSTEM_PROMPT + "\n你現在要一次輸出完整地圖。\n" + FINAL_SCHEMA_PROMPT, build_user_prompt_single_step(topic_seed, search_context), max_tokens=8000, temperature=0.25)


def request_map_multi_step(topic_seed: str, search_context: str) -> Dict[str, Any]:
    print("[pipeline] step1 lessons")
    lessons_data = generate_lessons(topic_seed, search_context)
    print("[pipeline] step2 structure")
    structure_data = generate_structure(topic_seed, search_context, lessons_data)
    print("[pipeline] step3 capital_flow")
    capital_data = generate_capital_flow(topic_seed, search_context, lessons_data, structure_data)
    print("[pipeline] step4 stocks")
    stocks_data = generate_stocks(topic_seed, search_context, lessons_data, structure_data, capital_data)
    print("[pipeline] step5 merge")
    return merge_map(topic_seed, search_context, lessons_data, structure_data, capital_data, stocks_data)


def main() -> None:
    topic_seed = load_topic_seed()
    if not topic_seed:
        return

    print(f"議題種子：{topic_seed}")
    print(f"使用本地 vLLM：{VLLM_URL}")
    print(f"模型：{MODEL_NAME}")
    print(f"搜尋模式：{SEARCH_MODE}")
    print(f"生成管線：{PIPELINE_MODE}")

    try:
        search_context = get_search_context(topic_seed)
        if PIPELINE_MODE == "single_step":
            generated = request_map_single_step(topic_seed, search_context)
        else:
            generated = request_map_multi_step(topic_seed, search_context)

        normalized = normalize_generated_map(generated, topic_seed)
        valid, errors = validate_map_repository(normalized)
        if not valid:
            print("模型輸出通過 JSON 解析，但結構驗證失敗：")
            for err in errors:
                print(f"- {err}")
            return

        repo = load_repository()
        repo.update(normalized)
        save_repository(repo)
        print(f"數據庫更新成功，目前共有 {len(repo)} 個主題地圖。")
    except requests.exceptions.RequestException as e:
        print(f"vLLM 請求失敗：{e}")
    except json.JSONDecodeError as e:
        print(f"模型輸出不是合法 JSON：{e}")
    except Exception as e:
        print(f"執行失敗：{e}")


if __name__ == "__main__":
    main()
