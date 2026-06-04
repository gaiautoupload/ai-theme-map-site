from search_provider import search
import json

results = search('矽光子 台股 供應鏈 股票 代號')
print(json.dumps(results[:3], ensure_ascii=False, indent=2))
