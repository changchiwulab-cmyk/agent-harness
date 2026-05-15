# Agent Harness v2 — 完整度與缺點審查（2026-05-15 快照）

- task_id: 20260515-002 ｜ skill_type: review ｜ risk: low
- 範圍：對照三平面/16 模組現況、評估自 `2026-05-02_project-completeness-analysis.md` 以來進展、列現存缺點
- 方法：純讀取證據（35 張 Task Card、31 筆 AUDIT_LOG、CI workflow、本 session PR #79 第一手事件）

---

## 0. 結論（TL;DR）

**作為「治理規格骨架」：完整度高（~90%）。作為「會自我執行 + 自我改善的系統」：~55%。**

- 16/16 模組檔案齊全、schema 受 `validate_task_card.py` 硬驗、CI 有 ~10 步護欄、且自 0502 起新增了**真實 runtime hook**（`permissions_guard.py`）與 **e2e smoke**——這兩項是 0502 分析點名的最嚴重缺口，已落地。
- 但核心病灶未除：**規則仍以 LLM 自律為主**（硬 enforcement 只覆蓋 Bash deny）、**學習迴路仍開環**（校準係數、retro 仍人工）、**前端仍非控制面**、**v3 外掛遷移做到一半**。
- 最具體的活體症狀：**35 張卡有 18 張卡在 `review` 不前進（51%）**、drafts 24 : reports 2、`logs/runs/` 仍只有 1 筆——graduation/閉環這一步在實務上幾乎沒發生。

---

## 1. 完整度評估：三平面 / 16 模組

| 平面 | 模組 | 在否 | 完整度 | 證據 / 備註 |
|------|------|:---:|:---:|------|
| 控制 | 1 Interface (Claude Code) | ✓ | 高 | 本 session 即在其上運行 |
| 控制 | 2 Task Card | ✓ | 高 | 35 張卡 + template + `validate_task_card.py` 硬驗 |
| 控制 | 3 Planner/Router | ✓ | 中 | `ROUTING_RULES.md` 為 NL 規則，無自動路由量測 |
| 控制 | 4 Decision Log | ✓ | 中 | template 在；7 筆 decisions（多 project glob） |
| 執行 | 5 Context Manager | ✓ | 中 | 3K/1.5K 硬限制；`check_context_budget` 有 CI 但屬症狀補丁 |
| 執行 | 6 Skill Executor | ✓ | 中 | 5 skills 各有 SKILL.md+eval；prompt 區隔非執行隔離 |
| 執行 | 7 Tool Executor | ✓ | 中高 | allowed_tools 白名單；**Bash deny 已有 runtime hook**，Edit/Write 未覆蓋 |
| 執行 | 8 Gate Verifier | ✓ | 中 | 4 層 gate 為 NL checklist；僅 schema 層有硬腳本 |
| 執行 | 9 Checkpoint | ✓ | 中 | git commit；hash 需**人工另一筆 commit 回填**（脆弱，見 §4-F2） |
| 治理 | 10 Agent Context | ✓ | 高 | `AGENT_CONTEXT.yaml` self-identity 清楚 |
| 治理 | 11 Permission | ✓ | 中高 | deny 有 `permissions_guard.py` 落地（A1） |
| 治理 | 12 Approval Policy | ✓ | 中 | 無 timeout、無批次審查、無信任分級 |
| 治理 | 13 Cost Policy | ✓ | 中 | 校準表存在但**創卡時仍人工套用**（本 session 手動套 ops 1.56 即證） |
| 治理 | 14 Failure Taxonomy | ✓ | 中低 | 14 種為文獻分類，無 `observed_count` 計數 |
| 治理 | 15 Execution Log | ✓ | 低 | D006 收斂後 `logs/runs/` 僅 1 筆，schema 幾乎未被行使 |
| 治理 | 16 Audit Log | ✓ | 中 | 31 筆；`generate_audit_log.py` 在，但實務仍**人工手寫**（本 session 即手寫） |

> 結論：**檔案層 16/16 齊全**；多數模組停在「中」——規格存在，但 enforcement / 自動量測 / 實證樣本不足以讓它「自己運作」。

---

## 2. 自 2026-05-02 以來的進展（既有 10 缺點逐項）

| # | 0502 缺點 | 現況 | 證據 |
|---|----------|:---:|------|
| ① | 規格≠執行（無 runtime hook） | **部分解** | `.claude/settings.json` 已掛 `permissions_guard.py` PreToolUse，攔 Bash deny（rm/email/webhook/payment/force-push）。**但 Edit/Write 無對應 layer**，gate 仍 NL 自檢 |
| ② | 實證樣本貧乏 | **部分解** | AUDIT_LOG 約 15→**31** 筆（近倍增）；但 `logs/runs/` 仍 1 筆、analysis 校準樣本仍 0 |
| ③ | 觀測性不對稱 | **部分解** | `generate_audit_log.py`、`governance_metrics.py`（+各自測試）已建；但 AUDIT_LOG 實務仍人工寫、指標未進 `data.json` 運算視圖 |
| ④ | 學習迴路開環 | **部分解** | governance metrics 自動化骨架在；校準係數**仍人工查表套用**、retro 仍人工觸發 |
| ⑤ | 單代理天花板 | **未解（遷移中）** | v3 外掛抽取進行中（n06/n11 `in_progress`、plugin-switch `pending`）→ 半遷移狀態本身是不完整 |
| ⑥ | HITL 瓶頸 | **部分解** | `create_task_card` ask→allow（好）；但 18/35 卡塞 `review` 是活體瓶頸 |
| ⑦ | 前端只是裝飾 | **未解** | 仍唯讀 `data.json` 視圖，無建卡/批准/中止控制面（Phase C 未啟動） |
| ⑧ | 無 e2e 流程驗證 | **已解** | `tests/e2e/test_dummy_task_smoke.py` 存在且進 CI（走 4 gate 契約） |
| ⑨ | 成本只是建議值 | **未解** | `max_*` 仍 self-policed，無 budget kill switch |
| ⑩ | 跨 session handoff 靠 git log | **未解** | 無結構化 resume point |

