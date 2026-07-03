# Harness 快速診斷 — Token 洩漏、失焦、易錯前三名

> 正式報告 ｜ 2026-07-03 ｜ Task Card `20260703-001` ｜ 產出者：Fable 5 session（一次性）
> 本報告是同日建立的制度檔（DELEGATION_PLAYBOOK / JUDGMENT_RUBRICS / DELEGATION_TEMPLATES / MAINTENANCE_PROTOCOL / LETTER_TO_FUTURE_SESSIONS）的共同依據。
> 依使用者指令直接寫入 reports/（指令即 ask 授權）。

## 摘要

| 排名 | 問題 | 一句話 | 修法落點 |
|:---:|------|--------|---------|
| 1 | Token 洩漏 | 每任務全量載入 4+ 個治理檔，且同一規則存在 2–3 份副本 | CLAUDE.md 改為「載入地圖」＋單一事實源 |
| 2 | 失焦 | 主對話親自做大量讀取/搜尋，中間產物灌爆 context，壓縮後丟失任務目標 | 指揮官不下場（DELEGATION_PLAYBOOK） |
| 3 | 易出錯 | 四層 gate 由產出者本人執行＝自產自驗，且量測數據空到不能支撐判斷 | 驗證不自驗（fresh-context 驗收）＋數據誠實化 |

三個問題互相放大：載入越肥 → context 越早滿 → 壓縮越早發生 → 目標越容易丟 → 錯誤越多 → 重試又燒更多 token。所以修法順序是 1 → 2 → 3，前面的修好會直接緩解後面的。

---

## 第 1 名：Token 洩漏 — 全量載入 + 規則三副本

### 證據

1. **舊 CLAUDE.md 執行流程 step 3** 要求每個任務載入：GLOBAL_RULES.md + AGENT_CONTEXT.yaml + APPROVAL_POLICY.yaml + GATE_POLICY.yaml + 對應 skill + project context。system/ 全目錄約 36KB；即使只載一半，每個任務固定墊高數千 token，其中大部分與當下任務無關（例如做 research 時載入 APPROVAL_POLICY 的批准紀錄 schema）。
2. **同一規則存在多份副本，且已經開始漂移**：
   - 權限：CLAUDE.md 摘要版 / PERMISSIONS.yaml 完整版 / AGENT_CONTEXT.yaml 的 boundaries 段，三處。
   - 成本規則：CLAUDE.md「Context 硬限制」/ GLOBAL_RULES.md「成本意識」/ COST_POLICY.md，三處。
   - 失敗處理：CLAUDE.md「驗證失敗處理」/ GATE_POLICY.yaml 的 on_fail，兩處。
3. **NATIVE_OVERLAP.yaml 自承**與 Claude Code 原生功能整體重疊 30%（Skill 路由 70%、「20 輪摘要壓縮」原生已具）。重疊的規則每載一次就是純浪費。

### 為什麼嚴重

副本不只浪費 token——**副本會漂移**。弱模型看到兩份不一致的規則時，會隨機選一份執行或兩份都執行，行為變得不可預測。這比浪費更貴。

### 修法（本次已執行）

1. CLAUDE.md 重寫為「載入地圖」：列出每種情境該載入哪一個檔，預設不載入任何治理細節檔。→ 見新版 `CLAUDE.md`。
2. 單一事實源原則：每條規則只有一個權威出處，其他地方只放一行指標。已把 CLAUDE.md 上的權限摘要、成本細節、驗證失敗處理細節刪除，改為指向 PERMISSIONS.yaml / COST_POLICY.md / GATE_POLICY.yaml。
3. 剩餘副本（GLOBAL_RULES 與 AGENT_CONTEXT / COST_POLICY 的重疊段）列入 `system/MAINTENANCE_PROTOCOL.md` 的收斂 backlog，逐次任務順手收，不一次大改。

---

## 第 2 名：失焦 — 主對話下場幹粗活，context 被中間產物灌爆

### 證據

