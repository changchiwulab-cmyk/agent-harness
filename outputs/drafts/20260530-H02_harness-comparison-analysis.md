# Agent Harness 比對分析：公開生態 vs 本專案（一人公司 Agent Harness v2）

> Task Card: 20260530-H02（analysis / Stage 2，model: claude-opus-4-8）
> 輸入：`outputs/drafts/20260530-H01_harness-landscape-scan.md` + 本 repo 設計面（CLAUDE.md, system/*, skills/*, logs/*, scripts/*）
> 證據等級：H01 的架構性觀察為主；H01 中標 [待驗證] 的量化宣稱僅供參考，不作為強結論依據。

---

## 結論與建議

**一句話：本專案在「執行前控制」這一端是公開生態裡少見地嚴格、且用「檔案 + CI」真正落地的（這是你的護城河）；但在「執行後可量測」這一端明顯落後——缺 observability/trace/replay 與可跑的 eval harness，導致四層 gate 的後兩層（completion / risk）目前是「LLM 說了算」而非「測得出來」。**

最該補的三件事（優先序）：
1. **把 `definition_of_done` 變成可跑的 eval**（completion gate 客觀化）—— 借 Inspect-AI / SWE-bench / Terminal-Bench 的 harness 思路。
2. **把模型路由正式落地**（本 workflow 的 Haiku→Opus 就是第一個真實案例，目前 COST_POLICY 仍只是 v2 提案）。
3. **加一層結構化 trace**（讓 `logs/runs/` 從事後敘述變成可回放、可量測的證據）。

本專案要刻意「不採納」的：主流框架的 emergent 多代理對話（AG2 式）與「<30 行極簡、少 guardrails」（smolagents 式）—— 兩者都與「可控 > 能力」相反，維持現狀（不做）是正確選擇。

---

## 比較維度表

| 維度 | 本專案做法 | 公開生態做法（代表） | 本專案優勢 | 缺口 | 可採納（優先級） |
|------|-----------|---------------------|-----------|------|-----------------|
| **任務閘控** | 「沒有 Task Card 不執行」硬規則；Task Card = 執行前合約（goal + definition_of_done 必填，CI 擋空） | 多為軟性 role/goal（CrewAI、AG2）；少數有結構化任務 | **強且少見**：執行前合約 + schema CI 強制，極可審計 | DoD 是文字、由 LLM 判定達成 | 把 DoD 升級成可跑斷言（P0） |
| **權限模型** | allow/ask/deny 三層宣告式檔案（`PERMISSIONS.yaml`）；`scripts/permissions_guard.py` 已有守門 | 程式碼鉤子（DeepAgents、Pydantic AI approve/reject、Goose 確定性閘）；DSL（NeMo、Guardrails AI） | 宣告式、人讀友善、與審批流綁定 | deny 多靠「LLM 自律」，runtime 強制覆蓋面不確定 | 擴大 `permissions_guard.py` 的 pre-flight 強制（P1） |
| **驗證 gates** | 4 層 schema→rule→completion→risk（`GATE_POLICY.yaml`）；schema/rule 由 `check_spec_consistency.rb` CI 真擋 | 多靠 evaluator-optimizer 迴圈（Anthropic cookbook）、tracing 驗證（LangSmith） | 前兩層（schema/rule）是**真·自動擋**，多數框架沒有 | 後兩層（completion/risk）無客觀量測 | completion gate 接 eval（P0） |
| **模型路由** | 未實作；`COST_POLICY.md` 只有 v2 提案（便宜模型抽取／強模型推理） | 普遍 model-agnostic，可自由配置（OpenAI SDK、LangGraph、Pydantic AI） | —（落後） | 一直用最強模型，成本未優化 | 把 Haiku→Opus 正式化（P0） |
| **記憶 / 狀態** | `memory/active_projects`、decisions log、長期記憶需人工確認；checkpoint=git commit | runtime 持久化 + resume（LangGraph durable execution、LlamaIndex 持久化） | 長期記憶「人為確認才寫」很克制、防污染 | 無自動 resume／狀態查詢，靠人工 git | 加結構化 progress 檔 + resume runbook（P2） |
| **可觀測性 / audit** | `AUDIT_LOG.md`（文字 yaml）+ `logs/runs/` + 前端 dashboard（`frontend/`） | 結構化 trace + replay + dataset（LangSmith、Langfuse、Inspect） | 有 audit 紀律、有治理面板 | **最大缺口**：無結構化 trace/回放，token/工具呼叫多為估計 | 落地結構化 run trace（P1） |
| **eval / 失敗處理** | `FAILURE_TAXONOMY.yaml`（14 模式，源自 Microsoft 分類）+ 連續失敗 3 次停 + `logs/errors/` | 標準 benchmark/harness（SWE-bench、Terminal-Bench、Inspect、OpenAI Evals） | 失敗分類 + RETRO + 成本校準，治理成熟度高 | 沒有「測自己 harness」的 eval；DoD 未變測試 | 引入 eval harness（P0）；更新失敗分類（P2） |
| **context 預算** | 硬上限（CLAUDE.md ≤3000、skill ≤1500 token、20 輪摘要、大檔路徑引用） | 多靠自動 compaction（Anthropic harness post、LangGraph、LlamaIndex） | **明確且嚴格**，比多數框架更有紀律 | 上限靠人為遵守，無自動量測告警 | 加 context 用量量測（P2，可併入 trace） |
| **多代理編排** | 拆成多張 Task Card 以 `input_data` 檔案接力（本 workflow 用 Haiku 子代理 fan-out） | orchestrator-subagent / graph（cookbook、LangGraph、Microsoft Agent Framework） | 檔案接力**全程可讀可審**，無黑箱 | 無動態編排／條件分支，全靠人預先拆卡 | 維持；必要時引入輕量條件鏈（P2） |

---

## 重點缺口深掘

**缺口 1：completion / risk gate 無客觀量測（最痛）。**
`GATE_POLICY.yaml` 的 schema_check / rule_check 有 `check_spec_consistency.rb` 真正把關（這點贏多數框架），但 completion_check 是「逐條列 DoD → 標 pass/fail」，由執行的 LLM 自己判斷；risk_check 同理。公開生態（SWE-bench、Terminal-Bench Harbor、Inspect-AI）的共同做法是把「完成」定義成**可執行測試**。本專案的 DoD 多數其實可測（例：「outputs/drafts/X.md 含某結構」「audit log 記一筆」都能寫成斷言）。

**缺口 2：observability 是事後文字，不是結構化證據。**
`AUDIT_LOG.md` 的 `estimated_tokens` 多為「~16K」式估計；`tools_called` 是人工填。LangSmith/Langfuse/Inspect 的價值在於**自動、結構化、可回放**。沒有它，RETRO（`RETRO_FLOW.md`）與成本校準（`COST_POLICY.md`）的數據基礎偏弱。

**缺口 3：模型路由還停在提案。**
這次 workflow（Haiku 三 lane 發現 → Opus 分析）本身就證明了便宜/強模型分工可行且省成本。`COST_POLICY.md` 已寫好分工原則，差「把它變成 Task Card 可宣告、audit 可記錄、CI 可驗」的最後一哩。

---

## 可採納建議（優先級排序，對應檔案）

> 評估含「一人公司適配度」：是否低維運、可漸進、單人可維持。

1. **[P0] DoD → 可跑 eval（completion gate 客觀化）**
   - 做法：先在 `skills/review/` 與 ops 類卡試點，要求每張卡的 DoD 至少 1 條寫成可執行斷言（檔案存在/含某段/通過某腳本）；新增 `tests/dod/` 或擴充 `scripts/` 一個 `check_dod.py`，由 `GATE_POLICY.yaml` 的 completion_check 引用。參考 Inspect-AI / Terminal-Bench Harbor 的 task 格式。
   - 一人公司適配度：**高**（可漸進，不必一次全改）。對應：`system/GATE_POLICY.yaml`、新增 `scripts/check_dod.py`、`tests/`。

2. **[P0] 模型路由正式落地**
   - 做法：把本 workflow 的 Haiku→Opus 從「convention」升級為機制：在 `TASK_CARD_TEMPLATE.yaml` 加**可選** `model` 欄位（預設沿用最強模型，向後相容），在 `check_spec_consistency.rb` 加白名單驗證（haiku/sonnet/opus 等），`generate_audit_log.py` 直接讀該欄位。`COST_POLICY.md` 的 v2 提案改為 v2「已實作」。
   - 一人公司適配度：**高**（直接省 token 成本；本次已驗證 Haiku 廣度發現夠用）。對應：`system/COST_POLICY.md`、`tasks/TASK_CARD_TEMPLATE.yaml`、`scripts/check_spec_consistency.rb`、`system/validate_task_card.py`。（屬「ask」層，需你核准動 schema/CI。）

3. **[P1] 結構化 run trace（observability）**
   - 做法：先不導入外部平台。為每次 run 落地一份結構化 JSON（run_id、每個 tool call、輸入/輸出摘要、token、gate 結果），放 `logs/runs/`（已有 `EXECUTION_LOG_SCHEMA.yaml` 可擴充）；前端 dashboard 加「單次 run 回放」視圖。若日後要平台，選 **Langfuse（self-host OSS）**。
   - 一人公司適配度：**中高**（JSON 落地成本低；平台化再議）。對應：`system/EXECUTION_LOG_SCHEMA.yaml`、`logs/runs/`、`frontend/`。

4. **[P1] 把 deny 從「LLM 自律」升級為確定性 pre-flight**
   - 做法：`scripts/permissions_guard.py` 已存在——擴大它對 deny 清單（刪除/外發/金流/改正式資料）的實際攔截覆蓋，並在 `GATE_POLICY.yaml` rule_check 明確引用為前置條件。借 Block Goose「確定性 stop-gate（非 LLM 決定）」的理念。
   - 一人公司適配度：**高**（基礎已在，屬補強）。對應：`scripts/permissions_guard.py`、`system/PERMISSIONS.yaml`、`system/GATE_POLICY.yaml`。

5. **[P2] 狀態持久化 / resume + progress 檔**
   - 做法：採 Anthropic harness post 的 `claude-progress.txt` 模式 + git history，定義「新 context window 如何快速回到狀態」；`RECOVERY_RUNBOOK.md` 已有災難恢復，補一節「正常接續」。概念對齊 LangGraph checkpoint-resume，但維持本專案的 git/檔案路線。
   - 一人公司適配度：**中**。對應：`system/RECOVERY_RUNBOOK.md`、新增 `memory/active_projects/<proj>/progress.md`。

6. **[P2] 用外部來源校準 `FAILURE_TAXONOMY.yaml`**
   - 做法：對照 Microsoft「Agentic AI 失敗模式分類」與工具呼叫可靠度論文（見 H01），檢查本專案 14 模式是否需新增（如「工具呼叫初始化/參數處理」細分）。純文件更新。
   - 一人公司適配度：**高**（低成本、純文件）。對應：`system/FAILURE_TAXONOMY.yaml`。

---

## 高風險假設

- **比對的證據面有限**：本分析建立在 H01 的快照式掃描上；若某重要框架/寫作未被掃到（「找到所有公開資料」本就不可能），某些「本專案獨特」的判斷可能被高估。處置：把「Task Card 執行前合約」這類強結論限定為「在掃到的範圍內少見」。
- **「等價」假設**：表中把各框架的 approval/guardrails 與本專案語義對齊；實際粒度不同（如 Pydantic 的工具審批 vs 本專案的 ask 層 vs Goose 的確定性閘），若據此直接抄實作會踩坑。處置：採納前先做小範圍 PoC。
- **量化未驗證**：H01 的安裝量/版本/金額等為子代理轉述且標 [待驗證]，本分析未用其下任何強結論；若未來引用須先查證。

## 待驗證

- 本專案 `definition_of_done` 中實際「可機械驗證」的比例有多高？（抽 10 張歷史卡實測，決定 P0 試點範圍）
- `scripts/permissions_guard.py` 目前實際攔截哪些 deny 動作？覆蓋率多少？（讀碼確認，決定 P1 補強幅度）
- Langfuse self-host 對一人公司的維運成本（記憶體/DB/升級）是否划算，或先停在「JSON 落地 + 現有 dashboard」即可。
- H01 中標 [待驗證] 的外部來源（Microsoft 失敗分類精確 URL、12-factor-agents、各 arxiv 編號）逐一查證後再進 `references/`。

## 建議下一步

1. 你先選方向：若同意，**先做 P0-2（模型路由落地）**——成本效益最直接，且本 workflow 已是現成案例；這會動 `system/` + CI，屬「ask」層，需你核准。
2. 接著 **P0-1（DoD eval 試點）**：挑 3 張歷史 ops/review 卡，把 DoD 改成可跑斷言，驗證 completion gate 客觀化可行。
3. P1（trace + permissions_guard 補強）併入下一次 RETRO（`RETRO_FLOW.md` 觸發條件：累積 5 卡或同類錯誤 2 次）。
4. 本兩張草稿（H01/H02）留在 `outputs/drafts/`，等你 review；若要升級為正式 `outputs/reports/` 需你核准（「ask」層）。
