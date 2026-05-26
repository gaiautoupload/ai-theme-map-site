import urllib.request, json
with urllib.request.urlopen('https://gaiautoupload.github.io/ai-theme-map-site/maps_repo.json') as r:
    data = json.load(r)
print('count=', len(data))
print('keys=', list(data.keys())[:8])
