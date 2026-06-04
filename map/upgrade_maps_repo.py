import json
from pathlib import Path
from map_generator import enrich_map

repo_path = Path('maps_repo.json')
backup_path = Path('maps_repo.stage1.backup.json')

with repo_path.open('r', encoding='utf-8') as f:
    data = json.load(f)

with backup_path.open('w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

normalized = {}
for key, value in data.items():
    if isinstance(value, dict) and 'title' in value:
        normalized[key] = enrich_map(key, value)

with repo_path.open('w', encoding='utf-8') as f:
    json.dump(normalized, f, indent=2, ensure_ascii=False)

print(f'backup={backup_path.resolve()}')
print(f'maps={len(normalized)}')
