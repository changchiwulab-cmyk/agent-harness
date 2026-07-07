# 自我評估與優化規劃 — 正式報告（harness-self-assessment-v1）

---

## 晉升標記

| 項目 | 內容 |
|------|------|
| **原始 draft** | `outputs/drafts/2026-05-29_harness-self-assessment.md` |
| **晉升日期** | 2026-05-29 |
| **晉升任務** | Task Card `20260529-002`（tasks/2026-05-29_promote-self-assessment.yaml） |
| **審閱者** | 人工確認（使用者於本 session 明確要求晉升） |
| **原始產出日期** | 2026-05-29 |
| **原始任務** | Task Card `20260529-001`（tasks/2026-05-29_harness-self-assessment.yaml） |

### 採納項目清單

| # | 項目 | 狀態 | 追蹤 |
|---|------|:----:|------|
| 1 | 雙軸 1-10 評估（綜合 ≈7/10、成熟度 3）作為正式基線 | ✅ 採納 | 本報告 §二 評分卡 |
| 2 | 校正 3 項原始盤點誤判，以本報告為準 | ✅ 採納 | 本報告 §一 |
| 3 | R1–R10 優化 roadmap 列為正式 backlog | ⏳ 待執行 | 各項另立 Task Card；改 `system/` 走 ask |
| 4 | 單一最高槓桿動作＝R5 故障演練 | ⏳ 建議優先 | 待排程 |

### 未觸發 v3 升級
本報告為評估性質，未變更任何 `system/` 檔；`NATIVE_OVERLAP` aggregate 維持 30%（< 50% 閾值），不觸發 v3。

---

以下為原始草稿全文保留（除上方「晉升標記」為新增，其餘未變動）。

---

# Agent Harness v2 — 自我評估與優化規劃方案

> **草稿（draft）** ｜ 日期：2026-05-29 ｜ Task Card：`20260529-001` ｜ skill：review
> 交付範圍：**只評估 + 規劃，不修改 `system/`**。R1–R10 為後續各自獨立 Task Card 的提案。
> 審閱通過後可依 `RETRO_FLOW` 晉升至 `outputs/reports/`。

---

## 摘要

| 項目 | 結論 |
|------|------|
| **綜合評等** | **≈ 7 / 10** |
| **成熟度等級** | **3（生產前）**，逼近 4 但卡在「設計完備、關鍵路徑未實證」 |
| **業界十維平均** | 7.2 / 10（招牌：安全 9、治理 9；短板：可觀測 6、耐久 6） |
| **馬鞍工程六原則平均** | 7.0 / 10（最高：驗證集中化 9；最低：執行紀錄結構化 5） |
| **單一最高槓桿動作** | **R5 故障演練**——把成熟度從 3 推到 4 的關鍵，且一次驗證 errors/runs/approvals 三條紀錄路徑 |

**研究方法**：2 個探索 agent（深度盤點本專案 ＋ 研究開源框架最佳實踐）＋ 1 個 Plan agent（roadmap 設計）＋ 親自校準原始檔（README、GLOBAL_RULES、GATE_POLICY、NATIVE_OVERLAP、COST_POLICY、RETRO_FLOW、APPROVAL_POLICY、EXECUTION_LOG_SCHEMA、CI workflow、logs/）。

**關於「馬鞍原理」**：經獨立查證，agent/系統設計領域**沒有**「saddle principle」這個既定術語（最接近的只有數學/賽局的 saddle point 鞍點＝多目標均衡點）。但 `README.md` 版本表已把每次升級的觸發寫成「**馬鞍工程原則**」——這是本專案**自家的設計哲學**。因此本評估採**雙軸**：(A) 業界十維最佳實踐；(B) 馬鞍工程六原則的自我一致性。

---

## 一、盤點校正（先把題目修對）

