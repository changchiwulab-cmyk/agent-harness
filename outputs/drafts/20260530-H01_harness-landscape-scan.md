# Agent Harness Engineering 公開資料掃描（Landscape Scan）

> Task Card: 20260530-H01（research / Stage 1）
> 產出方式：3 個 Haiku 子代理（model: claude-haiku-4-5）於 2026-05-30 分三條 lane 做 web fan-out 發現，主執行緒（Opus 4.8）彙整去重。
> 範圍：公開的 agent harness / agent 執行框架「harness engineering」資料 — 框架、最佳實踐、治理/guardrails、eval/benchmark。
> 驗證等級：URL 多數來自即時搜尋結果（已知事實）；具體數字、未來版本號、付費牆文章、精確 arxiv 編號標 [待驗證]。

---

## 結論

公開的「harness engineering」生態可分四群：(A) Anthropic/Claude 本源、(B) 其他 agent 框架、(C) 跨領域最佳實踐與治理/guardrails、(D) eval/benchmark/observability。「Harness engineering」是 Anthropic 近期明確使用的詞（見 *Effective harnesses for long-running agents*），核心關注「跨 context window 的長任務如何穩定推進」——這正是控制優先設計的母題。本專案採用的控制手法（執行前審批閘、allow/ask/deny 權限分層、human-in-the-loop、失敗分類、eval gate）在公開生態都有對應物：理念最接近的是 **Block Goose**（確定性 guardrails）、**LangChain DeepAgents / Pydantic AI**（工具執行前 approve/reject）、以及 **Microsoft「Agentic AI 失敗模式分類」**（本專案 `system/FAILURE_TAXONOMY.yaml` 的 14 模式、spec/coordination/verification/security 四分類明顯源自此）。相對於公開實務，本專案最大缺口是**缺一層 observability/eval harness**（LangSmith / Inspect-AI / SWE-bench 等）來把「4 層 gate」變成可量測、可回放的證據。

---

## 已知事實（依四大類，URL 來自搜尋結果）

### A. Anthropic / Claude 生態（harness engineering 本源）

- **Effective harnesses for long-running agents** — _Anthropic Engineering_ — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - 跨 context window 的長任務 orchestration 模式（subagent 隔離、接近上限時自動 compaction、結構化 handoff、多檢查點驗證）。
  - 相關度：高。直接對應本專案「context 預算硬限制 + checkpoint + 階段交接」。
- **Building agents with the Claude Agent SDK** — _Anthropic Engineering_ — https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
  - Claude Code SDK 改名 Claude Agent SDK；gather→act→verify loop；MCP 工具擴充；Planner/Generator/Evaluator 多代理 + 批判循環。
  - 相關度：高。本專案的多代理（Haiku 發現 → Opus 分析）即此 pattern 的縮小版。
- **Building Effective AI Agents** — _Anthropic Research_ — https://www.anthropic.com/research/building-effective-agents
  - workflow vs agent 區分、工具設計、用 subagent 省 context、自動 summarization。
  - 相關度：高。本專案「Task Card 化 workflow + skill 路由」呼應 workflow/agent 分野。
- **Demystifying evals for AI agents** — _Anthropic Engineering_ — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  - verification-as-evaluation、ground-truth 配對、Claude 自評；線上（生產流量）+ 離線（curated dataset）評估迴圈。
  - 相關度：高。本專案缺的就是這層；可把 `definition_of_done` 變成離線 eval 案例。
- **Writing/Building tools for agents** — _Anthropic Engineering_ — https://www.anthropic.com/engineering/writing-tools-for-agents
  - 工具設計哲學（atomic vs composable、明確用途文件、錯誤處理 fallback）。
  - 相關度：中。對應 Task Card 的 `allowed_tools` 白名單設計。
- **Anthropic Cookbook — agent patterns** — _GitHub_ — https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents
  - prompt chaining / routing / orchestrator-subagents / evaluator-optimizer 參考實作。
  - 相關度：高。`system/ROUTING_RULES.md` 即 routing pattern 的規則化。
- **Claude Code 官方文件（How Claude Code Works）** — _Claude Docs_ — https://code.claude.com/docs/en/how-claude-code-works
  - gather-context → LLM → tool → feedback 迴圈；自主工具呼叫與檔案存取。
  - 相關度：高。本 harness 即跑在 Claude Code 之上。
