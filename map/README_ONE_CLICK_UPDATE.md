# AI Theme Map 一鍵更新與上傳

## 文章是誰寫的？

文章主體不是 nanobot 手寫固定稿，而是由 `map_generator.py` 呼叫 vLLM 模型生成：

- Endpoint：`https://vllm-a5000.iii-ei-stack.com/v1/chat/completions`
- Model：`cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit`
- 搜尋模式：`search_augmented`
- 搜尋後端：`whitelist_rss`

nanobot / 我主要負責：

1. 設計 prompt、schema、流程。
2. 串接白名單新聞/RSS與證據檔。
3. 驗證股票代號與資料欄位。
4. 補上保底內容，例如資金流、火勢推演、產業分層。
5. 合併舊卡、發布、push 到 GitHub Pages。

## 一鍵更新方式

雙擊：

```bat
D:\map\一鍵更新並上傳_保留舊卡.bat
```

流程：

1. 建立/更新台股 ticker registry。
2. 從白名單 RSS 搜尋最新主題。
3. 建立 evidence 檔。
4. 由 vLLM 生成新主題文章。
5. 合併舊卡，避免覆蓋歷史內容。
6. 補齊 `capital_flow` 與 `structure_layers`。
7. 發布到 `D:\ai-theme-map-site`，commit 並 push 到 GitHub Pages。
8. 驗證網站 HTTP 200。

## 常用設定

在 bat 內可調整：

```bat
set MAP_DISCOVERY_RUN_TOP=5
```

代表每次生成前 5 個新主題。

## 注意

- 不會清掉舊卡，舊卡會從 `D:\ai-theme-map-site\maps_repo.json` 合併回來。
- 新卡會在最上方。
- 若 GitHub Pages 有快取，網站可能延遲 1–3 分鐘更新。