| # | 原始描述 | 實地查核 | 影響 |
|---|---------|---------|------|
| 1 | `logs/approvals/` 不存在 | **存在但只有 `.gitkeep`（0 筆紀錄）**，且被 `check_spec_consistency.rb:43` 與 CI 強制存在性檢查。真正問題：`APPROVAL_POLICY.yaml` 無紀錄格式；批准資料散在 3 處（AUDIT_LOG 內嵌／EXECUTION_LOG 的 `approvals:` 區塊／空的 approvals 目錄）。RETRO 指定讀的目錄永遠是空的 | 不是「建目錄」，是「定 schema＋坐實單一資料源」 |
| 2 | `logs/runs/` 只 1 筆、恢復路徑未實測 | 屬實。唯一 1 筆是 `completed` 的 system-validation，`token_estimate` 三欄全 0 | 成立，中期核心 |
| 3 | analysis eval 豐富度不如 research | **不成立**：`analysis/eval_examples.md`（115 行）反而最長。但 **analysis 成本校準樣本＝0** 屬實（`COST_POLICY.md:81`） | 重新聚焦為「成本校準」，不浪費力氣補 eval |
| 4 | NATIVE_OVERLAP 重疊偏高 | 屬實：aggregate 30%，Skill 85%／Tool 80%／Permission 75%；已設 >50% 觸發 v3 | 成立，長期戰略 |
| 5 | CI 未確認跑一致性檢查 | **已確認有跑**，且 CI 很強（~12 道關卡：Ruby 單元測試、spec 一致性、YAML 解析、context budget、frontend manifest 漂移 `--check`、permissions guard 測試、audit log 產生器測試、E2E smoke test） | 改為「擴充 CI 檢查面」 |
| 6 | D001–D005 缺 revisit 機制 | 屬實：每筆 decision 都有 `revisit_trigger` 欄位，但無任何掃描/提醒機制 | 成立，中期 |

---

## 二、1-10 評分卡

### A 軸 — 業界十維最佳實踐

| # | 維度 | 分數 | 依據（強項 / 扣分點） |
|---|------|:---:|------|
| 1 | 可靠性 Reliability | **7** | 有 circuit breaker（連續失敗 3 次停）、14 種 FAILURE_TAXONOMY、四層 GATE。但真實故障從未跑過，可靠性是「設計完備、未經實證」 |
| 2 | 可觀測性 Observability | **6** | 工具層（AUDIT_LOG、permissions_guard hook、CI、frontend 看板）紮實；但工作流層（gate 通過率、卡關）與業務層（每 skill 成本/品質趨勢）缺 |
| 3 | 安全性 Safety | **9** | deny-by-default 權限＋`permissions_guard.py` runtime hook＋對外只產草稿＋不自動 shell/外發＋四級風險。對照 Least Privilege / Zero Trust，最強項 |
| 4 | 可擴展性 Extensibility | **7** | 5 skill 結構一致＋skill 模板＋v1→v4 版本路線；但單代理、且高原生重疊可能讓部分抽象變冗餘 |
| 5 | 成本效率 Cost-Efficiency | **7** | **實測**校準係數（research 1.43／writing 2.00／ops 1.56／review 1.25）是真資產；扣分：analysis=0 筆、樣本少、run 級 token 全 0 |
| 6 | 開發者體驗 DevEx | **8** | README 完整、結構清晰、模板齊、`run_frontend.sh` 有 `--help/--version`、3 步上手；CLAUDE.md boot prompt 精煉 |
| 7 | 耐久性 Durability | **6** | git checkpoint 慣例＋GATE 有 rollback 定義；但 checkpoint 還原從未實測、無 recovery runbook、冪等性未明確處理 |
| 8 | 可審計性 Auditability | **7** | AUDIT_LOG（20–30 筆）＋7 筆決策日誌＋git 歷史＋CI schema 守護；扣分：批准紀錄無 schema 且分散、執行紀錄稀疏 |
| 9 | 效能 Performance | **6** | 對個人 harness 非重點（延遲/吞吐刻意不優化，見「現階段不做清單」）；context 預算控制到位。屬「刻意 out of scope」，非缺陷 |
| 10 | 治理成熟度 Governance Maturity | **9** | 12 個治理檔＋三平面架構＋approval/gate/failure/cost/native-overlap/retro 全套。以個人專案而言罕見的成熟，真正的招牌 |

**A 軸平均 ≈ 7.2 / 10**

### B 軸 — 馬鞍工程六原則的自我一致性

