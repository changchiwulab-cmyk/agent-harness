# Gap 盤點：以 Fable 5 + Claude Code 原生能力為基準

- Task Card：`20260614-001`
- skill_type：analysis
- 狀態：草稿，待人工審閱（通過後可晉升 `outputs/reports/`）
- 基準定義：**Fable 5**（前沿推理）+ **Claude Code 原生**（子代理並行、Plan mode、Hooks 的 allow/ask/deny、自動 context 壓縮、TodoWrite、Memory tool）

---

## 結論與建議

本框架的**規格層非常完整、強制層偏薄**。對照「會用 hook/CI 把規則變成程式、用前沿模型做並行編排、用 eval 量測品質」的原生基準，最關鍵的弱點不是缺規則，而是**規則大多停在文字、runtime 幾乎不擋**——而「控制」正是本框架的核心賣點。

建議強化順序：**強制力 → 可觀測 → 能力擴充**。理由：先讓既有規則真的被執行、結果可量測，再加多代理等新能力，才不會落入「給了新權力卻沒治理」的矛盾。砍冗餘（與原生高度重疊的模組）本次列為附帶發現、不主動執行（依使用者選擇）。

---

## 落差盤點

### A. 能力落差

| # | 落差 | 證據 | 嚴重度 | 建議 |
|---|------|------|:---:|------|
| A1 | **無多代理 / 編排**：明文禁止 agent-to-agent，複合任務只能拆多卡序列、用 output 檔接力，無法並行 fan-out、無依賴 DAG | `system/ROUTING_RULES.md:20,26-28` | 高 | 引入「有界編排 Task Card」（父卡 + subtasks DAG，經原生 Agent tool 並行），每 subtask 仍各自有卡/checkpoint/gate |
| A2 | **無 eval loop**：每 skill 有 `eval_examples.md` 黃金樣本，但沒有任何程式跑它；observability 只看成本/gate/error，**不量輸出品質** | `skills/*/eval_examples.md` 存在、無 runner；`governance_metrics.py` 無品質維度 | 高 | `run_evals.py` 以黃金集評分，品質指標納入 metrics，接進 RETRO |
| A3 | **模型路由未實作**：Task Card 無 `model` 欄位，永遠單一模型；Haiku 4.5 / Sonnet / Opus 4.8 / Fable 5 未分流 | `COST_POLICY.md:41-46`「v2 準備」 | 中 | Task Card 加 `model` + 路由表，落地 COST_POLICY 的 v2 段 |
| A4 | **記憶不可查詢**：decisions 為散落 YAML，無索引/檢索；intake 時不會先查「以前是否決策過」 | `memory/.../decisions/*.yaml`、`INTAKE_FLOW.md` 無查詢步驟 | 中 | `build_memory_index.py` 建索引，INTAKE 加「建卡前查既往決策」 |
| A5 | **失敗分類需重新定錨**：FAILURE_TAXONOMY 規格類失敗（角色漂移/步驟重複/不知何時停＝42%）多已被前沿模型 + 原生 plan/todo 緩解；框架相對高估這類、低估安全/成本/幻覺驅動 | `FAILURE_TAXONOMY.yaml`；`NATIVE_OVERLAP.yaml` 評估日 2026-05-09（早於 Fable 5） | 中 | 重估 taxonomy 權重，把強制資源移向模型無法自解的安全/成本維度 |

### B. 強制力落差（核心賣點目前多為文字）

runtime 真正被強制的只有 `permissions_guard.py`，而且**只管 Bash 的 deny pattern**。

