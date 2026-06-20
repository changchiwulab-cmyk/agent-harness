> **草稿（draft）** ｜ Task Card：20260620-001 ｜ skill：analysis（含 research 對照）
> 對外/正式化前須人工確認。本文為 v2.1 升級的研究佐證基準。

# Agent Harness v2 對照 2026 公開 AI 研究 — 差距基準與優化依據

## 結論

這個 harness **已經相當成熟**：它幾乎 1:1 對應 2026《Agent Harness Engineering: A Survey》
提出的 **ETCLOVG 七層分類學**（Execution / Tools / Context / Lifecycle / Observability /
Verification / Governance），七層全部都有對應實作（多數系統只實作 2–4 層）。其中**最強的兩層
正是 Observability 與 Governance**——這兩層在本 harness 是整個治理平面與量測腳本/稽核日誌，
因此把它們納入比對只會**強化「已成熟」結論**，4 個缺口仍然成立。
因此本次優化的正確策略是**加法式補缺口**，而非重寫。對照「2026 研究已收斂、harness 尚未顯式
納入」的方向，盤點出 **4 個高價值缺口**，全部可在不違背核心哲學（可控 > 能力、draft-first、
human-confirmed memory、單代理）的前提下補上，構成 v2.1。

> 命名注記：部分文獻把同一框架寫成六要素 `H=(E,T,C,S,L,V)`（State 顯式、未把 O/G 獨立）。
> 本文採該綜述 OpenReview 版的七層 ETCLOVG 為準；各來源對字母精確對應略有出入，標 `[待驗證]`。

## 已知事實

### ETCLOVG 七層對照（harness 現況）

| 層 | 論文定義 | harness 現有對應 | 評估 |
|----|---------|-----------------|------|
| **E** Execution | sandbox/隔離、observe-think-act、終止、錯誤恢復 | `CLAUDE.md` 9 步流程、連續失敗 3 次停止、checkpoint | 強 |
| **T** Tools | 協定、整合、白名單、schema 驗證 | Task Card `allowed_tools`、`permissions_guard.py` PreToolUse hook | 強（已落實「工具最小化」：per-task 白名單） |
| **C** Context | 記憶與持久化、壓縮、檢索 | `CLAUDE.md` context 規則、`COST_POLICY.md`、`memory/` | 中（壓縮粗略 + 程序記憶缺席 → 缺口 1/2/3） |
| **L** Lifecycle | 狀態、任務迴圈、跨 session | git checkpoint、`memory/`、`RECOVERY_RUNBOOK.md` | 中（接續狀態未結構化 → 缺口 3） |
| **O** Observability | traces、成本追蹤 | `governance_metrics.py`、`AUDIT_LOG.md`、`logs/runs/`、frontend 治理面板 | 強 |
| **V** Verification | 評估、回歸、回饋 | `GATE_POLICY.yaml` 四層閘、`eval_examples.md`、`FAILURE_TAXONOMY.yaml`、CI 測試 | 強 |
| **G** Governance | 權限、稽核 | `PERMISSIONS.yaml`、`APPROVAL_POLICY.yaml`、整個治理平面 | 強（缺顯式三要素建模 → 缺口 4） |

> 七層全部都有對應；**O（Observability）與 G（Governance）是 harness 覆蓋最強的兩層**——
> 整個治理平面 + 量測腳本 + 稽核/執行日誌 + 前端面板。把這兩層納入比對只會**強化「已成熟」**
> 結論，不新增缺口。論文「全棧實作」名單含 Claude Code、OpenHands、SWE-agent、AIOS；本 harness
> 疊在 Claude Code 之上，等同站在全棧基礎再加單人公司治理。
> `[待驗證]` 各來源對字母精確對應略有出入（另有六要素 `H=(E,T,C,S,L,V)` 寫法，State 顯式、未獨立 O/G）。

### 4 個研究已領先的缺口

1. **缺乏程序性記憶 / 失敗驅動學習迴圈。** harness 有靜態 `FAILURE_TAXONOMY`（14 模式）、
   人工 `RETRO_FLOW`、`logs/errors/`，但失敗**不會**精煉成「下次任務自動載入」的可引用指引。
   Reflexion 證明：把失敗寫成自然語言指引再回灌，pass@1 由 80%→91%（HumanEval），無需梯度更新。
   ACON 等 2025–2026 工作把「失敗驅動指引最佳化」系統化。

