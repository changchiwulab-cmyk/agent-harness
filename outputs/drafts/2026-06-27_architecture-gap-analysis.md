# Agent Harness 架構缺口分析 — 對齊 2025–2026 最新 AI 公開架構發展

> **草稿（draft）** ｜ 日期：2026-06-27 ｜ Task Card：`20260627-001` ｜ skill：analysis
> 交付範圍：**完整檢視 + 缺口分析 + 補齊 roadmap（M1–M6）**。system/ 實作走 task 002–006，本卡只產分析。
> 上游核准：本 session ExitPlanMode 已核准 plan（= system/ 變更的人工 gate）；決策另記 `D008`。

---

## 摘要

| 項目 | 結論 |
|------|------|
| **檢視結論** | v2 在「治理可審計」極強（自評 ≈7/10、安全 9、治理 9），但**未對照這一年 AI 架構演進補新面**。R1–R8 都是「把既有設計做實」，不是「補新架構」。 |
| **最大缺口** | **評估架構（M1）**——只有靜態 `eval_examples.md`，無執行器/評分/regression。「可量化」是核心價值卻最弱。 |
| **最高槓桿低風險** | **安全架構（M2）**——本框架其實已天生阻斷 lethal trifecta，卻**從未把它寫成架構**；補上即把招牌「安全」從 9 推向滿格。 |
| **補齊原則** | 嚴守「可控 > 能力」：六個模組**每個都綁一個 enforcement 點**（hook/CI/schema，即 v3 J5 判準），不做 swarm、不自動外發、記憶走人工 gate、子代理只做唯讀情境隔離。 |
| **與 v3 的關係** | 這是 v3「砍冗餘 + **深化治理層**」的**深化臂**。補的都是原生不做的治理/品質核心，不增加 NATIVE_OVERLAP。 |

**研究方法**：親自盤點本專案核心檔（README、CLAUDE.md、GLOBAL_RULES、AGENT_CONTEXT、NATIVE_OVERLAP、GATE_POLICY、FAILURE_TAXONOMY、EXECUTION_LOG_SCHEMA、check_spec_consistency、self-assessment、v3 extraction plan、ai-bubbly-mountain plan）＋ WebSearch 查證六軸最新架構（2025–2026）。

---

## 一、最新 AI agent 架構六軸（2025–2026，已查證）

| 軸 | 業界現況 |
|----|---------|
| **情境工程 Context Engineering** | 焦點從「prompt 怎麼寫」轉為「context 怎麼配置」。核心技術：compaction（規則式修剪）、結構化筆記（context 外記憶）、JIT 檢索（按需讀取而非全貼）、context-awareness（模型即時知道剩餘容量）、programmatic tool calling（用程式碼消化中間結果只回傳精煉值）。 |
| **記憶架構 Memory** | MemGPT/Letta 把 LLM context 當虛擬記憶（core/archival/external 分層 OS 式管理）；2026 Letta benchmark 顯示**檔案系統式記憶**具競爭力；Letta Code 的 Skill Library 把學會的樣式存成 `.md` 自動調用。Mem0/Zep/LangMem 各走 vector/temporal-graph/checkpoint 路線。 |
| **評估 Eval** | 主流是 **LLM-as-judge**（獨立評審模型對 faithfulness/relevance/groundedness 評分）＋上線前**離線 regression/trajectory eval**（對 goal drift、tool misuse、reasoning-action mismatch 連到 regression test）。 |
| **可觀測性 Observability** | **OpenTelemetry GenAI semantic conventions**（vendor-neutral 的 `gen_ai.*` span/metric）；要的是把 reasoning trace、考慮過的工具、實際呼叫、參數、回應、每步 token、每跳 latency 串成一條可重播的階層 trace。工具：Langfuse、Phoenix（皆 OSS）、LangSmith、Weave。 |
| **安全 Security** | **lethal trifecta**（Simon Willison）：私有資料存取 ＋ 未受信任內容曝露 ＋ 對外通訊，三者齊聚才可能資料外洩。Prompt injection 是 OWASP 2026 #1（YoY +340%），且**架構性無解**（指令與資料同為 token 流）。防線：把 agent 當未受信任中介、行動前驗證、最小權限、未受信任資料隔離。 |
| **子代理 Subagents** | subagent ＝ 情境隔離原語：fresh context window 處理 scoped 任務，把探索成本關在子代理裡，只回傳精煉摘要（對母代理只花幾百 token）。orchestrator-worker、唯讀 fan-out 並行。代價：多代理 token 數倍增。 |

