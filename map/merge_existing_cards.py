import json, os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_FILE = ROOT / os.getenv('MAP_REPO_FILE', 'maps_repo.json')
SITE_REPO = Path(os.getenv('MAP_SITE_REPO_DIR', 'D:/ai-theme-map-site'))

current = json.loads(REPO_FILE.read_text(encoding='utf-8'))
previous = {}
used = None

# Priority 1: previous published working tree.
site_map = SITE_REPO / 'maps_repo.json'
if site_map.exists():
    try:
        previous = json.loads(site_map.read_text(encoding='utf-8'))
        used = str(site_map)
    except Exception:
        previous = {}

# Priority 2: latest git HEAD in site repo.
if not previous and SITE_REPO.exists():
    try:
        raw = subprocess.check_output(['git','show','HEAD:maps_repo.json'], cwd=str(SITE_REPO), stderr=subprocess.DEVNULL)
        previous = json.loads(raw.decode('utf-8'))
        used = 'git HEAD:maps_repo.json'
    except Exception:
        pass

# Priority 3: local backup.
backup = ROOT / 'maps_repo.backup.json'
if not previous and backup.exists():
    previous = json.loads(backup.read_text(encoding='utf-8'))
    used = str(backup)

def title_of(v):
    if not isinstance(v, dict): return ''
    return (v.get('title') or v.get('theme_name') or v.get('name') or '').strip()

def date_of(v):
    if not isinstance(v, dict): return ''
    return str(v.get('updated_at') or v.get('date') or '')

merged = {}
seen_titles = set()

# New/current cards first.
for k, v in current.items():
    merged[k] = v
    t = title_of(v)
    if t: seen_titles.add(t)

kept = skipped = 0
for k, v in previous.items():
    t = title_of(v)
    if t and t in seen_titles:
        skipped += 1
        continue
    nk = k
    i = 2
    while nk in merged:
        nk = f'{k}_old{i}'
        i += 1
    merged[nk] = v
    if t: seen_titles.add(t)
    kept += 1

REPO_FILE.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
print('current_new', len(current), 'previous', len(previous), 'kept_old', kept, 'skipped_duplicate', skipped, 'merged', len(merged), 'previous_source', used)
print('top cards:')
for v in list(merged.values())[:8]:
    print('-', title_of(v), date_of(v))