2. **記憶未對齊認知四類型學。** 2026 記憶綜述收斂到 working / episodic / semantic / procedural
   四型；harness 的記憶以「專案/生命週期」組織，其中 procedural 一型實質缺席。

3. **壓縮觸發是輪數（20 輪）而非預算門檻。** 2026 上下文工程收斂到「context 用量達 ~70% 預算
   即觸發壓縮」、agent-controlled compaction、結構化 handoff journal；且 `RECOVERY_RUNBOOK`
   Scenario C（context 重置後接續）尚未實測、缺結構化接續狀態。研究指出 2025 約 65% 企業 agent
   失敗源於 context drift / memory loss，而非單純 context 耗盡。

4. **未顯式建模「致命三要素」。** 已有 deny list + 風險分級 + SEC-01..04 + draft-first，但未把
   2025–2026 主流安全框架「lethal trifecta（私有資料 + 不可信內容 + 對外動作）疊加 = 高風險」
   顯式納入 `risk_check`。對應 OWASP LLM06:2025 Excessive Agency。

## 合理推論

- harness 的 per-task `allowed_tools` 白名單**已預先吻合**論文最重的反模式警告之一
  「tool proliferation（移除 80% 工具反而更好）」，故 T 要素無需改動。（推論依據：論文把工具
  最小化列為首要建議，harness 設計與之一致。）
- 四個缺口都能用**加法 + 復用既有機制**完成：失敗回流接 `RETRO_FLOW`、接續接
  `RECOVERY_RUNBOOK` Scenario C、三要素閘掛 `GATE_POLICY` risk_check（其 on_fail 已能鎖 drafts）。
  故升級風險屬 medium、不破壞既有流程。
- 採檔案式 lessons（非向量/RAG）對單人公司是**正確取捨**：論文指出 context 壓力的解法常是架構
  （pointer/索引）而非重型檢索；單人公司任務量級下，檔案式精煉指引的訊噪比優於向量庫。

## 待驗證

- `[待驗證]` ~70% 壓縮門檻在本 harness 實際 token 預算下的最適值（70% 為研究通用建議，需累積
  數筆任務後於 RETRO 校準，可能落在 60–75%）。
- `[待驗證]` Scenario C「讀 resume_state 接續」需在下一次真實多階段任務中途實測一次（沿用
  2026-05-29 Scenario A 演練的方法論）。
- `[待驗證]` lessons 庫成長後是否需要「過期/退役」機制（status: superseded 已預留欄位，閾值待觀察）。

## 高風險假設

- 假設「失敗驅動指引能在單人公司低任務量下也帶來淨效益」。Reflexion 數據來自高重複 benchmark；
  單人公司任務異質性高，指引的可遷移性較低 → 緩解：lessons 維持 human-confirmed 晉升，只收
  「重複 ≥ 2 次的同類失敗」，避免噪音。
- 假設「致命三要素檢查不會造成過度升級（approval fatigue）」。研究指出使用者對 93% 請求都會
  approve，使核准失去意義 → 緩解：三要素閘只在**三者同時**成立時升級，屬罕見疊加，非逐項觸發。

## 來源

1. Agent Harness Engineering: A Survey（ETCLOVG 七層分類學、失敗模式、maturity；另有六要素 H=(E,T,C,S,L,V) 寫法）—
   https://github.com/Gloriaameng/Awesome-Agent-Harness ／ https://openreview.net/pdf?id=eONq7FdiHa
2. Awesome list for AI agent harness engineering（patterns/permissions/observability/memory）—
   https://github.com/ai-boost/awesome-harness-engineering
3. Memory in the Age of AI Agents: A Survey（working/episodic/semantic/procedural）—
   https://arxiv.org/abs/2512.13564 ／ paper list：https://github.com/Shichun-Liu/Agent-Memory-Paper-List
4. Reflexion（失敗→自然語言指引，91% vs 80% pass@1）—
   https://www.promptingguide.ai/techniques/reflexion
5. State of AI Agent Memory 2026（架構、production gaps）— https://mem0.ai/blog/state-of-ai-agent-memory-2026
6. AI Agent Context Compression: Strategies for Long-Running Sessions（~70% 預算門檻、agent-controlled）—
   https://zylos.ai/research/2026-02-28-ai-agent-context-compression-strategies/
7. 致命三要素 / OWASP LLM06:2025 Excessive Agency（見來源 2 Permissions 章節彙整）
