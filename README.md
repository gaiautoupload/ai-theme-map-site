# AI Theme Map Site

這是一包式正式專案：同一個 repo 同時包含 GitHub Pages 前端、主資料 `maps_repo.json`，以及每日主題地圖產線。

正式入口：`index.html`。

更新流程：
- `python run_daily_pipeline.py`：探索題材、建立 evidence、重建 `maps_repo.json`、發布。
- `python publish_site.py`：不重跑生成，只重新發布目前 `maps_repo.json`。

資料原則：事實優先、白名單來源、股票需通過官方代號 registry 與 evidence 檢查。
