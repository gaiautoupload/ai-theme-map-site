# ai-theme-map-site / 網站發布端鏡像

這個資料夾保存 GitHub Pages 網站發布端的鏡像與發布腳本。

> GitHub Pages 實際讀取的是 repo 根目錄的 `index.html` 與 `maps_repo*.json`。這個資料夾主要用來保存網站發布端專案結構，方便維護與備份。

---

## 主要檔案

- `index.html`：投資者導向題材地圖前端。
- `maps_repo.json`：最新題材資料。
- `maps_repo_YYYYMMDD_HHMMSS.json`：版本化資料檔，用來避免 stale cache。
- `publish_site.py`：發布腳本，將 `D:\map` 的輸出複製到網站 repo，並 commit / push。
- `publish_config.json.example`：發布設定範例。

---

## 網站設計定位

這個站不是技術資料庫，而是投資者決策支援網站。每個主題應優先回答：

1. 這個題材是什麼？
2. 它為什麼現在重要？
3. 題材如何演變？
4. 哪些股票位於受惠位置？
5. 資金可能先買誰、再擴散到誰？
6. 火勢升溫與降溫訊號是什麼？

---

## 發布注意事項

- 根目錄要保留 `index.html`，不能只放在子資料夾，否則 GitHub Pages 會 404。
- 每次發布會產生版本化 `maps_repo_*.json`。
- 前端應指向最新版本化 JSON，避免讀到舊資料。
- 若線上顯示舊內容，先檢查：
  - root `index.html` 是否更新。
  - 最新 `maps_repo_*.json` 是否存在。
  - GitHub Pages 快取是否尚未更新。

---

## 本機測試

```bat
cd /d D:\ai-theme-map-site
python -m http.server 8000
```

然後開：

```txt
http://localhost:8000/index.html
```
