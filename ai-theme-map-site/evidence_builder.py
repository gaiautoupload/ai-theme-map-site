import json
import os
from pathlib import Path
from typing import Any, Dict, List

from search_provider import search

DISCOVERY_FILE = Path(os.getenv("MAP_DISCOVERY_OUTPUT", "discovered_themes.json"))
EVIDENCE_DIR = Path(os.getenv("MAP_EVIDENCE_DIR", "evidence"))
MAX_RUN = int(os.getenv("MAP_DISCOVERY_RUN_TOP", "5"))
MAX_QUERIES_PER_THEME = int(os.getenv("MAP_EVIDENCE_MAX_QUERIES", "1"))


def load_discovery() -> Dict[str, Any]:
    if not DISCOVERY_FILE.exists():
        raise FileNotFoundError(f"找不到 discovery 結果：{DISCOVERY_FILE}")
    return json.loads(DISCOVERY_FILE.read_text(encoding="utf-8"))


def slugify(text: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in text).strip("_")
    return safe[:80] or "theme"


def build_theme_queries(theme_item: Dict[str, Any]) -> List[str]:
    theme = str(theme_item.get("theme", "")).strip()
    group = str(theme_item.get("group", "")).strip()
    tw_angle = str(theme_item.get("tw_angle", "")).strip()
    queries = [theme]
    if theme:
        queries.append(f"{theme} 台股 供應鏈")
        queries.append(f"{theme} 受惠股")
    if group:
        queries.append(f"{group} {theme}")
    if tw_angle:
        queries.append(tw_angle)
    deduped = []
    seen = set()
    for q in queries:
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            deduped.append(q)
    return deduped[:MAX_QUERIES_PER_THEME]


def classify_bucket(source_group: str) -> str:
    if source_group == "global_news":
        return "global_news"
    if source_group == "taiwan_finance_news":
        return "taiwan_finance_news"
    if source_group == "official_sources":
        return "official_sources"
    if source_group == "youtube_sources":
        return "youtube_sources"
    if source_group == "analyst_sources":
        return "analyst_sources"
    if source_group == "community_sources":
        return "community_sources"
    return "other"


def normalize_result(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "snippet": item.get("snippet", ""),
        "content": item.get("content", ""),
        "source_name": item.get("source_name", ""),
        "source_group": item.get("source_group", "other"),
        "source_engine": item.get("source_engine", ""),
        "published_at": item.get("published_at", ""),
        "match_score": item.get("match_score", 0),
    }


def build_evidence(theme_item: Dict[str, Any]) -> Dict[str, Any]:
    theme = str(theme_item.get("theme", "")).strip()
    queries = build_theme_queries(theme_item)
    payload: Dict[str, Any] = {
        "theme": theme,
        "group": theme_item.get("group", ""),
        "why_now": theme_item.get("why_now", ""),
        "market_link": theme_item.get("market_link", ""),
        "tw_angle": theme_item.get("tw_angle", ""),
        "queries": queries,
        "global_news": [],
        "taiwan_finance_news": [],
        "official_sources": [],
        "youtube_sources": [],
        "analyst_sources": [],
        "community_sources": [],
        "other": [],
    }

    seen_urls = set()
    for query in queries:
        results = search(query)
        for item in results:
            url = item.get("url", "")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            bucket = classify_bucket(item.get("source_group", "other"))
            payload[bucket].append(normalize_result(item))

    for key in ["global_news", "taiwan_finance_news", "official_sources", "youtube_sources", "analyst_sources", "community_sources", "other"]:
        payload[key] = payload[key][:12]

    payload["summary"] = {
        "global_news_count": len(payload["global_news"]),
        "taiwan_finance_news_count": len(payload["taiwan_finance_news"]),
        "official_sources_count": len(payload["official_sources"]),
        "youtube_sources_count": len(payload["youtube_sources"]),
        "analyst_sources_count": len(payload["analyst_sources"]),
        "community_sources_count": len(payload["community_sources"]),
        "other_count": len(payload["other"]),
        "total_count": sum(len(payload[k]) for k in ["global_news", "taiwan_finance_news", "official_sources", "youtube_sources", "analyst_sources", "community_sources", "other"]),
    }
    return payload


def save_evidence(theme: str, payload: Dict[str, Any]) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"theme_{slugify(theme)}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    discovery = load_discovery()
    themes = discovery.get("selected_themes", [])[:MAX_RUN]
    if not themes:
        print("沒有可建立 evidence 的主題")
        return

    for item in themes:
        theme = str(item.get("theme", "")).strip()
        if not theme:
            continue
        evidence = build_evidence(item)
        path = save_evidence(theme, evidence)
        summary = evidence.get("summary", {})
        print(f"evidence 已建立：{path.name}")
        print(
            f"  global={summary.get('global_news_count', 0)} "
            f"tw={summary.get('taiwan_finance_news_count', 0)} "
            f"official={summary.get('official_sources_count', 0)} "
            f"other={summary.get('other_count', 0)}"
        )


if __name__ == "__main__":
    main()
