import json
from pathlib import Path

p = Path(r'D:\map\maps_repo.json')
data = json.loads(p.read_text(encoding='utf-8'))
old_key = 'map_vera_rubin_ai_rack_scale_20260526_2201'
new_key = 'map_Vera_Rubin_機櫃級_AI_升級追蹤_20260527_004222'
if old_key in data and new_key in data:
    data.pop(old_key)
vr = data[new_key]
vr['market_size_tam'] = '2027年前相關 AI 機櫃液冷 / 電源 / 光互連升級機會合計可達數百億美元級'
vr['market_size_tam_source_type'] = 'analyst_style_estimate'
vr['market_cagr'] = '20%+（以 AI 資料中心基礎設施升級週期估）'
vr['market_cagr_source_type'] = 'analyst_style_estimate'
vr['theme_stage'] = '規格定義 → 驗證導入 → 2026下半年起追蹤放量'
vr['why_now'] = '現在要看 Vera Rubin，不是因為又有新 GPU 名字，而是資料中心開始被迫面對更高機櫃功耗、更高熱密度、更高頻寬互連與更複雜交付模式。只要市場開始用 rack、pod、cluster 討論建置，資金就不會只停在晶片，會往液冷、電源、光互連與整櫃 ODM 擴散。'
vr['primary_value_capture'] = '第一層先看液冷與高功率電源等剛性升級；第二層看高速光互連 / CPO / 高階連接；第三層看可整櫃交付的 ODM 與系統整合商。真正賺最多者通常是有規格主導權、驗證門檻與 ASP 提升能力的供應商。'
vr['key_bottleneck'] = '液冷可靠度與滲透速度、機櫃級供電架構、光互連成本 / 良率、ODM 整櫃交付驗證節奏。'
vr['related_themes'] = [
    'AI 數據中心液冷基礎設施',
    '高速光通訊模組',
    '先進封裝與電源管理',
    '智慧機房運維軟體',
    'BBU / PSU 備援電力升級',
    'CPO / LPO 與矽光子'
]
for layer in vr.get('structure_layers', []):
    name = layer.get('name', '')
    if '上游' in name:
        layer['pricing_power'] = 'high'
        layer['margin_profile'] = '高毛利但市場已高度認知，評價容易先反映'
        layer['value_capture'] = '高'
        layer['entry_barrier'] = '平台規格、先進封裝、互連協議門檻高'
    elif '中游' in name:
        layer['pricing_power'] = 'medium'
        layer['margin_profile'] = '若規格升級與滲透同步，毛利有上修空間'
        layer['value_capture'] = '中高'
        layer['entry_barrier'] = '客戶驗證、可靠度與量產能力決定勝負'
    elif '下游' in name:
        layer['pricing_power'] = 'medium'
        layer['margin_profile'] = '毛利不一定最高，但 ASP、能見度與接單黏著度可提升'
        layer['value_capture'] = '中高'
        layer['entry_barrier'] = '整合交付、驗證速度與全球製造服務能力'
for phase in vr.get('timeline_phases', []):
    ph = phase.get('phase', '')
    if '題材發酵' in ph:
        phase['investment_phase'] = '本夢比階段'
        phase['revenue_meaning'] = '先反映規格升級預期，財報貢獻有限'
        phase['watch_metric'] = '法說是否提及液冷、高功率 PSU、機櫃規格升級'
        phase['expected_market_focus'] = '先找最早被點名、最容易講故事的第一圈受惠股'
    elif '規格驗證' in ph:
        phase['investment_phase'] = '本夢比轉本益比過渡'
        phase['revenue_meaning'] = '開始觀察樣品、導入、驗證與 ASP 是否落地'
        phase['watch_metric'] = '認證進度、樣品轉量產、客戶新增設計導入'
        phase['expected_market_focus'] = '區分真假受惠，市場會淘汰只蹭題材者'
    else:
        phase['investment_phase'] = '本益比階段'
        phase['revenue_meaning'] = '看營收占比、毛利率與交付效率是否實際改善'
        phase['watch_metric'] = 'AI 營收占比、毛利率、出貨量與資本支出延續性'
        phase['expected_market_focus'] = '真正能穿越景氣循環的核心供應商'
stock_overrides = {
    '3231': ('AI 伺服器 / 機櫃相關營收比重有機會逐步提升，現階段以平台交付彈性觀察', '若整櫃交付比重提升，產品組合有助毛利改善', '大型 CSP / 品牌客戶集中，專案黏著度高', '2026-H1 驗證、2026-H2~2027 放量觀察', 'medium', 3),
    '2382': ('AI 伺服器營收占比相對較高，若 rack-level 採購擴大將更受惠', '高階 AI 平台占比拉升有助產品組合優化', '大型雲端客戶集中但合作深', '2026-H1~H2 規格導入觀察', 'medium', 3),
    '6669': ('AI / 雲端高階平台曝險高，若客戶轉向整櫃採購彈性更大', '高階平台比重上升時毛利表現通常較佳', 'CSP 客戶集中度高但切入深', '2026-H1 驗證、2026-H2 後放量', 'medium', 4),
    '3017': ('AI 液冷相關比重有望成為成長主軸之一', '高附加價值液冷模組滲透有利毛利率', '客戶驗證門檻高，通過後黏著度提升', '2026-Q1~Q3 持續驗證與放量', 'low', 4),
    '3324': ('AI 散熱 / 液冷比重提升中，屬第一圈受惠', '液冷產品放量有望改善產品組合', '客戶導入深度仍需追蹤', '2026-Q2~Q4 觀察', 'medium', 3),
    '2308': ('AI 電源 / 資料中心基建相關比重可望持續拉升', '高功率電源與基建方案通常優於一般電源毛利', '大型客戶與專案型交付特性明顯', '2026-H1 規格升級、2026-H2 起追蹤營收', 'low', 5),
    '2301': ('AI PSU / BBU 比重仍待法說驗證，但具切入機會', '若 AI 電源占比提升可帶動獲利結構改善', '客戶與產品線分散，需觀察是否切入核心案', '2026-H1~H2 觀察', 'medium', 2),
    '2345': ('AI 高速交換與資料中心網通需求是主要看點', '高階交換器與高速網通升級有助毛利結構', '大型雲端客戶與平台周期影響大', '2026-H2 起看 800G/1.6T 放量', 'medium', 4),
    '3715': ('AI 高速材料曝險屬延伸受惠，非第一圈', '若高階板材規格升級成功，毛利有改善空間', '客戶驗證與材料替代風險需注意', '2026-H2 之後觀察', 'medium', 2),
}
for s in vr.get('stocks', []):
    code = s.get('code')
    if code in stock_overrides:
        ai_exp, gm, cust, phase, subrisk, vcs = stock_overrides[code]
        s['ai_revenue_exposure'] = ai_exp
        s['gross_margin_impact'] = gm
        s['customer_concentration'] = cust
        s['commercialization_phase'] = phase
        s['substitution_risk'] = subrisk
        s['value_capture_score'] = vcs
        s['capacity_share_hint'] = '待公司法說 / 產能資料交叉驗證'
        s['switching_cost'] = 'high' if code in {'3017', '2308', '2345', '6669'} else 'medium'
        s['revenue_visibility'] = 'high' if code in {'3017', '2308', '2382', '6669'} else 'medium'
        if code in {'3017', '2308'}:
            s['pricing_power'] = 'high'
        elif code in {'2382', '6669', '2345'}:
            s['pricing_power'] = 'medium-high'

p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('updated maps_repo.json')
