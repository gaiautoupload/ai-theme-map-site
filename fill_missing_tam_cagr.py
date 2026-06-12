import json
import os
from pathlib import Path
import requests

VLLM_URL = os.getenv("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
MODEL_NAME = os.getenv("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")
TIMEOUT_SECONDS = int(os.getenv("MAP_TIMEOUT_SECONDS", "240"))

REPO_FILE = Path("maps_repo.json")

SYSTEM_PROMPT = """
你是一個專業的半導體與高科技產業分析師。請為輸入的主題推估合理的「潛在市場規模 (TAM)」與「複合年均成長率 (CAGR)」。
要求：
1. 只能輸出合法 JSON 格式，且屬性名必須為 "market_size_tam" 和 "market_cagr"。
2. 用詞必須精煉，字數限制在 12 字以內（例如：'2026年約50億美元'、'2025-2028約300億美元'；CAGR如：'20%~25%'、'CAGR 約 18%'）。
3. 一律使用繁體中文。
"""

def call_vllm_json(system_prompt: str, user_prompt: str) -> dict:
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1000,
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
    return json.loads(content)

def main():
    print("=== 開始補齊 maps_repo.json 中的市場規模 (TAM) 與複合年成長率 (CAGR) ===")
    
    if not REPO_FILE.exists():
        print("錯誤：找不到 maps_repo.json")
        return
        
    try:
        maps_repo = json.loads(REPO_FILE.read_text(encoding="utf-8"), strict=False)
    except Exception as e:
        print(f"讀取 maps_repo.json 失敗: {e}")
        return
        
    updated_count = 0
    for key, map_val in maps_repo.items():
        title = map_val.get("title", "")
        tam = map_val.get("market_size_tam", "待補資料")
        cagr = map_val.get("market_cagr", "待補資料")
        
        needs_tam = tam in ["待補資料", "待補", "", None]
        needs_cagr = cagr in ["待補資料", "待補", "", None]
        
        if needs_tam or needs_cagr:
            print(f"\n正在補齊主題：{title}")
            user_prompt = f"""
請根據以下產業鏈主題推估合理的潛在市場規模 (TAM) 與複合年均成長率 (CAGR)：
主題名稱：{title}
主題描述：{map_val.get('desc', '')}
"""
            try:
                res = call_vllm_json(SYSTEM_PROMPT, user_prompt)
                if needs_tam and "market_size_tam" in res:
                    map_val["market_size_tam"] = res["market_size_tam"]
                if needs_cagr and "market_cagr" in res:
                    map_val["market_cagr"] = res["market_cagr"]
                print(f"-> 成功補齊：TAM={map_val.get('market_size_tam')}, CAGR={map_val.get('market_cagr')}")
                updated_count += 1
            except Exception as e:
                print(f"-> 補齊失敗: {e}")
                
            # 即時存檔
            REPO_FILE.write_text(json.dumps(maps_repo, ensure_ascii=False, indent=2), encoding="utf-8")
            
    print(f"\n=== 補齊完成！共更新 {updated_count} 個主題地圖。 ===")

if __name__ == "__main__":
    main()
