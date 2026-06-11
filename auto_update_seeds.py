import json
import os
import re
from datetime import datetime
from pathlib import Path
import requests

from search_provider import search, tokenize_query

VLLM_URL = os.getenv("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
MODEL_NAME = os.getenv("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")
TIMEOUT_SECONDS = int(os.getenv("MAP_TIMEOUT_SECONDS", "240"))
SEEDS_FILE = Path(os.getenv("MAP_THEME_SEEDS_FILE", "theme_seeds.json"))

UPDATER_SYSTEM_PROMPT = """
你是一個前瞻性投資題材探索專家。你的任務是閱讀近期市場新聞與科技趨勢，並與現有的投資題材池進行比對，從中發現「全新、尚未被包含在現有題材池中」的投資題材。

【硬性要求】
1. 必須是繁體中文。
2. 題材必須是具備投資研究價值的「產業鏈級別」或「關鍵技術升級」題材，且能對接到台股/華人供應鏈（例如：光通訊、先進材料、半導體設備、網通升級、重電等）。
3. 只能輸出合法 JSON。
4. 題材敘述應清晰、具體，例如：「人形機器人關鍵電機與減速器供應鏈」或「高階 Wi-Fi 7 升級與射頻前端晶片商機」，而非籠統的「AI發展」或「電子業復甦」。
5. **絕對不能**與現有的題材重複或高度相似。
"""

def call_vllm_json(system_prompt: str, user_prompt: str, max_tokens: int = 3000, temperature: float = 0.5) -> dict:
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
    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()
    return json.loads(content)

def main():
    print("=== 開始自動探索與更新題材種子 ===")
    
    # 1. 讀取現有的 seeds
    if not SEEDS_FILE.exists():
        print(f"錯誤：找不到 {SEEDS_FILE}")
        return
    
    existing_data = json.loads(SEEDS_FILE.read_text(encoding="utf-8"))
    existing_groups = existing_data.get("seed_groups", [])
    
    # 整理所有現有題材，方便比對
    existing_themes_list = []
    for g in existing_groups:
        existing_themes_list.extend(g.get("themes", []))
    
    print(f"目前已有 {len(existing_themes_list)} 個題材種子。")

    # 2. 到 RSS 來源檢索最新的熱門詞彙，建立脈絡
    queries = ["科技 供應鏈", "半導體 新技術", "美股 產業趨勢", "資料中心 升級"]
    news_items = []
    seen_urls = set()
    
    print("正在檢索最新市場資訊以尋找靈感...")
    for q in queries:
        try:
            results = search(q)
            for r in results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    news_items.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", "")
                    })
        except Exception as e:
            print(f"檢索 {q} 失敗: {e}")
            
    print(f"成功收集到 {len(news_items)} 條近期新聞與趨勢。")

    # 3. 呼叫 vLLM 生成新主題
    user_prompt = f"""
請根據以下近期市場新聞與趨勢，分析是否有任何「全新、且尚未包含在現有題材池中」的投資題材（偏向可對接到台股/供應鏈的題材）。

【近期市場新聞與趨勢】
{json.dumps(news_items[:25], ensure_ascii=False, indent=2)}

【現有的題材池（請絕對不要重複這些主題）】
{json.dumps(existing_groups, ensure_ascii=False, indent=2)}

請輸出 JSON 格式如下：
{{
  "new_seed_groups": [
    {{
      "group": "群組名稱（可使用現有群組如 'AI 與半導體'、'太空與通訊'、'能源與基建'、'製造回流與政策' 等，或建立新群組）",
      "themes": [
        "全新題材名稱1（敘述需具備產業細節，且能對應到供應鏈）",
        "全新題材名稱2"
      ]
    }}
  ]
}}

限制：
1. 請產出 2 ~ 4 個全新題材。
2. 題材敘述必須與現有題材有明顯差異。
"""

    print("呼叫 AI 進行趨勢分析與新題材生成...")
    try:
        response_json = call_vllm_json(UPDATER_SYSTEM_PROMPT, user_prompt)
        new_groups = response_json.get("new_seed_groups", [])
    except Exception as e:
        print(f"AI 生成新題材失敗: {e}")
        return

    # 4. 合併新題材到既存的 seeds 中
    added_count = 0
    for new_g in new_groups:
        group_name = new_g.get("group", "").strip()
        new_themes = new_g.get("themes", [])
        if not group_name or not new_themes:
            continue
            
        # 尋找是否已有相同 group
        target_group = None
        for g in existing_groups:
            if g.get("group", "").strip() == group_name:
                target_group = g
                break
                
        if target_group is None:
            # 建立新 group
            target_group = {"group": group_name, "themes": []}
            existing_groups.append(target_group)
            print(f"新增群組：{group_name}")
            
        for theme in new_themes:
            theme = theme.strip()
            # 檢查是否重複
            is_dup = False
            for t in target_group["themes"]:
                # 簡單的相似度或字串包含檢查
                if theme in t or t in theme:
                    is_dup = True
                    break
            
            # 與全局所有題材做一次比對
            for ext in existing_themes_list:
                if theme in ext or ext in theme:
                    is_dup = True
                    break
                    
            if not is_dup:
                target_group["themes"].append(theme)
                existing_themes_list.append(theme)
                print(f"  [+] 新增題材於 [{group_name}]: {theme}")
                added_count += 1
            else:
                print(f"  [-] 略過重複或極相似題材: {theme}")

    if added_count > 0:
        # 更新更新時間並存檔
        existing_data["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        existing_data["seed_groups"] = existing_groups
        SEEDS_FILE.write_text(json.dumps(existing_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"=== 自動更新完成！共新增了 {added_count} 個新題材到 {SEEDS_FILE} ===")
    else:
        print("沒有發現足夠新穎且不重複的題材，未進行更新。")

if __name__ == "__main__":
    main()
