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

**這條原則有前提，20260725-A01 補上實測數字**：prompt cache 只在前綴達到**最小可快取長度**
時才會生效，未達門檻是靜默不快取（不報錯）。該門檻**因模型世代而異且非單調遞減**：

| 世代 | 最小可快取前綴 | 本專案穩定前綴（實測 2,130 tokens）是否可快取 |
|------|--------------|--------------------------------|
| Opus 5 | 512 tokens | ✅ |
| Opus 4.8 | 1,024 tokens | ✅ |
| Opus 4.6 / 4.5、Haiku 4.5 | 4,096 tokens | ❌ 靜默不快取 |

穩定前綴（`CLAUDE.md` + `GLOBAL_RULES.md`）實測 2,130 tokens（20260725-A01 後，
`check_context_budget.rb`：861 + 1,269）。兩點推論：

1. **本專案的組裝順序紀律在當代是真的有回報的**，在 4.6 世代則沒有 —— 過去這條原則是憑理論寫的，現在有數字。
2. 前綴**變短不一定更好**：低於門檻反而完全失去快取。壓縮 `CLAUDE.md` 時要看的是門檻，不是「越小越好」。

驗證方式：看回應的 `cache_read_input_tokens`；若重複同前綴的請求該值恆為 0，代表前綴中有
每次都變的內容（時間戳、UUID）或未達門檻。

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

## 收尾的硬檢查點

本節原為一份「自我檢查」勾選清單，20260725-A01 移除 —— 其中可機器驗證的兩項已有
腳本專責（不需要 prompt 再叮嚀一次），其餘兩項屬本檔上文已述的紀律：

| 原檢查項 | 現由誰負責 |
|---------|-----------|
| `check_context_budget.rb` 仍綠？ | CI（`.github/workflows/spec-consistency.yml` 的 Context budget check） |
| 跨 session 前更新 `state/last_checkpoint.yaml` | `state/last_checkpoint.SCHEMA.yaml` + RECOVERY_RUNBOOK 場景 C |
| context 是否塞了用不到的全文 | 本檔 §二 JIT 檢索紀律 |
| 中間結論是否已卸載到 scratchpad | 本檔 §三 scratchpad 慣例 |

> 為什麼移除：當代模型會自行驗證產出，**額外的自我檢查指令會造成過度驗證**（重複跑
> 已由腳本保證的檢查、產出冗長的自檢報告）。這裡移除的只是 **prompt 層與腳本層重複的
> 叮嚀**；`gate_check.py` / `verification_loop.py` / `GATE_POLICY.yaml` / CI 這些
> **腳本層驗證一律不動** —— 那是稽核控制，不是模型自檢，兩者不可混為一談。
