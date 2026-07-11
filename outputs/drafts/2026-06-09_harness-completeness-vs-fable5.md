# Agent Harness v2 完整度比對：以 Fable 5 時代 Anthropic Harness Engineering 為基準

- Task Card：`tasks/2026-06-09_harness-completeness-vs-fable5.yaml`（task_id: 20260609-001）
- 基準（雙軌）：(A) Anthropic engineering blog 兩篇 + 官方參考實作 `anthropics/cwc-long-running-agents`；(B) Claude Code 本身的 harness 架構
- 狀態：草稿，待人工審閱後 promote

## 結論

以 13 個維度的合併 rubric 評估，本專案完整度約 **75–80%**（✅ 已具備 7 項、🟡 部分具備 4 項、❌ 缺失 2 項）。**治理、權限、稽核、成本控管四個面向超過官方教材的基準**——官方教材幾乎不談成本與審批，而本專案有實證校準的 token 預算與完整 approval trail；`NATIVE_OVERLAP.yaml` 的季度重疊度評估更是官方 meta 原則（「harness 元件編碼對模型弱點的假設，模型變強就該拆掉」）的制度化實作，多數團隊沒有做到。**集中缺口在 long-running 自治執行面**：builder/grader 結構性分離、evidence-gated 完成驗證、跨 session handoff 協議、執行中操作者控制（kill-switch/steer）、sub-agent 分工。這些缺口在目前「短任務 + 人工在場」的一人公司使用型態下實際風險低，但若未來要跑多小時自治任務，就是必補項。

## 已知事實

### 基準 A：Anthropic 官方 harness engineering 教材要點

1. **Effective harnesses for long-running agents**：initializer agent（首次執行建環境）+ coding agent（每 session 增量推進）；feature list 拆解（全部預設未完成）；`init.sh` 環境重建；agent 自維護 progress/handoff 工件跨 context window 接力；自我驗證後才標記完成。
2. **Harness design for long-running application development**（Fable/Opus 4.5 世代）：planner / generator / evaluator 三 agent 架構；**fresh-context evaluator**（與建置者分離、不帶建置脈絡的評審）對抗自評偏誤，被列為最強槓桿之一；評分 rubric（功能、設計、craft、原創性）；evaluator 以 Playwright 實機操作驗證；模型升級後拆掉過時 scaffolding（如 context reset 因 compaction 改善而移除）。
3. **anthropics/cwc-long-running-agents**（官方參考實作，已完整取得）：
   - **Default-FAIL contract**：`test-results.json` 全部 feature 預設 `"passes": false`；PreToolUse hook（verify-gate）擋住「未先讀 evidence 檔案就改寫結果」的寫入——**「done 由 gate 結構性強制，不靠 prompt 客氣話」**。
   - **Fresh-context evaluator subagent**：read-only（無 Write/Edit）、從乾淨 context 審 diff 與截圖、回傳 PASS / NEEDS_WORK。
   - **Handoff**：agent 重啟先讀 `PROGRESS.md`、停止前寫回；`commit-on-stop.sh`（Stop hook）兜底未 commit 的工作。
   - **操作者控制**：`kill-switch.sh`（偵測到 `AGENT_STOP` 檔案即 halt 所有 tool call）、`steer.sh`（讀 `STEER.md` 中途轉向，不必重啟）。
   - **終止條件迴圈**：`/goal` 或外層 while-loop（grep 到還有 `"passes": false` 就再跑一輪 build→evaluate）。

### 基準 B：Claude Code 原生 harness 機制

permission modes 與 allow/ask/deny rules、hooks（PreToolUse / PostToolUse / Stop / SessionStart 等）、skills（自動載入 + /skill 觸發）、subagents 與 agent teams、plan mode、自動 compaction、checkpoint/rewind、CLAUDE.md 與 auto memory、MCP、background tasks、`/goal` 與 routines/loop 排程。

### 本專案現況（盤點證據）

14 個 system/ 治理檔全數完整非 stub；5 個 skills 各含 `eval_examples.md`；51 張 Task Cards（45 張實際執行日期卡）；41 筆 audit 紀錄 + 1 次受控失敗演練（R5）；`scripts/permissions_guard.py` 以 PreToolUse hook 做 runtime deny 強制；13-step CI（schema lint、context budget、YAML parse、E2E gate flow、failure-drill 回歸）；`system/RECOVERY_RUNBOOK.md` 4 情境、1 已演練；checkpoint commit 格式嚴格遵守；frontend dashboard + M1–M4 治理指標。

