# Agent Harness v2 — 完整重評分 v2 ＋ 最新 AI 技術對標

> **草稿（draft）**｜日期：2026-06-20｜Task Card：`20260620-001`｜skill：review
> 交付範圍：**評估 + 規劃 + 低風險 quick-win 實作**。本報告只評估；實作走各自 Task Card（見 §六）。
> 審閱通過後可依 `RETRO_FLOW` §5 晉升至 `outputs/reports/`。

---

## 摘要

| 項目 | 結論 |
|------|------|
| **綜合評等** | **≈ 7.6 / 10**（v1 為 7.0） |
| **成熟度等級** | **逼近 4（生產級）**，已從「設計完備、關鍵路徑未實證」推進到「關鍵路徑已實測、最新技術軸未補」 |
| **A 軸 業界十維** | 7.8 / 10（招牌：安全 9、治理 9；已上修：可觀測 8、耐久 8、可靠 8） |
| **B 軸 馬鞍六原則** | 7.8 / 10（執行紀錄結構化由 5 → 7：R5 真實失敗已坐實） |
| **C 軸 2026 最新 AI 技術（新增）** | **5.9 / 10**——本次最大落差與最高槓桿所在 |
| **單一最高槓桿動作** | **L1 最新模型路由 + prompt caching**：成本與快取是 v1 完全沒碰、業界 2026 標配的軸 |

**自 v1（2026-05-29）以來**：R1–R8 已全數落地，v1 列為「推到成熟度 4 主幹」的失敗實測（R5）、災難恢復演練（R8）、三層觀測（R7）、批准/token schema（R1/R6）皆已關閉。本次重評因此把可靠/可觀測/耐久/可審計四維上修，並**新增 C 軸**反映使用者「對標最新公開 AI 技術」的要求——這是 v1 報告未涵蓋、且分數最低的一軸。

---

## 一、自 v1 以來的 Delta（R1–R10 現況）

| ID | 項目 | 現況 | 對分數影響 |
|----|------|------|-----------|
| R1 | 批准紀錄 schema 化 | **已關閉** `logs/approvals/` 有 template + 首筆真實樣本 | 可審計 7→8 |
| R2 | CI logs schema lint | **已關閉** `check_spec_consistency.rb` 擴充 + CI | 防漂移成立 |
| R3 | analysis 成本校準 | **部分** 任務已開，但 `COST_POLICY.md` analysis 校準樣本仍 ≈0 | 成本仍 7 |
| R4 | 決策 revisit 追蹤 | **已關閉** `scripts/check_decision_revisit.rb` + CI | 馬鞍·決策可追溯 7→7.5 |
| R5 | 故障演練 | **已關閉** `logs/runs/RUN-20260529-003`（首筆真實 failed）+ `logs/errors/` + `tests/e2e/test_failure_drill.py` | 可靠 7→8、馬鞍·執行紀錄 5→7 |
| R6 | EXECUTION_LOG token 來源 | **已關閉** `token_estimate.source` 欄 | 可審計上修 |
| R7 | 三層可觀測 | **已關閉** `governance_metrics.py --observability`（工作流/業務/失敗）+ 前端治理面板 | 可觀測 6→8 |
| R8 | 災難恢復 runbook | **已關閉** `RECOVERY_RUNBOOK.md` + checkpoint 還原演練 | 耐久 6→8 |
| R9 | NATIVE_OVERLAP 季度自動化 | **未動** | — |
| R10 | v3 遷移就緒度評估 | **未動**（`2026-05-09_v3_extraction_plan.md` 仍為素材） | — |

> 結論：v1 的「主幹缺口」已補完，成熟度從 3 逼近 4。剩餘短板從「未實證」轉移到「**統計樣本仍薄**（run 2 筆 / approval 1 筆 / error 2 筆）」與「**最新技術軸未補**（C 軸）」。

---

## 二、三軸評分卡

### A 軸 — 業界十維最佳實踐