- **Scaling Managed Agents（decoupling the brain）** — _Anthropic Engineering_ — https://www.anthropic.com/engineering/managed-agents
  - 把「決策腦」與「執行 harness」解耦的擴展模式。
  - 相關度：中高。呼應本專案「控制層（CLAUDE.md/system）vs 執行層（skill）」分離。
- **Governing Claude Code: Secure Agent Harness Rollouts** — _Kong Engineering_ — https://konghq.com/blog/engineering/claude-code-governance-with-an-ai-gateway
  - gateway 層做認證/限流/token 預算/prompt-response 紀錄/內容過濾，不改 agent。
  - 相關度：中高。是本專案 `PERMISSIONS.yaml` + audit log 的「企業 gateway」版。

### B. 其他 agent 框架 / harness

- **OpenAI Agents SDK**（Swarm 後繼）— _輕量 SDK_ — https://openai.github.io/openai-agents-python/
  - 內建 input/output guardrails、sessions（自動歷史）、tracing；極簡抽象。
  - 相關度：中。有 guardrails/tracing，但無 Task-Card 審批閘與細權限分層。
- **LangGraph** — _低階 orchestration runtime_ — https://github.com/langchain-ai/langgraph
  - durable execution、checkpoint resume、human-in-the-loop、雙層記憶。
  - 相關度：高。checkpoint/狀態持久化比本專案（git commit checkpoint）更系統化，值得借鏡。
- **LangChain DeepAgents** — _batteries-included harness_ — https://github.com/langchain-ai/deepagents
  - 工具呼叫前 approve/edit/reject、可插拔 state/store、context 管理（摘要/卸載）。
  - 相關度：高。pre-execution approval 與本專案 ask 層、drafts-only 高度一致。
- **CrewAI** — _角色式多代理_ — https://github.com/crewAIInc/crewAI
  - role/goal/backstory、結構化任務輸出；社群採用量大。
  - 相關度：中。結構化任務 ≈ Task Card，但審批閘不明確。
- **AG2（前 AutoGen）** — _事件驅動多代理_ — https://github.com/ag2ai/ag2
  - GroupChat、LLM 推理 speaker selection；偏 emergent 對話。
  - 相關度：低中。emergent 取向與「確定性控制」相反。
- **Microsoft Agent Framework / Semantic Kernel** — _企業多代理_ — https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/
  - graph-based workflow、多 provider、A2A/MCP 互通。
  - 相關度：中。graph 可審視，但細權限/審批不明確。
- **Pydantic AI** — _型別安全輕量框架_ — https://github.com/pydantic/pydantic-ai
  - human-in-the-loop 工具審批、Pydantic 型別（寫期錯誤偵測）、內建 MCP。
  - 相關度：高。型別安全 ≈ 本專案 schema 驗證；工具審批 ≈ ask 層。
- **OpenHands（前 OpenDevin）Software Agent SDK** — _事件流 coding agent_ — https://github.com/OpenHands/software-agent-sdk
  - 事件流（observation→action）、Docker 沙箱隔離、子代理委派。
  - 相關度：中。沙箱隔離強，偏程式任務。
- **SWE-agent** — _研究型 coding 框架_ — https://github.com/princeton-nlp/SWE-agent
  - Agent-Computer Interface（ACI）抽象層；源自 SWE-bench。
  - 相關度：中。ACI 的「為 agent 設計的確定性動作介面」概念可借鏡 `allowed_tools`。
- **smolagents（Hugging Face）** — _code-first 極簡框架_ — https://huggingface.co/docs/smolagents/index
  - <30 行原型、CodeAgent 以程式碼表達動作。
  - 相關度：低。設計哲學與控制優先相反（少 guardrails）。
- **LlamaIndex Workflows & Agents** — _RAG-first orchestration_ — https://docs.llamaindex.ai/
  - event-driven async workflow、context 管理/持久化、AgentWorkflow。
  - 相關度：中。context 管理/持久化值得參考。
- **Block Goose — Agentic Guardrails & Controls** — _guardrails-first_ — https://block.github.io/goose/blog/2026/01/05/agentic-guardrails-and-controls/
  - 確定性 stop-gate（非 LLM 決定）、執行前工具授權檢查、scoped credentials、runtime 圍堵、HITL。
  - 相關度：**最高**。與本專案「可控 > 能力」哲學最貼近；其「確定性閘」正是本專案 gate 想要的。

