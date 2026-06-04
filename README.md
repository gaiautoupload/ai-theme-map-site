# AI Theme Map Site / 產業題材地圖專案

這個 repo 同時保存兩個層次：

1. **GitHub Pages 網站發布檔**：根目錄的 `index.html`、`maps_repo.json`、`maps_repo_*.json`。
2. **生成端原始專案**：`map/`。
3. **網站發布端專案鏡像**：`ai-theme-map-site/`。

網站網址：

https://gaiautoupload.github.io/ai-theme-map-site/

---

## 目錄結構

```txt
/
├─ index.html                       # GitHub Pages 直接載入的首頁
├─ maps_repo.json                   # 最新題材資料
├─ maps_repo_YYYYMMDD_HHMMSS.json   # 版本化資料，避免快取與舊站不一致
├─ map/                             # 生成端：搜尋、vLLM 生成、補欄位、一鍵更新
└─ ai-theme-map-site/               # 發布端鏡像：網站與 publish 腳本備份
```

> 注意：根目錄仍保留 `index.html` 與 `maps_repo*.json`，是為了讓 GitHub Pages 不被破壞。真正開發與更新流程請看 `map/`。

---

## 文章是誰寫的？

文章主體由 vLLM 模型生成，不是人工手寫固定稿。

目前預設：

```txt
模型：cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit
API：https://vllm-a5000.iii-ei-stack.com/v1/chat/completions
搜尋：whitelist_rss 白名單 RSS / trusted sources
```

AI assistant / nanobot 負責：

- 設計 prompt 與 JSON schema。
- 搜尋與 evidence pipeline。
- 台股 ticker registry 驗證。
- 補齊資金流向、火勢推演、產業結構分層。
- 合併舊卡，避免舊主題被覆蓋。
- 發布與 push 到 GitHub Pages。

---

## 一鍵更新與上傳

在 Windows 雙擊：

```bat
D:\map\一鍵更新並上傳_保留舊卡.bat
```

或在 repo 內執行鏡像版：

```bat
map\一鍵更新並上傳_保留舊卡.bat
```

流程會自動完成：

1. 更新台股 ticker registry。
2. 從白名單來源探索最新主題。
3. 建 evidence 檔。
4. 呼叫 vLLM 生成新主題文章。
5. 合併舊卡，新卡排最上方。
6. 補齊 `capital_flow` 與 `structure_layers`。
7. 發布到網站 repo。
8. commit / push 到 GitHub Pages。
9. 驗證網站 HTTP 狀態。

---

## 重要原則

- 不用虛構財務數字；不可靠數值使用 `待補`、`估計中`、`需外部資料驗證`。
- 股票必須通過 official ticker registry 與 evidence 交叉檢查。
- 舊資料不要覆蓋掉，新資料應保留版本化 JSON。
- 投資者閱讀優先：先講題材是什麼、如何演變、誰受惠、資金可能怎麼流。

---

## 子專案 README

- 生成端：[`map/README.md`](map/README.md)
- 一鍵更新說明：[`map/README_ONE_CLICK_UPDATE.md`](map/README_ONE_CLICK_UPDATE.md)
- 發布端：[`ai-theme-map-site/README.md`](ai-theme-map-site/README.md)
