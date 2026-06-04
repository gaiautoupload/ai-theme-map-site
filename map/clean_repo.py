import json

# Load the backup repo
with open('D:/map/maps_repo.backup.json', encoding='utf-8') as f:
    repo = json.load(f)

# Remove the junk top-level keys that aren't map IDs
valid_keys = [k for k in repo.keys() if k not in ('map_unique_id', 'title', 'date', 'heat', 'period', 'desc', 'icon', 'color', 'concepts', 'stocks')]

cleaned = {k: repo[k] for k in valid_keys}

with open('D:/map/maps_repo.json', 'w', encoding='utf-8') as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f'Cleaned repo: {len(cleaned)} themes')
print('Keys:', list(cleaned.keys()))
