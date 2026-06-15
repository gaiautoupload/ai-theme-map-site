import os
import sys
import json
import sqlite3
import requests
import urllib3
from datetime import datetime, timedelta

# 停用 SSL 憑證警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設定專案路徑與檔案路徑
PROJECT_DIR = r"D:\ai-theme-map-site"
DB_PATH = os.path.join(PROJECT_DIR, "institutional_chips.db")
SUMMARY_JSON_PATH = os.path.join(PROJECT_DIR, "institutional_chips_summary.json")
MAPS_REPO_PATH = os.path.join(PROJECT_DIR, "maps_repo.json")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chips_history (
            date TEXT,
            symbol TEXT,
            name TEXT,
            foreign_net INTEGER,
            trust_net INTEGER,
            dealer_net INTEGER,
            total_net INTEGER,
            PRIMARY KEY (date, symbol)
        )
    """)
    conn.commit()
    conn.close()

def clean_int(val):
    if not val:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    val_str = str(val).replace(",", "").strip()
    try:
        return int(val_str)
    except ValueError:
        try:
            return int(float(val_str))
        except ValueError:
            return 0

def fetch_twse_data(date_str):
    """
    抓取證交所三大法人買賣超
    """
    url = f"https://www.twse.com.tw/fund/T86?response=json&date={date_str}&selectType=ALLBUT0999"
    print(f"抓取證交所資料 ({date_str}): {url}")
    try:
        resp = requests.get(url, timeout=15, verify=False)
        if resp.status_code != 200:
            print(f"證交所請求失敗，狀態碼: {resp.status_code}")
            return []
        
        data = resp.json()
        if data.get("stat") != "OK" or "data" not in data:
            print(f"證交所無資料或狀態錯誤: {data.get('stat')}")
            return []
        
        results = []
        for row in data["data"]:
            if len(row) < 19:
                continue
            symbol = row[0].strip()
            name = row[1].strip()
            
            # 外資買賣超 (外陸資買賣超股數(不含外資自營商) + 外資自營商買賣超股數)
            foreign_net_shares = clean_int(row[4]) + clean_int(row[7])
            # 投信買賣超
            trust_net_shares = clean_int(row[10])
            # 自營商買賣超 (自行買賣 + 避險)
            dealer_net_shares = clean_int(row[11])
            # 三大法人合計
            total_net_shares = clean_int(row[18])
            
            # 轉換為「張」 (1張 = 1000股)
            results.append({
                "date": date_str,
                "symbol": symbol,
                "name": name,
                "foreign_net": int(round(foreign_net_shares / 1000.0)),
                "trust_net": int(round(trust_net_shares / 1000.0)),
                "dealer_net": int(round(dealer_net_shares / 1000.0)),
                "total_net": int(round(total_net_shares / 1000.0))
            })
        print(f"證交所抓取成功: 共 {len(results)} 筆")
        return results
    except Exception as e:
        print(f"抓取證交所出錯: {e}")
        return []

def fetch_tpex_data(date_str):
    """
    抓取櫃買中心三大法人買賣超 (OpenAPI)
    """
    # 櫃買中心 OpenAPI 只能查詢當日？ 或是可以使用 date 參數？
    # 根據 OpenAPI 說明，路徑可以加 ?date=YYYY-MM-DD
    # 例如：20260612 -> 2026-06-12
    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    url = f"https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading?date={formatted_date}"
    print(f"抓取櫃買中心資料 ({formatted_date}): {url}")
    try:
        resp = requests.get(url, timeout=15, verify=False)
        if resp.status_code != 200:
            print(f"櫃買中心請求失敗，狀態碼: {resp.status_code}")
            return []
        
        data = resp.json()
        if not isinstance(data, list) or len(data) == 0:
            print("櫃買中心無資料或非陣列格式")
            return []
        
        results = []
        for item in data:
            symbol = item.get("SecuritiesCompanyCode", "").strip()
            name = item.get("CompanyName", "").strip()
            if not symbol:
                continue
            
            # 外資買賣超 (包含外資自營商的 Difference)
            # 在 API 中，ForeignInvestorsInclude MainlandAreaInvestors-Difference 是總外資買賣超
            # 若 key 名字可能微調，我們直接尋找包含 'ForeignInvestorsInclude' 與 'Difference' 的 key
            foreign_key = None
            for k in item.keys():
                if "ForeignInvestorsInclude" in k and "Difference" in k:
                    foreign_key = k
                    break
            
            if foreign_key:
                foreign_net_shares = clean_int(item.get(foreign_key, 0))
            else:
                # 備用方案：外資(不含自營商) + 外資自營商
                foreign_net_shares = (clean_int(item.get("Foreign Investors include Mainland Area Investors (Foreign Dealers excluded)-Difference", 0)) + 
                                      clean_int(item.get("Foreign Dealers-Difference", 0)))
            
            trust_net_shares = clean_int(item.get("SecuritiesInvestmentTrustCompanies-Difference", 0))
            dealer_net_shares = clean_int(item.get("Dealers-Difference", 0))
            total_net_shares = clean_int(item.get("TotalDifference", 0))
            
            # 轉換為張數
            results.append({
                "date": date_str,
                "symbol": symbol,
                "name": name,
                "foreign_net": int(round(foreign_net_shares / 1000.0)),
                "trust_net": int(round(trust_net_shares / 1000.0)),
                "dealer_net": int(round(dealer_net_shares / 1000.0)),
                "total_net": int(round(total_net_shares / 1000.0))
            })
        print(f"櫃買中心抓取成功: 共 {len(results)} 筆")
        return results
    except Exception as e:
        print(f"抓取櫃買中心出錯: {e}")
        return []

def save_to_db(records):
    if not records:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR REPLACE INTO chips_history 
        (date, symbol, name, foreign_net, trust_net, dealer_net, total_net)
        VALUES (:date, :symbol, :name, :foreign_net, :trust_net, :dealer_net, :total_net)
    """, records)
    conn.commit()
    conn.close()
    print(f"成功將 {len(records)} 筆記錄寫入 SQLite 資料庫")

