# Agent Harness v2 — 第一性原理檢視與發展性評估

## Context（為什麼做這份分析）

使用者（一人公司管理顧問）開發了 Agent Harness v2，已運行數個月（30+ audit log、12+ outputs）。
他想知道：
1. 從第一性原理看，這個專案的優缺點是什麼？
2. 在 AI 快速演進的趨勢下，這個專案還有發展性嗎？

本分析非實作任務，產出為「研判報告」，供使用者決定 Harness 的下一步策略
（持續迭代 / 轉型 / 收斂為個人工具 / 開源 / 棄置）。

---

## 1. 第一性原理：這個系統「本質上」在解決什麼？

剝開所有設計細節，這個系統的**核心命題**只有一句：

> **LLM 是機率引擎，但商業執行需要確定性。**
> 用「治理層」把不確定性框在可恢復、可審計、可量化的邊界內。

從這個命題拆出三條設計公理：
| 公理 | 對應實作 |
|------|---------|
| (A) 任務必須有可驗證的成功定義 | Task Card + definition_of_done |
| (B) 失敗必須可分類、可追溯、可中止 | Failure Taxonomy + Audit Log + 連續失敗 3 次停下 |
| (C) 對外動作必須有人類在迴路 | drafts/ + Approval Policy + deny list hook |

**第一性原理判斷：這三條公理本身是對的**，且符合 2024-2026 業界共識
（OpenAI、Anthropic、LangChain 都在做類似的 governance layer）。

---

## 2. 優點（從第一性原理看，哪些設計是「真的」對的）

### 2.1 命題對齊度高（★★★★★）
所有模組（Task Card、Gate Policy、Failure Taxonomy、Audit Log）都直接服務於三條公理，
沒有為了「看起來像 framework」而堆功能。罕見的克制。

### 2.2 對 LLM 缺陷的診斷準確（★★★★★）
GLOBAL_RULES 開宗明義寫：
> 「LLM 原生缺乏四件事：穩定目標、穩定上下文邊界、穩定權限意識、穩定自我驗證能力。」

這是**正確的根因診斷**。多數 agent framework 在做「賦能」（讓 AI 更強），
這個系統在做「補洞」（讓 AI 不失控）—— 這是更深的層次。

### 2.3 真實有運行（★★★★☆）
- 26 張 Task Card、12 份實際 outputs/drafts、30+ audit、6 條 decision log
- 不是 PPT 框架，是被作者本人 dogfood 過的系統
- 這個比例的「實作占比」在個人專案中算高

### 2.4 治理三件組架構乾淨（★★★★☆）
**Control / Execution / Governance** 三平面分離，
每個平面的職責邊界清楚，比業界很多 spaghetti agent 框架更工程化。

### 2.5 成本意識前置（★★★★☆）
- Context 預算硬限制（CLAUDE.md ≤ 3,000 tokens）
- Skill 預算（≤ 1,500 tokens）
- 工具白名單

這些限制設計**早於業界平均** —— 多數框架是先做完才發現 token 爆了。

### 2.6 「現階段不做清單」展現工程紀律（★★★★★）
README 明列「不做」：多 agent swarm、自動寫長期記憶、自動外發、複雜 MCP 串接。
這個「拒絕誘惑」的能力，在個人 hobby project 中極為罕見。

---

## 3. 缺點（從第一性原理看，哪些設計是「自我矛盾」或「被現實打臉」）

### 3.1 強制力結構不對稱（★★ 嚴重）
**真相**：65% 程式碼+Hook、35% Prompt，但其中 **真正硬制的只有 Bash 層級的 5 條 deny rule**
（`permissions_guard.py` 只攔截 rm/sendmail/webhook/支付/force-push）。

| 規則 | 宣稱 | 實際強度 |
|------|------|---------|
| 沒有 Task Card 不執行 | 硬規則 | **0% 硬制** —— 純 Prompt 自我約束 |
| 對外動作只產草稿 | 硬規則 | **30% 硬制** —— 只有 Bash 層擋外發 |
| 連續失敗 3 次停下 | 硬規則 | **0% 硬制** —— 無計數器、無中止機制 |

