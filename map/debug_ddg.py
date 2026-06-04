import requests
url = 'https://html.duckduckgo.com/html/?q=%E7%9F%BD%E5%85%89%E5%AD%90%20%E5%8F%B0%E8%82%A1'
resp = requests.get(url, timeout=30)
print(resp.status_code)
print(resp.text[:1000])