### C. 跨領域最佳實踐、治理與 guardrails

- **12-Factor Agents（HumanLayer）** — _最佳實踐_ — https://github.com/humanlayer/12-factor-agents [待驗證精確 URL]
  - 把可靠 LLM 應用拆成 12 條工程原則（own your prompts/context、small focused agents、HITL）。
  - 相關度：高。與本專案「小步、人為審批、擁有 context」一致。
- **NVIDIA NeMo Guardrails** — _guardrails 框架_ — https://developer.nvidia.com/nemo-guardrails
  - Colang DSL 定義 input/output 審核、主題控制、jailbreak 偵測、資料存取政策。
  - 相關度：中高。是 allow/ask/deny 的 runtime 可執行版。
- **Guardrails AI** — _guardrails 框架_ — https://github.com/guardrails-ai/guardrails [待驗證]
  - 結構化輸出驗證、validators、re-ask。
  - 相關度：中。對應 schema gate。
- **Policy-as-Prompt: AI Governance Rules as Guardrails** — _論文/治理_ — https://arxiv.org/abs/2509.23994 [待驗證編號]
  - 把合規政策轉成可執行 guardrails。
  - 相關度：中高。對應把 `PERMISSIONS.yaml`/`APPROVAL_POLICY.yaml` 變 runtime 決策點。
- **Taxonomy of Failure Modes in Agentic AI Systems（Microsoft）** — _失敗分類_ — https://www.microsoft.com/en-us/research/ [待驗證精確 URL]
  - 跨 1,600+ traces 的失敗模式，spec/coordination/verification 三類根因（+security）。
  - 相關度：**最高**。本專案 `FAILURE_TAXONOMY.yaml`（14 模式、42% spec / 37% coordination / 21% validation + security）顯然源自此。
- **Enforcing Human-in-the-Loop Controls（Prefactor）** — _HITL 治理_ — https://prefactor.tech/learn/enforcing-human-in-the-loop-controls [待驗證]
  - full-context approval 介面（觸發原因/涉及資料/預期結果/政策）、async vs sync 審批層。
  - 相關度：高。直接對應 drafts-only + 審批分層。

### D. Eval / benchmark / observability harness

- **SWE-bench（含 Verified）** — _eval harness_ — https://github.com/SWE-bench/SWE-bench
  - 以真實 GitHub issue 評 agent；可重現 harness；多變體。
  - 相關度：高。可作「completion gate」客觀化的範式。
- **Terminal-Bench** — _eval harness（終端任務）_ — https://www.tbench.ai/ [待驗證 2.0 版本宣稱]
  - 終端環境任務 + Harbor task 格式 + agent-agnostic harness。
  - 相關度：高。Harbor「goal + 驗證測試 + 沙箱」≈ Task Card「goal + definition_of_done」。
- **Inspect AI（UK AISI）** — _eval 框架_ — https://github.com/UKGovernmentBEIS/inspect_ai
  - 200+ 內建 eval、多輪、tool use、model-graded scoring；Anthropic/DeepMind 採用。
  - 相關度：高。最現成的「把 definition_of_done 變可跑 eval」工具。
- **LangSmith / Langfuse** — _observability/eval 平台_ — https://www.langchain.com/langsmith-platform ；Langfuse: https://github.com/langfuse/langfuse [待驗證 Langfuse URL]
  - 完整執行樹 tracing、custom evaluators、dataset replay、品質指標。
  - 相關度：高。補本專案最大缺口（audit log 是事後文字，缺結構化 trace/replay）。
- **OpenAI Evals** — _eval 框架_ — https://github.com/openai/evals
  - 可組合的 eval 註冊與執行。
  - 相關度：中。
- **Evaluation-Driven Development & Ops of LLM Agents（論文）** — _方法論_ — https://arxiv.org/pdf/2411.13768 [待驗證]
  - agent 開發生命週期整合 eval/監控/回饋的參考架構。
  - 相關度：中高。對應 `logs/runs/` 執行紀錄 + RETRO 迴圈。

---

## 合理推論

