# P1 規則減量提案（20261031-P02 階段一）

> 狀態：草稿，等待人工核准。核准前不修改 `system/`。

## 結論

- **每次執行都要載入的規則可以砍掉約 6 成**：從約 10.8KB 降到約 4.4KB。這是真正影響成本和行為的數字。
- **`system/` 總量只能降約 26%**：從 65.2KB 降到約 48KB，達不到原本「減半」的目標。原因是約 28KB 屬於程式或 CI 會讀取的格式定義（GATE_POLICY、PERMISSIONS、EXECUTION_LOG_SCHEMA 等），硬砍會破壞 hook 和 CI。
- **建議接受「執行期大減、總量中減」的結果**，不要為了湊到一半去動這些格式定義。

## 實證依據（已驗證）

| 證據 | 數據 | 代表什麼 |
|---|---|---|
| 真實錯誤紀錄 | `logs/errors/` 只有 2 筆：1 筆事後重建的範例、1 筆刻意演練，實際運作中的錯誤為 0 | 失敗分類學裡的 17 種失敗模式，沒有一種在實際運作中被觀察到過 |
| 「累計超過 5 次工具呼叫就先 checkpoint」 | 有記錄實際呼叫數的 81 張卡中，60 張（74%）超過 5 次（最高 61 次）；卡片自己設的 `max_tool_calls` 常落在 15–40 | 這條規則實務上沒人照做，等於已經失效 |
| 「單一任務最多 3 輪外部查詢」 | 100 張卡中有 81 張把 `max_web_searches` 設為 0 | 上限幾乎沒有生效過，實際上由每張卡自己決定 |
| COST_POLICY 的校準表 | 最後一次校正在 2026-04-17，每類只有 1–2 筆樣本；說好「再累積 5 筆就重算」，之後完成 70 多張卡也沒有重算 | 每週量測流程沒有實際執行 |
| COST_POLICY「升級到 v2 的觸發條件」 | 系統早已是 v2 | 這段已經過時 |
| 執行期載入集 | CLAUDE.md 第 3 步要求載入 GLOBAL_RULES、AGENT_CONTEXT、APPROVAL_POLICY；CONTEXT_ENGINEERING 另外要求加載 GATE_POLICY 和 INPUT_GUARDRAILS | 每個任務都先付約 11–18KB 的規則成本 |

## 逐檔處置

圖例：**保留**＝不動；**瘦身**＝刪掉非格式定義的段落；**合併**＝內容併入別檔後刪除本檔；**刪除**＝整檔移除；**移出載入集**＝檔案保留，但不再每次任務都載入，需要時才查。

| 檔案 | 現況 | 處置 | 依據 | 程式依賴 | 處理後 |
|---|---:|---|---|---|---:|
| AGENT_CONTEXT.yaml | 1.4K | **刪除** | 拒絕與升級條件已經寫在 CLAUDE.md 的三條硬規則和 PERMISSIONS；檔案自己也寫明「不再重複列舉」 | 無 | 0 |
| APPROVAL_POLICY.yaml | 4.1K | **瘦身＋移出載入集** | 觸發條件那段和 PERMISSIONS 的 ask 清單、settings.json 的 ask 規則三處重複。保留核准紀錄格式（`approval_record`，CI 會檢查）和 2 條升級規則 | check_spec_consistency.rb 讀紀錄格式 | 1.6K |
| GLOBAL_RULES.md | 2.4K | **瘦身** | 刪除「最多 3 輪外部查詢」「超過 5 次工具呼叫先 checkpoint」兩條（已失效，改由各卡的 `max_*` 欄位決定）；成本意識段和 COST_POLICY 重複，壓到 2 行 | check_context_budget.rb 計算它的大小（不受影響） | 1.5K |
| ROUTING_RULES.md | 1.8K | **合併到 INTAKE_FLOW** | 路由表和原生 skill 自動觸發重複（檔案開頭自己也寫「降級為後援」）。保留 3 條：一卡一 skill、跨 skill 就拆卡、判斷不了就問 | 無 | 0 |
| INTAKE_FLOW.md | 2.7K | **保留，吸收上面 3 條** | 「先釐清需求再建卡」的流程仍有用 | 無 | 3.0K |
| RETRO_FLOW.md | 2.6K | **合併到 skills/retro/SKILL.md** | 和 retro skill 內容高度重疊，兩份會各自走樣 | 無（README、skill 有引用，需同步改） | 0（skill 約增加 0.8K） |
| COST_POLICY.md | 6.0K | **瘦身** | 刪除行為規則段（和 GLOBAL_RULES 重複）、每週量測流程（沒有執行）、升級到 v2 的觸發條件（已過時）。保留模型路由表和校準表（標成歷史數據） | 無 | 2.5K |
| CONTEXT_ENGINEERING.md | 4.5K | **瘦身** | 組裝順序段和 CLAUDE.md 重複，而且它要求的載入集比 CLAUDE.md 更大，兩邊互相矛盾。保留 scratchpad 和子任務 context 隔離兩段 | 無 | 2.0K |
| RECOVERY_RUNBOOK.md | 6.4K | **瘦身** | 2 份演練紀錄附錄移到 `logs/`，本檔只留操作程序 | session_start_context.py 只引用檔名 | 4.9K |
| FAILURE_TAXONOMY.yaml | 4.2K | **保留，小修** | 保留 ID（錯誤紀錄和 skill 有引用）。刪掉「~42% / ~37% / ~21%」這組比例：它們不是本系統的實測數據，來源待查，留著會誤導 | session_start_context.py | 4.0K |
| CLAUDE.md（不在 system/） | 2.9K | **小修** | 第 3 步載入集改為「GLOBAL_RULES＋對應 skill＋project context」；其他規則檔改成需要時才查 | check_context_budget.rb | 2.8K |
| PERMISSIONS / GATE_POLICY / VERIFICATION_LOOP / EXECUTION_LOG_SCHEMA / INPUT_GUARDRAILS / validate_task_card.py | 約 26.8K | **保留** | hook、gate_check、verification_loop 或 e2e 測試直接讀取 | 有 | 不變 |
| NATIVE_OVERLAP.yaml | 2.5K | **保留，另案重評** | 已超過 90 天沒更新，但重評屬於另一項工作 | governance_metrics 等程式 | 不變 |