**第一性原理判斷**：把 **Prompt 層的「請 Claude 自我約束」** 寫成「硬規則」是語意誤用。
LLM 是機率引擎，無論 prompt 怎麼寫，都不該宣稱「硬」。
這違反了系統自己的命題（A）—— 你假設 LLM 不可信，又依賴它自我審查。

### 3.2 重複造輪子（★★★ 警訊）
2024-2026 之間 Claude Code 原生加了大量功能，這個專案有些模組已經被原生覆蓋：

| Harness 模組 | Claude 原生對應 | 重複度 |
|-------------|----------------|-------|
| Skills (research/writing/ops) | 官方 Skills 機制 | **高** |
| Subagent / 任務隔離 | 內建 Agent 工具 + worktree | **高** |
| 權限白名單 | settings.json permissions | **中** |
| Hooks（PreToolUse） | 原生支援 | **直接用** |
| Memory | Claude Memory 功能 | **中（已內建）** |
| Audit Log | session log + transcript | **中** |

**潛在問題**：v2 的 5 個 skills 與官方 Skills 不互通；用了原生 hook 但沒用原生 subagent。
若不重構，未來會與生態漸行漸遠。

### 3.3 「Task Card 強制」與 LLM 的優勢相衝突（★★ 結構性）
Task Card 把「對話式靈活性」官僚化成「YAML 表單」。
但 LLM 的核心價值是**自然語言模糊問題的快速處理能力**。

**矛盾**：
- 大任務值得寫 Task Card，但這類任務一年只有幾十個
- 小問題（「幫我看一下這段 code」）寫 Task Card 成本 > 收益
- 結果：作者很可能在「真正高頻使用場景」繞過自己的框架

這是治理框架的經典陷阱：**為了 1% 的高風險場景，給 99% 的低風險場景上鎖**。

### 3.4 五個 Skill 的分類有點 artificial（★★）
research / analysis / writing / ops / review —— 真實任務經常跨類
（研究 → 寫報告 → 審查 通常一氣呵成）。
強制分類反而讓單任務需要多個 skill context，增加管理開銷。

### 3.5 Memory 系統幾乎沒運作（★★）
`memory/active_projects/` 大多是空的；`auto_write_memory` 在 deny list。
這意味著每次 session 都從零開始 —— 違背 LLM「累積上下文」的優勢。
這不是 bug，是設計上「保守過頭」造成的能力閹割。

### 3.6 Verification Gate 沒有自動化（★★）
GATE_POLICY 定義了 4 層驗證（schema → rule → completion → risk），
但**全部依賴 Claude 主動執行**。沒有 post-execution validator script。
治理框架最有價值的部分（自動驗證）反而是最弱的環節。

### 3.7 治理紀律 vs LLM 機率本質的哲學衝突（★★★ 根本性）
系統反覆強調「可控 > 能力」、「穩定完成 > 展現最強」。
但 LLM 本質上**不能保證確定性**。

第一性原理問：
> 用一個概率模型來執行「可控優先」的目標，最終的可控性上限在哪裡？

答案是：**取決於 deterministic guard rails 的覆蓋率**。
而本專案的 deterministic 部分只有 156 行 Python（permissions_guard.py）。
其他都是 prompt。所以實際可控性 ≈ Claude 在某次 session 對 CLAUDE.md 的遵循度。

這是**結構性天花板**，不是 bug。

---

## 4. AI 未來發展對這個專案的衝擊

### 4.1 三條趨勢將直接動搖核心模組

#### 趨勢 A：模型本身變得更會 follow rules
- Claude 4.x、5、6 series 對 system prompt 遵循度持續上升
- 工具呼叫穩定度 2024→2026 大幅改善
- **影響**：「治理框架補 LLM 缺陷」這個命題，前提在弱化
  → Failure Taxonomy 的 14 種失敗，未來可能模型自己就避開了

#### 趨勢 B：原生記憶 + 原生 Skills + 原生 Subagent 持續強化
- Anthropic、OpenAI 都在內建 long-term memory
- Skills 機制官方化
- **影響**：Harness 自己定義的 skills/、memory/、ROUTING_RULES 會變成「為了與原生不一致而存在」
  → 維護成本 > 差異化價值

