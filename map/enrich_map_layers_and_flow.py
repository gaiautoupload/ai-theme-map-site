import json, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent
path = ROOT / 'maps_repo.json'
repo = json.loads(path.read_text(encoding='utf-8'))
TZ = timezone(timedelta(hours=8))
now = datetime.now(TZ).strftime('%Y-%m-%dT%H:%M:%S+08:00')

ROLE_KEYWORDS = [
    ('散熱 / 液冷', ['散熱','液冷','風扇','熱','均熱','水冷','CDU','cooling','Thermal']),
    ('電源 / 重電 / 能源', ['電源','電力','重電','變壓','儲能','UPS','PSU','BBU','能源','配電']),
    ('伺服器 / 系統整合', ['伺服器','系統','ODM','整機','機櫃','server','rack']),
    ('高速傳輸 / 網通', ['網通','交換器','光通訊','光','CPO','LPO','高速','連接','switch','矽光子']),
    ('半導體 / 先進封裝', ['半導體','封裝','CoWoS','晶圓','IC','載板','基板','測試','設備']),
    ('材料 / 零組件', ['材料','零組件','PCB','銅箔','化學','導熱','結構件','機構']),
    ('軟體 / 應用服務', ['軟體','AI','Agent','資料','資安','雲端','平台','服務']),
]

def as_list(x):
    if isinstance(x, list): return x
    if x is None: return []
    return [x]

def text_of_stock(s):
    return ' '.join(str(s.get(k,'')) for k in ['name','ticker','sector','linkage','reason','benefit_logic','theme_linkage','concept_highlight','desc','role'])

def stock_name(s):
    name = s.get('name') or s.get('company') or s.get('title') or s.get('ticker') or s.get('symbol') or '未命名'
    ticker = s.get('ticker') or s.get('symbol') or s.get('code') or s.get('stock_code') or s.get('id') or ''
    return f"{name}({ticker})" if ticker and ticker not in str(name) else str(name)

def pick_groups(stocks):
    groups = []
    for label, kws in ROLE_KEYWORDS:
        matched = []
        for s in stocks:
            txt = text_of_stock(s)
            if any(k.lower() in txt.lower() for k in kws):
                matched.append(stock_name(s))
        if matched:
            groups.append((label, list(dict.fromkeys(matched))[:5]))
    if not groups and stocks:
        buckets = {}
        for s in stocks:
            sec = s.get('sector') or s.get('category') or s.get('stage') or s.get('role') or '概念供應鏈'
            buckets.setdefault(sec, []).append(stock_name(s))
        groups = [(str(k), list(dict.fromkeys(v))[:5]) for k,v in list(buckets.items())[:4]]
    if not groups:
        groups = [('核心供應鏈', ['待補股票驗證'])]
    return groups[:5]

def infer_bottleneck(title, summary):
    txt = (title + ' ' + summary).lower()
    if any(k in txt for k in ['散熱','液冷','能源','電力','data center','資料中心']): return '功耗、散熱與供電容量'
    if any(k in txt for k in ['封裝','cpo','光','傳輸','玻璃基板','cowos']): return '先進製程、封裝良率與高速互連規格'
    if any(k in txt for k in ['機器人','自動化']): return '關鍵模組可靠度、量產成本與客戶導入'
    if any(k in txt for k in ['ai agent','軟體','資安','雲端']): return '企業導入案例、資料治理與續約率'
    return '規格升級、訂單能見度與毛利率驗證'

def build_structure(mapv):
    title = mapv.get('title') or mapv.get('theme_name') or '本主題'
    summary = mapv.get('summary') or mapv.get('desc') or mapv.get('thesis') or ''
    stocks = [s for s in as_list(mapv.get('stocks')) if isinstance(s, dict)]
    groups = pick_groups(stocks)
    bottleneck = infer_bottleneck(title, summary)
    layers = []
    base_names = ['上游：規格與關鍵瓶頸', '中游：核心零組件 / 模組', '下游：系統整合與終端導入', '延伸：材料、設備與小中型補漲']
    for i, name in enumerate(base_names):
        label, names = groups[min(i, len(groups)-1)]
        if i == 0:
            pos = '規格定義與瓶頸層，決定本主題最先被市場重估的位置'
            summ = f'{title} 的第一層要先看「{bottleneck}」。資金通常先找最能解決瓶頸、最容易被訂單或規格驗證的供應商。'
            value = '高'; pricing='high'; barrier='高'; leader='掌握規格、認證或客戶先發者'
        elif i == 1:
            pos = '把上游規格轉成可出貨產品的關鍵模組層'
            summ = f'這一層承接規格升級，重點看 {label} 的產品組合是否升級、是否進入國際客戶供應鏈。'
            value = '中高'; pricing='medium'; barrier='中高'; leader='良率、交期與客戶認證較強者'
        elif i == 2:
            pos = '連接終端客戶、雲端大廠或企業導入的整合層'
            summ = '這一層受惠較接近營收確認，但毛利率與議價能力要看是否只是代工組裝，或能提供完整方案。'
            value = '中'; pricing='medium'; barrier='中'; leader='具規模、客戶關係與整合能力者'
        else:
            pos = '題材擴散後的補漲與次供應鏈層'
            summ = '當核心股評價先反映後，市場會往材料、設備、測試、零組件與小中型股尋找落後補漲機會。'
            value = '中到高波動'; pricing='low'; barrier='待補資料'; leader='低基期且營收開始驗證者'
        layers.append({
            'name': name,
            'position': pos,
            'summary': summ,
            'key_points': [f'對應環節：{label}', f'受惠位置：{pos}', f'關鍵驗證：訂單、營收、毛利率與客戶認證'],
            'beneficiaries': names,
            'pricing_power': pricing,
            'margin_profile': '需觀察產品組合升級與客戶議價狀況' if i != 0 else '若掌握稀缺產能或規格門檻，毛利率較有支撐',
            'value_capture': value,
            'entry_barrier': barrier,
            'leader_type': leader,
        })
    return layers

