import json
from pathlib import Path

repo_path = Path('maps_repo.json')
backup_path = Path('maps_repo.backup.json')

with repo_path.open('r', encoding='utf-8') as f:
    data = json.load(f)

with backup_path.open('w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

normalized = {}

if isinstance(data, dict):
    for key, value in data.items():
        if isinstance(value, dict) and 'title' in value and isinstance(value.get('concepts'), list) and isinstance(value.get('stocks'), list):
            normalized[key] = value

with repo_path.open('w', encoding='utf-8') as f:
    json.dump(normalized, f, indent=2, ensure_ascii=False)

print(f'backup={backup_path.resolve()}')
print(f'maps={len(normalized)}')
print('keys=', list(normalized.keys()))
