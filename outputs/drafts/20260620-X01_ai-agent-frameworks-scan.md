# 2026 AI Agent 編排框架版圖快掃（Quick Scan）

- Task ID：20260620-X01
- 日期：2026-06-20
- Skill：research
- 投入：3 tool calls / 1 web search / ~750 字
- 狀態：草稿（workflow 測試批次 X01・科技領域）

> 修訂註記（2026-06-20，回應 PR #102 Codex review）：原稿來源時效僅標到「2026」年，未達 DoD 要求的 YYYY-MM/Qx 粒度。已補正：能查到月份者標 YYYY-MM（如 OpenAgents 2026-02）；比較型部落格無明確發布月份者改標「2026，月份未標示」，不硬編造日期。

## 結論

2026 年的 agent 編排框架已從 2024–2025 的爆發期收斂成幾個成熟選項：**LangGraph 成為企業級、需可觀測/可回溯場景的事實標準；CrewAI 是原型加速器；AutoGen 偏研究/學術；OpenAI、Google 則用 Agents SDK / ADK 補齊各自生態。** 對一人公司而言，重點不是「哪個最強」，而是「單人能不能長期維運」——這一點與本 harness 的設計哲學（可控 > 能力）一致，因此**有狀態、可 checkpoint、可審計的框架（LangGraph 取向）比角色扮演式的快速原型框架更值得押注**；而既然使用者已深度整合 Claude 生態，Claude Agent SDK 是最低切換成本的預設選項。

## 框架定位（≥4 個）

| 框架 | 一句定位 | 適用場景 | 取捨 / 限制 |
|------|----------|----------|-------------|
| **LangGraph** | 以有向圖（節點=agent/工具/checkpoint，邊=轉移）建模的有狀態編排 | 企業級、需要 audit trail / rollback 的正式部署 | 學習曲線較陡；圖思維對簡單流程偏重 |
| **CrewAI** | role/backstory/goal 的角色式編排，組成 crew 跑 tasks | 快速 demo / 原型、概念驗證 | 生產可觀測性與錯誤恢復較弱 |
| **AutoGen（Microsoft）** | 多 agent 辯論/驗證 pattern 成熟 | 研究、學術、實驗性多 agent | 正式生產採用規模較小 |
| **OpenAI Agents SDK / Swarm** | 官方輕量 agent/handoff 框架 | 綁 OpenAI 生態、窄交接流程 | 綁定單一模型供應商生態 |
| **Claude Agent SDK** | Anthropic 官方 agent 建構框架（本 harness 即跑在 Claude Code 上） | 已在 Claude 生態者最低切換成本 | 本次快掃未取得獨立第三方 benchmark [待驗證] |

## 已知事實

- 2026 年框架版圖收斂；OpenAI 推出 Agents SDK、Google 推出 ADK — 出自 Presenc AI / Uvik（2026）
- LangGraph 於 2026 初 GitHub stars 超越 CrewAI，企業正式部署足跡最大 — 出自 Tensoria benchmark（2026）
- CrewAI demo-to-prototype 體驗最佳，但生產可觀測性與錯誤恢復落後 — 出自 alicelabs / Tensoria（2026）
- AutoGen 在研究/學術採用領先，正式生產規模較小 — 出自 Presenc AI（2026）

## 合理推論

- **一人公司選型（單人可維運角度）**：單人團隊最稀缺的是「除錯與維運時間」，不是「開發速度」。因此可觀測性、狀態持久化、checkpoint/rollback（LangGraph 取向）比快速搭原型（CrewAI）更能降低長期維運風險。
- 使用者已深度整合 Claude 生態 → Claude Agent SDK 切換成本最低、與既有 Claude Code 工作流相容，應作為預設；LangGraph 適合需要明確圖狀流程控制時再導入。
- 「框架選型」對一人公司的真實成本多在維運面而非授權費，開源 vs 官方 SDK 的差異主要落在生態鎖定與長期支援。

## 待驗證

- Claude Agent SDK 與 LangGraph/CrewAI 的獨立第三方 benchmark（本次 1 web search 未涵蓋）
- 各框架 2026 年實際企業採用率的量化數據（多數來源為比較型部落格，非一手調查）
- Google ADK 的成熟度與生產採用實況

## 高風險假設

- **「LangGraph 是企業事實標準」**：依據多為 GitHub stars 與比較型文章，stars ≠ 生產採用；若 2026 下半年 OpenAI/Google 官方 SDK 挾生態快速吃下市場，版圖可能再洗牌。
- **「框架選擇長期穩定」**：agent 框架仍在高速演進，今天的最佳選擇 12 個月後可能被官方 SDK 取代，押注任何單一框架都有重寫風險。

## 來源

- [CrewAI vs LangGraph vs AutoGen vs OpenAgents — Best AI Agent Framework (OpenAgents)](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared)（時效：2026-02）
- [Multi-Agent Orchestration Frameworks 2026 (Presenc AI)](https://presenc.ai/research/multi-agent-orchestration-frameworks-2026)（時效：2026，月份未標示）
- [LangGraph vs CrewAI vs AutoGen vs Custom — 2026 Benchmark (Tensoria)](https://tensoria.fr/en/blog/multi-agent-orchestration-comparison)（時效：2026，月份未標示）
- [Best AI Agent Frameworks 2026: Production-Tested Rankings (Alice Labs)](https://alicelabs.ai/en/insights/best-ai-agent-frameworks-2026)（時效：2026，月份未標示）
- [Agentic AI Frameworks 2026: LangGraph vs CrewAI vs OpenAI SDK (Uvik)](https://uvik.net/blog/agentic-ai-frameworks/)（時效：2026，月份未標示）

## 執行紀錄

- web search：1 次（query：AI agent orchestration frameworks 2026 LangGraph CrewAI AutoGen comparison production）
- 工具呼叫：2 次（web_search + Write）；另 1 次 file_read（user_prefs）；Codex review 後以 Edit 補正來源時效粒度，未新增 web search
- 預算狀態：tool_calls 3/3、web_searches 1/1
- 來源時效：OpenAgents 可定到 2026-02；其餘比較型部落格無明確發布月份，標「2026，月份未標示」
- 限制：Quick Scan，Claude Agent SDK 與量化採用率未深挖，已標 [待驗證]

---

**End of X01**