**淨評**：0502 最高槓桿的 Phase A 已落地 2/4 關鍵項（A1 hook、A3 e2e；A2 audit 生成器有骨架）。Phase B/C 大多未動，**根因型缺點（規格≠執行、開環、前端非控制面）仍在**。

---

## 3. 現存缺點（依嚴重度）

### 嚴重 — 結構性

1. **規則靠自律，硬 enforcement 覆蓋面窄**：`permissions_guard.py` 只攔 Bash；Edit/Write/外發判斷、4 層 gate、成本上限全靠 LLM 自我遵守。規格存在 ≠ 規格被執行。
2. **學習迴路仍開環**：本 session 親身證實——建卡時需**人工**查 COST_POLICY 套 ops 校準 1.56；AUDIT_LOG **人工**手寫。measure→adjust 的 adjust 環節無自動化。
3. **graduation/閉環在實務上沒發生**：18/35（51%）卡停 `review`、drafts 24 : reports 2、`logs/runs/` 1 筆。0502 那張分析自己的卡（`2026-05-02_phase-a…`）至今也還是 `review`——機制存在但流程不收斂。

### 中 — 流程脆弱（本 session 第一手證據）

4. **`frontend/data.json` drift footgun（F1，親歷）**：generator 序列化 `status` 等欄位；任何卡狀態變動未重生 data.json → CI `validate-spec` 紅。本 session **一個任務內踩兩次**（新卡未入 data.json；status pending→done 未重生）。只在 CI 攔、無 pre-commit/自動重生 → 對「自主跑 PR 迴圈」是反覆絆腳石。
5. **checkpoint hash 人工回填（F2，親歷）**：hash 需在第二筆 commit 補回 Task Card，是易錯儀式（雖因 `checkpoints` 未被序列化而不致 drift）。
6. **PR 事件迴圈會被過時 re-run 誤導（F4，親歷）**：舊 commit 的失敗 run 被重跑，對已被取代的 commit 發 failure webhook；需主動比對 HEAD 才能判定「無需處置」。自主迴圈若不做此比對會誤修。

### 低 — 工具品質

7. **觀測工具用 grep 而非解析 YAML**：Task Card template/尾註的 inline comment 會污染樸素 status 掃描（本次盤點即見「done # pending→…」雜訊）。治理量測應 parse YAML。
8. **`FAILURE_TAXONOMY` 無 `observed_count`**：14 種仍是文獻分類，無法用實證淘汰/加權（0502 已指出，未動）。

---

## 4. 已知事實 / 合理推論 / 待驗證 / 高風險假設

- **已知事實**：16 模組檔案齊全；35 卡狀態分布（done~12 / review 18 / in_progress 2 / pending 2）；AUDIT_LOG 31 筆；`logs/runs/` 1 筆；reports 2 / drafts 24；`permissions_guard.py` 已掛 PreToolUse；e2e smoke 在 CI；本 session PR #79 兩次 data.json drift 為實測。
- **合理推論**：review 大量堆積 = draft→report graduation 流程依賴人工且少被執行（與 0502「開環」一致）；校準/retro 仍人工（本 session 親證手動套用）。
- **待驗證**：A4（budget kill switch）、跨 session resume point 是否在他處實作（本次未見證據，標 [待驗證]）；`generate_audit_log.py` 是否已實際取代手寫（本 session 觀察為「仍手寫」，需多筆樣本確認）。
- **高風險假設**：若假設「規格寫了 = 行為會遵守」——本 session 的 drift 兩連踩正好反證；自主化程度越高，此假設越危險。

---

## 5. 建議下一步（依槓桿排序）

1. **把 data.json 重生變成 pre-commit hook 或 Task Card 收尾步驟**（解 F1，最低成本、立即止血；本 session 已用「狀態定稿後才重生並單一 commit」手動規避，應制度化）。
2. **review→done / draft→report 設一個收斂機制**：例如 retro 時批次 graduation，或 Stop hook 提示「N 張卡停在 review > X 天」（解缺點 3、⑥）。
3. **建卡時自動套 calibration_factor**（B2，解缺點 2/④）：讀 COST_POLICY 表自動調 `max_*`，消滅人工查表。
4. **擴大 runtime hook 到 Edit/Write 或關鍵 gate**（解缺點 1/①），縮小「規格≠執行」面積。
5. **收斂 v3 外掛遷移**（解⑤）：n06/n11/plugin-switch 是半遷移狀態，建議排定收尾或明確凍結，避免長期雙軌。
6. 觀測工具改 parse YAML（解缺點 7）；`FAILURE_TAXONOMY` 加 `observed_count`（解⑧）。

---

## 6. 四層 Gate 驗證

| Gate | 結果 | 說明 |
|------|:---:|------|
| schema_check | ✅ pass | `validate_task_card.py` exit 0 |
| rule_check | ✅ pass | 工具皆白名單內；純讀取+草稿，無 deny 動作；未改 system/skills/memory；web search 0 |
| completion_check | ✅ pass | DoD 6 條逐條對應（完整度評估/進展逐項/缺點分級+第一手證據/四象限/建議/gate+audit） |
| risk_check | ✅ pass | 實際動作 = 唯讀+草稿，與 risk=low 一致；輸出於 outputs/drafts/，無對外動作 |

**狀態：done**（low、checkpoints<3 → 依 EXECUTION_LOG_SCHEMA 免寫 logs/runs/，記入 AUDIT_LOG）。
