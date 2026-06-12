import json
import os
import subprocess
import sys
from pathlib import Path

DISCOVERY_FILE = Path(os.getenv("MAP_DISCOVERY_OUTPUT", "discovered_themes.json"))
REPORT_FILE = Path(os.getenv("MAP_REPORT_FILE", "report.txt"))
REPO_FILE = Path(os.getenv("MAP_REPO_FILE", "maps_repo.json"))
MAX_RUN = int(os.getenv("MAP_DISCOVERY_RUN_TOP", "5"))


def load_discovery():
    if not DISCOVERY_FILE.exists():
        raise FileNotFoundError(f"找不到 discovery 結果：{DISCOVERY_FILE}")
    return json.loads(DISCOVERY_FILE.read_text(encoding="utf-8"))


def run_generator(theme: str):
    REPORT_FILE.write_text(theme, encoding="utf-8")
    print(f"開始生成：{theme}")
    subprocess.run([sys.executable, "map_generator.py"], check=True)


def main():
    payload = load_discovery()
    themes = payload.get("selected_themes", [])[:MAX_RUN]
    if not themes:
        print("沒有可生成的題材")
        return

    if REPO_FILE.exists():
        print(f"保留既存資料庫，新主題將進行增量合併：{REPO_FILE}")

    count = 0
    for item in themes:
        theme = str(item.get("theme", "")).strip()
        if not theme:
            continue
        run_generator(theme)
        count += 1

    print(f"快速重建完成，共生成 {count} 個主題地圖。")


if __name__ == "__main__":
    main()
