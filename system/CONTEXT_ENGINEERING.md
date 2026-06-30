# Context Engineering — 上下文工程紀律（G-C）

## 立場

把 context 從「**不可超的 token 預算**」（既有 CLAUDE.md 硬上限 + `check_context_budget.rb`）
升級為「**可工程化的產物**」。業界 2025-26 把這件事命名為 *context engineering*：
context 的**內容與排列順序**對表現的影響，大於幾乎任何其他單一因素。

> 本檔只寫「Claude Code 原生**沒**做、需要本 harness 自己守的紀律」。
> 原生已做的（見下表）一律**不重造**，呼應 `system/NATIVE_OVERLAP.yaml`。

## 原生 vs 本 harness 的分工（避免冗餘）

| 能力 | 由誰負責 | 備註 |
|------|---------|------|
| 自動壓縮 / 長對話摘要 / context window 管理 | **Claude Code 原生** | CLAUDE.md「20 輪壓縮」是對齊原生，不另寫機制 |
| token 硬上限守護 | 本 harness（`check_context_budget.rb` CI） | 原生不強制專案級上限 |
| **組裝順序紀律** | 本 harness（本檔） | 綁定本專案具體檔案 |
| **JIT 檢索 / 路徑引用紀律** | 本 harness（本檔 + GLOBAL_RULES） | 「大檔用路徑引用」已是規則，這裡成文 |
| **結構化工作筆記（scratchpad）** | 本 harness（本檔） | 讓 memory/ 真正運作，且不違反 deny |

## 一、組裝順序（context assembly order）

每次 session 啟動／任務執行，context 依此序組裝（高穩定→高變動）：

1. **系統指令**：`CLAUDE.md`（boot）→ `system/GLOBAL_RULES.md`。
2. **自我認知與邊界**：`system/AGENT_CONTEXT.yaml`、相關 policy（`APPROVAL_POLICY` / `GATE_POLICY` / `INPUT_GUARDRAILS`）。
3. **任務與技能**：當前 `tasks/*.yaml` Task Card → 對應 `skills/<type>/SKILL.md`。
4. **專案記憶**：`memory/active_projects/<project>/context.md`（**JIT**，只載入當前 project）。
5. **工作歷史**：對話歷史 + 本任務 scratchpad（見三）。

順序原則：穩定的放前面（利於 prompt cache），易變的放後面。

## 二、JIT 檢索紀律（just-in-time retrieval）

- **預設用路徑引用，不全文貼入**（延續 GLOBAL_RULES 成本意識）。需要某段時才讀那段（用 offset/limit）。
- 大型來源（raw data、長報告）只在「即將使用」時載入；用完不反覆貼回 context。
- 先查 repo 內既有資料（`memory/`、`outputs/`）再 web search（延續 research skill 流程）。
- 不把整個目錄塞進 context；用搜尋（grep/glob）定位後只讀命中片段。

## 三、結構化工作筆記（scratchpad）— 讓 memory/ 真正運作

過去 `memory/` 幾乎沒運作，因為唯一寫入管道是「長期記憶（需人工確認）」，門檻過高，
導致**任務內的中間思考無處可放**，每次都靠對話歷史硬扛。補上**任務範圍**的工作筆記層：

| 層 | 位置 | 生命週期 | 權限 |
|----|------|---------|------|
| 工作筆記 scratchpad | `outputs/drafts/<task_id>-scratchpad.md` | 任務內；完成後可丟棄或併入產出 | **allow**（write_drafts） |
| 跨 session 接續點 | `state/last_checkpoint.yaml`（G-D） | 跨 session；任務 done 後失效 | allow（write_logs 同級） |
| 長期記憶 | `memory/active_projects/<project>/` | 永久；**需人工確認** | ask |

**scratchpad 慣例**：
- 用途：把長對話中「值得保留但還不是產出」的中間結論寫進 scratchpad，從 context 卸載，
  之後 JIT 讀回（業界稱 structured note-taking / agentic memory）。
- 內容：待辦、已確認的中間結論、暫存路徑引用、下一步。**不存**敏感資料（同 memory 禁則）。
- 不違反 `deny: auto_write_memory`：scratchpad 是任務範圍暫存草稿，**不是**長期知識；
  要變長期記憶仍須經 `memory/` 的人工確認流程。

## 四、子任務 context 隔離

- 當一個子任務的 context 與主線**明顯不同**（如大量原始資料整理），用獨立 scratchpad 隔離，
  整理完只把**結論**帶回主線，原始材料留在 scratchpad/路徑引用。
- **不**為此引入 multi-agent swarm（在 README「現階段不做清單」）；這是 context 衛生，不是編排。

## 自我檢查（長任務中途與收尾）

- [ ] context 是否塞了用不到的全文？（應改路徑引用）
- [ ] 中間結論是否已卸載到 scratchpad，而非全靠對話歷史？
- [ ] 跨 session 前是否已更新 `state/last_checkpoint.yaml`（G-D）？
- [ ] `check_context_budget.rb` 仍綠？
