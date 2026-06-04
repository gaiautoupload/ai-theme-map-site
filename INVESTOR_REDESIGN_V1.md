# 投資人版改版清單 v1

這份文件把目前 AI Theme Map 從「工程技術導向展示站」調整成「投資決策導向主題站」的第一版實作藍圖。

目標不是一次把所有數據都做滿，而是先把：

- 頁面順序
- JSON schema
- 內容語言
- 投資人關心的比較框架

全部改成正確方向。

---

## 一、改版核心方向

### 現況問題

目前站點比較像：
- 工程師技術地圖
- 題材資料庫
- LLM 生成內容展示器

但投資人要先看的是：
- 這是什麼題材
- 為什麼現在重要
- 市場有多大（TAM / CAGR）
- 誰最受惠
- 什麼時候開始變成營收
- 哪家公司拿走最多利潤
- 哪些股票只是跟風，哪些真的有護城河

### 改版後定位

改成：
- 投資人的獲利雷達預警牆
- 主題研究入口
- 題材 → 代表股 → 財務化驗證 → 風險校正 的決策介面

---

## 二、UI 順序重排（最重要）

### 目前順序（問題）
- 技術觀念解析
- 結構分層
- 資金流與火勢
- 股票清單

### 建議順序（v1）
1. 題材總覽 / 投資 Thesis
2. 概念股主篩選表
3. 資金流與火勢
4. 結構分層與價值捕捉
5. 商用時程 / 驗證節點
6. 產業投資邏輯與觀念解析
7. 比較器 / PK

### index.html 文案建議

把側欄按鈕改名：
- `技術觀念解析` → `產業投資邏輯與觀念解析`
- `結構分層` → `價值鏈分層 / 誰賺得最多`
- `商用時程 / 驗證節點` 保留，但要加上「概念期 / 放量期」語意

---

## 三、首頁卡片改版

### 首頁主題卡應新增欄位
每個主題卡至少顯示：
- 題材名稱
- 一句投資 thesis
- TAM
- CAGR
- 現在所處階段
- 優先關注股票 3 檔
- 一句「為什麼現在要看」

### 建議卡片結構
- 標題：Vera Rubin 機櫃級 AI 升級追蹤
- 副標：從 GPU 單點升級走向整櫃供電、散熱、互連的價值擴散
- TAM：2027E US$xxB
- CAGR：xx%
- 階段：驗證走向放量
- 優先關注：緯創 / 廣達 / 奇鋐
- 現在重點：觀察 GB200 / NVL72 導入與機櫃級交付節奏

---

## 四、主題頁 Hero 重構

### 最上方先回答 4 件事
1. 這是什麼題材？
2. 為什麼現在重要？
3. 市場有多大？
4. 台灣誰最代表？

### Hero 區建議新增欄位
- `market_size_tam`
- `market_cagr`
- `theme_stage`
- `why_now`
- `key_bottleneck`
- `primary_value_capture`

### Hero 區塊建議版型
- 左側：題材名稱 + thesis + why_now
- 右側：
  - TAM
  - CAGR
  - 題材階段
  - 核心瓶頸
  - 最大價值捕捉點

---

## 五、maps_repo.json schema 升級

### 主題層級新增欄位

```json
{
  "market_size_tam": "2027E 約 450 億美元",
  "market_cagr": "2025-2028 CAGR 28%",
  "theme_stage": "驗證走向放量",
  "why_now": "Blackwell / Rubin 平台升級，帶動整櫃供電、散熱與高速互連同步升級",
  "key_bottleneck": "高功耗密度下的散熱、供電與訊號完整性",
  "primary_value_capture": "高規格散熱與電源架構供應鏈",
  "market_narrative": "從單顆晶片升級，走向機櫃級基礎設施升級",
  "evidence_confidence": "medium"
}
```

### 股票層級新增欄位

```json
{
  "ai_revenue_exposure": "2026E 15-25%",
  "gross_margin_impact": "高規格產品比重提升，毛利率有上修空間",
  "customer_concentration": "NVIDIA / CSP 高度相關",
  "sole_supplier": false,
  "pricing_power": "medium",
  "value_capture_score": 4.2,
  "substitution_risk": "medium",
  "commercialization_phase": "2026 H1 驗證 / 2026 H2 放量",
  "capacity_share_hint": "具機櫃級散熱模組先行量產優勢",
  "switching_cost": "medium-high",
  "revenue_visibility": "medium"
}
```

---

## 六、哪些欄位可先用 LLM，哪些不能亂生

### 可先由 LLM + evidence 輔助生成（v1 可上）
- why_now
- market_narrative
- key_bottleneck
- primary_value_capture
- commercialization_phase
- pricing_power（文字分級）
- substitution_risk（文字分級）
- switching_cost（文字分級）
- gross_margin_impact（文字判斷）

### 不建議直接讓模型亂估，需標記為估計或後補資料
- TAM 數字
- CAGR 數字
- AI Revenue Exposure %
- Gross Margin % 具體數字
- P/E Band
- 營收貢獻佔比
- Capacity Share %
- 法人買賣超 / 即時量能

### v1 做法
先允許這些欄位以：
- `"待補"`
- `"估計中"`
- `"需外部資料驗證"`

來呈現，避免假精準。

---

## 七、Stock Modal 升級

### 目前已有
- 角色
- Pros / Cons
- Catalyst
- timeframe
- pureLevel
- barrierLevel

### 建議新增資訊格
1. 題材營收含金量
   - `ai_revenue_exposure`
2. 毛利率變化空間
   - `gross_margin_impact`
3. 客戶集中度 / 獨家性
   - `customer_concentration`
   - `sole_supplier`
