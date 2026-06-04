import json
import os
import subprocess
from pathlib import Path

DISCOVERY_FILE = Path(os.getenv("MAP_DISCOVERY_OUTPUT", "discovered_themes.json"))
REPORT_FILE = Path(os.getenv("MAP_REPORT_FILE", "report.txt"))
MAX_RUN = int(os.getenv("MAP_DISCOVERY_RUN_TOP", "3"))


def load_discovery():
    if not DISCOVERY_FILE.exists():
        raise FileNotFoundError(f"找不到 discovery 結果：{DISCOVERY_FILE}")
    return json.loads(DISCOVERY_FILE.read_text(encoding="utf-8"))


def main():
    payload = load_discovery()
    themes = payload.get("selected_themes", [])[:MAX_RUN]
    if not themes:
        print("沒有可生成的題材")
        return

    for item in themes:
        theme = str(item.get("theme", "")).strip()
        if not theme:
            continue
        REPORT_FILE.write_text(theme, encoding="utf-8")
        print(f"開始生成：{theme}")
        subprocess.run(["python", "map_generator.py"], check=True)

    print(f"完成，共生成 {len(themes)} 個主題地圖。")


if __name__ == "__main__":
    main()