## 逐維度評級（合併 rubric）

| # | 維度 | 評級 | 本專案證據 | 對照基準的差距 |
|---|------|------|-----------|---------------|
| 1 | 任務拆解與 contract（feature list / DoD） | ✅ 已具備 | Task Card schema（goal、definition_of_done、allowed_tools、成本上限）+ `system/validate_task_card.py` + 51 張實卡 | Task Card 是 feature list 的治理強化版；唯 DoD 非機器可讀的 default-FAIL contract（見 #2） |
| 2 | Evidence-gated 完成驗證 | 🟡 部分 | `system/GATE_POLICY.yaml` completion_check 逐條比對 DoD | 比對由同一 agent 自我宣告，無 cwc verify-gate 式 hook 強制「先讀 evidence 才能標 pass」；hook 基礎設施已存在（permissions_guard.py），可擴充 |
| 3 | Builder / grader 分離 | 🟡 部分 | `skills/review/SKILL.md:54` 明文警告循環驗證、要求審不同 session 的產出；audit log 中 R02（opus）審 R01 有換模型實例 | 是流程約定而非結構：無 read-only fresh-context evaluator subagent、無強制 PASS/NEEDS_WORK 結構化裁決——官方視為最強槓桿之一 |
| 4 | 結構性強制（hooks vs prose） | ✅ 已具備 | `scripts/permissions_guard.py`（PreToolUse runtime deny）+ 13-step CI + 8 個測試套件 | deny 面已達官方「結構性強制」哲學；completion 面尚未（見 #2） |
| 5 | Checkpoint 與復原 | ✅ 已具備 | checkpoint commit 慣例嚴格遵守；GATE_POLICY 每層 rollback 定義；`RECOVERY_RUNBOOK.md` 已演練（byte-identical、5ms 還原）；R5 失敗演練 | 僅缺 cwc `commit-on-stop.sh` 式 Stop hook 兜底未 commit 工作（小缺口） |
| 6 | 跨 session handoff / context 管理 | 🟡 部分 | AUDIT_LOG、logs/runs/、memory/context.md、7 筆 decision logs 提供完整溯源；context 硬限制有 CI 護欄 | 溯源是給人看的；缺 agent 自用的 PROGRESS.md 式協議（重啟先讀、停止前寫回），長任務跨 context window 無接力機制 |
| 7 | 環境初始化（init.sh / initializer） | ❌ 缺失 | 僅 `scripts/run_frontend.sh` 局部、CI 內含環境 setup | 無 init.sh / initializer agent 概念；現有任務型態（research/writing）不需要，優先級低 |
| 8 | 操作者控制與可觀測性 | 🟡 部分 | 可觀測性強：frontend dashboard、`governance_metrics.py` M1–M4、audit log；事前控制完整：APPROVAL_POLICY 8 個觸發條件 + approval 紀錄 | 缺執行中控制：無 kill-switch（AGENT_STOP halt）、無 steer（STEER.md 中途轉向）——控制只存在於事前，執行中只能中斷 session |
| 9 | Sub-agent 架構 | ❌ 缺失 | 單 agent + `ROUTING_RULES.md` skill 路由 | 路由選的是 skill 不是 agent；無 planner/generator/evaluator 分工；Claude Code 原生 subagents 可直接補（與 #3 同解） |
| 10 | 權限 / 沙箱 | ✅ 已具備 | 三層 allow/ask/deny + 4 風險等級 + runtime guard + Task Card 工具白名單 | 與 Claude Code 原生 permissions 語意近 1:1（NATIVE_OVERLAP 75–80%）；沙箱依賴平台層，合理 |
| 11 | Skills 模組化 | ✅ 已具備 | 5 skills 完整 + 每個附 eval_examples.md（good/bad 範本——官方教材沒有的做法）+ token 上限 CI 護欄 | 僅 research 已 symlink 至 `.claude/skills/`，其餘 4 個未註冊原生自動載入 |
| 12 | 成本控管 | ✅ 已具備（超過基準） | COST_POLICY + 8 筆真實任務校準係數（1.25–2.0x）+ Task Card max_tool_calls/max_web_searches + M1–M4 | 官方教材幾乎不談成本；此為超出基準項 |
| 13 | Meta 原則：隨模型升級拆 harness | ✅ 已具備（罕見亮點） | `system/NATIVE_OVERLAP.yaml`：季度評估與原生功能重疊度（aggregate 30%，>50% 為重構觸發點），逐模組列 native 對應與證據 | 正是官方「每個 harness 元件編碼對模型弱點的假設」原則的制度化；唯 2026-05-09 評估早於 Fable 5 發布，數值待更新 |

