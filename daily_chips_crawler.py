import os
import sys
import json
import sqlite3
import requests
from datetime import datetime, timedelta

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
        resp = requests.get(url, timeout=15)
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
        resp = requests.get(url, timeout=15)
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
    從 stocks_wiki.json 與 maps_repo.json 中解析 股號 -> 題材清單
    """
    import re
    stock_themes = {}
    
    # 1. 優先從 stocks_wiki.json 載入
    stocks_wiki_path = os.path.join(PROJECT_DIR, "stocks_wiki.json")
    if os.path.exists(stocks_wiki_path):
        try:
            with open(stocks_wiki_path, "r", encoding="utf-8") as f:
                wiki = json.load(f)
            for sym, info in wiki.items():
                themes = info.get("themes", [])
                if themes:
                    if sym not in stock_themes:
                        stock_themes[sym] = []
                    for t in themes:
                        if t not in stock_themes[sym]:
                            stock_themes[sym].append(t)
            print(f"成功從 stocks_wiki.json 載入 {len(stock_themes)} 筆個股題材對照")
        except Exception as e:
            print(f"解析 stocks_wiki.json 出錯: {e}")
            
    # 遞迴掃描器，用來掃描所有字串欄位中的 (股號) 與 symbol 鍵值
    def scan_obj_for_symbols(obj, current_key=None):
        syms = []
        if isinstance(obj, str):
            for m in re.finditer(r'\((\d{4,6})\)', obj):
                syms.append(m.group(1))
            if current_key in ["symbol", "ticker", "code"] and re.match(r'^\d{4,6}$', obj):
                syms.append(obj)
        elif isinstance(obj, (int, float)):
            val_str = str(int(obj))
            if current_key in ["symbol", "ticker", "code"] and re.match(r'^\d{4,6}$', val_str):
                syms.append(val_str)
        elif isinstance(obj, list):
            for item in obj:
                syms.extend(scan_obj_for_symbols(item, current_key))
        elif isinstance(obj, dict):
            for k, val in obj.items():
                syms.extend(scan_obj_for_symbols(val, k))
        return syms

    # 2. 輔助/備用從 maps_repo.json 載入
    if os.path.exists(MAPS_REPO_PATH):
        try:
            with open(MAPS_REPO_PATH, "r", encoding="utf-8") as f:
                repo = json.load(f)
            
            for map_id, map_data in repo.items():
                if not isinstance(map_data, dict):
                    continue
                theme_name = map_data.get("theme_name") or map_data.get("title")
                if not theme_name:
                    continue
                
                # 掃描整張地圖的所有欄位，找出所有提及的股號
                found_symbols = scan_obj_for_symbols(map_data)
                for sym in found_symbols:
                    if sym not in stock_themes:
                        stock_themes[sym] = []
                    if theme_name not in stock_themes[sym]:
                        stock_themes[sym].append(theme_name)
                                
            print(f"完成整合 maps_repo.json，個股題材庫總共: {len(stock_themes)} 筆對照")
        except Exception as e:
            print(f"解析 maps_repo.json 出錯: {e}")
            
    return stock_themes

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
                
        # 附加題材資訊
        r_themes = stock_themes.get(sym, [])
        r["themes"] = r_themes
        r["is_cohort"] = is_cohort
        r["is_surge"] = is_surge
        
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
                "total_net": r["total_net"]
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
    focus_themes = sorted(focus_themes, key=lambda x: x["total_net_buy"], reverse=True)
    
    # 5. 輸出統計檔案
    summary_data = {
        "date": target_date,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "focus_themes": focus_themes,               # 今日法人集體佈局焦點題材 (同買 + 爆量且 >= 2檔)
        "cohort_buys": sorted(cohort_buys, key=lambda x: x["total_net"], reverse=True)[:50],  # 今日法人同買明細 (前50)
        "foreign_surges": sorted(foreign_surges, key=lambda x: x["foreign_net"], reverse=True)[:50], # 今日外資爆量個股
        "top_buys": top_buys                         # 今日全部買超前100大個股
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
