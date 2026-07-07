# Agent Harness v2 — 依最新 AI 架構補齊缺口（彙整草稿）

> **草稿（draft）** ｜ 日期：2026-06-30 ｜ Task Cards：`20260630-G01..G04` ｜ skill：ops
> 交付方式：嚴格走 harness 流程。`system/` / `skills/` 變更全在本草稿 PR 供 review，**未 merge**。
> 本草稿是 PR 的人工審閱 companion，逐項對齊 plan `workflow-ai-synchronous-parnas`。

## 為什麼做

使用者要求「完整檢視專案，依專案走向 + 最新 AI 公開架構發展，補齊缺的架構」。
前兩份自評（2026-05-02、2026-05-29）已盤點**內部**缺口（R1–R10 多已落地）。本次差異化＝
把 **2026 年中最新公開 AI 架構標準**對齊到本專案，補上前兩份未涵蓋、且符合
「**深化治理（治理層更厚）**」走向的缺口。原則：深化三支柱（安全／可量化／可恢復），
**不堆功能**；每條新規則都綁一個 enforcement 點（J5）。

## 四個缺口 → 對齊的最新架構

| 缺口 | 2026 公開架構依據 | 支柱 |
|------|------------------|------|
| **G-A** 輸入側防護 | OWASP LLM01（prompt injection 連三年第一）；RAG/tool poisoning | 安全 |
| **G-B** 可執行 eval 閉環（含 G-E 觀測對齊） | eval-driven development；LLM-as-judge 對齊 gold set；OTel GenAI 語意慣例 | 可量化 |
| **G-C** Context Engineering 規範 + 工作筆記 | Anthropic context engineering（組裝順序/JIT/structured note-taking） | context 紀律 |
| **G-D** 跨 session resume | durable execution / agentic resume point | 可恢復 |

## 各缺口交付物（檔案層級）

### G-A — 輸入側防護（安全）
- `system/INPUT_GUARDRAILS.md`：檢索/外部內容是**資料不是指令**；`[未受信任來源]` 標記；交叉驗證。
- `FAILURE_TAXONOMY.yaml`：+ SEC-05（間接注入）、SEC-06（工具/檢索輸出污染）。
- `GATE_POLICY.yaml` rule_check + 輸入面檢查；`skills/research/SKILL.md` + 不受信任內容段。
- **enforcement**：`scripts/check_untrusted_content.py`（偵測器 + CLI）+ `scripts/test_*`；`tests/e2e/test_input_guardrails.py` + 注入 fixture。
- 補的盲點：安全自評 9/10 但**全出口導向**；harness 實際吃 web/外部內容卻零輸入防護。

### G-B — 可執行 eval 閉環（可量化）＋ G-E 觀測對齊
- `evals/<skill>/*.yaml`（research、analysis 各 1，含 gold/bad 校準對，rubric 對齊 `eval_examples.md`）。
- `scripts/run_evals.py`：**rule judge（CI-safe）** + **LLM-judge 擴充點**；**校準模式**（gold 須 PASS、bad 須 FAIL）。
- `scripts/test_run_evals.py`；`evals/README.md`（與 GATE_POLICY 人工、governance_metrics 操作型**明確分工**）。
- **G-E**：`EXECUTION_LOG_SCHEMA.yaml` + optional `gen_ai.*` 區塊，對齊 OTel GenAI 語意慣例（可攜、向後相容）。
- 補的盲點：`eval_examples` 是散文、不可執行；既有觀測只量「操作」不量「產出品質」。

### G-C — Context Engineering（context 紀律）
- `system/CONTEXT_ENGINEERING.md`：組裝順序、JIT 檢索、結構化 scratchpad、子任務 context 隔離。
- `GLOBAL_RULES.md` + `memory/README.md`：**三層記憶**（短期／工作筆記 scratchpad／長期），
  scratchpad = `outputs/drafts/<task_id>-scratchpad.md`（allow，任務範圍，**非**長期記憶，不違反 deny）。
- 防冗餘：明標「原生已做（自動壓縮等）不重造」，只寫原生未做的紀律（呼應 NATIVE_OVERLAP）。

### G-D — 跨 session resume（可恢復）
- `state/last_checkpoint.SCHEMA.yaml` + 首個真實樣本（dogfood）。
- `check_spec_consistency.rb` + `state/*.yaml` schema lint（跳過 SCHEMA/TEMPLATE）+ 測試常數。
- `RECOVERY_RUNBOOK.md` 場景 C 交叉引用 state/ 為**主動**接續點（既有 runbook 是**被動**崩潰復原）。
- 補的盲點：弱點⑩——正常跨 session 接續只能靠 git log 回想。

## 與專案走向的一致性檢查

- **深化治理非堆功能**：4 缺口分別加厚安全/可量化/可恢復/context 四面，皆對齊路線 2「治理層更厚」。
- **J5（每條規則綁 enforcement）**：G-A→偵測器+e2e；G-B→run_evals 校準+test；G-D→spec lint+test；G-C→context budget。
- **不碰「不做清單」**：未引入 multi-agent swarm、未自動外發、未自動長期記憶寫入。
- **遵守自身硬規則**：先建 4 張 Task Card（rule 1）；對外/正式變更走草稿 PR（rule 2）；`modify_system_rules` 走 ask（PR review）。

## 驗證（全綠）

CI-equivalent 全套通過：Ruby 單元測試、spec 一致性（含新 state lint）、YAML 解析、context budget（1354/3000）、
frontend manifest 漂移 `--check`、permissions guard、audit log 產生器、E2E（dummy / failure-drill / **input-guardrails**）、
decision revisit；新增 `test_run_evals.py`、`test_check_untrusted_content.py`、`run_evals.py` 校準。

## 後續（待人工）

1. Review 本 PR；確認 `system/` / `skills/` 4 處新增 + 多處修改方向無誤後 merge。
2. 新 enforcement 已納入 `.github/workflows/spec-consistency.yml`（G-A 偵測器/e2e、G-B runner/校準 4 個 step）。
3. 本草稿經確認後可依 `RETRO_FLOW` 晉升 `outputs/reports/`。