## 合理推論

1. **缺口的共同根因是「單 agent、單 session、人工在場」的設計假設**。五個 🟡/❌ 缺口（#2、#3、#6、#8、#9）都源自同一假設；官方教材的場景是多小時無人自治，假設不同，缺口才顯著。依目前使用型態（41 筆任務全為短任務、approval 在場），這些缺口的實際風險低。
2. **補缺口的成本不對稱地低**，因為 hook 與 CI 基礎設施已經存在。建議優先序：
   - **P1 — evaluator subagent**：建 `.claude/agents/evaluator.md`（read-only、fresh context、回傳 PASS/NEEDS_WORK），把 review skill 掛上去。一次解 #3 + #9，官方認證的最強槓桿，成本最低。
   - **P1 — evidence-gated completion**：DoD 加機器可讀 contract（default-FAIL），用 PreToolUse/Stop hook 強制「先有 evidence 讀取紀錄才能標 pass」（cwc verify-gate 模式可直接參考）。解 #2。
   - **P2 — handoff 協議**：長任務 Task Card 配一個 PROGRESS 檔（重啟先讀、停止前寫回），解 #6；搭配 commit-on-stop hook 解 #5 殘餘缺口。
   - **P2 — kill-switch + steer hooks**：cwc 的兩個 shell script 幾乎可直接搬，解 #8。
   - **P3** — 其餘 4 skills symlink 至 `.claude/skills/`；init.sh（等有 app 型任務再做）。
3. **NATIVE_OVERLAP 應在 Fable 5 後重評**。官方 meta 原則預測模型升級會讓更多 harness 元件可拆（例：Opus 4.5 讓 context reset 退役）；Fable 5（2026-06-09 發布）支援數天級自治、自建 harness 與自評，30% 這個數字大概率已偏低，且上述 P1/P2 建議若採原生 subagents/hooks 實作，重疊度會進一步上升——這正是該檔案設計要捕捉的訊號。

## 待驗證

- 兩篇 Anthropic engineering blog 原文被 403 擋（HN 討論串亦同），細節由官方 cwc repo（完整取得）+ 搜尋摘要 + 二手來源（InfoQ 等）交叉重建；原文可能有未捕捉的 nuance。[待驗證]
- `/goal`、agent teams 等 Claude Code 功能的可用範圍依版本/通路而異，採用前需確認當前版本支援。[待驗證]
- 「review 針對不同 session 產出」的約定遵守率：僅抽查 R01/R02 一例，未逐筆核對全部 41 筆。[待驗證]

## 高風險假設

- **「任務都是短任務」**：本報告對缺口風險的「低」評價建立在單 context window 內完成 + 人工在場的使用型態上。若開始跑多小時自治任務（如 plugin v3 自動化、長期排程），#2/#3/#6/#8 立刻從低風險變成高風險，P1/P2 需先行。
- **30% 重疊度仍有效**：該數值為 2026-05-09 人工評估，早於 Fable 5 發布；若實際已超過 50% 重構閾值而未察覺，會持續投資在應該拆除的自建元件上。

## 來源

- [Effective harnesses for long-running agents — Anthropic Engineering](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)（原文 403，經摘要與 cwc repo 交叉重建）
- [Harness design for long-running application development — Anthropic Engineering](https://www.anthropic.com/engineering/harness-design-long-running-apps)（同上）
- [anthropics/cwc-long-running-agents — 官方參考實作](https://github.com/anthropics/cwc-long-running-agents)（完整取得）
- [Claude Code Documentation — Overview](https://code.claude.com/docs/en/overview)
- [InfoQ：Anthropic Designs Three-Agent Harness](https://www.infoq.com/news/2026/04/anthropic-three-agent-harness-ai/)
- [Claude Fable 5 and Claude Mythos 5 — Anthropic](https://www.anthropic.com/news/claude-fable-5-mythos-5)
- 本 repo：`system/`（14 檔）、`skills/`（5 skills）、`scripts/`（8 enforcement scripts）、`logs/AUDIT_LOG.md`（41 筆）、`tasks/`（51 卡）、`.github/workflows/spec-consistency.yml`、`frontend/`
