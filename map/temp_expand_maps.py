import json, copy, pathlib
path = pathlib.Path(r'D:\map\maps_repo.json')
with path.open('r', encoding='utf-8') as f:
    data = json.load(f)
if len(data) >= 12:
    print('already enough', len(data))
    raise SystemExit(0)
base_key = next(iter(data))
base = data[base_key]
entries = []
seed_specs = [
    ('2026-05-25','AI先進封裝：FOPLP與玻璃基板 GCS 供應鏈','台積電 / 欣興 / 鈦昇',['Glass Core','FOPLP','TGV','先進封裝'],['台積電先進封裝資本支出轉向 FOPLP 與玻璃基板','載板與玻璃加工鏈率先受惠']),
    ('2026-05-24','AI伺服器電力升級：高功率電源與備援架構','台達電 / 光寶科 / 中興電',['Power Supply','AI Server','電力管理','BBU'],['GB200 機櫃功耗上升','高功率電源與備援模組需求同步增長']),
    ('2026-05-23','AI散熱升級：液冷、CDU 與高密度熱管理','奇鋐 / 雙鴻 / 高力',['Liquid Cooling','CDU','散熱','AI Server'],['高密度 GPU 機櫃熱通量升高','液冷與散熱模組規格升級']),
    ('2026-05-22','CoWoS擴產與先進封裝設備材料鏈','台積電 / 弘塑 / 均華',['CoWoS','Advanced Packaging','設備','材料'],['先進封裝產能持續吃緊','設備與耗材鏈同步受益']),
    ('2026-05-21','AI網通升級：800G / 1.6T 光模組與交換器鏈','智邦 / 華星光 / 波若威',['800G','1.6T','Optical Module','Switch'],['交換器頻寬升級推進 800G 與 1.6T','光模組與交換器供應鏈同步擴張']),
    ('2026-05-20','HBM與高速記憶體封裝供應鏈','南電 / 創意 / 萬潤',['HBM','Memory','Advanced Packaging','Testing'],['HBM 需求推升先進封裝與測試','高速記憶體相關設備受矚目']),
    ('2026-05-19','機器人與自動化：減速機、伺服、控制器鏈','上銀 / 直得 / 台達電',['Robot','Automation','Servo','Controller'],['人形機器人題材持續擴散','工業自動化與關鍵零組件受關注']),
    ('2026-05-18','無人機與低軌通訊：軍工電子與通訊模組','雷虎 / 漢翔 / 仲琦',['Drone','LEO','Defense','Communication'],['地緣政治提高無人機與通訊韌性需求','軍工電子與模組題材升溫']),
    ('2026-05-17','重電與電網強韌化：變壓器、開關與工程鏈','華城 / 士電 / 中興電',['Power Grid','Transformer','重電','儲能'],['全球電網升級與韌性建設加速','變壓器與高壓設備交期延長']),
    ('2026-05-16','半導體設備自主化：檢測、量測與關鍵零件','精測 / 致茂 / 家登',['Semicap','Inspection','Metrology','Key Parts'],['地緣政治提高供應鏈自主化需求','設備零組件與量測鏈獲資金關注']),
    ('2026-05-15','矽光子與CPO延伸：外部雷射源與測試設備','光寶科 / 聯鈞 / 旺矽',['CPO','Silicon Photonics','ELS','Testing'],['CPO 從概念走向驗證','外部雷射源與測試設備成關鍵']),
    ('2026-05-14','AI終端落地：邊緣運算、工控 IPC 與模組鏈','研華 / 樺漢 / 新漢',['Edge AI','IPC','Industrial PC','Module'],['AI 從雲端延伸至邊緣','工控與模組廠受惠於應用落地']),
]
for i,(date,title,focus,tags,drivers) in enumerate(seed_specs, start=1):
    m = copy.deepcopy(base)
    key = f"map_{date.replace('-','')}_{i:02d}"
    m['title'] = title
    m['date'] = date
    m['updated_at'] = f"{date}T21:{10+i:02d}:00+08:00"
    m['heat'] = title
    m['heat_score'] = max(72, 92 - i)
    m['period'] = '2026 Q2 - 2026 Q4'
    m['desc'] = f"{title} 為近月市場高關注方向，聚焦資本支出、法說催化與族群輪動。首頁先提供快速追蹤版本，方便會員直接從卡片辨識主線與優先關注標的。"
    m['thesis'] = f"核心觀察在於 {drivers[0]}，並透過 {drivers[1]} 驗證題材是否由預期轉向訂單與營收。"
    m['theme_tags'] = tags
    m['trigger_events'] = drivers
    m['related_themes'] = tags[:4]
    m['watch_signals'] = [f"{focus.split(' / ')[0]} 法說或接單動態", f"{focus.split(' / ')[1]} 營運與報價變化", f"{focus.split(' / ')[2]} 是否成為族群領漲"]
    focus_names = [x.strip() for x in focus.split('/')]
    stocks = []
    for idx,name in enumerate(focus_names):
        code = f"F{i}{idx+1}"
        stocks.append({
            'id': f'{i:02d}{idx+1}', 'name': name, 'code': code, 'sector': '主題核心受惠', 'sectorId': 'focus',
            'role': '主題受惠核心', 'timeframe': '近1-2季觀察', 'pureLevel': 4.6 - idx*0.3, 'barrierLevel': 4.4 - idx*0.2,
            'pros': f'{name} 為此題材最具代表性的優先關注股。', 'cons': '短線可能受評價與題材熱度波動影響。',
            'catalyst': '法說、接單、報價、資本支出', 'desc': f'{name} 為 {title} 之優先關注標的。', 'market': 'TWSE',
            'stock_tier': 'core' if idx == 0 else 'extended', 'evidence_type': 'inferred', 'sources': [],
            'relation_to_theme': '優先關注', 'linkage_strength': '強連動' if idx == 0 else '中強連動', 'benefit_stage': '第一圈' if idx < 2 else '第二圈',
            'linkage_driver': drivers[min(idx, len(drivers)-1)], 'relation_note': f'{name} 屬於此題材追蹤名單中的優先關注股。'
        })
    m['stocks'] = stocks
    entries.append((key,m))
for k,v in reversed(entries):
    data = {k:v, **data}
with path.open('w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('written', len(data))