- 業界正從「能不能做（capability）」轉向「做得穩不穩（reliability/control）」：guardrails、HITL approval、failure taxonomy、eval harness 同時成為主流話題，**佐證本專案「可控 > 能力」的方向押對了**（推論依據：四群資料中 C/D 兩群佔比高，且多為 2025–2026 內容）。
- 「執行前工具審批」正在成為標配（DeepAgents、Pydantic AI、Goose 都有）——本專案的 ask 層 + drafts-only 屬同一範式，但本專案把它**規則化成檔案（Task Card/PERMISSIONS）**，比多數框架的程式碼鉤子更「可審計」。
- 主流框架（LangGraph/OpenHands/LlamaIndex）把 **checkpoint/狀態持久化**做成 runtime 機制，本專案用 git commit 當 checkpoint —— 概念相同但缺「自動 resume / 狀態查詢」。
- 幾乎沒有公開框架把「**Task Card = 執行前合約**」當硬性前置（多數是 role/goal 軟性描述）——這是本專案相對獨特的控制點。

## 待驗證

- 具體量化宣稱：Building Effective Agents「+13.7pp」、tool response「25k token 上限」、OpenHands「Series A $18.8M、AMD/Apple/Google/Netflix/NVIDIA 採用」、CrewAI「1.3M/月安裝」、AG2「~100k/月」——均為子代理轉述，未獨立查證。
- 未來版本/日期宣稱：Microsoft Agent Framework「1.0（2026-04）」、OpenAI Agents SDK「v0.17.1（2026-05）」、Terminal-Bench「2.0」、Goose 部落格「2026-01-05」——可能正確但需核對。
- 精確 URL/編號待核：Microsoft 失敗分類白皮書確切連結、12-factor-agents 與 Guardrails AI 的 repo 路徑、arxiv 2509.23994 / 2411.13768 / 2601.16280、Langfuse repo。
- 付費牆/需登入文章（多篇 Medium）僅讀到摘要，內文未驗證。

## 高風險假設

- **「找到所有公開資料」不可能成立**：本掃描是三條 lane 各 ~3 次搜尋的快照，必有遺漏（如中文圈/日文圈 harness 寫作、各家 cookbook 細節、新近 release）。若把本清單當「窮舉」會誤判缺口。
- 假設子代理回報的 URL 與要點忠實反映頁面內容；若有 Haiku 幻覺（尤其量化數字），下一階段比對會被污染——故 Stage 2 應只用「已知事實」層做強結論，量化僅供參考。
- 假設這些框架的「approval/guardrails」與本專案語義等價；實際上各家粒度不同，逐維度比對時需小心對齊定義。

## 來源

Anthropic/Claude：
- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
- https://www.anthropic.com/research/building-effective-agents
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- https://www.anthropic.com/engineering/writing-tools-for-agents
- https://www.anthropic.com/engineering/managed-agents
- https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents
- https://code.claude.com/docs/en/how-claude-code-works
- https://konghq.com/blog/engineering/claude-code-governance-with-an-ai-gateway

其他框架：
- https://openai.github.io/openai-agents-python/
- https://github.com/langchain-ai/langgraph
- https://github.com/langchain-ai/deepagents
- https://github.com/crewAIInc/crewAI
- https://github.com/ag2ai/ag2
- https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/
- https://github.com/pydantic/pydantic-ai
- https://github.com/OpenHands/software-agent-sdk
- https://github.com/princeton-nlp/SWE-agent
- https://huggingface.co/docs/smolagents/index
- https://docs.llamaindex.ai/
- https://block.github.io/goose/blog/2026/01/05/agentic-guardrails-and-controls/

最佳實踐 / 治理 / guardrails：
- https://github.com/humanlayer/12-factor-agents [待驗證]
- https://developer.nvidia.com/nemo-guardrails
- https://github.com/guardrails-ai/guardrails [待驗證]
- https://arxiv.org/abs/2509.23994 [待驗證]
- https://www.microsoft.com/en-us/research/ [待驗證精確 URL]
- https://prefactor.tech/learn/enforcing-human-in-the-loop-controls [待驗證]

Eval / benchmark / observability：
- https://github.com/SWE-bench/SWE-bench
- https://www.tbench.ai/
- https://github.com/UKGovernmentBEIS/inspect_ai
- https://www.langchain.com/langsmith-platform
- https://github.com/openai/evals
- https://arxiv.org/pdf/2411.13768 [待驗證]
