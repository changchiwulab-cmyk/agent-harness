# Fable 5 快速診斷：Agent Harness 三大漏點

日期：2026-07-02  
適用 repo：`changchiwulab-cmyk/agent-harness`  
目的：把本次高能力 session 的判斷先落檔，供後續弱模型引用。  
限制：本次能查到 GitHub repo 與官方 Claude Code 文件；無法直接讀取使用者本機 `/model`、`/effort`、MCP server、`~/.claude/` 使用者層設定，因此凡涉及「實際可用模型與本機工具」一律要求下一個 session 先做 discovery，不得憑印象。

---

## 結論

目前最漏 token、最容易失焦、最容易出錯的前三名不是模型不夠強，而是制度缺口：

1. **CLAUDE.md 承擔太多流程責任，缺少路由層。**
2. **模型調度仍停在成本政策構想，沒有可執行派工守則。**
3. **驗證主要由執行者自驗，缺少 fresh-context 對抗審查與 read-back 合約。**

這三件事修完後，Sonnet / Opus / Haiku 這類較弱模型才會穩定受益。

---

## 1. CLAUDE.md 承擔太多流程責任，缺少路由層

### 已知事實

既有 `CLAUDE.md` 已有三條硬規則、權限摘要、執行流程、context 限制、checkpoint、驗證失敗處理。它是可用的，但它把「憲法、SOP、路由表、例外處理」混在一起。

### 風險

- 弱模型容易把每次任務都拉回完整流程，導致小任務也重跑 Task Card / Gate / Audit。
- 長流程寫在 boot prompt 會吃掉每次 session 的 context。
- 規則衝突時，弱模型不知道該優先遵守哪一條。
- 一旦要改模型調度、派工或維護規則，會一直膨脹 `CLAUDE.md`。

### 具體修法

- `CLAUDE.md` 只保留：身份、硬規則、風險紅線、路由表、完成回報格式。
- 長內容抽到獨立檔：
  - `system/FABLE5_FAST_DIAGNOSIS.md`
  - `system/MODEL_ROUTING_POLICY.md`
  - `system/JUDGMENT_RUBRIC.md`
  - `system/DELEGATION_PROMPTS.md`
  - `system/MAINTENANCE_PROTOCOL.md`
  - `system/FUTURE_SESSION_LETTER.md`
- 弱模型遇到流程問題，先看路由表，不要自行發明新流程。

### 驗收條件

- `CLAUDE.md` 少於 100 行。
- 每個長規則都有明確引用檔。
- 任務開始前能用 30 秒判斷該讀哪個檔，不需要全文載入所有制度檔。

---

## 2. 模型調度停在構想，沒有可執行派工守則

### 已知事實

既有 `system/COST_POLICY.md` 已有 v2 準備方向：分類、抽取、格式檢查走便宜模型；規劃、推理、整合分析走強模型。但它還不是可直接執行的調度政策。

官方 Claude Code 文件顯示模型 alias 包含 `best`、`fable`、`opus`、`sonnet`、`haiku`、`opusplan`；Fable 5 需用 `/model fable` 選擇，且適合長時間、自主、模糊、高難任務。官方文件也說 `/effort` 可調 effort，`ultracode` 會送出 `xhigh` 並啟用 dynamic workflows。  
來源：Anthropic Claude Code model configuration docs, 2026-07-02 checked.

### 風險

- 強模型會被拿去做日常批次任務，燒掉最高價值 session。
- 弱模型遇到難題會反覆重試，而不是升級。
- subagent 回報太長，主對話被污染。
- 沒有明確降級機制，解出模式後仍用昂貴模型批量套用。

### 具體修法

建立 `system/MODEL_ROUTING_POLICY.md`，要求：

- 主對話是指揮官，不下場掃 repo、查大量網頁、批次改檔。
- 大量讀取、掃描、搜尋、批次改檔、審查一律派 subagent 或獨立 worker。
- 每次派工必帶三件套：
  1. 目標與動機。
  2. 驗收條件。
  3. 回報格式。
- subagent 僅回：結論、證據、檔案路徑、行號、風險、下一步；長產物落檔回路徑。
- 小模型錯一次升級；中階模型同一子任務連錯兩次，帶完整失敗軌跡升級。
- 同一件事最多重試兩輪；第三輪不是努力，是治理失敗。

### 驗收條件

- 任何任務開始前，都能明確指定 model / effort / worker / 驗收方式。
- 任何 worker 回來，都不應把大量原始資料塞回主對話。
- 成功解出的模式必須降級給便宜模型批次套用。

---

## 3. 驗證主要由執行者自驗，缺少 fresh-context 對抗審查

### 已知事實

既有 `system/GATE_POLICY.yaml` 有 schema / rule / completion / risk 四層 Gate，方向正確。但它沒有強制要求「執行者與驗收者分離」。

### 風險

- 執行者會為自己的產出找理由，弱模型尤其容易漏看模糊規則。
- 文件任務會「看起來很完整」，但沒有 read-back 證明確實落地。
- 程式碼任務會把 lint / typecheck 當成完整驗證，卻沒有實跑 user flow。
- 高風險判斷會被單一模型品味綁架。

### 具體修法

建立 fresh-context 驗收合約：

- 檔案任務：驗收者不得讀執行者總結，直接 read-back 每個檔案。
- 程式碼任務：測試或實跑為主；無法實跑時標示缺口，不可宣稱完成。
- 高風險判斷：加第二意見或多答案評審選優。
- 產出完成前必列：
  - changed files
  - backup path
  - read-back result
  - failed / partial items
  - unresolved risks

### 驗收條件

- 每次制度修改都有備份。
- 每個新檔都能被 read-back。
- 審查者能指出「規則互相打架、路徑錯誤、弱模型會誤讀的句子」。
- 修完後才可總結。