| # | 落差 | 證據 | 建議 |
|---|------|------|------|
| B1 | **Write/Edit 不設防**：寫 `system/`、`skills/`、`memory/`（皆 ask 級）或把 high-risk/正式輸出寫到 `outputs/reports/`（應只到 drafts/），runtime 全不擋 | `permissions_guard.py:138-141`「Edit/Write are guarded by other layers」—那層只是 PERMISSIONS.yaml 的文字 | 把 guard 擴成路徑感知，這些 ask 級路徑回 `ask`、reports/ 回 `ask` |
| B2 | 硬規則「無 Task Card 不執行」無程式檢查 | CLAUDE.md 規則 | Stop hook 驗證任務有對應 Task Card |
| B3 | 硬規則「連 3 次失敗停」無計數器 | `COST_POLICY.md:24` | session 計數 + Stop hook |
| B4 | 四層 gate 是文字 checklist 非程式；`risk_check`（high-risk 須在 drafts/）只在 e2e 測試斷言、runtime 不跑 | `GATE_POLICY.yaml`、`tests/e2e/test_dummy_task_smoke.py` | `run_gates.py` 把四層 gate 變可執行（重用 `validate_task_card.py`），接 CI + Stop hook |
| B5 | 成本上限（max_tool_calls / 3 web / 5-call checkpoint）無計數強制 | `COST_POLICY.md:20-22` | PostToolUse 計數 + 越界提示 |

### C. 可觀測落差

| # | 落差 | 證據 | 建議 |
|---|------|------|------|
| C1 | 採集靠手寫 audit；token source 常為 `rule_estimated`/`not_recorded`；run log 只在失敗/高風險寫 → 業務層樣本偏少且偏誤 | `EXECUTION_LOG_SCHEMA.yaml`、決策 D006 | PostToolUse 自動採集真實工具數 |
| C2 | 無 PostToolUse 自動採集（只有一個 PreToolUse hook） | `.claude/settings.json` | 新增 `session_recorder.py` 寫 `logs/runs/session-*.jsonl` |
| C3 | metrics 不進 CI、無自動告警；M4>50%、M3<80% 觸發點要靠人記得手跑 | `governance_metrics.py:9`「not part of CI」 | 把 metrics 納入 CI（先非阻斷報告） |
| C4 | 無品質可觀測 | 同 A2 | eval 指標納入 metrics |

---

## 高風險假設

- **假設前沿模型已弱化規格類失敗**：若未來改用較弱模型，A5 的重新定錄會反向（規格類緩解需求回升）。→ taxonomy 重估應保留「依模型能力切換權重」的彈性。
- **假設 Claude Code hook 支援 `ask` 決策**：強制力強化（B1/B4）依賴 PreToolUse/Stop hook 能回 `ask`/`deny`。若 runtime 不支援，需退回「block + 提示改路徑」。本次實作以官方 `hookSpecificOutput.permissionDecision` 格式為準，並用單元測試 pin 住行為契約。

## 待驗證

- NATIVE_OVERLAP 以 Fable 5 重估後的聚合重疊度（本次先更新評估日與逐模組註記，數值待真實使用一輪後校正）。
- run_gates 的 rule_check 啟發式（工具白名單/checkpoint 節奏）對真實 run 的誤判率。

## 來源

- 本 repo：`system/ROUTING_RULES.md`、`system/COST_POLICY.md`、`system/PERMISSIONS.yaml`、`system/GATE_POLICY.yaml`、`system/NATIVE_OVERLAP.yaml`、`scripts/permissions_guard.py`、`scripts/governance_metrics.py`、`tests/e2e/test_dummy_task_smoke.py`、`skills/*/eval_examples.md`
- 基準：Claude Code 原生功能（Skills、子代理、Hooks、Plan mode、自動壓縮、Memory）；Fable 5 / Opus 4.8 / Sonnet 4.6 / Haiku 4.5 模型分層

## 建議下一步（對應強化路線）

1. **Phase 1 強制力**：路徑感知 guard（B1）、`run_gates.py`（B4）、Stop/PostToolUse（B2/B3/B5）
2. **Phase 2 可觀測**：`session_recorder.py`（C1/C2）、metrics 進 CI（C3）、前端趨勢面板
3. **Phase 3 能力**：模型路由（A3，低風險先做）、記憶索引（A4）、eval loop（A2/C4）、有界編排（A1，反轉決策 D003 → 需人工核可）

---

> **已晉升為 `outputs/reports/fable5-baseline-gap-analysis-v1.md`**（2026-06-15，Task Card `20260615-001`）。本 draft 保留作歷史備援。