| 原則（出處 `README.md` 版本表） | 分數 | 說明 |
|------|:---:|------|
| 驗證集中化 | **9** | GATE_POLICY 四層（schema→rule→completion→risk）集中且每層有 on_fail＋rollback |
| 系統自知 | **8** | AGENT_CONTEXT.yaml＋NATIVE_OVERLAP 自評（連「我跟原生重疊多少」都量化） |
| 決策可追溯 | **7** | 7 筆結構化決策日誌（D001–D007）；扣分：有 `revisit_trigger` 欄位卻無回看機制 |
| 批准流程獨立化 | **6** | APPROVAL_POLICY 已獨立成檔 ✓；但無紀錄 schema＋專屬目錄空＋資料散 3 處 |
| 失敗模式可引用 | **7** | FAILURE_TAXONOMY 14 種、各有 mitigation；扣分：尚未連結到任何真實事件實例 |
| 執行紀錄結構化 | **5** | EXECUTION_LOG_SCHEMA 設計良好（D006 收斂條件合理）；但只 1 筆、token 全 0、從未在失敗下被填過 |

**B 軸平均 ≈ 7.0 / 10**

### 綜合判定

> **總分 ≈ 7 / 10。成熟度等級 3（生產前），逼近 4 但卡在同一句話：「設計完備，但關鍵路徑未經實證」。**

天花板不是「再加功能」，而是「**把既有設計實測一遍＋全程可觀測＋schema 守住**」。

---

## 三、最大優點（招牌，務必保留）

1. **治理即代碼，且自洽**：硬規則（無 Task Card 不執行／對外只草稿／3 次失敗即停）＝業界 Circuit Breaker＋Dry-Run/Staging＋Human-in-the-Loop 的集合體，且用 `permissions_guard.py` 把 deny 抬到 runtime。
2. **實測驅動的成本控制**：校準係數是真數據不是猜測，多數開源框架只談 token budget，少有人持續回測校準。
3. **異常誠實的自知**：NATIVE_OVERLAP 主動承認「我有 30% 跟 Claude Code 原生重疊、Skill 模組高達 85%」並預設 >50% 就觸發重構——成熟的自我淘汰機制。
4. **失敗可分類、決策可追溯**：14 種失敗分類學＋結構化決策日誌，是知識資產化的正確方向。

---

## 四、缺點 / 落差（校正後，按嚴重度）

1. **失敗→恢復閉環從未實證**（弱點 2）— 最關鍵。所有恢復設計都是紙上談兵。
2. **批准資料「三個家」結構性不一致**（弱點 1）— 無 schema、專屬目錄空、RETRO 讀空目錄。
3. **可觀測性只到工具層**（新發現）— 工作流層/業務層指標缺，無法回答「哪層 gate 最常失敗」「哪類任務成本在漲」。
4. **checkpoint 還原與災難恢復無 runbook 且未演練**（弱點 2 延伸）。
5. **analysis 成本校準空白**（弱點 3 重新聚焦）。
6. **決策/重疊有觸發欄位卻無回看機制**（弱點 4、6）。

---

## 五、優化 Roadmap（R1–R10）

**落地通則（每項都遵守你自己的規則）**：每個 R 項目先開一張 Task Card（硬規則 1）→ 產出先進 `outputs/drafts/`（硬規則 2）→ 改 `system/`／`skills/` 走 `ask`（列 diff 後人工確認）→ 寫 `logs/` 屬 `allow`。

### 短期（1 週）— Quick wins：補可審計性、防漂移

| ID | 項目 | 解決 | 動作（檔案層級） | impact/effort/risk |
|----|------|:---:|------|:---:|
| **R1** | 批准紀錄 schema 化＋首筆回填 | #1 | `APPROVAL_POLICY.yaml` 加 `approval_record` 段（欄位對齊 `EXECUTION_LOG_SCHEMA.yaml:48-52`）；`logs/approvals/` 放 template；把 `logs/runs/20260409-001` 的 2 筆批准獨立成首個真實樣本；`RETRO_FLOW.md:23` 註記 schema 位置 | 高/低/低 |
| **R2** | CI 擴充：logs schema lint | #5,1,2 | 擴充 `scripts/check_spec_consistency.rb`：驗 `logs/runs/*`、`logs/approvals/*`、`logs/errors/*` 必填欄位與枚舉；同步加 `test_check_spec_consistency.rb`（workflow 已跑，免改） | 高/低/低 |
| **R3** | analysis 成本校準補樣本 | #3 | 開 1–2 張真實 analysis 任務 → 記 token → 下次 RETRO 填入 `COST_POLICY.md:61,81` 兩張表 | 中/低/低 |
| **R4** | 決策 revisit 追蹤 | #6 | 新增唯讀 `scripts/check_decision_revisit.rb`（掃 decisions、比對觸發、標「待回看」）；`RETRO_FLOW.md:27` 分析維度加一列 | 中/低/低 |