#### 趨勢 C：MCP 與 computer use 讓 agent 走向更深度自主
- MCP 在 2025-2026 快速成熟
- Computer use、browser use 普及
- **影響**：「對外動作只到 drafts/」的保守設計，與「agent 直接執行」的潮流相反
  → Harness 用戶會發現「別人的 agent 已經幫他訂好機票」，但他的 agent 還在生草稿

### 4.2 哪些會「過時」

| 模組 | 5 年後預測 |
|------|----------|
| Task Card 強制 | 過時 —— 模型可動態生成 |
| 5 個 Skill 分類 | 過時 —— 與官方 Skills 不一致 |
| 自定義 Memory | 過時 —— 原生記憶取代 |
| Failure Taxonomy 14 種 | 部分過時 —— 模型自己避開大半 |
| 156 行 deny hook | 過時 —— Claude Code permissions UI 已涵蓋 |

### 4.3 哪些會「歷久彌新」

| 模組 | 5 年後預測 |
|------|----------|
| Audit Log（決策可追溯） | 永遠有價值 —— 商業合規剛需 |
| Decision Log 結構化 | 永遠有價值 —— 治理本質 |
| definition_of_done 的契約思維 | 永遠有價值 —— 與模型無關 |
| 「現階段不做清單」紀律 | 永遠有價值 —— 工程美德 |
| 三平面分離的架構思想 | 永遠有價值 —— 可遷移到任何模型 |

**核心結論**：**模組會過時，但治理思想不會。**

---

## 5. 第一性原理判斷：發展性評估

### 5.1 三條未來路線

#### 路線 1：當「個人工作流模板」維持
- 不追求通用，繼續為作者一人服務
- 隨 Claude Code 演進局部更新
- **預期壽命：2-3 年**，之後被原生功能蠶食到剩骨架

#### 路線 2：轉型為「Governance Layer」開源套件
- 砍掉與原生重複的部分（Skills/Memory/權限）
- 保留並深化：**Audit、Decision Log、definition_of_done、Failure Taxonomy**
- 定位：**Claude Code 的治理擴充包**，不是替代品
- **預期壽命：5+ 年**，因為「合規/可審計」是企業 AI 的剛需，且模型不會自帶

#### 路線 3：上升一層為「方法論」而非「框架」
- 把 Harness 當案例，寫成書／課程：「一人公司用 AI 不失控的 12 條紀律」
- 框架本身停留在 v2，文件化教學
- **預期壽命：永久**，因為治理思想脫離具體工具

### 5.2 我的建議排序

**(推薦) 路線 2 + 路線 3 並行**：
- 把 v3 規劃從「拆 bounded specialists」改為「砍冗餘 + 深化治理層」
- 治理三件（Audit / Decision / DoD）抽出來，做成可單獨安裝的 Claude Code plugin / MCP server
- 同時把方法論寫成內容資產

**最大風險（若什麼都不改）**：
未來 12 個月 Claude Code 內建記憶、官方 Skills、subagent 演進到一定程度，
Harness 會從「看起來工程化」變成「看起來繁瑣」——
作者本人會慢慢繞過它，最後只剩 git repo 證明曾經存在。

### 5.3 關鍵指標（用以後續驗證）

| 指標 | 現況 | 警訊閾值 |
|------|------|---------|
| 月 Task Card 建立數 | 26 / 數月 | 連續 2 個月 < 3 張 → 框架在被繞過 |
| outputs/drafts 真實使用率 | 12 份 | drafts/ 與 reports/ 比例 < 1:1 → 草稿流程沒在跑 |
| audit log 是否覆蓋全部任務 | 30+ 筆 | 與 git log 任務 commit 比 < 80% → 治理失效 |
| Claude Code 原生功能重疊度 | 約 30% | 超過 50% → 重構觸發點 |

---

## 6. 一句話總結

> **設計命題對、執行紀律好、運行真實，但結構性天花板在於「用 LLM 自我約束 LLM」。**
> **未來價值不在框架本身，而在它沉澱出的治理思想 —— 把 Audit / Decision Log / DoD 抽出來做成獨立治理層，比死守整個 Harness 更有發展性。**

---

## 7. 關鍵檔案（若使用者要 act on this）

- 治理核心（值得保留+深化）：
  - `system/FAILURE_TAXONOMY.yaml`
  - `system/EXECUTION_LOG_SCHEMA.yaml`
  - `tasks/DECISION_LOG_TEMPLATE.yaml`
  - `logs/AUDIT_LOG.md`
