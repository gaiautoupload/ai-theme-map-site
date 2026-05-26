from pathlib import Path
html = Path(r'D:\ai-theme-map-site\index_v2.html').read_text(encoding='utf-8')
for needle in ['maps_repo_v3.json?v=202605261930', 'broadened.forEach', 'related.slice(0, 2)', 'index_v2']:
    print(needle, needle in html)