來源見文末。

---

## 二、缺口對照（最新架構 → 專案現況 → 缺口 → 補齊模組 → enforcement）

| # | 軸 | 專案現況 | 缺口 | 補齊模組 | enforcement 點 |
|---|----|---------|------|---------|---------------|
| **M1** | Eval | `skills/*/eval_examples.md`（靜態好/壞範例＋判斷標準表） | **無 eval 執行器、無評分、無 regression set** | 評估架構 | `scripts/run_evals.py`＋test＋CI lint＋`logs/evals/` |
| **M2** | Security | deny-list hook＋draft-only（已阻斷 trifecta 外發腿，但**未命名**）；做 web search 卻**無未受信任資料協定** | 無 prompt-injection 防線、無 provenance 分層、taxonomy 缺注入類 | 安全架構 | FAILURE_TAXONOMY `SEC-05`＋provenance 慣例＋CI 枚舉檢查 |
| **M3** | Context Eng | 只有 token **預算**（CLAUDE.md ≤3K、check_context_budget.rb） | 無 compaction 協定／結構化筆記／JIT 檢索**工程** | 情境工程 | EXECUTION_LOG `context_snapshot` 欄＋budget check |
| **M4** | Memory | `memory/` 形同虛設、auto-write 在 deny | 無分層記憶架構、無學習樣式庫；保守過頭＝能力閹割 | 受控記憶 | 記憶分層對應 PERMISSIONS allow/ask＋learned-pattern schema |
| **M5** | Subagents | 單代理；多代理在「不做清單」 | 未區分「情境隔離子代理（該做）」vs「swarm（不做）」 | 受控子代理 | `SUBAGENT_POLICY.md`：唯讀＋主代理復驗＋COST 上限 |
| **M6** | Observability | `governance_metrics.py`（R7，工具/工作流/業務層） | 無 trajectory/trace 級、無標準 schema | trace 可觀測 | EXECUTION_LOG `trace` 區塊（對齊 OTel GenAI）＋schema lint |

---

## 三、逐項證明：補齊沒有違反「現階段不做清單」

> 「不做清單」（README §現階段不做）：多 agent swarm／自動長期記憶擴寫／太多工具串接／自動寫正式資料庫／自動外發／把所有規則塞進單一超長 prompt／複雜 MCP／自動 shell。

| 模組 | 可能的疑慮 | 為何不違反 |
|------|-----------|-----------|
| M1 Eval | 「LLM-as-judge 會自動跑、燒 token」 | judge 為**人工/輔助**步驟；**確定性檢查**才入 CI。scorecard 進 `logs/`（allow），晉升仍走人工 gate。 |
| M2 Security | — | 純加固，零放寬；命名既有防線＋taxonomy＋provenance。是「不做清單」的**強化**而非鬆綁。 |
| M3 Context Eng | 「結構化筆記＝自動長期記憶？」 | 不是。compaction note/working note 是 **session 內**情境工程，非長期記憶自動擴寫；晉升長期仍走 M4 的人工 gate。 |
| M4 Memory | 「這不就是自動長期記憶？」 | **明文保留 auto-write deny**。只定義 working memory 可累積的**位置**與**人工晉升 gate**（Tier3 learned-pattern 必 human-confirm）。解能力閹割，不破 deny。 |
| M5 Subagents | 「這不就是 multi-agent swarm？」 | **明文仍不做 swarm**。子代理**唯讀**、無對等寫入/行動、主代理保留全部決策與 gate、結果須復驗。是「情境隔離」不是「自治群」。 |
| M6 Observability | — | 純 schema/紀錄擴充，無新自治能力。對齊 OTel 是為**可攜性**，非引入複雜 MCP。 |