1. 本 harness 設計為「單一核心 agent」（memory context 明文），**完全沒有派工概念**。research/review 類任務的原始搜尋結果、整頁檔案內容、web search 原文全部進主對話 context。
2. 自家 FAILURE_TAXONOMY 已經記錄了後果卻沒記錄根因：SPEC-03（對話歷史遺失）、COORD-01（context 被重置）、COORD-03（目標偏離）合計是 taxonomy 裡最大的一群。根因就是 context 被非結論性內容佔滿，觸發壓縮，Task Card 的 goal 和中途決策被摘要掉。
3. COST_POLICY 自己引用的數據也證實：「子代理 context 隔離 省 ~67%」——寫在檔案裡，但流程從未使用。

### 為什麼嚴重

弱模型比強模型更容易被長 context 帶偏：注意力被最近讀到的原始資料吸走，忘記最初的驗收條件。強模型靠能力扛住，弱模型必須靠結構。

### 修法（本次已執行）

1. 建立 `system/DELEGATION_PLAYBOOK.md`：指揮官不下場——大量讀取、掃 repo、web search、批次改檔一律派 subagent，主對話只進結論。含量化門檻（什麼算「大量」）。
2. 回報合約：subagent 只回結論 + 檔案:行號，長產物落檔傳路徑，禁止把原文倒回主對話。
3. 派工三件套 + 五份填空模板（`system/DELEGATION_TEMPLATES.md`），讓弱模型不需要自己想怎麼派工。

---

## 第 3 名：易出錯 — 自產自驗 + 數據空洞

### 證據

1. **GATE_POLICY 四層驗證全部由產出者本人執行**。FAILURE_TAXONOMY 的 VAL-01（假完成）、VAL-02（驗證不完整）、VAL-03（格式對就當內容對）有分類、有 mitigation 文字，但 mitigation 全是「自己再檢查一次」——同一個 context 產生的錯誤，同一個 context 通常看不見。
2. **量測數據空到不能支撐判斷**：`logs/runs/20260409-001` 的 token_estimate 三欄全 0；COST_POLICY 校準係數表的樣本數是 2/1/2/2/0 筆，卻被當成「實測資產」引用（writing 係數 2.00 來自單一樣本）。用 n=1 的數據調參數，比沒有數據更危險。
3. 自我評估報告（harness-self-assessment-v1）已把「失敗→恢復閉環從未實證」列為第一缺點，方向正確，但解法（R5 故障演練）仍然是自己演練自己驗。

### 為什麼嚴重

假完成是弱模型最常見、也最貴的失敗：使用者以為做完了，下游決策建立在沒驗過的產出上。驗證必須來自沒有沉沒成本、沒有「我剛寫完它」偏誤的 context。

### 修法（本次已執行）

1. `system/DELEGATION_PLAYBOOK.md`「驗證不自驗」節：驗收一律派 fresh-context agent；檔案產出用 read-back、程式碼用測試或實跑、高風險判斷加第二意見或多答案評審選優。
2. `system/JUDGMENT_RUBRICS.md`「何時算真的完成」：把完成的判準寫成可勾稽的 checklist（含正反例），取代「感覺做完了」。
3. 數據誠實化：校準係數表在樣本 <5 筆前只能標「參考值，不得作為調參依據」——已列入 MAINTENANCE_PROTOCOL 的規則。

---

## 誠實條款：這三項修法補不了的東西

- 拆解、驗證、多樣本評審能把**執行品質**拉近強模型水準。
- **模糊題**（需求本身不成熟）與**品味判斷**（好報告 vs 及格報告的差距）補不了。遇到時的處置寫在 `system/JUDGMENT_RUBRICS.md` 誠實條款節：升級模型、外部第二意見、或明說做不到——不要假裝 rubric 能解決。

## 本報告的使用方式

未來 session 不需要重讀本報告；它的結論已經物化進 CLAUDE.md 與四個制度檔。本報告的用途是：(1) 使用者審閱依據；(2) 未來懷疑「這條規則為什麼存在」時的溯源文件。
