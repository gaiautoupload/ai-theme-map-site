import json
import os
from pathlib import Path
from typing import Dict, Any

import requests
import urllib3

# 停用 SSL 憑證警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUTPUT_FILE = Path(os.getenv("MAP_TICKER_REGISTRY", "ticker_registry_tw.json"))
TIMEOUT = int(os.getenv("MAP_SEARCH_TIMEOUT", "30"))

TWSE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
TPEX_URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}


def normalize_aliases(*values: str) -> list[str]:
    seen = set()
    aliases = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in {"－", "-", "--"}:
            continue
        if text not in seen:
            seen.add(text)
            aliases.append(text)
    return aliases


def load_cached_registry() -> Dict[str, Dict[str, Any]]:
    if not OUTPUT_FILE.exists():
        return {}
    try:
        data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception as exc:
        print(f"讀取既有 ticker registry 失敗，將忽略快取：{exc}")
    return {}


def fetch_json(url: str, label: str):
    try:
        return requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False).json()
    except Exception as exc:
        print(f"{label} 下載，或寫入 registry 取得失敗：{exc}")
        return None


def build_twse_registry() -> Dict[str, Dict[str, Any]]:
    data = fetch_json(TWSE_URL, "TWSE")
    if data is None:
        return {}
    registry: Dict[str, Dict[str, Any]] = {}
    for row in data:
        code = str(row.get("公司代號", "")).strip()
        name = str(row.get("公司簡稱") or row.get("公司名稱") or "").strip()
        full_name = str(row.get("公司名稱", "")).strip()
        if not code.isdigit() or not name:
            continue
        registry[code] = {
            "name": name,
            "market": "TWSE",
            "aliases": normalize_aliases(full_name, row.get("英文簡稱", "")),
            "industry": str(row.get("產業別", "")).strip(),
            "source": "TWSE OpenAPI t187ap03_L",
        }
    return registry


def build_tpex_registry() -> Dict[str, Dict[str, Any]]:
    data = fetch_json(TPEX_URL, "TPEX")
    if data is None:
        return {}
    registry: Dict[str, Dict[str, Any]] = {}
    for row in data:
        code = str(row.get("SecuritiesCompanyCode", "")).strip()
        name = str(row.get("CompanyName", "")).strip()
        if not code.isdigit() or not name:
            continue
        registry[code] = {
            "name": name,
            "market": "TPEX",
            "aliases": [],
            "industry": "",
            "source": "TPEX OpenAPI tpex_mainboard_quotes",
        }
    return registry


def build_registry() -> Dict[str, Dict[str, Any]]:
    cached = load_cached_registry()
    merged: Dict[str, Dict[str, Any]] = {}
    twse = build_twse_registry()
    tpex = build_tpex_registry()
    if twse:
        merged.update(twse)
    else:
        merged.update({k: v for k, v in cached.items() if v.get("market") == "TWSE"})
    if tpex:
        merged.update(tpex)
    else:
        merged.update({k: v for k, v in cached.items() if v.get("market") == "TPEX"})
    if not merged and cached:
        merged.update(cached)
    if not merged:
        raise RuntimeError("無法建立 ticker registry：官方來源與既有快取皆不可用")
    return dict(sorted(merged.items(), key=lambda kv: kv[0]))


def main() -> None:
    registry = build_registry()
    OUTPUT_FILE.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    twse_count = sum(1 for x in registry.values() if x.get("market") == "TWSE")
    tpex_count = sum(1 for x in registry.values() if x.get("market") == "TPEX")
    print(f"ticker registry 已建立：{OUTPUT_FILE}")
    print(f"TWSE: {twse_count} 筆")
    print(f"TPEX: {tpex_count} 筆")
    print(f"總計: {len(registry)} 筆")


if __name__ == "__main__":
    main()