### 中期（2–4 週）— 把「恢復」與「可觀測」做實（成熟度 3→4 主幹）

| ID | 項目 | 解決 | 動作 | impact/effort/risk |
|----|------|:---:|------|:---:|
| **R5** | **故障演練：實測失敗/partial 紀錄路徑** | #2 | 開一張刻意可控失敗的演練 Task Card，走完整 schema fail→重試 1 次→停；驗證 `logs/errors/`＋`logs/runs/`（`status: failed`）＋（如涉及）`logs/approvals/` 三處同時被坐實；固化成 `tests/e2e/` 失敗路徑 smoke | 高/中/中 |
| **R6** | EXECUTION_LOG token 量測坐實 | #2,3 | `EXECUTION_LOG_SCHEMA.yaml` 的 `token_estimate` 加「來源」欄；之後 run log 必填非零 token；與 R3 串接餵回校準 | 中/中/低 |
| **R7** | 觀測工作流層/業務層補強 | 新 | 擴 `scripts/governance_metrics.py`：四層 gate pass 率、每 skill 趨勢、對照 FAILURE_TAXONOMY 14 類實際命中；接到 `frontend/` 新增「治理成熟度」面板 | 高/中/低 |
| **R8** | 災難恢復 runbook＋checkpoint 還原實測 | #2 | 新增 `RECOVERY_RUNBOOK.md`（對應 COORD-01/SPEC-03）；在 R5 演練中途模擬中斷，依 runbook 從 checkpoint 還原並記步驟/耗時；與 GATE_POLICY rollback 交叉引用 | 高/高/中 |

### 長期（季度級）— 原生重疊治理與 v3 戰略

| ID | 項目 | 解決 | 動作 | impact/effort/risk |
|----|------|:---:|------|:---:|
| **R9** | NATIVE_OVERLAP 季度 revisit 自動化 | #4 | 把逐模組重評納入季度 RETRO；`governance_metrics.py` 加：讀 `aggregate_estimate_pct`，>40% 預警、>50% 觸發 v3 評估建議；與 R4 合流 | 中/中/中 |
| **R10** | v3 遷移就緒度評估 | #4 | 產 `outputs/drafts/v3-readiness-assessment.md`：逐模組標「保留/下放原生/並存」，明確不可替代資產（校準表、FAILURE_TAXONOMY、Decision/Audit 紀錄）；對齊既有 `2026-05-09_v3_extraction_plan.md`，更新 D003/D007。**只評估不遷移** | 中/高/高 |

### 相依性與排程

```
週1（quick wins，大致並行）：R1 ┐  R3  R4（皆獨立）
                                  └→ R2（需 R1 的 schema）
週2-4（核心，強相依）：R2 → R5 ┬→ R6（token 坐實）
                               ├→ R7（需 run/gate 樣本）
                               └→ R8（需可中斷任務）
                       R3 ─────→ R6
季度（戰略）：R4 + R7 → R9 → R10
關鍵路徑：R1 → R2 → R5 → (R7/R8)  ＝ 推到成熟度 4 的主幹
```

### 成熟度 3 → 4（生產前 → 生產級）缺口對照

| 缺口 | 生產級要求 | 現況 | 補齊項 |
|------|----------|------|------|
| 災難恢復實測 | 有 runbook 且演練過 | 機制有、未還原過 | **R8**（+R5） |
| 失敗路徑驗證 | 真實故障下跑過 post-mortem | run log 僅 1 筆 completed | **R5** |
| 全可觀測（三層） | 工具+工作流+業務皆有指標 | 僅工具層 | **R7** |
| 批准/成本可審計 | schema 化、可回溯、無漂移 | 批准無 schema、analysis 空白 | **R1、R3、R6** |
| 規格防漂移自動化 | 全 schema 由 CI 守 | logs 三類未守 | **R2** |
| 決策/重疊定期回看 | 有 revisit 追蹤 | 有欄位無機制 | **R4、R9** |

