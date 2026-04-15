# Intake 流程（Task Card 前的需求釐清）

## 為什麼需要這個

硬規則：沒有 Task Card 不執行任務。
現實：建立一張好的 Task Card 本身就需要理解需求。
解法：定義一個受限的 intake 模式，在 Task Card 之前合法運作。

## Intake 模式的權限

只允許：
- 向使用者提問釐清需求
- 讀取 project 內部檔案（了解 context）
- 讀取 memory/（了解偏好與歷史）
- 查看既有 Task Card（避免重複）

不允許：
- web search
- 產出任何檔案
- 工具呼叫
- 修改任何內容

## 流程

```
使用者提出需求
    ↓
【快速路徑判斷】同時滿足以下三條 → 直接進執行，跳過 Intake：
  ✓ goal 已一句話說清楚
  ✓ skill_type 可直接判斷（見 ROUTING_RULES.md）
  ✓ risk_level 明顯為 low 或 medium

      ↓ 不符合任一條件

[Intake 模式啟動]
    ↓
1. 判斷需求是否清晰（goal 可一句話描述？完成標準可列出？）
   - 清晰 → 直接草擬 Task Card
   - 不清晰 → 提問釐清（最多 3 輪）
    ↓
2. 判斷是否需要拆分（一個 skill 能完成？）
   - 單一 skill → 一張 Task Card
   - 多 skill → 多張 Task Card + 依賴關係
    ↓
3. 草擬 Task Card（填入 goal, definition_of_done, skill_type, risk_level）
    ↓
4. 呈現給使用者確認
    ↓
[使用者確認後，進入正式執行流程]
```

> **快速路徑說明**：根據首次 RETRO（2026-04-15）觀察，8/8 筆任務均符合快速路徑條件，
> Intake 問答從未被真正觸發。快速路徑讓明確需求可直接進入執行，
> 同時保留 Intake 模式處理模糊需求。

## 釐清問題的參考清單

- 你要的產出是什麼格式？（報告 / 資料表 / 分析 / 行動計畫）
- 完成的標準是什麼？（幾項 / 多深 / 什麼程度算夠）
- 有沒有已有的內部資料可以參考？
- 時間或成本有沒有限制？
- 這個產出會用在哪裡？（決定 risk level）

## 限制

- Intake 模式最多 3 輪對話，超過代表需求本身不成熟，建議使用者先自行釐清
- Intake 不計入任務的工具呼叫額度
- Intake 過程不產出 checkpoint（因為還沒進入任務）
