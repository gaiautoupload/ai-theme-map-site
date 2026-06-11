import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus, urlparse

import requests

CACHE_FILE = Path(os.getenv("MAP_SEARCH_CACHE", "search_cache.json"))
CONTEXT_FILE = Path(os.getenv("MAP_SEARCH_CONTEXT", "search_context.json"))
EVIDENCE_DIR = Path(os.getenv("MAP_EVIDENCE_DIR", "evidence"))
TRUSTED_SOURCES_FILE = Path(os.getenv("MAP_TRUSTED_SOURCES", "trusted_sources.json"))
SEARCH_BACKEND = os.getenv("MAP_SEARCH_BACKEND", "whitelist_rss")
SEARCH_TIMEOUT = int(os.getenv("MAP_SEARCH_TIMEOUT", "30"))
SEARCH_MAX_RESULTS = int(os.getenv("MAP_SEARCH_MAX_RESULTS", "10"))
FETCH_ENABLED = os.getenv("MAP_SEARCH_FETCH_ENABLED", "1") == "1"
FETCH_MAX_CHARS = int(os.getenv("MAP_FETCH_MAX_CHARS", "2200"))
MIN_DELAY = float(os.getenv("MAP_SEARCH_MIN_DELAY", "2.5"))
MAX_DELAY = float(os.getenv("MAP_SEARCH_MAX_DELAY", "5.5"))

SAFE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

SOURCE_ENDPOINTS = {
    "Reuters": [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.reuters.com/reuters/technologyNews",
        "https://feeds.reuters.com/reuters/worldNews",
    ],
    "CNBC": [
        "https://www.cnbc.com/id/10001147/device/rss/rss.html",
        "https://www.cnbc.com/id/19854910/device/rss/rss.html",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    ],
    "MoneyDJ": [
        "https://www.moneydj.com/KMDJ/RSS/RSSViewer.aspx?A=MB00",
        "https://www.moneydj.com/KMDJ/RSS/RSSViewer.aspx?A=MB010000",
    ],
    "鉅亨網": [
        "https://news.cnyes.com/rss/news/cat/tw_stock",
        "https://news.cnyes.com/rss/news/cat/tech",
        "https://news.cnyes.com/rss/news/cat/headline",
    ],
    "TechNews": [
        "https://technews.tw/feed/",
        "https://finance.technews.tw/feed/",
    ],
    "DIGITIMES": [
        "https://www.digitimes.com.tw/rss/daily.xml",
    ],
    "TWSE": [
        "https://www.twse.com.tw/rss/zh/news/news_all.xml",
    ],
    "TPEx": [
        "https://www.tpex.org.tw/web/rss/news.xml",
    ],
}

SOURCE_GROUP_MAP = {
    "Reuters": "global_news",
    "CNBC": "global_news",
    "MoneyDJ": "taiwan_finance_news",
    "鉅亨網": "taiwan_finance_news",
    "TechNews": "taiwan_finance_news",
    "DIGITIMES": "taiwan_finance_news",
    "TWSE": "official_sources",
    "TPEx": "official_sources",
    "MOPS": "official_sources",
    "YouTube": "youtube_sources",
    "Analyst": "analyst_sources",
    "Community": "community_sources",
}


