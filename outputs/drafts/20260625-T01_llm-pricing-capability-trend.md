<!--
task_id: 20260625-T01
date: 2026-06-25
skill_type: research
status: draft
-->

# 2026 LLM 價格 / 能力 / long-context 趨勢盤點

## 結論

2026 年中的 LLM 市場呈現「能力趨同、價格分層」的格局：前沿模型（Claude Opus 4.8、GPT-5.5、Gemini 3.1 Pro）在 1M token 長上下文的「真實可用率」拉開差距（約 74–76%），但同質化使選型重心從「誰最強」轉向「每千 token 多少錢、長上下文真有用嗎」。對一人公司而言，務實做法是**分層用模型**：高頻、低複雜任務走超低價 Flash 級（Gemini 3.1 Flash-Lite、DeepSeek V4 Flash，輸入低至 $0.10–$0.14/Mtok），需要推理品質與長上下文可靠度時才動用 Opus/GPT-5.5 級（輸入約 $5/Mtok）。2026 最值得注意的結構性變化：**Anthropic 取消長上下文加價**（過去 >200K token 部分輸入加倍計費，現行世代取消），降低了長文件處理的成本門檻。

## 已知事實

**主流供應商 API 價格（每百萬 token，輸入/輸出；資料截至 2026-06-18 更新）**

| 供應商 | 模型 | 輸入 $/Mtok | 輸出 $/Mtok |
|---|---|---|---|
| Anthropic | Claude Haiku 4.5 | 1 | 5 |
| Anthropic | Claude Sonnet 4.6 | 3 | 15 |
| Anthropic | Claude Opus 4.8 | 5 | 25 |
| Anthropic | Claude Fable 5（旗艦） | 10 | （高階定位） |
| OpenAI | GPT-5.4 | 2.50 | 15.00 |
| OpenAI | GPT-5.4 Pro | 30.00 | 180.00 |
| OpenAI | GPT-5.5 | 5（填 1M 窗計） | — |
| Google | Gemini 3.1 Flash-Lite | 0.10 | 0.40 |
| Google | Gemini 2.5 Flash | 0.15 | 0.60 |
| Google | Gemini 3 Flash | 0.50 | 3.00 |
| Google | Gemini 3.1 Pro | 4.00 | — |
| DeepSeek | V4 Flash / V4 Pro | 0.14 / 0.44 | — |

- 同級「填滿 1M token 輸入」的成本差距達 **71 倍**：DeepSeek V4 Flash 約 $0.14，Claude Fable 5 約 $10。
- Flash / Lite 級（Gemini 3.1 Flash-Lite $0.10/$0.40、Gemini 2.5 Flash $0.15/$0.60）明確定位高頻、高量、低成本場景。

**long-context 現況**

- 已有 **13 款模型搭載 1M+ token 上下文窗**，包含 Claude Fable 5、Claude Opus 4.8、GPT-5.5、Gemini 3.1 Pro、DeepSeek V4、MiniMax M3、Qwen3.5-Plus 等。
- 上限最高為 **Llama 4 Scout 的 10M token**，但獨立測試指出超過 1M 後「有效召回（recall）」明顯衰退。
- 2026 獨立測試：在「真正用得到 1M token」這件事上，**GPT-5.5 約 74%、Claude Opus 級約 76%** 為最可靠者——亦即「窗口大小」≠「可用程度」。
- **Anthropic 取消長上下文加價**：早期世代 >200K token 的輸入以 2× 計費，現行世代取消，是 2026 年最大的單一價格政策變化。

## 合理推論

- **價格分層已成預設架構**：依脈絡推論，主流用法不再是「一個模型打天下」，而是「便宜模型做量、貴模型做難」。依據：Flash/Lite 與 Opus/Pro 級價差達一到兩個數量級，且供應商主動以命名（Flash-Lite / Pro）區隔場景。
- **長上下文的瓶頸已從「容量」轉到「召回品質」**：依據為「10M 窗但 >1M 後召回衰退」「1M 真實可用率僅 74–76%」——容量競賽邊際效益遞減，品質與穩定度成為新戰場。
- **對一人公司／harness 的成本啟示**：本專案 COST_POLICY 的任務級預算（research 32K、analysis 20K）若以 Opus 級 $5/Mtok 估算，單任務 API 成本仍在數美分量級；瓶頸通常不是單價，而是「無謂重試與上下文灌水」（與 GLOBAL_RULES 的成本意識一致）。

## 待驗證

- Claude Opus 版本號：本次來源同時出現「Opus 4.7（$5/$25）」與「Opus 4.8（$5 輸入）」。以環境脈絡與較新來源採 **Opus 4.8** 為現行，但兩者並存屬 [待驗證]，輸出單價是否同為 $25 需再確認。
- GPT-5.5、Claude Fable 5 的**完整輸出單價**本次僅取得輸入或「填窗」單一數字，輸出端定價 [待驗證]。
- 「1M 真實可用率 74–76%」來自單一輪獨立測試彙整，方法學與樣本 [待驗證]，不宜當權威基準直接外引。
- 各家是否全面取消長上下文加價（本次僅確認 Anthropic）[待驗證]。

## 高風險假設

- **假設價格在採用期間維持穩定**：LLM 定價 2026 年仍在快速下行（本批資料 6 月才更新），任何 ROI 試算若鎖死當前單價，3–6 個月後可能失準。
- **假設「窗口越大越好」**：若據此把大量內容硬塞進單次 1M 上下文，可能因召回衰退而得到看似完整、實則漏讀的結果——對需精確引用的研究/合規任務風險最高。
- **假設超低價模型可無痛替代前沿模型**：Flash/Lite 在難推理、長鏈條任務的品質落差未在本次量化，直接替代有隱性品質風險。

## 來源

- [LLM API Pricing 2026 — BenchLM.ai](https://benchlm.ai/llm-pricing)
- [Claude API Pricing 2026: Opus 4.8, Sonnet 4.6, Haiku 4.5 — MetaCTO](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
- [LLM API Pricing 2026 — TLDL](https://www.tldl.io/resources/llm-api-pricing-2026)
- [LLM Context Window Comparison (2026) — Morph](https://www.morphllm.com/llm-context-window-comparison)
- [AI Context Window Comparison 2026: 1M to 10M Tokens — DigitalApplied](https://www.digitalapplied.com/blog/ai-context-window-comparison-2026-1m-to-10m-tokens)
- [Claude's 1 Million Context Window (2026) — Substack](https://karozieminski.substack.com/p/claude-1-million-context-window-guide-2026)

---
*字數約 1,450 字（中文實算，扣除 Markdown 標記與表格符號）。web search：2 / 3 輪。skill：research。*
