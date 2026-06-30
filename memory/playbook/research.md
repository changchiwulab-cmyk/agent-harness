# Research Playbook

程序記憶：research skill 的可重用啟發與踩過的坑。格式見 `PLAYBOOK_ENTRY_TEMPLATE.md`。

<!-- ENTRY id=PB-research-001 skill=research tags=web-search,rate-limit,cost -->
## 保留 1 輪 web search 緩衝，不要 3/3 用滿
連續呼叫 web search 會觸發外部服務 rate limit；正常用至多 2 輪，保留 1 輪供遇阻補救。
觸發 rate limit 時以既有結果 + 自身知識補洞，不立即重試。
來源：memory/episodes/20260404-E001_research-web-search-rate-limit.yaml / outputs/drafts/retro-2026-04-15.md

<!-- ENTRY id=PB-research-002 skill=research tags=sources,quality,fact-check -->
## 每個事實主張都要綁具體來源
「根據研究」「據報導」不算來源。事實與推論分區塊寫；不確定的標 [待驗證]。
搜尋結果要消化重組，不直接複製貼上。
來源：skills/research/eval_examples.md 判斷標準

<!-- ENTRY id=PB-research-003 skill=research tags=internal-first,cost -->
## 先查內部資料再 web search
先查 memory/（episodes/playbook/decisions）與既有 outputs/，不足時才上網。
能讀檔解決的不耗 web search 額度。
來源：skills/research/SKILL.md 執行流程 / system/COST_POLICY.md