def build_capital_flow(mapv):
    title = mapv.get('title') or mapv.get('theme_name') or '本主題'
    summary = mapv.get('summary') or mapv.get('desc') or mapv.get('thesis') or ''
    stocks = [s for s in as_list(mapv.get('stocks')) if isinstance(s, dict)]
    groups = pick_groups(stocks)
    core = groups[0][1] if groups else ['核心供應鏈']
    second = groups[1][1] if len(groups)>1 else core
    third = []
    for _, names in groups[2:]: third += names
    if not third: third = [stock_name(s) for s in stocks[5:10]] or ['延伸供應鏈']
    bottleneck = infer_bottleneck(title, summary)
    return [
        {'phase':'第一波：國際敘事與核心瓶頸先點火','timeframe':'新聞 / 法說會 / 規格公布初期','focus':bottleneck,'logic':f'市場先確認 {title} 是否從新聞變成投資主線；資金會優先買進最純、最容易被理解、與「{bottleneck}」直接相關的公司。火勢上升訊號：國際大廠提高 Capex、規格升級、供應鏈被點名、股價帶量突破。','beneficiary_groups':core},
        {'phase':'第二波：資金擴散到台股核心供應鏈','timeframe':'訂單能見度提高 / 月營收開始反映','focus':'核心零組件、模組與系統整合','logic':'當第一波主線被確認後，資金會從大型權值或最純題材股，擴散到具客戶認證、產能開出與產品組合升級的台灣供應鏈。火勢延燒訊號：同族群多檔輪動、營收連續改善、法人報告開始提高目標價或新增覆蓋。','beneficiary_groups':second},
        {'phase':'第三波：小中型與次供應鏈補漲','timeframe':'核心股評價偏高 / 市場尋找低基期標的','focus':'材料、設備、測試、零組件與落後補漲','logic':'核心股漲多後，市場會往低基期、籌碼較輕、但能接到同一主題訂單的延伸標的移動；這一波彈性較大但驗證風險也較高。火勢降溫訊號：只剩低基期股亂漲、營收沒有跟上、成交量放大但族群輪動變短。','beneficiary_groups':list(dict.fromkeys(third))[:6]},
    ]

def is_rich_structure(x):
    return isinstance(x, list) and len(x) >= 3 and all(isinstance(i, dict) and i.get('summary') and i.get('beneficiaries') for i in x[:3])

def is_rich_flow(x):
    return isinstance(x, list) and len(x) >= 3 and all(isinstance(i, dict) and i.get('logic') and i.get('beneficiary_groups') for i in x[:3])

changed = 0
for key, mapv in repo.items():
    if not isinstance(mapv, dict):
        continue
    if not is_rich_structure(mapv.get('structure_layers')):
        mapv['structure_layers'] = build_structure(mapv)
        changed += 1
    if not is_rich_flow(mapv.get('capital_flow')):
        mapv['capital_flow'] = build_capital_flow(mapv)
        changed += 1
    if not mapv.get('who_makes_money') or str(mapv.get('who_makes_money')).strip() in ['待補資料','待補','']:
        names=[]
        for layer in mapv.get('structure_layers',[])[:3]:
            names += layer.get('beneficiaries',[]) if isinstance(layer,dict) else []
        names=list(dict.fromkeys(names))[:6]
        mapv['who_makes_money']='先看掌握瓶頸規格與客戶認證的供應商；再看能把產品組合升級轉成營收與毛利率的核心零組件/系統整合廠。代表受惠：' + ('、'.join(names) if names else '待補資料驗證')
        changed += 1
    mapv['content_quality_note'] = '已補齊資金流向與火勢推演、產業結構分層與受惠位置；數字型 TAM/CAGR 仍需外部資料驗證。'

path.write_text(json.dumps(repo, ensure_ascii=False, indent=2), encoding='utf-8')
print('themes', len(repo), 'fields_changed', changed)
for v in list(repo.values())[:5]:
    print('-', v.get('title'), len(v.get('structure_layers',[])), len(v.get('capital_flow',[])))
