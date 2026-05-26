import urllib.request
for url in [
    'https://gaiautoupload.github.io/ai-theme-map-site/',
    'https://gaiautoupload.github.io/ai-theme-map-site/maps_repo.json',
]:
    print('URL:', url)
    data = urllib.request.urlopen(url).read(400).decode('utf-8', 'ignore')
    print(data[:400])
    print('---')
