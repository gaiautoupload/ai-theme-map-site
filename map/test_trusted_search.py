from search_provider import ddg_html_search, search
import json

query = 'AI 資料中心 電網 強韌化 台股 受惠股'
print('BASE')
print(json.dumps(ddg_html_search(query, 5), ensure_ascii=False, indent=2))
print('FINAL')
print(json.dumps(search(query)[:5], ensure_ascii=False, indent=2))
