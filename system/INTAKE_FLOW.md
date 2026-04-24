# Intake 流程（Task Card 前的需求釐清）

## 為什麼需要這個

硬規則：沒有 Task Card 不執行任務。
現實：當需求已明確時，硬塞釐清問答反而成為阻力；當需求模糊時，一定需要釐清再建卡。
解法：**快速路徑為預設主路**，intake 模式作為需求不明時的 fallback。

---

## 預設主路：Fast-path（直接建 Task Card）

當使用者的需求同時滿足以下三條，直接進入「草擬 Task Card → 使用者確認 → 執行」：

1. `goal` 可以一句話說清楚
2. `skill_type` 可直接判斷（見 `system/ROUTING_RULES.md`）
3. `risk_level` 明顯為 low 或 medium

```
使用者提出需求
    ↓
[Fast-path 檢查] 三條都符合？
    ↓ 是
草擬 Task Card（填 goal / definition_of_done / skill_type / risk_level）
    ↓
呈現給使用者確認
    ↓
[確認後進入執行流程]
```

> **實證依據**：首次 RETRO（2026-04-15）8/8 筆任務皆符合 fast-path 條件，intake 問答從未被觸發。
> 故 2026-04-24 起將 fast-path 提升為預設主路。

---

## Fallback：Intake 模式（需求不明時啟動）

當 fast-path 三條件**任一不符**，啟動 Intake 模式。

### Intake 模式的權限

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

### Intake 流程

```
[Fast-path 檢查失敗] → Intake 模式啟動
    ↓
1. 判斷需求是否清晰（goal 可一句話描述？完成標準可列出？）
   - 清晰 → 直接草擬 Task Card
   - 不清晰 → 提問釐清（最多 3 輪）
    ↓
2. 判斷是否需要拆分（一個 skill 能完成？）
   - 單一 skill → 一張 Task Card
   - 多 skill → 多張 Task Card + 依賴關係
    ↓
3. 草擬 Task Card（填 goal / definition_of_done / skill_type / risk_level）
    ↓
4. 呈現給使用者確認
    ↓
[確認後進入執行流程]
```

### 釐清問題的參考清單

- 你要的產出是什麼格式？（報告 / 資料表 / 分析 / 行動計畫）
- 完成的標準是什麼？（幾項 / 多深 / 什麼程度算夠）
- 有沒有已有的內部資料可以參考？
- 時間或成本有沒有限制？
- 這個產出會用在哪裡？（決定 risk level）

---

## 限制

- Intake 模式最多 3 輪對話，超過代表需求本身不成熟，建議使用者先自行釐清
- Intake 不計入任務的工具呼叫額度
- Intake 過程不產出 checkpoint（因為還沒進入任務）
- Fast-path 若中途發現需求實為模糊 → 退回 Intake 模式
