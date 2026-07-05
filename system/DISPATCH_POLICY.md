# DISPATCH_POLICY — 模型調度守則

> 讀者：未來每個 session 的主對話（指揮官，預設 `opus`）。型號事實一律引用
> `system/MODEL_ROSTER.md`；填空模板在 `system/DELEGATION_TEMPLATES.md`；
> 「該不該升級／換路」的判準在 `system/JUDGMENT_RUBRICS.md`。
> 計費前提：訂閱制——派 subagent 的邊際成本近似固定，**用隔離 context 換穩定性是划算的**。
>
> 名詞澄清：本檔的「派工」指 Claude Code 原生 Agent tool 的 subagent（一問一答、
> 用完即棄、結果回主對話）。這**不是** README「不做清單」裡禁止的 multi-agent swarm
> ／agent-to-agent 對話路由——那指的是多個常駐 agent 互相對話協商，仍然禁止。
> 同理，PERMISSIONS deny 的 `spawn_background_process` 指 shell 層背景程序
> （`&`、nohup、daemon），**不包含** Agent tool 的 subagent 執行——派 subagent
> 是本檔明文允許的。

---

## §1 指揮官不下場

主對話的 context 是全任務最稀缺的資源：它裝著 Task Card、使用者意圖、與所有決策脈絡。
每塞進一頁原始材料，目標就被稀釋一分。所以：**指揮官只做判斷與整合，材料處理下放。**

觸發表（滿足任一條 → 必須派 subagent，不要自己動手）：

| 情境 | 觸發門檻 | 派給 |
|------|---------|------|
| 讀檔案回答問題 | 預估要讀 **>3 個檔**或 **>300 行** | `Explore`（唯讀，回結論） |
| 掃 repo / 找定義 / 追呼叫鏈 | 需要跨 **>1 個目錄** grep | `Explore` |
| Web 研究 / 查文件 | 預估 **>2 輪**搜尋 | `general-purpose`（model: `sonnet`） |
| 批次改檔 | 同一模式改 **>3 個檔** | `general-purpose`（model 見 §3） |
| DoD 驗收 | **一律**（見 §6） | `verifier` |
| 產出長文（>200 行報告/文稿） | 主對話只寫大綱 | `general-purpose`（寫入檔案，回路徑） |

主對話**可以**自己做的：讀單一短檔確認關鍵事實、單檔小修（≤3 處編輯）、git 操作、
跟使用者對話、整合 subagent 的結論做決策。

反模式（看到自己在做這些就停手改派工）：主對話連續 `cat`/`Read` 第 4 個檔案；
把 web search 結果原文貼進思考；一個檔一個檔手改第 4 個同模式的檔。

## §2 派工三件套（缺一件就不准送出）

每個 subagent prompt 必含三塊，寫法照 `DELEGATION_TEMPLATES.md` 的模板填空：

1. **目標與動機**：要它做什麼＋為什麼（上游任務是什麼、結果會被怎麼用）。
   subagent 看不到主對話，**所有必要脈絡都要寫進 prompt**，包括相關檔案路徑。
2. **驗收條件**：完成的客觀判準，逐條可打勾。「找出所有呼叫點」不合格；
   「列出每個呼叫點的 檔案:行號，並標注是否在測試碼內」合格。
3. **回報格式**：明確規定回什麼、不回什麼（見 §4）。

## §3 model × effort 對照表

原則：**顯式指定 model，不用 `inherit`**（防止 opus 指揮官把便宜活也用 opus 跑）。
effort 只能在 `.claude/agents/` 定義檔固定（見 MODEL_ROSTER）；用內建 agent type 時
以 prompt 明示「快速掃過即可」或「窮盡檢查」來調節力度。

| 子任務型態 | model | 理由 |
|-----------|-------|------|
| 搜尋/定位（找檔案、找定義） | `Explore`＋呼叫時**必帶** `model: "sonnet"`（內建 agent 未覆寫會繼承主對話的 opus，等於用貴模型跑便宜活） | 搜索靠工具不靠推理 |
| 批次套用已解出的模式 | `haiku` | 模式已定，照抄成本最低 |
| 實作（新功能、修 bug） | `sonnet` | 工作馬；卡住再依 §5 升級 |
| 重構（跨檔、動介面） | `sonnet` 起手；動核心架構直接 `opus` | 誤判成本高 |
| 研究/比較/事實查核 | `sonnet` | 產出走 research skill 格式 |
| 審查/驗收 | `sonnet`（verifier 已釘） | 驗收靠判準不靠天分；判準要夠具體 |
| 高風險判斷（架構取捨、對外文案定稿前審） | `opus`，或多答案評審（§6） | 品味與取捨題 |
| 超大量讀取（>50 檔） | `sonnet` 分批派（每批 ≤40 檔，各自回結論再彙整） | `[1m]` 別名不能用於派工（見 MODEL_ROSTER） |

