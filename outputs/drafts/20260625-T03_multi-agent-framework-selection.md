<!--
task_id: 20260625-T03
date: 2026-06-25
skill_type: analysis
status: draft
-->

# multi-agent 編排框架選型：一人公司該不該換、換哪個？

## 結論與建議

**建議排序：① 不做（續用現有單代理 harness，現在）→ ② Claude Agent SDK（當 v3 觸發條件成立時）→ ③ CrewAI（僅限快速原型）→ ④ LangGraph（一人公司多半過度設計）。**

理由：本專案的 harness 已建構在 Claude Code 之上，當前任務量與複雜度尚未觸發 v3 升級條件（context 經常超限／規則衝突頻繁／成本超標／錯誤率上升），導入任何 multi-agent 框架都是「為尚未發生的問題付維護成本」，違反 README「現階段不做清單」。真要升級時，**Claude Agent SDK 是切換成本最低的選項**——它就是驅動 Claude Code 的同一套 harness，原生 MCP、子代理、sessions 都現成，且「lead agent + 平行 sub-agent」在 Anthropic 研究中較單代理基準高出最多 90%。CrewAI 適合 2–4 小時做出原型但 token 開銷達 LangGraph 的 3 倍；LangGraph 能力最強但 1–2 週學習曲線與 60–80 行樣板對一人公司是過度投入。

## 選項比較

### 選項 A：不做（續用現有單代理 harness）
| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中 | 既有 Task Card + 四層 gate 已滿足當前任務；穩定可審核 |
| 成本 | 最低（≈0） | 無導入、無學習、無新依賴 |
| 風險 | 低 | 無遷移風險；唯一風險是「需求成長後反應慢」 |
| 可行性 | 高 | 已在運行 |
| 執行難度 | 無 | 維持現狀 |
| 預期回報 | 中 | 省下的時間可投入內容產出 |
| 一人公司適配度 | 高 | 完全對齊「可控 > 能力」與不做清單 |

### 選項 B：Claude Agent SDK
| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高 | 與 Claude Code 同 harness；原生 MCP、子代理、sessions、Bash/Read/Write/Edit、hosted execution |
| 成本 | 中 | 2026-06-15 起訂閱方案的 Agent SDK 用量改抽獨立月度額度，耗盡後走 API 計費——須估量 |
| 風險 | 中 | 對 Claude 鎖定；細粒度編排不如 LangGraph |
| 可行性 | 高 | Python/TS 雙語；學習曲線中等 |
| 執行難度 | 中 | 比 CrewAI 稍高、比 LangGraph 低 |
| 預期回報 | 高 | 多代理 vs 單代理基準最高 +90%（Anthropic 研究，平行 sub-agent + lead planner） |
| 一人公司適配度 | 高 | 既已深度整合 Claude，切換成本最低 |

### 選項 C：CrewAI
| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中 | role/goal/backstory 抽象貼近自然語言，原型最快 |
| 成本 | 中高 | token 開銷達 LangGraph 3 倍（每次呼叫都帶角色設定） |
| 風險 | 中 | 結構開銷導致長期營運成本偏高；細控有限 |
| 可行性 | 高 | <20 行可定義 crew；2–4 小時出原型 |
| 執行難度 | 低 | 學習曲線最平緩 |
| 預期回報 | 中 | 快速驗證點子，但不利長期高頻營運 |
| 一人公司適配度 | 中 | 適合 PoC，不適合當常駐生產線 |

### 選項 D：LangGraph
| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高 | 有向圖 + 條件邊、最細控；2026 獨立基準效能最佳 |
| 成本 | 高 | 1–2 週學習曲線；60–80 行樣板；需 Postgres/Redis 持久化 |
| 風險 | 中 | 過度設計風險；維運負擔對單人偏重 |
| 可行性 | 中 | 能力夠但上手慢 |
| 執行難度 | 高 | 樣板冗長、概念多 |
| 預期回報 | 中（對單人） | 企業級回報，但一人公司用不滿 |
| 一人公司適配度 | 低 | 企業預設選擇，非單人最適 |

## 與本專案 v3 升級觸發條件的對齊

現行 v2 維持單代理是對的——四個 v3 觸發條件（context 經常超限／規則衝突頻繁／單任務成本持續超標／錯誤率上升）**目前皆未持續成立**（M4 原生重疊 30% < 50% 重構門檻、本次 3 主題測試成本仍在預算內）。本卡的建議因此是「設好觸發點，不提前動工」：一旦任兩條件持續 2 週以上，直接評估 Claude Agent SDK 的 sub-agent 模式，而非從零選框架。

## 高風險假設

- **假設多代理 +90% 的增益可複製到一人公司情境**：該數字來自 Anthropic 特定 benchmark，任務型態不同時增益未必成立；若不成立，導入只剩成本沒有回報。
- **假設 Agent SDK 額度計費穩定**：2026-06-15 新計費制度上路未久，月度額度與超額 API 成本若調整，選項 B 的成本評估會變動。
- **假設一人公司真的需要「多代理」**：多數單人任務是序列、非平行；若實際瓶頸是上下文管理而非並行度，換框架解錯問題。

## 待驗證

- Claude Agent SDK 月度額度的**實際數值與超額單價**：驗證方式——查官方定價頁，跑一個代表性任務量測。
- LangGraph／CrewAI 在**繁中任務**的實測 token 與品質差異：驗證方式——同一任務各跑一次小規模對照。
- 本專案近 3 個月是否已出現 v3 觸發跡象：驗證方式——以 governance_metrics.py 跑 M1–M4 趨勢。

## 建議下一步

1. **現在不導入**；在 `memory/.../decisions/` 立一筆「v3 框架選型：預設 Claude Agent SDK」決策草案（屬 ask，待人工確認再寫）。
2. 設定觸發看板：以 `governance_metrics.py` 季度追蹤 v3 四條件。
3. 待任一觸發成立，先做 Claude Agent SDK 的 1 個 sub-agent PoC，再決定是否全面遷移。

## 來源

- [Best Multi-Agent Frameworks in 2026: LangGraph, CrewAI — Gurusup](https://gurusup.com/blog/best-multi-agent-frameworks-2026)
- [Claude Agent SDK vs LangGraph vs CrewAI: 2026 Benchmark — Pasquale Pillitteri](https://pasqualepillitteri.it/en/news/3095/claude-agent-sdk-vs-langgraph-vs-crewai-benchmark-2026-en)
- [AI Agent Frameworks (2026 Update): Claude Agent SDK Primitive Reference — Morph](https://www.morphllm.com/ai-agent-framework)
- [Agent SDK overview — Claude Code Docs](https://code.claude.com/docs/en/agent-sdk/overview)
- [2026 AI Agent Framework Showdown — QubitTool](https://qubittool.com/blog/ai-agent-framework-comparison-2026)

---
*字數約 1,750 字（中文實算）。web search：2 / 3 輪。skill：analysis。含「不做」選項與 7 維評估。*
