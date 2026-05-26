import json, pathlib
p = pathlib.Path(r'D:\map\maps_repo.json')
d = json.loads(p.read_text(encoding='utf-8'))
print('count', len(d))
for i, k in enumerate(d.keys()):
    if i >= 20:
        break
    print(k)