def load_json_file(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_cache() -> Dict[str, Any]:
    data = load_json_file(CACHE_FILE)
    return data if isinstance(data, dict) else {}


def save_cache(data: Dict[str, Any]) -> None:
    save_json_file(CACHE_FILE, data)


def load_search_context() -> Dict[str, List[Dict[str, str]]]:
    data = load_json_file(CONTEXT_FILE)
    if isinstance(data, dict):
        return data
    return {}


def safe_sleep() -> None:
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    time.sleep(delay)


def build_headers() -> Dict[str, str]:
    return {
        "User-Agent": random.choice(SAFE_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml,application/atom+xml,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }


def strip_html_tags(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def blocked_url(url: str) -> bool:
    blocked_hosts = [
        "accounts.google.com",
        "consent.yahoo.com",
        "login.live.com",
        "facebook.com",
        "instagram.com",
        "x.com",
        "twitter.com",
    ]
    return any(host in url for host in blocked_hosts)


def score_match(text: str, query_terms: List[str]) -> int:
    hay = text.lower()
    return sum(1 for term in query_terms if term and term.lower() in hay)


def tokenize_query(query: str) -> List[str]:
    raw_terms = re.split(r"[\s,，、/|]+", query)
    terms = [x.strip() for x in raw_terms if len(x.strip()) >= 2]
    seen = set()
    output = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            output.append(term)
    return output[:8]


def parse_rss_items(xml_text: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    item_pattern = re.compile(r"<(item|entry)>([\s\S]*?)</\1>", re.IGNORECASE)

    def extract(block: str, tag: str) -> str:
        m = re.search(rf"<{tag}[^>]*>([\s\S]*?)</{tag}>", block, re.IGNORECASE)
        if m:
            return strip_html_tags(m.group(1))
        return ""

    def extract_link(block: str) -> str:
        m = re.search(r"<link[^>]*>([\s\S]*?)</link>", block, re.IGNORECASE)
        if m:
            return strip_html_tags(m.group(1))
        m = re.search(r'<link[^>]*href="([^"]+)"', block, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return ""

    for match in item_pattern.finditer(xml_text):
        block = match.group(2)
        title = extract(block, "title")
        link = extract_link(block)
        desc = extract(block, "description") or extract(block, "summary") or extract(block, "content")
        pub_date = extract(block, "pubDate") or extract(block, "published") or extract(block, "updated")
        if title and link:
            items.append({
                "title": title,
                "url": link,
                "snippet": desc,
                "published_at": pub_date,
            })
    return items


def fetch_text(url: str) -> str:
    if blocked_url(url):
        return ""
    safe_sleep()
    resp = requests.get(url, headers=build_headers(), timeout=SEARCH_TIMEOUT, allow_redirects=True)
    if resp.status_code >= 400:
        return ""
    return resp.text


def fetch_rss_source(source_name: str, query_terms: List[str]) -> List[Dict[str, str]]:
    endpoints = SOURCE_ENDPOINTS.get(source_name, [])
    matched: List[Dict[str, str]] = []
    for endpoint in endpoints:
        try:
            xml_text = fetch_text(endpoint)
            items = parse_rss_items(xml_text)
            for item in items:
                combined = " ".join([
                    item.get("title", ""),
                    item.get("snippet", ""),
                    item.get("url", ""),
                ])
                match_score = score_match(combined, query_terms)
                if match_score <= 0:
                    continue
                row = dict(item)
                row["source_name"] = source_name
                row["source_group"] = SOURCE_GROUP_MAP.get(source_name, "other")
                row["source_engine"] = "whitelist_rss"
                row["match_score"] = match_score
                row["content"] = ""
                matched.append(row)
        except Exception:
            continue
    return matched


def build_twse_search_url(query: str) -> str:
    return f"https://www.twse.com.tw/zh/search/news?query={quote_plus(query)}"


def build_tpex_search_url(query: str) -> str:
    return f"https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_result.php?l=zh-tw&keyword={quote_plus(query)}"


def build_mops_search_url(query: str) -> str:
    return f"https://mops.twse.com.tw/mops/web/t05sr01_1?TYPEK=all&step=1&keyword={quote_plus(query)}"


def enrich_results(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    enriched: List[Dict[str, str]] = []
    for item in results:
        result = dict(item)
        if FETCH_ENABLED:
            try:
                result["content"] = strip_html_tags(fetch_text(result.get("url", "")))[:FETCH_MAX_CHARS]
            except Exception:
                result["content"] = ""
        enriched.append(result)
    return enriched


def dedupe_results(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    output = []
    for item in results:
        key = item.get("url", "") or item.get("title", "")
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def rank_results(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    priority = {
        "official_sources": 0,
        "global_news": 1,
        "taiwan_finance_news": 2,
        "other": 3,
    }
    return sorted(
        results,
        key=lambda x: (
            priority.get(x.get("source_group", "other"), 9),
            -int(x.get("match_score", 0)),
            x.get("published_at", ""),
        ),
        reverse=False,
    )


def persist_evidence(query: str, results: List[Dict[str, str]]) -> None:
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in query)[:80] or "query"
    path = EVIDENCE_DIR / f"{safe_name}.json"
    payload = {
        "query": query,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "backend": SEARCH_BACKEND,
        "results": results,
        "official_search_pages": {
            "twse": build_twse_search_url(query),
            "tpex": build_tpex_search_url(query),
            "mops": build_mops_search_url(query),
        },
    }
    save_json_file(path, payload)


def search(query: str) -> List[Dict[str, str]]:
    cache = load_cache()
    if query in cache and isinstance(cache[query], list):
        return cache[query]

    results: List[Dict[str, str]] = []
    query_terms = tokenize_query(query)

    if SEARCH_BACKEND == "whitelist_rss":
        source_order = ["Reuters", "CNBC", "MoneyDJ", "鉅亨網", "TechNews", "DIGITIMES", "TWSE", "TPEx"]
        for source_name in source_order:
            results.extend(fetch_rss_source(source_name, query_terms))
        results = dedupe_results(results)
        results = enrich_results(results)
        results = rank_results(results)[:SEARCH_MAX_RESULTS]

    if not results:
        context = load_search_context()
        results = context.get(query, []) if isinstance(context.get(query, []), list) else []

    cache[query] = results
    save_cache(cache)
    if results:
        persist_evidence(query, results)
    return results


def format_search_context(query: str, results: List[Dict[str, str]]) -> str:
    if not results:
        return (
            f"查詢主題：{query}\n"
            f"目前沒有白名單來源結果。可手動補查官方搜尋頁：\n"
            f"- TWSE: {build_twse_search_url(query)}\n"
            f"- TPEx: {build_tpex_search_url(query)}\n"
            f"- MOPS: {build_mops_search_url(query)}"
        )

    lines = [f"查詢主題：{query}", "以下是白名單來源上下文："]
    for idx, item in enumerate(results, start=1):
        lines.append(f"[{idx}] 標題：{item.get('title', '')}")
        if item.get("url"):
            lines.append(f"    來源：{item['url']}")
        lines.append(f"    來源名稱：{item.get('source_name', '')}")
        lines.append(f"    來源分類：{item.get('source_group', 'other')}")
        if item.get("published_at"):
            lines.append(f"    發布時間：{item['published_at']}")
        if item.get("snippet"):
            lines.append(f"    摘要：{item['snippet']}")
        if item.get("content"):
            lines.append(f"    內容：{item['content']}")
    lines.append("官方補查入口：")
    lines.append(f"- TWSE: {build_twse_search_url(query)}")
    lines.append(f"- TPEx: {build_tpex_search_url(query)}")
    lines.append(f"- MOPS: {build_mops_search_url(query)}")
    return "\n".join(lines)


def build_search_context_from_evidence(theme: str, payload: Dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return format_search_context(theme, [])

    lines = [f"查詢主題：{theme}", "以下是主題 evidence 白名單上下文："]
    for bucket in ["official_sources", "global_news", "taiwan_finance_news", "other"]:
        items = payload.get(bucket, [])
        if not isinstance(items, list) or not items:
            continue
        lines.append(f"【{bucket}】")
        for idx, item in enumerate(items[:8], start=1):
            if not isinstance(item, dict):
                continue
            lines.append(f"[{bucket}-{idx}] 標題：{item.get('title', '')}")
            if item.get("url"):
                lines.append(f"    來源：{item['url']}")
            lines.append(f"    來源名稱：{item.get('source_name', '')}")
            lines.append(f"    來源分類：{item.get('source_group', bucket)}")
            if item.get("published_at"):
                lines.append(f"    發布時間：{item['published_at']}")
            if item.get("snippet"):
                lines.append(f"    摘要：{item['snippet']}")
            if item.get("content"):
                lines.append(f"    內容：{item['content']}")

    lines.append("官方補查入口：")
    official_search_pages = payload.get("official_search_pages", {})
    if isinstance(official_search_pages, dict) and official_search_pages:
        if official_search_pages.get("twse"):
            lines.append(f"- TWSE: {official_search_pages['twse']}")
        if official_search_pages.get("tpex"):
            lines.append(f"- TPEx: {official_search_pages['tpex']}")
        if official_search_pages.get("mops"):
            lines.append(f"- MOPS: {official_search_pages['mops']}")
    else:
        lines.append(f"- TWSE: {build_twse_search_url(theme)}")
        lines.append(f"- TPEx: {build_tpex_search_url(theme)}")
        lines.append(f"- MOPS: {build_mops_search_url(theme)}")

    return "\n".join(lines)