| # | 維度 | v1 | v2 | 依據 |
|---|------|:--:|:--:|------|
| 1 | 可靠性 | 7 | **8** | circuit breaker + 14 FAILURE_TAXONOMY + 四層 GATE，且 R5 已在真實 failed 下跑過 post-mortem |
| 2 | 可觀測性 | 6 | **8** | R7 補齊工作流層（gate 通過率/checkpoints）+ 業務層（每 skill）+ 失敗分佈；前端治理面板 |
| 3 | 安全性 | 9 | **9** | deny-by-default + `permissions_guard.py` runtime hook + 對外只草稿 + 四級風險 |
| 4 | 可擴展性 | 7 | **7** | 5 skill 結構一致；高原生重疊（Skill 85%）使部分抽象偏冗餘 |
| 5 | 成本效率 | 7 | **7** | 實測校準係數是真資產；扣分：analysis=0 筆、無 prompt caching、無 model routing |
| 6 | 開發者體驗 | 8 | **8** | README/模板齊、`run_frontend.sh --help/--version`、CLAUDE.md boot prompt 精煉 |
| 7 | 耐久性 | 6 | **8** | R8 runbook + checkpoint 還原演練（~5ms、byte-identical） |
| 8 | 可審計性 | 7 | **8** | R1 批准 schema + R6 token 來源 + 決策日誌 + CI schema 守護 |
| 9 | 效能 | 6 | **6** | 個人 harness 刻意 out of scope（見「現階段不做清單」） |
| 10 | 治理成熟度 | 9 | **9** | 14 治理檔 + 三平面 + approval/gate/failure/cost/native-overlap/retro 全套 |

**A 軸平均 ≈ 7.8 / 10**（v1 7.2）

### B 軸 — 馬鞍工程六原則

| 原則 | v1 | v2 | 說明 |
|------|:--:|:--:|------|
| 驗證集中化 | 9 | **9** | GATE 四層各有 on_fail + rollback |
| 系統自知 | 8 | **8** | AGENT_CONTEXT + NATIVE_OVERLAP 量化自評 |
| 決策可追溯 | 7 | **7.5** | R4 revisit 追蹤器補上「有欄位無機制」缺口 |
| 批准流程獨立化 | 6 | **7.5** | R1 schema + 首筆真實樣本，三處資料源收斂 |
| 失敗模式可引用 | 7 | **7.5** | R5 把 FAILURE_TAXONOMY 連到第一個真實事件 |
| 執行紀錄結構化 | 5 | **7** | R5/R6 在真實 failed 下填過 schema、token 來源坐實 |

**B 軸平均 ≈ 7.8 / 10**（v1 7.0）

### C 軸（新增）— 2026 最新 AI 技術對標

> 對標 2026-06 公開最佳實踐（來源見 §七）。打分＝**採用程度**。

| # | 技術主題 | 分數 | 現況 / 落差 |
|---|---------|:--:|------|
| 1 | Harness 驗證工具（非模型）| **9** | `permissions_guard.py` 已把 schema/deny 抬到 runtime——2026 公認的「harness 不是 prompt」核心，最強項 |
| 2 | Human-in-loop / draft-first | **9** | 對外只草稿 + 四級風險 gate，符合 blocking/escalating 模式 |
| 3 | 結構化 audit / 觀測 | **7** | audit log + `governance_metrics` 三層；缺 trace-based online scoring 迴圈 |
| 4 | Harness 安全（injection/timeout/over-tooling）| **7** | deny-by-default + runtime hook；缺對 harness 本身的注入/逾時測試 |
| 5 | Tool contracts / 冪等性 | **6** | 白名單 + deny；冪等性未明確處理（v1 已標） |
| 6 | 原生 Agent Skills 格式 | **5** | `research` 已具 frontmatter 並接 `.claude/skills/`；其餘 4 個 skill 未轉、未註冊 → 重疊 85% 未收斂 |
| 7 | Context engineering（JIT / compaction / memory-as-component）| **5** | 有路徑引用 + 「20 輪壓縮」；未形式化 JIT 載入、未明述「關鍵規則須存活壓縮」、memory 已是獨立元件但無與壓縮的契約 |
| 8 | Evals-in-CI | **5** | `eval_examples.md`（5 skill, good/bad）存在但**未**作自動 eval；CI 只守 schema |
| 9 | 最新模型路由 | **3** | `COST_POLICY.md` 僅「v2 model routing 準備」，未落地具體模型（Opus 4.8 / Sonnet 4.6 / Haiku 4.5 / Fable 5） |
| 10 | Prompt caching | **2** | 完全未涉及——2026 最大成本槓桿（快取讀 ~0.1×、可省 ~90%）缺席 |

