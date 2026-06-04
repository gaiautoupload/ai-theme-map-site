# map / 題材地圖生成端

這個資料夾是 AI Theme Map 的生成端，負責從可信來源搜尋事件、建立 evidence、呼叫 vLLM 生成題材文章，最後輸出 `maps_repo.json`。

---

## 核心流程

```txt
白名單 RSS / trusted sources
        ↓
theme_discovery.py
        ↓
evidence_builder.py
        ↓
rebuild_maps_repo_from_discovery.py / map_generator.py
        ↓
merge_existing_cards.py
        ↓
enrich_map_layers_and_flow.py
        ↓
publish_site.py
```

---

## 主要檔案

- `theme_discovery.py`：從白名單來源探索最新題材。
- `evidence_builder.py`：為每個題材建立 evidence context。
- `map_generator.py`：呼叫 vLLM 生成投資者導向題材文章。
- `rebuild_maps_repo_from_discovery.py`：根據 discovery 結果重建新主題資料。
- `merge_existing_cards.py`：把舊卡合併回來，避免只剩新卡。
- `enrich_map_layers_and_flow.py`：補齊資金流向、火勢推演、產業結構分層與受惠位置。
- `publish_site.py`：把資料發布到 `D:\ai-theme-map-site` 並推上 GitHub Pages。
- `一鍵更新並上傳_保留舊卡.bat`：Windows 雙擊一鍵更新。

---

## vLLM 設定

預設在 bat 內：

```bat
set MAP_VLLM_URL=https://vllm-a5000.iii-ei-stack.com/v1/chat/completions
set MAP_MODEL_NAME=cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit
set MAP_SEARCH_MODE=search_augmented
set MAP_SEARCH_BACKEND=whitelist_rss
set MAP_DISCOVERY_RUN_TOP=5
```

若要一次生成較少主題，可改：

```bat
set MAP_DISCOVERY_RUN_TOP=3
```

---

## 一鍵更新

在 Windows 雙擊：

```bat
D:\map\一鍵更新並上傳_保留舊卡.bat
```

或從這個 repo 的鏡像資料夾執行：

```bat
map\一鍵更新並上傳_保留舊卡.bat
```

---

## 資料品質要求

每個主題至少應包含：

- `summary` / `plain_explanation`
- `stocks`
- `capital_flow`
  - 第一波：國際敘事與核心瓶頸先點火
  - 第二波：資金擴散到台股核心供應鏈
  - 第三波：小中型與次供應鏈補漲
- `structure_layers`
  - 上游：規格與關鍵瓶頸
  - 中游：核心零組件 / 模組
  - 下游：系統整合與終端導入
  - 延伸：材料、設備與小中型補漲

若缺少上述欄位，一鍵流程會用 `enrich_map_layers_and_flow.py` 補齊保底內容。
