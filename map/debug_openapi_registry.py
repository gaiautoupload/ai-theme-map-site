import requests

print('TWSE')
data = requests.get('https://openapi.twse.com.tw/v1/opendata/t187ap03_L', timeout=30).json()
print(type(data).__name__, len(data))
print(list(data[0].keys())[:12])
print(data[0])

print('TPEX')
data2 = requests.get('https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes', timeout=30).json()
print(type(data2).__name__, len(data2))
print(list(data2[0].keys())[:12])
print(data2[0])
