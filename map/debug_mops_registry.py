import requests

url = 'https://mops.twse.com.tw/mops/web/ajax_t51sb01'
resp = requests.post(url, data={'encodeURIComponent':1,'step':1,'firstin':1,'TYPEK':'sii','code':''}, timeout=30)
print(resp.status_code)
print(resp.text[:2000])