**結論**：六模組全部落在「治理/品質核心」，且每個綁 enforcement。三條設計公理（可驗證成功定義／可分類可中止失敗／人類在迴路）一條未動搖。

---

## 四、補齊 roadmap（M1–M6）

### 立即實作（high-priority，full：doc + schema + script + CI + test）

- **M1 評估架構**（task 002）：`system/EVAL_POLICY.md`＋`evals/rubrics/<skill>.yaml`(×5)＋`evals/regression/manifest.yaml`＋`scripts/run_evals.py`(+test)＋`logs/evals/`＋CI lint＋GATE completion 引用。
- **M2 安全架構**（task 003）：`system/SECURITY_ARCHITECTURE.md`＋FAILURE_TAXONOMY `SEC-05`＋provenance 標記＋CI SEC lint。
- **M3 情境工程**（task 004）：`system/CONTEXT_ENGINEERING.md`＋EXECUTION_LOG `context_snapshot`。

### 本輪 policy doc + schema 落地（自動化 staged）

- **M4 受控記憶**（task 005）：`memory/MEMORY_ARCHITECTURE.md`（Tier0–3）＋`memory/playbooks/`＋learned-pattern schema。
- **M5 受控子代理**（task 006）：`system/SUBAGENT_POLICY.md`。
- **M6 trace 可觀測**（task 006）：EXECUTION_LOG `trace` 區塊＋`docs/otel-genai-mapping.md`。

### 後續另開卡（不在本輪）

- M4-b learned-pattern 晉升自動化（讀寫 gate hook）。
- M6-b run_evals/governance_metrics 輸出真實 OTel trace 並接 Langfuse/Phoenix。
- M1-b LLM-as-judge 半自動評分腳本（含成本上限）。

---

## 五、相依與排程

```
本輪（單一 PR）：
  D0 分析(001) → 卡 002–006 已開
  M1(002) ─┐
  M2(003)  ├─ 互相獨立，可並行實作
  M3(004) ─┘
  M4(005) / M5+M6(006) ─ doc 層，獨立
  最後：README + NATIVE_OVERLAP 更新 → 重生 data.json → CI 全綠 → push → draft PR
關鍵路徑：M1（最大缺口、含 script+CI+test）
```

---

## 六、來源

- Anthropic — [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Sourcegraph — [Context Engineering: A Practical Guide for AI Agents (2026)](https://sourcegraph.com/blog/context-engineering)
- Letta — [Benchmarking AI Agent Memory: Is a Filesystem All You Need?](https://www.letta.com/blog/benchmarking-ai-agent-memory/)
- [2026 AI Agent Memory Wars: Three Architectures](https://chauyan.dev/en/blog/ai-agent-memory-wars-three-schools-en)；[Mem0 vs Letta (MemGPT)](https://vectorize.io/articles/mem0-vs-letta)
- Confident AI — [Top 7 LLM Observability Tools in 2026](https://www.confident-ai.com/knowledge-base/compare/top-7-llm-observability-tools)；Morph — [AI Agent Evaluation (2026)](https://www.morphllm.com/ai-agent-evaluation)
- [AI Agent Observability 2026: Tracing & Monitoring Stack](https://www.digitalapplied.com/blog/ai-agent-observability-2026-tracing-monitoring-stack-guide)（OTel GenAI semantic conventions）
- airia — [AI Security in 2026: Prompt Injection, the Lethal Trifecta](https://airia.com/ai-security-in-2026-prompt-injection-the-lethal-trifecta-and-how-to-defend/)；Help Net Security — [OWASP prompt injection 2026](https://www.helpnetsecurity.com/2026/06/11/owasp-prompt-injection-ai-security-failures/)
- Claude Code Docs — [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)；[Inside Claude Code's architecture: how the agent loop works](https://callsphere.ai/blog/inside-claude-code-s-architecture-how-the-agent-loop-works)

---

## 七、後續

- 本卡只產草稿。M1–M6 實作見 task 002–006（同一 PR）。
- 經人工確認後，可依 `RETRO_FLOW` 晉升本分析至 `outputs/reports/`。