**C 軸平均 ≈ 5.9 / 10**——明顯低於 A/B，是本次最大增量空間。

### 綜合判定

> **總分 ≈ 7.6 / 10。成熟度逼近 4。** 治理/安全/可觀測已生產級；天花板從「實測既有設計」轉為「**補上 2026 最新技術軸**——快取、最新模型路由、原生 Skills、evals-in-CI、context engineering 形式化」。

---

## 三、最大優點（招牌，務必保留）

1. **治理即代碼且自洽**：三條硬規則＝Circuit Breaker + Human-in-Loop + Dry-Run 的集合，並用 `permissions_guard.py` 把 deny 抬到 runtime——正是 2026「agent 是 harness 不是 prompt」的論點落地。
2. **實測驅動的成本控制**：校準係數是真數據（research 1.43／writing 2.00／ops 1.56／review 1.25）。
3. **異常誠實的自知**：NATIVE_OVERLAP 主動承認 30%／Skill 85% 重疊並設 >50% 觸發 v3。
4. **失敗已坐實**：R5 把 14 種失敗分類學連到第一個真實事件，run/error log 不再是紙上談兵。

---

## 四、缺點 / 落差（重評後，按嚴重度）

1. **C 軸最新技術全面落後**（新發現，最關鍵）：無 prompt caching、無最新模型路由、原生 Skills 只轉 1/5、evals 未自動化。
2. **統計樣本仍薄**：run 2 筆、approval 1 筆、error 2 筆、analysis 校準 0 筆——指標引擎已建好，缺真實流量餵養。
3. **R9/R10 未動**：原生重疊季度自動化與 v3 就緒度評估仍待做。
4. **冪等性與 context engineering 未形式化**：壓縮存活、JIT 載入只是慣例，無明文契約。

---

## 五、新優化 Roadmap（L1–L7，對標 C 軸四主題）

> 落地通則同 v1：每項先開 Task Card → 產出先進 `outputs/drafts/` → 改 `system/`/`skills/` 走 `ask`（列 diff）→ CI 綠 → checkpoint。
> **★ = 本 session 即實作的 quick-win**（見 §六）；其餘留作後續提案。

| ID | 主題 | 項目 | impact/effort/risk |
|----|------|------|:---:|
| **L1 ★** | 最新模型+成本 | `COST_POLICY.md` 落地具體模型路由表（planning/analysis/review→Opus 4.8；預設執行→Sonnet 4.6；classify/extract/lint/schema→Haiku 4.5；最難長程→Fable 5）+ prompt caching 策略；`EXECUTION_LOG_SCHEMA.yaml` 加 cache 觀測欄 | 高/低/低 |
| **L2 ★** | Context engineering | 把 JIT 載入 / 5 階段 compaction / 「關鍵規則須存活壓縮」/ memory-as-component 寫成原則段（`COST_POLICY.md`），`GLOBAL_RULES.md` 加一行指標（守住 3K 預算） | 中/低/低 |
| **L3 ★** | 原生 Skills + 降重疊 | 其餘 4 skill 補原生 frontmatter（`name`/`description`）+ 接 `.claude/skills/`；更新 `NATIVE_OVERLAP.yaml` Skill 證據 | 中/低/低 |
| **L4 ★** | Evals + 觀測 | `governance_metrics.py` 加 model 分佈（+ 預留 cache 命中）；新增 `scripts/check_skill_evals.py` 結構檢查（每 skill eval 含 good+bad）接進 CI | 中/低/低 |
| L5 | Evals 深化 | 把 `eval_examples.md` 升級為 LLM-judge 自動 eval harness（需呼叫模型，成本/CI 設計） | 高/高/中 |
| L6 | 原生 Skills 全面化 | 5 skill 全面轉原生格式 + progressive disclosure，收斂 Skill 重疊 85%→目標 <50% | 高/中/中 |
| L7 | 原生重疊治理 + v3 | 落地 R9（季度自動化）+ R10（v3 就緒度），對標 model routing/subagent 隔離決定保留/下放 | 中/高/高 |