> 簡言之：成熟度 4 的門檻不是再加功能，而是把既有設計「實測一遍 + 全程可觀測 + schema 守住」。短期 R1/R2/R3 補可審計性與防漂移，中期 R5/R6/R7/R8 補失敗實測與全觀測，即可宣稱達生產級；長期 R9/R10 處理與原生平台的長期共存與 v3 戰略。

---

## 六、後續

- 本評估只產草稿，**未修改任何 `system/` 檔**。R1–R10 維持提案。
- 你決定要做哪些後，每個項目各自開一張 Task Card；改 `system/`／`skills/` 會走 `ask`（列 diff 後人工確認），產出先進 `outputs/drafts/`。
- **建議第一步＝R5 故障演練**：它是把成熟度從 3 推到 4 的單一最高槓桿動作，並一次驗證 errors/runs/approvals 三條紀錄路徑。
- 本草稿經人工確認後，可依 `RETRO_FLOW` §5 晉升至 `outputs/reports/`。

---

### 來源（業界最佳實踐對照）

- Anthropic — Building Effective AI Agents / Building agents with the Claude Agent SDK
- LangGraph、OpenAI Agents SDK、Microsoft Agent Framework、CrewAI、HuggingFace smolagents、Dify
- 設計模式：Circuit Breaker、Least Privilege / Zero Trust、Human-in-the-Loop Gates（Advisory/Validating/Blocking/Escalating）、Durable Execution / Checkpointing、Token Budget / Context Compaction、Dry-Run / Staging
- 評估維度與成熟度等級 1–5：取自業界 agent 可靠性/可觀測性/評估框架文獻

---

## Addendum — 2026-06-09 優化回寫（task 20260609-001）

> 本段為 addendum，**不改寫上方歷史分析**。記錄 self-assessment 後續落地進度與 2026-06-09 這輪優化。

### 已落地：R1–R8（§五 roadmap）
git 歷史顯示 R1–R8 已全數 ship（approval schema / logs lint / analysis cost sample /
decision-revisit tracker / failure drill / token source / observability metrics + frontend /
recovery runbook）。其中 **R5 故障演練**（§五「單一最高槓桿動作」）已完成，
`logs/runs/RUN-20260529-003.yaml`（status: failed）+ `tests/e2e/test_failure_drill.py` 坐實了失敗紀錄路徑。

### 2026-06-09 這輪：把宣稱的硬規則變成 deterministic 強制
針對 plan `ai-bubbly-mountain.md` §3.1「強制力結構不對稱」與 §3.6「gate 未自動化」：

| 三條硬規則 | 2026-05 之前強制力 | 2026-06-09 後 |
|-----------|------------------|---------------|
| 沒有 Task Card 不執行 | 0%（純 prompt） | **正式產出硬制**：`scripts/task_card_guard.py` 擋無對應卡片的 `outputs/reports/` 新檔；`drafts/` 探索仍 prompt（刻意，避免 §3.3 為 1% 替 99% 上鎖） |
| 對外動作只產草稿 | 30%（Bash egress） | Bash egress（`permissions_guard.py`）**＋** reports/ 守門：正式產出須走 draft→review→promote |
| 連續失敗 3 次停下 | 0%（無計數器） | **有計數器 + halt hook**：`scripts/failure_counter.py` 達 3 次後 block 後續工具，直到 `--reset`；惟「記錄失敗」動作本身仍 best-effort |

- **GATE 自動化**：新增 `scripts/gate_check.py`，把 GATE_POLICY 四層（schema/rule/completion/risk）做成 post-execution validator（L1 重用 validate_task_card；L2 比對 run log tools；L3 驗產物存在；L4 驗 drafts 收斂）。三支新元件各有單元測試並納入 CI。
- **狀態漂移校正**：`memory/.../context.md`（停在 2026-04-15）與 `README.md` 同步至 2026-06-09 現況。
- 殘餘 prompt-only（誠實標註）：drafts 階段的 Task Card 約束、ask 等級人工確認、以及失敗的「判定與記錄」仍依賴 Claude 遵循 CLAUDE.md —— 這是「用 LLM 約束 LLM」的結構性天花板，非本輪可消除。