**執行期載入集**：從 CLAUDE.md＋GLOBAL_RULES＋AGENT_CONTEXT＋APPROVAL_POLICY（約 10.8KB）降到 CLAUDE.md＋GLOBAL_RULES（約 4.4KB），**少約 59%**。

**`system/` 總量**：從 65.2KB 降到約 48KB，**少約 26%**。

## 不在這次刪減範圍

- 三條硬規則（Task Card 先行、對外動作只出草稿、連續失敗 3 次熔斷）
- deny 清單和所有 hook
- `memory/` 內的歷史決策紀錄：裡面有引用到要刪的檔名，但那是歷史紀錄，不回頭改，避免動到長期記憶

## 風險與緩解

| 風險 | 等級 | 緩解 |
|---|---|---|
| 刪掉 checkpoint 和查詢次數規則後，長任務沒有中途存檔 | 低 | 每張卡的 `max_tool_calls` 和 hook 的失敗熔斷仍在；CLAUDE.md 的「每個關鍵階段 commit」保留 |
| 刪檔後留下引用斷鏈 | 中 | 落地時用 grep 掃全 repo 引用（`memory/` 除外），並跑 spec consistency 檢查 |
| 少載入 APPROVAL_POLICY 後，漏掉某條核准規則 | 低 | 核准觸發條件的實際執行點在 settings.json 的 ask 規則和 PERMISSIONS，不在這份檔案 |
| 規則合併時誤刪仍有用的細節 | 中 | 階段二每個檔案各自 commit，可逐檔回滾 |

## 待驗證

- 精簡規則後，模型在長任務上是否一樣穩定：沒有量化資料。建議落地後拿 3–5 張真實任務卡觀察，看 `logs/errors/` 有沒有新增案例。
- FAILURE_TAXONOMY 那組百分比的原始出處。

## 一人公司適用性評估

- **適合做**：維護面積變小，每個任務的 context 成本下降，規則之間互相矛盾的地方減少。
- **條件**：一次合併成一個 PR、逐檔 commit；落地後跑過全套測試和檢查才結案。
- **優先度**：高於 P1-4（evals）和 P2 那幾張卡，因為那些卡會在現有規則上繼續疊規則。

## 請核准

請逐組核准，或指出要排除的項目：

- A. 刪除 AGENT_CONTEXT、合併 ROUTING_RULES 到 INTAKE_FLOW、合併 RETRO_FLOW 到 retro skill
- B. 瘦身 GLOBAL_RULES（含刪除 5 次與 3 輪兩條限制）和 CLAUDE.md 的載入集
- C. 瘦身 APPROVAL_POLICY、COST_POLICY、CONTEXT_ENGINEERING
- D. 搬移 RECOVERY_RUNBOOK 的演練附錄，刪除 FAILURE_TAXONOMY 的比例數字