def get_stock_themes():
    """
    從大眾投資人看得懂的常見板塊對照表，以及 ticker_registry_tw.json 產業分類中，
    建立乾淨、通俗易懂的 股號 -> 題材清單（排除複雜月地圖主題名稱）。
    """
    stock_themes = {}
    
    # 1. 優先使用大眾投資人最熟悉、直觀的熱門概念板塊對照表
    COMMON_THEME_MAP = {
        # 晶圓代工與半導體
        "2330": ["晶圓代工"], "2303": ["晶圓代工"], "5347": ["晶圓代工"], "6488": ["矽晶圓"], "3707": ["矽晶圓"],
        # 先進封裝與封測設備
        "3711": ["半導體封測"], "3131": ["先進封裝設備"], "3583": ["先進封裝設備"], "6187": ["先進封裝"], "2404": ["半導體設備"],
        # IC 設計
        "2454": ["IC設計"], "3034": ["IC設計"], "2379": ["IC設計"], "3661": ["IP/IC設計"], "3443": ["IP/IC設計"], "3529": ["IP/IC設計"],
        # 被動元件與石英元件
        "2327": ["被動元件"], "2492": ["被動元件"], "6175": ["被動元件"], "3042": ["被動元件/石英"], "3026": ["被動元件"], "2478": ["被動元件"],
        # PCB、銅箔基板、載板
        "3044": ["PCB"], "6191": ["PCB"], "2368": ["PCB"], "8358": ["PCB/銅箔"], "2383": ["銅箔基板/CCL"], "6213": ["銅箔基板/CCL"], "6274": ["銅箔基板/CCL"], "3037": ["IC載板"], "3189": ["IC載板"], "8046": ["IC載板"],
        # 矽光子與光通訊
        "3081": ["矽光子/光通訊"], "4979": ["矽光子/光通訊"], "3234": ["矽光子/光通訊"], "6451": ["矽光子/光通訊"], "3363": ["矽光子/光通訊"], "4908": ["矽光子/光通訊"], "3450": ["矽光子/光通訊"],
        # 散熱與機殼
        "3017": ["散熱/機殼"], "3324": ["散熱/機殼"], "2421": ["散熱/機殼"], "3653": ["散熱"], "6230": ["散熱"],
        # 金融股
        "2883": ["金融"], "2881": ["金融"], "2882": ["金融"], "2880": ["金融"], "2884": ["金融"], "2885": ["金融"], "2886": ["金融"], "2891": ["金融"], "2892": ["金融"], "2887": ["金融"], "2888": ["金融"], "2801": ["金融"], "2890": ["金融"], "5880": ["金融"], "5871": ["金融"],
        # AI伺服器/代工
        "2317": ["AI伺服器/代工"], "2382": ["AI伺服器/代工"], "3231": ["AI伺服器/代工"], "2356": ["AI伺服器/代工"], "6669": ["AI伺服器/代工"], "2308": ["電源供應器"],
        # 重電與綠能電力
        "1513": ["重電/電力系統"], "1514": ["重電/電力系統"], "1519": ["重電/電力系統"], "1503": ["重電/電力系統"], "6806": ["綠能/電力"],
        # 低軌衛星
        "3491": ["低軌衛星"], "2314": ["低軌衛星"], "6285": ["低軌衛星"],
        # 其他材料
        "6509": ["電池材料"],
    }
    
    for sym, themes in COMMON_THEME_MAP.items():
        stock_themes[sym] = list(themes)
        
    # 2. 備用：若不在常見熱門表，則載入 ticker_registry_tw.json 產業分類並進行通俗化轉換
    registry_path = os.path.join(PROJECT_DIR, "ticker_registry_tw.json")
    if os.path.exists(registry_path):
        industry_map = {
            "01": "水泥", "02": "食品", "03": "塑膠", "04": "紡織纖維",
            "05": "電機機械", "06": "電器電纜", "07": "化學", "08": "玻璃陶瓷",
            "09": "造紙", "10": "鋼鐵", "11": "橡膠", "12": "汽車",
            "13": "電子", "14": "建材營造", "15": "航運", "16": "觀光餐旅",
            "17": "金融", "18": "貿易百貨", "19": "綜合", "20": "其他",
            "21": "化學", "22": "生技醫療", "23": "油電燃氣", "24": "半導體",
            "25": "電腦及週邊", "26": "光電", "27": "通信網路", "28": "電子零組件",
            "29": "電子通路", "30": "資訊服務", "31": "其他電子"
        }
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                registry = json.load(f)
            for sym, info in registry.items():
                if sym in stock_themes:
                    continue  # 已經有常見對照表了，跳過
                ind = info.get("industry")
                if ind and ind != "未分類":
                    mapped_name = industry_map.get(ind, ind)
                    stock_themes[sym] = [mapped_name]
        except Exception as e:
            print(f"解析 ticker_registry_tw.json 出錯: {e}")
            
    return stock_themes

