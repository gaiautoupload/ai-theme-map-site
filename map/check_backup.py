import json
data = json.load(open('D:/map/maps_repo.backup.json', encoding='utf-8'))
print('Keys:', list(data.keys()))
print('Count:', len(data))
