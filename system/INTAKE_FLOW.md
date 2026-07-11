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
[In-flight 查重] python3 scripts/check_inflight.py <goal 關鍵字>
    命中 → 停止開卡，呈報使用者裁決：續作既有卡 / 接手 in-flight 分支 / 確認新題
    ↓ 無命中（或裁決為新題）
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

## 開卡前 In-flight 查重（fast-path 與 intake 兩路都適用）

**為什麼**：2026-07-06 架構診斷實證——eval harness 同題五做（#113–#118）、R9/R10 兩做、
R11–R14 編號撞車。跨 session 看不見 in-flight 的工作，是「無整合平面」缺點的入口端。

**怎麼查**：`python3 scripts/check_inflight.py <關鍵字...>`（建議中英文各 1–2 個）掃三個來源：

1. `tasks/*.yaml` 的 goal 欄位 + 檔名 slug（既有卡）
2. `git ls-remote --heads origin` 分支名（in-flight 分支）
3. open PR 標題（`--pr-json` 提供時；與 `governance_metrics.py --pr-json` 同一份 JSON）

**能力邊界**：關鍵字比對抓不到語意重複（「eval harness」vs「評測框架」），故定位為
advisory——命中時停止開卡、呈報使用者裁決，不做硬擋。工具不可用時退化為人工
grep `tasks/*.yaml` 的 goal，並在卡片 `context` 註明查重方式。

---

## Fallback：Intake 模式（需求不明時啟動）

當 fast-path 三條件**任一不符**，啟動 Intake 模式。

### Intake 模式的權限

只允許：
- 向使用者提問釐清需求
- 讀取 project 內部檔案（了解 context）
- 讀取 memory/（了解偏好與歷史）
- 查看既有 Task Card 與 in-flight 分支/open PR（執行 `scripts/check_inflight.py`，避免重複；
  查重腳本為唯讀，不算「工具呼叫」限制的違例）

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
