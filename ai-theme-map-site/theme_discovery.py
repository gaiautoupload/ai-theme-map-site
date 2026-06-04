import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

VLLM_URL = os.getenv("MAP_VLLM_URL", "https://vllm-a5000.iii-ei-stack.com/v1/chat/completions")
MODEL_NAME = os.getenv("MAP_MODEL_NAME", "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit")
TIMEOUT_SECONDS = int(os.getenv("MAP_TIMEOUT_SECONDS", "240"))
SEEDS_FILE = Path(os.getenv("MAP_THEME_SEEDS_FILE", "theme_seeds.json"))
OUTPUT_FILE = Path(os.getenv("MAP_DISCOVERY_OUTPUT", "discovered_themes.json"))
MAX_SELECTED = int(os.getenv("MAP_DISCOVERY_MAX_SELECTED", "5"))

DISCOVERY_SYSTEM_PROMPT = """
你是一個投資主題發現代理。
任務不是只延續單一公司敘事，而是根據近期全球市場最有機會形成主線的方向，從候選題材池中選出最值得建立主題地圖的題材。

硬性要求：
1. 只能輸出合法 JSON。
2. 必須使用繁體中文。
3. 避免所有主題都圍繞單一公司。
4. 優先考慮近日國際主題、地緣政治、資本支出、技術路線升級、政策與供應鏈重組。
5. 請偏向可映射到台股/華人供應鏈的研究題材。
"""


def load_seed_groups() -> Dict[str, Any]:
    if not SEEDS_FILE.exists():
        raise FileNotFoundError(f"找不到題材池：{SEEDS_FILE}")
    return json.loads(SEEDS_FILE.read_text(encoding="utf-8"))


def extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    start = cleaned.find('{')
    if start == -1:
        raise ValueError("找不到 JSON 起點")
    depth = 0
    in_string = False
    escape = False
    end = -1
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
    if end == -1:
        raise ValueError("JSON 結尾不完整")
    return json.loads(cleaned[start:end])


def call_vllm_json(system_prompt: str, user_prompt: str, max_tokens: int = 3000, temperature: float = 0.35) -> Dict[str, Any]:
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
    return extract_json_object(content)


def build_prompt(seed_groups: Dict[str, Any]) -> str:
    return f"""
請從下列候選題材池中，選出今日最值得建立主題地圖的題材。

輸出 JSON 結構：
{{
  "macro_brief": ["近期最值得追蹤的國際主題摘要"],
  "selected_themes": [
    {{
      "rank": 1,
      "theme": "主題名稱",
      "group": "所屬群組",
      "why_now": "為什麼現在值得追",
      "market_link": "與近日國際市場/政策/戰爭/技術主線的連結",
      "tw_angle": "可映射的台股/供應鏈角度",
      "priority_score": 88
    }}
  ],
  "rejected_but_watch": ["本次未列入前幾名但值得持續觀察的題材"]
}}

限制：
1. selected_themes 最多 {MAX_SELECTED} 個。
2. 不要全部集中在同一群組。
3. priority_score 介於 0-100。
4. 至少涵蓋 3 個不同群組。

【候選題材池】
{json.dumps(seed_groups, ensure_ascii=False, indent=2)}
"""


def normalize_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    selected = payload.get("selected_themes", [])
    if not isinstance(selected, list):
        selected = []
    selected = selected[:MAX_SELECTED]
    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(selected, start=1):
        if not isinstance(item, dict):
            continue
        score_raw = item.get("priority_score", 0)
        try:
            score = int(score_raw)
        except Exception:
            score = 0
        score = max(0, min(100, score))
        normalized.append({
            "rank": idx,
            "theme": str(item.get("theme", "")).strip(),
            "group": str(item.get("group", "未分類")).strip(),
            "why_now": str(item.get("why_now", "")).strip(),
            "market_link": str(item.get("market_link", "")).strip(),
            "tw_angle": str(item.get("tw_angle", "")).strip(),
            "priority_score": score,
        })
    return {
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "macro_brief": payload.get("macro_brief", []),
        "selected_themes": normalized,
        "rejected_but_watch": payload.get("rejected_but_watch", []),
    }


def main() -> None:
    seeds = load_seed_groups()
    prompt = build_prompt(seeds)
    result = call_vllm_json(DISCOVERY_SYSTEM_PROMPT, prompt)
    normalized = normalize_result(result)
    OUTPUT_FILE.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"題材探索完成，共選出 {len(normalized['selected_themes'])} 個主題。")
    for item in normalized["selected_themes"]:
        print(f"- #{item['rank']} [{item['group']}] {item['theme']} ({item['priority_score']})")


if __name__ == "__main__":
    main()