def get_outstanding_shares():
    """
    獲取並快取上市櫃公司已發行張數(千股)資料，用於計算「投本比」與「外本比」
    """
    cache_file = os.path.join(PROJECT_DIR, "outstanding_shares.json")
    shares_map = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                shares_map = json.load(f)
            print(f"從快取載入 {len(shares_map)} 筆個股發行張數資料")
            return shares_map
        except Exception as e:
            print("讀取發行張數快取失敗，重新獲取", e)
            
    print("正在下載 TWSE / TPEx 已發行張數與股本資料...")
    # 1. TWSE 上市基本資料 (包含已發行普通股數)
    try:
        url_twse = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
        res = requests.get(url_twse, timeout=20, verify=False)
        data = res.json()
        if data and len(data) > 0:
            # 尋找包含 TDR 或普通股發行的欄位，考量 CP950 亂碼，進行動態特徵匹配
            first = data[0]
            code_key = None
            for k in first.keys():
                val = str(first.get(k, "")).strip()
                if len(val) == 4 and val.isdigit():
                    code_key = k
                    break
            
            shares_key = next((k for k in first.keys() if "TDR" in k), None)
            
            # 備用方案
            candidate_keys = list(first.keys())
            if not code_key and len(candidate_keys) > 1:
                code_key = candidate_keys[1]
            if not shares_key and len(candidate_keys) > 32:
                shares_key = candidate_keys[32]
            
            if code_key and shares_key:
                print(f"動態匹配 TWSE 欄位 - 代號欄位: {code_key}, 股數欄位: {shares_key}")
                for row in data:
                    code = str(row.get(code_key, "")).strip()
                    val_str = str(row.get(shares_key, "0")).strip().replace(",", "")
                    if code.isdigit() and val_str.isdigit():
                        # 已發行普通股數以「股」為單位，轉為「張(千股)」除以1000
                        shares_map[code] = float(val_str) / 1000.0
            print(f"TWSE 已發行張數載入完成，目前累計: {len(shares_map)} 筆")
    except Exception as e:
        print("下載 TWSE 已發行普通股數失敗", e)
        
    # 2. TPEx 上櫃行情資料 (包含 Capitals 實收資本額)
    try:
        url_tpex = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"
        res = requests.get(url_tpex, timeout=20, verify=False)
        data = res.json()
        if data:
            for row in data:
                code = str(row.get("SecuritiesCompanyCode", "")).strip()
                cap_val = row.get("Capitals")
                if code.isdigit() and cap_val is not None:
                    # Capitals 以元為單位。面額多為 10 元。
                    # 已發行張數(千股) = Capitals / 10 / 1000 = Capitals / 10000
                    shares_map[code] = float(cap_val) / 10000.0
            print(f"TPEx 已發行張數載入完成，目前累計: {len(shares_map)} 筆")
    except Exception as e:
        print("下載 TPEx 股本資料失敗", e)
        
    if shares_map:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(shares_map, f, ensure_ascii=False, indent=2)
            print(f"已儲存發行張數快取檔案: {cache_file} (總計 {len(shares_map)} 筆)")
        except Exception as e:
            print("寫入發行張數快取失敗", e)
            
    return shares_map

