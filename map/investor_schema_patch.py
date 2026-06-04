from pathlib import Path

p = Path(r'D:\map\map_generator.py')
text = p.read_text(encoding='utf-8')

text = text.replace('''    "structure_layers": [
      {
        "name": "結構層名稱",
        "position": "在整體系統中的位置",
        "summary": "這一層的任務與關鍵價值",
        "key_points": ["重點1", "重點2"],
        "beneficiaries": ["受惠廠商類型1", "受惠廠商類型2"]
      }
    ],''', '''    "market_size_tam": "2027E 約 450 億美元 / 若無可靠依據請寫 待補資料",
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
    ],''')

text = text.replace('''    "timeline_phases": [
      {
        "phase": "設備建置期",
        "timeframe": "2025-2026",
        "summary": "這段時間市場在驗證什麼",
        "winners": ["設備廠", "加工廠"]
      }
    ],''', '''    "timeline_phases": [
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
    ],''')

text = text.replace('''      {
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
        "desc": "背景分析"
      }''', '''      {
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
      }''')

text = text.replace('''    enriched.setdefault("related_themes", [])
    enriched.setdefault("tech_lessons", [])''', '''    enriched.setdefault("related_themes", [])
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
    enriched.setdefault("tech_lessons", [])''')

text = text.replace('''    if not enriched["timeline_phases"]:
        enriched["timeline_phases"] = [
            {
                "phase": "觀察與驗證期",
                "timeframe": enriched.get("period", "觀察期"),
                "summary": "重點在於技術是否進入客戶驗證、試產或小量導入。",
                "winners": [s.get("name", "") for s in enriched["stocks"][:3] if s.get("name")],
            }
        ]''', '''    if not enriched["timeline_phases"]:
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
        ]''')

text = text.replace('''        enriched["structure_layers"] = [
            {
                "name": "供應鏈結構",
                "position": "由上游材料/設備延伸至中下游整合",
                "summary": "用供應鏈位置去理解誰先受惠、誰後受惠，而不是只看概念股名單。",
                "key_points": sectors[:5],
                "beneficiaries": sectors[:5],
            }
        ]''', '''        enriched["structure_layers"] = [
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
        ]''')

text = text.replace('''    return enriched''', '''    for layer in enriched["structure_layers"]:
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

    return enriched''')

text = text.replace('''  "structure_layers": [
    {"name": "", "position": "", "summary": "", "key_points": [""], "beneficiaries": [""]}
  ],
  "timeline_phases": [
    {"phase": "", "timeframe": "", "summary": "", "winners": [""]}
  ]''', '''  "structure_layers": [
    {"name": "", "position": "", "summary": "", "key_points": [""], "beneficiaries": [""], "pricing_power": "", "margin_profile": "", "value_capture": "", "entry_barrier": "", "leader_type": ""}
  ],
  "timeline_phases": [
    {"phase": "", "timeframe": "", "summary": "", "winners": [""], "investment_phase": "", "revenue_meaning": "", "watch_metric": "", "expected_market_focus": ""}
  ]''')

text = text.replace('''要求：
1. structure_layers 要有供應鏈位置感，不只是分類。
2. timeline_phases 要有驗證/導入/量產節奏。
3. 請偏向投資研究視角。
"""''', '''要求：
1. structure_layers 要有供應鏈位置感，不只是分類。
2. timeline_phases 要有驗證/導入/量產節奏。
3. 每個 structure layer 盡量補 pricing_power、margin_profile、value_capture、entry_barrier、leader_type。
4. 每個 timeline phase 盡量補 investment_phase、revenue_meaning、watch_metric、expected_market_focus。
5. 請偏向投資研究視角，不要只做技術教學。
"""''')

text = text.replace('''  "heat": "",
  "heat_score": 0,
  "heat_drivers": [""],
  "period": "",
  "thesis": "",
  "desc": "",
  "theme_tags": [""],''', '''  "heat": "",
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
  "theme_tags": [""],''')

text = text.replace('''要求：
1. heat_score 必須是 0-100 的整數。
2. capital_flow 至少 3 段，講清楚資金為何先後移動。
3. thesis 要像投資主論點，不是摘要重寫。
"""''', '''要求：
1. heat_score 必須是 0-100 的整數。
2. capital_flow 至少 3 段，講清楚資金為何先後移動。
3. thesis 要像投資主論點，不是摘要重寫。
4. 補 why_now、primary_value_capture、key_bottleneck、market_narrative。
5. 若 TAM / CAGR 缺乏可靠依據，可寫 待補資料，不可硬編假精準數字。
"""''')

text = text.replace('''      "desc": "背景分析"
    }}''', '''      "desc": "背景分析",
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
    }}''')

text = text.replace('''要求：
1. 若股票代號或公司簡稱不確定，就不要列。
2. sector / sectorId 要有可用分類意義。
3. pureLevel、barrierLevel 為 0-5 數值。
4. 最多輸出 12 檔。
"""''', '''要求：
1. 若股票代號或公司簡稱不確定，就不要列。
2. sector / sectorId 要有可用分類意義。
3. pureLevel、barrierLevel 為 0-5 數值。
4. 請盡量補 ai_revenue_exposure、gross_margin_impact、customer_concentration、pricing_power、substitution_risk、commercialization_phase、switching_cost、revenue_visibility。
5. 若缺乏可靠資料，請寫 待補資料 或 medium，不可編造精確數字。
6. 最多輸出 12 檔。
"""''')

text = text.replace('''        "desc": capital_data.get("desc", ""),
        "thesis": capital_data.get("thesis", ""),''', '''        "desc": capital_data.get("desc", ""),
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
        "evidence_confidence": capital_data.get("evidence_confidence", "medium"),''')

p.write_text(text, encoding='utf-8')
print('done')