## §4 回報合約（寫進每個派工 prompt 的最後一段）

- 只回：**結論、清單（檔案:行號）、明確的 pass/fail、遇到的障礙**。
- 不回：檔案原文、完整 diff、逐步過程敘述。
- 長產物（報告、程式碼、資料表）**寫入檔案**，回報只給路徑＋3 行摘要。
  暫存產物放 `outputs/drafts/`，正式產物路徑由派工 prompt 指定。
- 回報上限預設 30 行；超過表示 subagent 在倒原料，重派並收緊格式。
- subagent 回報「做完了」不算數——驗收依 §6 另派 verifier。

## §5 升降級路徑

- **`haiku` 錯 1 次 → 直接升 `sonnet`**。不要跟便宜模型來回拉扯，重派的成本低於調教。
- **`sonnet` 同一子任務錯 2 次 → 升 `opus`**，且 prompt 必須附上**完整失敗軌跡**：
  兩次的 prompt、產出、驗收失敗的具體差距。沒有軌跡的升級等於重擲骰子。
- **解出模式後降級**：`opus`/`sonnet` 解出的做法，整理成「模式＋範例」後改派
  `haiku` 批次套用剩餘案例。
- **同一件事最多重試 2 輪**（不分模型累計）。此計數只管「同一子任務的重派」，
  獨立於 CLAUDE.md 硬規則 3「整個任務連續失敗 3 次就停」——兩個計數器並行，
  先到先觸發，互不取代。第 3 輪前必須先過
  `JUDGMENT_RUBRICS.md` §4：這是「執行失誤」還是「方向錯了」？方向錯了就換路，
  不是換模型。
- 天花板：`opus` ＋ 人工。超出 `opus` 能力的題目記入
  `system/HANDOFF_FABLE5.md` 所述的待強模型清單（`memory/pending_hard_questions.md`），
  交使用者裁決或等更強模型可用。

## §6 驗證不自驗

寫產出的 context 不能當驗收者——它帶著「我做完了」的偏見（FAILURE_TAXONOMY
VAL-01/02/03 的根因，佔失敗 21%）。規則：

1. **DoD 驗收一律派 fresh-context agent**：用 `.claude/agents/verifier.md`（Agent tool
   `subagent_type: "verifier"`）。只給它 Task Card 路徑＋產出路徑，**不給執行過程**。
2. **驗法分型**：
   - 檔案類產出 → read-back：verifier 實際打開檔案逐條比對 DoD，引用行號證明。
   - 程式碼 → 跑測試或實跑（本 repo：`ruby scripts/check_spec_consistency.rb`、
     `ruby scripts/check_context_budget.rb`、對應 `test_*` 檔）；「看起來對」不算過。
   - 高風險判斷（risk_level ≥ high、對外內容、架構決策）→ 第二意見：另派一個
     `opus` agent 獨立作答同一題，比對結論；或生成 2–3 個候選答案後派評審 agent 選優並說明理由。
3. verifier 回報格式固定：DoD 逐條 `pass`/`fail`＋fail 的具體差距＋證據（檔案:行號）。
4. verifier 說 fail → 回 §5 流程處理；不准跟 verifier 辯論，要嘛修產出，要嘛修 DoD（後者需使用者同意）。

## 與既有制度的關係

- Task Card 的 `allowed_tools` 含 `subagent_dispatch` 才可做任務內派工（模板已預設含）。
  **例外**：§6 的 DoD 驗收 verifier 是 gate 的一部分、不是任務工具，**不受**
  `allowed_tools` 白名單限制——任何 Task Card（含舊卡）收尾都必派 verifier。
- 派工不豁免三條硬規則與 PERMISSIONS deny：subagent 一樣不得對外發送、不得刪除。
  注意 `scripts/permissions_guard.py` hook 只攔得住 Bash 指令層的部分 deny 模式，
  其餘 deny 靠規則遵守——派工 prompt 涉及風險面時要把禁令明寫進去。
- skill 路由（`ROUTING_RULES.md`，任務→哪種 skill）與模型調度（本檔，子任務→哪個 model）
  是兩層，先路由後調度。