def analyze_chips(target_date):
    """
    分析籌碼，並產出 summary JSON
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 取得目標日期的所有資料
    cursor.execute("""
        SELECT * FROM chips_history WHERE date = ?
    """, (target_date,))
    today_records = [dict(row) for row in cursor.fetchall()]
    
    if not today_records:
        print(f"資料庫中無 {target_date} 的籌碼資料，無法生成分析摘要。")
        conn.close()
        return
    
    # 2. 取得近 5 日的外資買超紀錄，用來判斷「量增/爆量」
    # 我們需要找出這一天之前的 5 個交易日日期
    cursor.execute("""
        SELECT DISTINCT date FROM chips_history 
        WHERE date < ? 
        ORDER BY date DESC LIMIT 5
    """, (target_date,))
    past_dates = [row["date"] for row in cursor.fetchall()]
    print(f"歷史對比交易日: {past_dates}")
    
    # 載入歷史外資買超數據
    past_foreign_sums = {}
    if past_dates:
        placeholders = ",".join("?" for _ in past_dates)
        cursor.execute(f"""
            SELECT symbol, foreign_net FROM chips_history 
            WHERE date IN ({placeholders})
        """, past_dates)
        for row in cursor.fetchall():
            sym = row["symbol"]
            val = row["foreign_net"]
            if sym not in past_foreign_sums:
                past_foreign_sums[sym] = []
            past_foreign_sums[sym].append(val)
            
    conn.close()
    
    # 載入個股題材對照表
    stock_themes = get_stock_themes()
    # 載入發行張數/股本對照表
    shares_map = get_outstanding_shares()
    
    # 3. 執行過濾與計算
    cohort_buys = []       # 三大法人同買
    foreign_surges = []    # 外資爆量同買
    top_buys = []          # 今日排行前 50 名
    
    # 排行排序 (以三大法人合計買超為主)
    sorted_today = sorted(today_records, key=lambda x: x["total_net"], reverse=True)
    top_buys = sorted_today[:100]  # 取前 100 筆為排行榜
    
    for r in today_records:
        sym = r["symbol"]
        f_net = r["foreign_net"]
        t_net = r["trust_net"]
        d_net = r["dealer_net"]
        tot_net = r["total_net"]
        
        # 條件 1: 三大法人同買 (都 > 0)
        is_cohort = (f_net > 0 and t_net > 0 and d_net > 0)
        
        # 條件 2: 外資爆量量增
        # 量增定義：今日外資買超張數 > 歷史 5 日平均買超的 1.5 倍
        # 且今日外資買超必須 > 100 張 (防小量干擾)
        is_surge = False
        hist_vals = past_foreign_sums.get(sym, [])
        
        # 如果有歷史資料，計算平均買超 (只看買超日，若都是賣超則設為 50 作為基準值以防除以零或雜訊)
        if hist_vals:
            # 只取歷史中大於 0 的買超值，若沒有則設為基值
            pos_hist = [v for v in hist_vals if v > 0]
            avg_hist = sum(pos_hist) / len(pos_hist) if pos_hist else 50
            if f_net > avg_hist * 1.5 and f_net > 100:
                is_surge = True
        else:
            # 沒有歷史資料時，採用絕對高買超張數 (如大於 500 張) 作為爆量判定
            if f_net > 500:
                is_surge = True
                
        # 附加題材資訊與投本比/外本比
        r_themes = stock_themes.get(sym, [])
        r["themes"] = r_themes
        r["is_cohort"] = is_cohort
        r["is_surge"] = is_surge
        
        shares = shares_map.get(sym, 0.0)
        if shares > 0:
            r["foreign_ratio"] = round((f_net / shares) * 100, 3)
            r["trust_ratio"] = round((t_net / shares) * 100, 3)
        else:
            r["foreign_ratio"] = 0.0
            r["trust_ratio"] = 0.0
        
        if is_cohort:
            cohort_buys.append(r)
            if is_surge:
                foreign_surges.append(r)
                
    # 4. 進行「題材群聚/分群」分析 (針對外資爆量且同買的個股)
    theme_clusters = {}
    for r in foreign_surges:
        for theme in r["themes"]:
            if theme not in theme_clusters:
                theme_clusters[theme] = {
                    "theme_name": theme,
                    "stocks": [],
                    "total_foreign_buy": 0,
                    "total_trust_buy": 0,
                    "total_net_buy": 0
                }
            theme_clusters[theme]["stocks"].append({
                "symbol": r["symbol"],
                "name": r["name"],
                "foreign_net": r["foreign_net"],
                "trust_net": r["trust_net"],
                "dealer_net": r["dealer_net"],
                "total_net": r["total_net"],
                "foreign_ratio": r["foreign_ratio"],
                "trust_ratio": r["trust_ratio"]
            })
            theme_clusters[theme]["total_foreign_buy"] += r["foreign_net"]
            theme_clusters[theme]["total_trust_buy"] += r["trust_net"]
            theme_clusters[theme]["total_net_buy"] += r["total_net"]
            
    # 過濾出至少有 2 檔股票集體發動的題材
    focus_themes = []
    for t_info in theme_clusters.values():
        if len(t_info["stocks"]) >= 2:
            # 排序個股買超
            t_info["stocks"] = sorted(t_info["stocks"], key=lambda x: x["total_net"], reverse=True)
            focus_themes.append(t_info)
            
    # 依題材總買超金額排序
    # 4.5 計算外本比與投本比的獨立排行 (限買超 > 0，由大到小)
    top_foreign_ratio = sorted([r for r in today_records if r.get("foreign_ratio", 0) > 0], key=lambda x: x["foreign_ratio"], reverse=True)[:50]
    top_trust_ratio = sorted([r for r in today_records if r.get("trust_ratio", 0) > 0], key=lambda x: x["trust_ratio"], reverse=True)[:50]

    # 5. 輸出統計檔案
    summary_data = {
        "date": target_date,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "focus_themes": focus_themes,               # 今日法人集體佈局焦點題材 (同買 + 爆量且 >= 2檔)
        "cohort_buys": sorted(cohort_buys, key=lambda x: x["total_net"], reverse=True)[:50],  # 今日法人同買明細 (前50)
        "foreign_surges": sorted(foreign_surges, key=lambda x: x["foreign_net"], reverse=True)[:50], # 今日外資爆量個股
        "top_buys": top_buys,                        # 今日全部買超前100大個股
        "top_foreign_ratio": top_foreign_ratio,      # 今日外本比排行 (前50)
        "top_trust_ratio": top_trust_ratio           # 今日投本比排行 (前50)
    }
    
    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    print(f"成功產出籌碼分析摘要 JSON: {SUMMARY_JSON_PATH}")

def main():
    init_db()
    
    # 預設為今天，若提供參數則以參數為主
    date_str = datetime.now().strftime("%Y%m%d")
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--test":
            # 測試模式：使用最近的交易日
            date_str = "20260612"
        elif len(arg) == 8 and arg.isdigit():
            date_str = arg
            
    # 執行抓取
    twse_records = fetch_twse_data(date_str)
    tpex_records = fetch_tpex_data(date_str)
    all_records = twse_records + tpex_records
    
    if all_records:
        save_to_db(all_records)
        analyze_chips(date_str)
    else:
        print(f"未抓取到 {date_str} 的任何法人籌碼資料，略過存庫與分析。")

if __name__ == "__main__":
    main()
