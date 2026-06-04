import json
from pathlib import Path
from collections import OrderedDict

repo_path = Path(r"D:\map\maps_repo.json")
repo = json.loads(repo_path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)

key = "map_vera_rubin_ai_rack_scale_20260526_2201"
repo[key] = {
  "title": "Vera Rubin 機櫃級 AI 升級追蹤",
  "date": "2026-05-26",
  "updated_at": "2026-05-26T22:01:00+08:00",
  "heat": "Vera Rubin 機櫃級 AI 升級追蹤",
  "heat_score": 93,
  "heat_drivers": [
    "NVIDIA Vera Rubin 平台把 AI 基礎設施升級從單機板推向 rack-scale system",
    "高功耗 GPU 與整櫃設計同步拉動液冷、電源備援、連接器與高速互連規格升級",
    "ODM 與雲端業者開始從單一伺服器採購轉向整機櫃交付與模組化部署",
    "市場資金將從 GPU 主晶片擴散到散熱、供電、機櫃整合、矽光子與測試驗證供應鏈"
  ],
  "period": "2026 Q2 - 2027",
  "desc": "本主題專門追蹤 NVIDIA Vera Rubin 將 AI 伺服器推向機櫃級整合後，對供應鏈造成的規格升級與資金輪動。重點不是單一晶片性能，而是整櫃功耗、液冷滲透、電源備援、高速互連與 ODM 交付模式是否同步升級。",
  "thesis": "Vera Rubin 的投資主軸不在於單顆 GPU 再次升級，而在於 AI 基礎設施正式進入 rack-scale competition。當系統設計重心從 board-level 走向 rack-level，最先受惠的不只 GPU 核心供應商，還包括液冷散熱、電源與備援、連接器/銅箔基板、高速互連、機櫃整合與系統測試廠。若市場開始從『算力』轉向『每櫃功耗、部署密度、可維護性與交付速度』評價，這條線會成為未來數季重要主題。",
  "icon": "cpu",
  "color": "from-cyan-500 to-indigo-600",
  "theme_tags": [
    "Vera Rubin",
    "Rack Scale",
    "AI Server",
    "Liquid Cooling",
    "Power",
    "NVLink",
    "Silicon Photonics"
  ],
  "trigger_events": [
    "NVIDIA 釋出 Vera Rubin 平台路線與機櫃級設計細節",
    "ODM/雲端業者上修 AI 機櫃建置與交付節奏",
    "液冷、BBU/PSU、連接器與高速互連規格升級被明確點名",
    "法說開始以 rack、pod、cluster 為單位揭露功耗、散熱或資本支出需求"
  ],
  "risks": [
    "Vera Rubin 實際量產時程遞延，導致供應鏈題材提前反映後拉回",
    "液冷與高功率機櫃方案導入速度低於市場預期",
    "CSP 自研 ASIC 或自定義機櫃架構，分散單一平台外溢效應",
    "高估值題材股先漲過頭，若法說未證實訂單與 ASP 提升，容易出現修正"
  ],
  "watch_signals": [
    "NVIDIA GTC / roadmap 是否進一步揭露 Vera Rubin 機櫃架構",
    "奇鋐、雙鴻、台達電、光寶科等是否在法說提及 AI 機櫃規格升級",
    "鴻海、廣達、緯穎、英業達等 ODM 是否提高整櫃交付能見度",
    "高速互連、矽光子、連接器與電源備援廠是否出現同步接單訊號"
  ],
  "related_themes": [
    "AI散熱升級：液冷、CDU 與高密度熱管理",
    "AI伺服器電力升級：高功率電源與備援架構",
    "AI網通升級：800G / 1.6T 光模組與交換器鏈",
    "AI 基礎設施：CPO 與矽光子高速傳輸鏈",
    "HBM與高速記憶體封裝供應鏈"
  ],
  "tech_lessons": [
    {
      "title": "為何 Vera Rubin 代表 board-level 走向 rack-scale",
      "subtitle": "AI 基礎設施評價單位從單機板轉為整機櫃",
      "problem": "過去市場多以單顆 GPU、單板卡或單台伺服器來評估 AI 升級，但當高功耗 GPU、交換器與 HBM 整合後，系統瓶頸不再只是晶片效能，而是整櫃供電、散熱、佈線、維護與部署密度。若仍用舊方法看供應鏈，容易低估非晶片環節的重要性。",
      "mechanism": "Rack-scale 設計會把多台伺服器、交換器、電源模組、液冷模組與高速互連視為一個整體工程。這意味著供應商要同時滿足功耗密度、熱通量、佈線損耗、可維修性與交付速度。平台升級的價值將從單機 BOM 擴展為整櫃 ASP 與系統整合能力。",
      "why_now": "Vera Rubin 被市場視為下一代 AI 基礎設施平台時，投資焦點也將從 GPU 單點升級擴大到 rack-level 配套，這正是液冷、電源與 ODM 整合鏈有機會在未來數季持續被資金反覆點火的原因。",
      "desc": "本模組說明 Vera Rubin 為何不是單一晶片題材，而是 AI 伺服器架構從 board-level 升級到 rack-scale 的代表。"
    },
    {
      "title": "整櫃功耗上升為何先帶動液冷與電源備援",
      "subtitle": "高密度 AI 機櫃的第一層瓶頸是熱與電",
      "problem": "當 AI 機櫃從數十 kW 往更高功耗密度提升，傳統風冷、一般 PSU 與備援設計很快接近極限。若散熱與供電不先解決，再強的 GPU 也無法穩定部署。",
      "mechanism": "整櫃功耗升高會同步推升冷板、CDU、液冷分配模組、泵浦、快接頭、PSU、BBU 與配電模組需求。這些環節不是附屬零件，而是決定 AI pod 是否能穩定上線的必要條件，因此 ASP 與規格通常會隨平台升級往上抬。",
      "why_now": "從 Blackwell 到 Vera Rubin，市場敘事明顯從算力提升延伸到每櫃可承載的熱與電。只要雲端與 ODM 開始公開談液冷滲透率與機櫃功耗，就表示這條線正式進入主投資邏輯。",
      "desc": "本模組聚焦高功耗機櫃下最先顯性的兩個受惠方向：液冷散熱與電源備援。"
    },
    {
      "title": "高速互連與矽光子為何是 Vera Rubin 的第二波擴散",
      "subtitle": "算力密度上升後，資料移動成本會成為新瓶頸",
      "problem": "當 GPU 數量與 HBM 頻寬同步提升，如果機櫃內外的資料傳輸仍依賴舊架構，就會面臨功耗、延遲與訊號完整性問題，導致 AI cluster 效率下降。",
      "mechanism": "Vera Rubin 這類 rack-scale 平台需要更高速的 GPU 間互連、交換器上行頻寬與更有效率的光互連方案。這會帶動 NVLink、生態鏈交換器、800G/1.6T 光模組、矽光子與 CPO 被反覆討論。",
      "why_now": "市場初期可能先炒散熱與電源，但當平台規格逐漸明朗後，資金通常會往高速互連與矽光子擴散，因為這是大規模 AI cluster 真正放量時不可或缺的第二層基礎建設。",
      "desc": "本模組說明為何 Vera Rubin 題材後續很可能延伸到高速互連、光模組與矽光子。"
    },
    {
      "title": "ODM 與整機櫃交付能力為何會重估",
      "subtitle": "平台競爭從零件供應延伸到整合交付",
      "problem": "若 AI 基礎設施採購從單機轉向整櫃，僅能提供單一零件的廠商不一定能吃到最大價值，真正掌握交付節奏的反而是能整合伺服器、網通、散熱與電源的 ODM。",
      "mechanism": "ODM 廠在 rack-scale 時代的價值來自系統整合、量產驗證、機櫃設計、客戶協同開發與全球交付。當客戶採購單位變成 rack 或 cluster，ODM 的議價權與能見度都可能提升。",
      "why_now": "若 Vera Rubin 平台帶動的需求不是單點 GPU，而是整櫃與 pod 級部署，ODM 將從『組裝廠』被重估為 AI 基礎設施整合平台的重要執行者。",
      "desc": "本模組整理 Vera Rubin 題材中，ODM 與系統整合商為何值得被獨立追蹤。"
    }
  ],
  "structure_layers": [
    {
      "name": "上游：GPU / HBM / 高速互連核心規格",
      "position": "平台定義層，決定機櫃級 AI 系統的性能上限與連接架構",
      "summary": "Vera Rubin 的最上游是 GPU、HBM、NVLink / 高速交換架構與機櫃拓撲。這一層決定整個供應鏈的功耗、散熱與資料流方向，也是後續所有零組件升級的起點。",
      "key_points": [
        "GPU 與 HBM 功耗升級決定熱設計與供電規格",
        "NVLink / 高速交換拓撲決定背板、連接器與光互連需求",
        "平台從單機板升級為整櫃配置後，系統規格外溢到更多零組件"
      ],
      "beneficiaries": [
        "GPU / AI ASIC 平台商",
        "HBM 與先進封裝供應鏈",
        "高速交換與互連晶片供應商"
      ]
    },
    {
      "name": "中游：液冷、電源、連接器與光互連模組",
      "position": "規格放大量產層，直接承接 rack-scale 升級帶來的 BOM 變化",
      "summary": "當整櫃功耗、熱密度與傳輸頻寬提升，中游零件供應商將最先反映在報價、規格升級與接單能見度上。這一層是題材最容易從概念走向業績的區段。",
      "key_points": [
        "液冷模組、CDU、冷板與快接頭受惠於熱密度提升",
        "高功率 PSU、BBU、配電模組受惠於整櫃供電升級",
        "連接器、銅箔基板、800G/1.6T 光模組與矽光子受惠於高速資料傳輸需求"
      ],
      "beneficiaries": [
        "散熱模組廠",
        "電源與備援供應商",
        "高速互連與光通訊供應商"
      ]
    },
    {
      "name": "下游：ODM、系統整合與雲端建置",
      "position": "最終交付層，決定平台何時從題材轉為營收",
      "summary": "真正讓 Vera Rubin 題材落地的是 ODM 與雲端業者是否以 rack / pod / cluster 為單位放量建置。此層負責把 GPU、散熱、供電與網通系統整合成可部署產品。",
      "key_points": [
        "ODM 的交付能力與驗證速度決定平台放量節奏",
        "CSP 資本支出會直接牽動整櫃建置量能",
        "若採購模式從伺服器台數轉為 rack 數量，系統整合商的價值將提高"
      ],
      "beneficiaries": [
        "AI 伺服器 ODM",
        "機櫃與整機櫃整合商",
        "大型雲端服務業者"
      ]
    }
  ],
  "capital_flow": [
    {
      "phase": "第一波：散熱與電源先行",
      "timeframe": "2026 Q2 - 2026 Q3",
      "focus": "液冷、CDU、PSU、BBU、配電",
      "logic": "市場剛理解 Vera Rubin 題材時，最容易先看到的是整櫃功耗與熱密度，因此資金往往先湧向液冷散熱與電源備援股。這些公司較容易在法說與接單中被驗證，短線彈性也較高。",
      "beneficiary_groups": [
        "液冷散熱供應鏈",
        "電源與備援供應鏈",
        "高功率配電模組廠"
      ]
    },
    {
      "phase": "第二波：高速互連與矽光子擴散",
      "timeframe": "2026 Q3 - 2026 Q4",
      "focus": "800G/1.6T、矽光子、CPO、連接器",
      "logic": "當市場從功耗與散熱開始往更深層規格思考時，會轉向關注資料傳輸瓶頸。這時高速互連、光模組、矽光子與 CPO 題材會接棒，成為第二波擴散主軸。",
      "beneficiary_groups": [
        "高速光模組與交換器供應鏈",
        "矽光子 / CPO 供應鏈",
        "高階連接器與材料供應商"
      ]
    },
    {
      "phase": "第三波：ODM 與整機櫃交付重估",
      "timeframe": "2026 Q4 - 2027",
      "focus": "整櫃交付、系統整合、雲端建置",
      "logic": "當客戶開始真正以 rack 或 pod 為單位部署，市場就會重估 ODM 與整合商的角色，因為它們不再只是代工，而是掌握交付與驗證節奏的關鍵節點。這一階段更偏向中線趨勢股。",
      "beneficiary_groups": [
        "AI 伺服器 ODM",
        "整機櫃整合商",
        "雲端建置與系統驗證供應商"
      ]
    }
  ],
  "timeline_phases": [
    {
      "phase": "題材發酵期",
      "timeframe": "2026 Q2 - 2026 Q3",
      "summary": "市場開始用 Vera Rubin 描述下一代 AI 平台升級，資金先聚焦液冷、電源與機櫃規格升級。此時重點是概念建立與法說佐證。",
      "winners": [
        "液冷散熱供應鏈",
        "高功率電源與備援供應鏈",
        "具題材辨識度的機櫃零組件股"
      ]
    },
    {
      "phase": "規格驗證與供應鏈擴散期",
      "timeframe": "2026 Q3 - 2026 Q4",
      "summary": "若平台細節與供應鏈規格逐步明確，資金會往高速互連、矽光子、連接器與 ODM 延伸。此階段開始區分真假受惠股。",
      "winners": [
        "高速光通訊與矽光子供應鏈",
        "高階連接器與基板供應商",
        "具客戶驗證優勢的 ODM"
      ]
    },
    {
      "phase": "量產與交付期",
      "timeframe": "2027 及以後",
      "summary": "當 Vera Rubin 相關平台正式放量，市場會回到交付能力、ASP、良率與資本支出效率。這時真正能穿越景氣循環的是具系統整合與量產能力的核心供應商。",
      "winners": [
        "頭部 ODM / 系統整合商",
        "可規模量產的液冷與電源供應商",
        "真正打入高速互連關鍵規格的供應鏈"
      ]
    }
  ],
  "concepts": [
    {
      "title": "Rack-scale AI 不是單純的伺服器升級",
      "subtitle": "評價單位從板卡變成機櫃",
      "desc": "Vera Rubin 的重要性在於把 AI 基礎設施的投資主軸，從單機板升級為機櫃與 cluster 級整合。"
    },
    {
      "title": "液冷與電源是第一圈受惠",
      "subtitle": "高功耗必然先撞到熱與電瓶頸",
      "desc": "整櫃功耗密度上升後，市場最先看見的通常是液冷、CDU、PSU、BBU 與配電模組需求增加。"
    },
    {
      "title": "高速互連與矽光子是第二圈擴散",
      "subtitle": "算力上升後，資料移動成本成為新瓶頸",
      "desc": "當 rack-scale 平台放大資料吞吐需求，高速光通訊、矽光子與 CPO 會成為後續資金擴散的主要方向。"
    },
    {
      "title": "ODM 交付能力決定題材能否變營收",
      "subtitle": "系統整合在 AI 機櫃時代被重估",
      "desc": "若客戶採購單位從 server 轉向 rack，ODM 與整機櫃整合商的戰略地位將顯著上升。"
    }
  ],
  "stocks": [
    {
      "id": "3231",
      "name": "緯創",
      "code": "3231",
      "sector": "整機櫃整合 / ODM",
      "sectorId": "odm",
      "role": "AI 伺服器與整機櫃交付",
      "timeframe": "2026-2027 觀察",
      "pureLevel": 4.2,
      "barrierLevel": 4.0,
      "pros": "具 AI 伺服器製造與系統整合能力，若客戶採購單位轉向整櫃與 pod，交付角色可能被重估。",
      "cons": "受客戶集中度與毛利率結構限制，題材轉單不一定立即反映獲利。",
      "catalyst": "AI 機櫃量產、整櫃交付能見度提升、法說揭露 rack 級訂單。",
      "desc": "Vera Rubin 若帶動 rack-scale 採購，緯創有望受惠於 AI 系統整合與量產交付。"
    },
    {
      "id": "2382",
      "name": "廣達",
      "code": "2382",
      "sector": "整機櫃整合 / ODM",
      "sectorId": "odm",
      "role": "大型 AI 伺服器平台整合",
      "timeframe": "2026-2027 觀察",
      "pureLevel": 4.3,
      "barrierLevel": 4.2,
      "pros": "在 AI 伺服器整合與大型雲端客戶關係上具優勢，若平台升級走向整機櫃，有機會持續受惠。",
      "cons": "市場熟悉度高，估值反映速度快，需觀察交付節奏是否超預期。",
      "catalyst": "雲端客戶資本支出提升、AI 機櫃出貨成長、法說對 rack-level 需求轉強。",
      "desc": "廣達是 Vera Rubin 題材中觀察整櫃 AI 交付的重要指標股。"
    },
    {
      "id": "6669",
      "name": "緯穎",
      "code": "6669",
      "sector": "整機櫃整合 / ODM",
      "sectorId": "odm",
      "role": "高階 AI 伺服器與資料中心整合",
      "timeframe": "2026-2027 觀察",
      "pureLevel": 4.4,
      "barrierLevel": 4.3,
      "pros": "與 CSP 客戶關係緊密，若 AI 機櫃導入加速，具高彈性與高 ASP 潛力。",
      "cons": "波動大，且市場容易提前反映未來成長。",
      "catalyst": "CSP 新平台建置、AI 整機櫃交付增加、法說上修資本支出受惠。",
      "desc": "緯穎可視為 Vera Rubin 題材中 ODM / CSP 交會點的重要追蹤股。"
    },
    {
      "id": "3017",
      "name": "奇鋐",
      "code": "3017",
      "sector": "液冷散熱",
      "sectorId": "cooling",
      "role": "高功耗 AI 液冷解決方案",
      "timeframe": "近1-3季觀察",
      "pureLevel": 4.6,
      "barrierLevel": 4.3,
      "pros": "AI 伺服器液冷滲透率提升時最直接的受惠方向之一，具技術與客戶驗證優勢。",
      "cons": "股價容易先反映題材，需觀察實際放量速度與毛利維持。",
      "catalyst": "液冷模組新訂單、AI 機櫃規格升級、法說提及高功耗平台需求。",
      "desc": "若 Vera Rubin 帶動整櫃液冷升級，奇鋐是最核心的第一圈受惠股之一。"
    },
    {
      "id": "3324",
      "name": "雙鴻",
      "code": "3324",
      "sector": "液冷散熱",
      "sectorId": "cooling",
      "role": "AI 散熱與液冷模組",
      "timeframe": "近1-3季觀察",
      "pureLevel": 4.2,
      "barrierLevel": 4.0,
      "pros": "受惠高密度 AI 機櫃熱管理升級，若液冷導入加速具題材彈性。",
      "cons": "需持續驗證 AI 液冷占比與客戶導入深度。",
      "catalyst": "新平台散熱設計導入、液冷規格升級、客戶驗證進展。",
      "desc": "雙鴻是 Vera Rubin 題材中液冷與高密度散熱的重要追蹤股。"
    },
    {
      "id": "2308",
      "name": "台達電",
      "code": "2308",
      "sector": "電源 / 配電",
      "sectorId": "power",
      "role": "高功率電源、配電與基礎設施",
      "timeframe": "2026-2027 觀察",
      "pureLevel": 4.5,
      "barrierLevel": 4.5,
      "pros": "電源與基礎設施能力完整，是 AI 機櫃功耗升級下的核心受惠方向。",
      "cons": "體量較大，短線題材彈性可能不如中小型股。",
      "catalyst": "高功率 PSU / 配電訂單、資料中心基建升級、法說釋出 AI 電源需求。",
      "desc": "台達電是 Vera Rubin 題材中電源與整體基礎設施能力最值得追蹤的核心股之一。"
    },
    {
      "id": "2301",
      "name": "光寶科",
      "code": "2301",
      "sector": "電源 / 備援",
      "sectorId": "power",
      "role": "PSU / BBU / AI 電源模組",
      "timeframe": "近1-2季觀察",
      "pureLevel": 4.0,
      "barrierLevel": 3.8,
      "pros": "若 AI 機櫃朝更高功率與備援設計演進，電源模組與備援鏈有望受惠。",
      "cons": "需觀察 AI 相關比重拉升速度。",
      "catalyst": "BBU / PSU 新規格放量、法說提及 AI 伺服器電源占比提升。",
      "desc": "光寶科可作為 Vera Rubin 題材中電源與備援升級的重點觀察股。"
    },
    {
      "id": "2345",
      "name": "智邦",
      "code": "2345",
      "sector": "高速互連 / 網通",
      "sectorId": "network",
      "role": "高速交換器與網通升級",
      "timeframe": "2026-2027 觀察",
      "pureLevel": 4.1,
      "barrierLevel": 4.1,
      "pros": "若 rack-scale 帶動交換器頻寬與整體網通架構升級，高速交換鏈具中線受惠機會。",
      "cons": "需視平台實際放量與客戶採購節奏。",
      "catalyst": "800G/1.6T 交換器放量、CSP 網通升級、法說對 AI 網路需求轉強。",
      "desc": "智邦是 Vera Rubin 題材第二圈擴散中，高速網通與交換器鏈的重要觀察股。"
    },
    {
      "id": "3715",
      "name": "定穎投控",
      "code": "3715",
      "sector": "高速材料 / 板材",
      "sectorId": "materials",
      "role": "高速高頻板材與系統板升級",
      "timeframe": "中期觀察",
      "pureLevel": 3.7,
      "barrierLevel": 3.6,
      "pros": "若機櫃級設計帶動高速高頻材料需求上升，板材與 PCB 升級可望受惠。",
      "cons": "屬第二圈受惠，需觀察高階 AI 需求是否實際滲透。",
      "catalyst": "高速材料需求增加、AI 板升級、客戶新平台導入。",
      "desc": "定穎投控屬 Vera Rubin 題材中，高速材料與系統板升級的延伸觀察股。"
    }
  ],
  "sources": [
    {
      "type": "manual-theme",
      "label": "使用者提供題材方向",
      "note": "依使用者提供之 Vera Rubin 題材截圖與需求，整理為獨立追蹤主題。"
    },
    {
      "type": "analysis",
      "label": "nanobot 主題歸納",
      "note": "依既有 AI 伺服器、液冷、電源、高速互連與 ODM 供應鏈脈絡進行結構化整理。"
    }
  ]
}

repo_path.write_text(json.dumps(repo, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"added {key}; total={len(repo)}")