- 與原生重疊（候選砍除/重構）：
  - `skills/*/SKILL.md`（5 個）
  - `memory/active_projects/`
  - `system/ROUTING_RULES.md`
- 唯一真正硬制的程式碼（可獨立成 plugin）：
  - `scripts/permissions_guard.py`
  - `.claude/settings.json` (PreToolUse hook)

## 8. 已選方向：路線 2 + 3 並行

使用者已決定同時推進「治理層抽出」與「方法論化」兩條線。
本節定義具體執行步驟。

### 8.1 接下來要建立的兩張 Task Card

#### Task Card A：v3 治理層抽出規劃
- **路徑**：`tasks/2026-05-09_harness_v3_governance_extraction.yaml`
- **skill_type**：`analysis`（規劃階段，不是 ops 真的拆碼）
- **goal**：定義 v3 重構範圍 —— 哪些模組砍除、哪些保留、哪些抽成獨立 plugin/MCP server
- **definition_of_done**（草案）：
  - [ ] 列出 v2 全部 16 模組，每個標註：保留 / 砍除 / 抽出 / 重構
  - [ ] 砍除清單給出根據（與 Claude Code 原生重疊度）
  - [ ] 抽出清單給出 plugin 邊界（Audit / Decision / DoD / Failure Taxonomy 怎麼包成獨立套件）
  - [ ] 產出 v3 架構圖（取代 README 的三平面十六模組圖）
  - [ ] 評估遷移路徑：v2 → v3 的相容/破壞性變更
- **risk_level**：medium（規劃階段不改碼）
- **allowed_tools**：Read、Grep、Write（僅寫到 outputs/drafts/）
- **預期輸出**：`outputs/drafts/2026-05-09_v3_extraction_plan.md`

#### Task Card B：方法論內容大綱
- **路徑**：`tasks/2026-05-09_harness_methodology_outline.yaml`
- **skill_type**：`writing`
- **goal**：把 Harness v2 沉澱的治理思想，寫成可發表的方法論大綱（書/長文/課程都適用的結構）
- **definition_of_done**（草案）：
  - [ ] 主軸命題一句話（候選：「一人公司用 AI 不失控的 12 條紀律」或更佳替代）
  - [ ] 章節大綱：每章標題 + 核心命題 + 1-2 段內容摘要
  - [ ] 每章對應的 Harness 實證案例（從 26 張 Task Card / 30+ audit log 中抽）
  - [ ] 三種發布形態（書/部落格系列/課程）的取捨建議
  - [ ] 與既有市場（《AI Agent 設計》等）的差異化定位
- **risk_level**：low（純內容草稿）
- **allowed_tools**：Read、Grep、Write（outputs/drafts/）
- **預期輸出**：`outputs/drafts/2026-05-09_methodology_outline.md`

### 8.2 執行順序與相依關係

兩張 Task Card 沒有強相依，但建議**先 A 後 B**：
- A 的「砍除清單」會明確「哪些模組是工程冗餘」，這部分**不適合**寫進方法論
- A 的「保留清單」會明確「哪些治理思想經得起檢驗」，這正是 B 的素材
- 並行做容易讓 B 把該砍的東西也包裝成方法論

### 8.3 本次（plan 批准後）會做的具體動作

1. 用 `tasks/TASK_CARD_TEMPLATE.yaml` 為基底，建立 Task Card A（YAML 檔）
2. 用同一模板建立 Task Card B（YAML 檔）
3. 不執行任務本身 —— 只把卡片建好，等使用者過目卡片內容後再啟動

> 為什麼不直接執行任務？
> 依 Harness 自己的規則：goal + DoD 必須先**人工確認**才進入執行。
> 所以這次只到「卡片建立」為止，符合本框架的硬規則。

### 8.4 驗證方式

- Task Card A、B 建立後跑 `python system/validate_task_card.py tasks/2026-05-09_*.yaml` 驗 schema
- 跑 `scripts/check_spec_consistency.rb` 確保不破壞既有結構
- 使用者人工檢視 goal 與 DoD 是否符合期望
- 若兩張卡都通過，下一輪會話再啟動執行