4. 定價權 / 價值捕捉
   - `pricing_power`
   - `value_capture_score`
5. 替代風險
   - `substitution_risk`
6. 切入時程
   - `commercialization_phase`
7. 客戶黏著度
   - `switching_cost`

### Modal 語言要改成投資語境
把：
- `Pros` 改成 `投資亮點`
- `Cons` 改成 `風險提醒`
- `Catalyst` 改成 `股價催化 / 驗證事件`
- `Role` 改成 `受惠位置 / 供應鏈角色`

---

## 八、Structure Layers 改成 Value Capture Map

### 現況問題
現在結構分層比較像供應鏈教學。

### v1 改法
每一層除了 name / summary，新增：
- `pricing_power`
- `margin_profile`
- `value_capture`
- `entry_barrier`
- `leader_type`

### 範例
```json
{
  "name": "機櫃級散熱模組",
  "summary": "高熱通量場景下，散熱模組由選配變成系統必要條件。",
  "pricing_power": "high",
  "margin_profile": "優於標準組裝代工",
  "value_capture": "高",
  "entry_barrier": "熱設計、驗證經驗、與平台同步開發能力",
  "leader_type": "具平台導入經驗的模組廠"
}
```

### 視覺化建議
- 金色：高 value capture / 高 pricing power
- 青藍：中等
- 灰藍：低

讓投資人一眼看出誰是「吃肉」，誰只是「喝湯」。

---

## 九、Timeline 改成投資節奏線

### 要明確分成
- 概念期
- 驗證期
- 小量出貨期
- 放量期
- 財報貢獻期

### timeline_phases 每段建議新增
- `investment_phase`
- `revenue_meaning`
- `watch_metric`
- `expected_market_focus`

### 範例
```json
{
  "phase": "驗證期",
  "timeframe": "2026 H1",
  "investment_phase": "本夢比轉本益比前段",
  "revenue_meaning": "尚未大量認列，但可觀察樣品、設計導入與供應鏈位置確認",
  "watch_metric": "認證進度 / 新平台導入 / 小量出貨",
  "expected_market_focus": "市場會提前反映訂單想像與平台卡位"
}
```

---

## 十、火勢 / 資金流改成雙層設計

### 第一層：目前可做（文字層）
保留 LLM 推演：
- 為什麼資金會先流向 A 再擴散到 B
- 為什麼某些股票只是題材跟漲

### 第二層：未來要補（量化層）
新增欄位預留：
- `volume_momentum`
- `foreign_buy_sell`
- `investment_trust_flow`
- `price_breakout_status`
- `relative_strength`

### 原則
v1 先把 UI 預留好，但數據未到位前，不能假裝即時量化。

---

## 十一、比較器 / PK 功能升級

### 現況可能太偏描述
### v1 應新增比較維度
- 誰的題材純度更高
- 誰的毛利率彈性更高
- 誰更接近放量
- 誰更有定價權
- 誰客戶黏著度更高
- 誰替代風險更低

### 可新增比較欄位
- `comparison_dimensions`
- `capacity_share_hint`
- `switching_cost`
- `pricing_power`
- `substitution_risk`
- `revenue_visibility`

---

## 十二、資料標示規範（很重要）

為了避免未來被質疑「這些數字是不是 AI 掰的」，所有欄位都應標記資料性質。

### 建議每個重要欄位加上 source_type
- `official`
- `news_derived`
- `analyst_estimate`
- `llm_inference`
- `manual_review`

### 範例
```json
{
  "market_size_tam": "2027E 約 450 億美元",
  "market_size_tam_source_type": "analyst_estimate",
  "pricing_power": "high",
  "pricing_power_source_type": "llm_inference"
}
```

這個機制對你以後做商業化非常重要。

---

## 十三、v1 實作優先順序

### P1：立刻改
1. 側欄順序與名稱
2. 首頁卡加入 TAM / CAGR / 階段 / why now
3. 主題頁 Hero 加入投資語言
4. Stock modal 增加投資欄位框位
5. Structure layers 改成 value capture 語言
6. Timeline 改成投資節奏語言

### P2：這週內做
7. schema 升級
8. map_generator prompt 升級成投資人語境
9. source_type 標記制度
10. comparison 升級

### P3：第二階段做
11. 法人 / 量價 / 技術面量化火勢
12. 真實財務資料接入
13. P/E band / 毛利率 / AI exposure 百分比資料化

---

## 十四、map_generator Prompt 升級方向

在生成主題與股票時，要明確要求模型：

- 站在外資分析師 / buy-side 研究員視角
- 先講商業價值，不要先講技術教學
- 先回答 TAM / CAGR / 為什麼現在重要
- 說明誰有定價權、誰拿走最多價值
- 每檔股票要解釋：
  - 受惠位置
  - 放量時程
  - 毛利率彈性
  - 替代風險
  - 客戶黏著度

同時加一條約束：
- 若缺乏可靠證據，請輸出「待補資料」而不是編造精確數字。

---

## 十五、最終定位語句（對外）

未來首頁最上方可以從：
- 技術教學 + 結構分層 + 資金流推演

改成：
- 從全球題材，追蹤台股最可能吃到價值的代表公司
- 先看市場天花板，再看誰真正有定價權與營收放量機會

---

## 十六、v1 成功標準

如果改版成功，使用者打開任一主題頁後，應能在 10 秒內回答：
- 這是什麼題材
- 為什麼現在重要
- 市場有多大
- 哪 3 檔最值得先看
- 誰最可能真的賺到錢
- 何時可能開始反映到營收

如果還要花很多時間看技術名詞，代表改版還不夠成功。