### 相依與關鍵路徑

```
本 session（quick-win，大致並行）：L1 ┐ L3  L4
                                    └→ L2（與 L1 同改 COST_POLICY，連續做）
後續：L4 → L5（evals 深化）；L3 → L6（全面原生）；L6 + R9/R10 → L7（v3 戰略）
關鍵路徑：L1 → L4 ＝ 把 C 軸從 5.9 推向 7+ 的主幹（成本可觀測 + evals 自動化）
```

---

## 六、本 session 實作的 Quick-wins（L1–L4）

各自獨立 Task Card、draft-first、改 system/skills 列 diff、CI 綠後 checkpoint：

- **QW1 / L1**（`20260620-002`，ops）：`COST_POLICY.md` 模型路由表 + prompt caching 策略；`EXECUTION_LOG_SCHEMA.yaml` cache 欄。模型事實經 `claude-api` skill 校準（Opus 4.8 $5/$25、Sonnet 4.6 $3/$15、Haiku 4.5 $1/$5、Fable 5 $10/$50；快取讀 ~0.1×、寫 1.25×(5m)/2×(1h)、最小可快取前綴 Opus 4.8 4096 / Sonnet 4.6・Fable 5 2048 tokens）。
- **QW2 / L2**（`20260620-003`，ops）：`COST_POLICY.md` context-engineering 原則段；`GLOBAL_RULES.md` 一行指標（過 `check_context_budget.rb`）。
- **QW3 / L3**（`20260620-004`，ops）：4 skill 補原生 frontmatter + `.claude/skills/` symlink；更新 `NATIVE_OVERLAP.yaml`。
- **QW4 / L4**（`20260620-005`，ops）：`governance_metrics.py` model 分佈 + test；`scripts/check_skill_evals.py` + CI。

> **不在本 session 實作**（留 roadmap）：L5 LLM-judge eval、L6 全面原生轉換、L7 v3 遷移與外部 trace 平台。

---

## 七、後續

- 本評估只產草稿，**未修改任何 `system/` 檔**（quick-win 的 system/ 變更走各自 Task Card 的 `ask` 流程）。
- 建議第一步＝**L1**：prompt caching + 最新模型路由是 v1 完全沒碰、2026 標配、且一次拉動「成本效率 + C 軸成本/快取」兩處。
- 本草稿經人工確認後，可依 `RETRO_FLOW` §5 晉升至 `outputs/reports/`。

---

### 來源（2026 最新最佳實踐對照）

- Anthropic — Effective context engineering for AI agents（JIT context、compaction、critical rules survive compaction）
- Anthropic — Equipping agents with Agent Skills（progressive disclosure、跨 Claude.ai/Code/SDK 載入）
- Claude Agent SDK overview（六平台層：context/orchestration/security/observability/evaluation/persistence）
- AI Agent Best Practices: Production-Ready Harness Engineering (2026) / awesome-harness-engineering（permissions/evals/memory/MCP/observability）
- State of AI Agent Memory 2026（memory 為獨立架構元件）
- Agent observability: the complete guide for 2026（trace 為 durable asset；online scoring → eval case → CI gating）
- Don't Break the Cache: Prompt Caching for Long-Horizon Agentic Tasks（arXiv）
- 模型/快取事實：`claude-api` skill（current models 表、prompt-caching 規格）
- 基準：`outputs/reports/harness-self-assessment-v1.md`（v1 雙軸評分卡）
