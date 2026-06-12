import json
import os
import sys
import datetime
import subprocess
from pathlib import Path

# Add imports from our existing scripts
from monthly_stock_updater import update_single_stock, REGISTRY_FILE, WIKI_FILE

def main():
    target_codes = ["2330", "2303", "2454", "2317"]  # 台積電, 聯電, 聯發科, 鴻海
    print(f"=== 開始針對特定個股進行 LLM Wiki 結構化更新 ===")
    print(f"目標個股：{target_codes}")
    
    if not REGISTRY_FILE.exists():
        print("錯誤：找不到 ticker_registry_tw.json")
        return
        
    registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    
    wiki_data = {}
    if WIKI_FILE.exists():
        try:
            wiki_data = json.loads(WIKI_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"讀取既存 wiki 失敗: {e}")
            
    for code in target_codes:
        if code not in registry:
            print(f"警告：找不到代號 {code}")
            continue
            
        entry = registry[code]
        name = entry.get("name", "")
        industry = entry.get("industry", "未分類")
        market = entry.get("market", "")
        
        print(f"\n正在更新 {code} ({name})...")
        try:
            existing_record = wiki_data.get(code, {})
            new_record = update_single_stock(code, name, industry, market, existing_record)
            wiki_data[code] = new_record
            print(f"-> {code} ({name}) 更新成功！")
        except Exception as e:
            print(f"-> {code} ({name}) 更新失敗: {e}")
            
    WIKI_FILE.write_text(json.dumps(wiki_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== 更新完成！執行發布與 Git 推送 ===")
    
    try:
        subprocess.run([sys.executable, "publish_site.py"], check=True)
        print("發布並成功推送至 GitHub Pages！")
    except Exception as e:
        print(f"Git 推送失敗: {e}")

if __name__ == "__main__":
    main()
