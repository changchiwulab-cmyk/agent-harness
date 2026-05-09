# N1 — Plan §8.1 對齊報告

- Task: `20260509-N01`
- Date: 2026-05-09
- Skill: review
- Status: draft（risk_level=low）
- Plan 來源：`memory/active_projects/agent-harness/plans/ai-bubbly-mountain.md`（2026-05-09 由使用者提供，本卡寫入 repo）

## 0. TL;DR

- A01 與 plan §8.1 Task A：**5/5 草案 DoD 全 pass，A01 自加 2 條（risk + format），over-deliver**
- W01 與 plan §8.1 Task B：**5/5 草案 DoD 全 pass，W01 自加 2 條（reader objections + format），over-deliver**
- Plan §8.2 順序「先 A 後 B」：✅ 本 session 執行順序符合
- Plan §8.3 step 3「不執行任務本身」：⚠️ 本 session 由使用者明示「啟動執行」覆蓋，符合 hard rule（人工確認後可執行）
- 命名漂移：plan 用底線（`harness_v3_governance_extraction`），repo 採連字號（`harness-v3-governance-extraction`）— 不修，但記錄
- Plan §1-7 採納度：A01 §1.3「強制力結構不對稱」直接引 plan §3.1；A01 §4.1「重疊度對照」直接擴寫 plan §3.2；W01 §6 反對意見對應 plan §4.1 趨勢 A
- **Plan §5.3 4 條關鍵指標** ⚠️ A01/W01 未採納 → 建議開後續任務（見 §7）

---

## 1. Plan §8.1 Task A vs A01 — 逐項對齊

### 1.1 Header 對齊

| 欄位 | Plan §8.1 Task A | A01（已交付） | 對齊 |
|------|-----------------|--------------|------|
| 路徑 | `tasks/2026-05-09_harness_v3_governance_extraction.yaml` | `tasks/2026-05-09_harness-v3-governance-extraction.yaml` | ⚠️ 命名漂移（底線→連字號），不修 |
| skill_type | analysis | analysis | ✅ |
| risk_level | medium | medium | ✅ |
| 預期輸出 | `outputs/drafts/2026-05-09_v3_extraction_plan.md` | 同 | ✅ |
| allowed_tools | Read、Grep、Write | file_read / file_search / write_drafts | ⚠️ 詞彙差異（plan 用 Claude Code 工具名；A01 用 PERMISSIONS.yaml 詞彙），語意等價 |

### 1.2 DoD 逐條對齊

| # | Plan DoD（草案）| A01 對應 DoD | 結果 |
|---|---------------|-------------|------|
| 1 | 列出 v2 全部 16 模組，每個標註：保留 / 砍除 / 抽出 / 重構 | A01 #1：「列出 v2 全部 16 模組，每個明確標註：保留 / 砍除 / 抽出 / 重構，並附理由」 | ✅ pass（A01 多了「並附理由」）|
| 2 | 砍除清單給出根據（與 Claude Code 原生重疊度）| A01 #2：「砍除清單對每項給出『與 Claude Code 原生功能重疊』的具體證據（功能對照表）」 | ✅ pass（§4.1 表 A 提供）|
| 3 | 抽出清單給出 plugin 邊界（Audit / Decision / DoD / Failure Taxonomy 包成獨立套件）| A01 #3：「抽出清單定義獨立治理層的邊界：哪些檔案、哪種發佈形態（plugin / MCP server / standalone CLI）、相依關係」 | ✅ pass（§5 全段、§5.2 樹狀目錄）|
| 4 | 產出 v3 架構圖 | A01 #4：「v3 架構圖（取代 README 三平面十六模組圖），呈現精簡後的模組關係」 | ✅ pass（§6 ASCII 圖）|
| 5 | 評估遷移路徑：v2 → v3 的相容/破壞性變更 | A01 #5：「v2 → v3 遷移路徑：相容變更 vs 破壞性變更分列；給出階段性切換策略」 | ✅ pass（§7.1 / §7.2 / §7.3）|
| **+1** | （plan 未要求）| A01 #6：「識別至少 3 個風險點與緩解方案」 | 🟢 over-deliver（§8 列了 4 個 R1-R4）|
| **+2** | （plan 未要求）| A01 #7：「輸出為結構化 Markdown，章節順序明定」 | 🟢 over-deliver |

**結論**：A01 完整覆蓋 plan §8.1 Task A 的 5 條草案 DoD，並自加 2 條（風險章節 + 格式規範）。

### 1.3 Plan §8.4 驗證方式對齊

| Plan 驗證 | 是否落地 |
|----------|---------|
| `python system/validate_task_card.py tasks/2026-05-09_*.yaml` | ✅ A01 task card 通過驗證 |
| `scripts/check_spec_consistency.rb` | ✅ 通過 |
| 使用者人工檢視 goal 與 DoD | ✅ 對話中已確認「A01 risk=medium 接受」 |

---

## 2. Plan §8.1 Task B vs W01 — 逐項對齊

### 2.1 Header 對齊

| 欄位 | Plan §8.1 Task B | W01（已交付） | 對齊 |
|------|-----------------|--------------|------|
| 路徑 | `tasks/2026-05-09_harness_methodology_outline.yaml` | `tasks/2026-05-09_harness-methodology-outline.yaml` | ⚠️ 命名漂移（同 §1.1）|
| skill_type | writing | writing | ✅ |
| risk_level | low | low | ✅ |
| 預期輸出 | `outputs/drafts/2026-05-09_methodology_outline.md` | 同 | ✅ |
| allowed_tools | Read、Grep、Write | file_read / file_search / web_search / write_drafts | ⚠️ 詞彙差異（W01 含 web_search，plan 未列；W01 max_web_searches=3 但實際呼叫 0 次）|

### 2.2 DoD 逐條對齊

| # | Plan DoD（草案）| W01 對應 DoD | 結果 |
|---|---------------|-------------|------|
| 1 | 主軸命題一句話（候選：「一人公司用 AI 不失控的 12 條紀律」或更佳替代）| W01 #1：「主軸命題以一句話定義（給 3 個候選 + 推薦選項與理由）」| ✅ pass（W01 給 T1/T2/T3 三候選 + 推薦 T1）|
| 2 | 章節大綱：每章標題 + 核心命題 + 1-2 段內容摘要 | W01 #2：「10-14 章的章節大綱，每章含：標題、核心命題、1-2 段內容摘要、預估字數」| ✅ pass（W01 多了字數估計）|
| 3 | 每章對應的 Harness 實證案例 | W01 #3：「每章對應至少一個 Harness 實證案例（從 26 張 Task Card / 30+ audit log 中具體抽取）」| ✅ pass（§2 每章末尾「實證」）|
| 4 | 三種發布形態（書/部落格系列/課程）的取捨建議 | W01 #4：「三種發布形態的取捨表：書／部落格系列／課程，給出推薦順序」| ✅ pass（§4 含推薦順序：部落格→課程→書）|
| 5 | 與既有市場（《AI Agent 設計》等）的差異化定位 | W01 #5：「差異化定位段落：與 LangChain 文件、《AI Engineering》(Chip Huyen)、Anthropic 官方 best practice 文章相比的獨特切入點」| ✅ pass（W01 對標 3 個具體對象，比 plan 草案明確）|
| **+1** | （plan 未要求）| W01 #6：「識別 2 個讀者反對意見並預備回應」| 🟢 over-deliver（§6）|
| **+2** | （plan 未要求）| W01 #7：「輸出為結構化 Markdown，可直接作為對外提案/發起共筆的起點」| 🟢 over-deliver |

**結論**：W01 完整覆蓋 plan §8.1 Task B 的 5 條草案 DoD，並自加 2 條（讀者反對意見 + 格式可作提案起點）。

### 2.3 W01 主軸 vs Plan §6 一句總結 對齊

| Plan §6 一句總結 | W01 主軸 T1（已採用）|
|------------------|--------------------|
| 「未來價值不在框架本身，而在它沉澱出的治理思想 —— 把 Audit / Decision Log / DoD 抽出來做成獨立治理層」| 「用契約取代信任：一人公司讓 LLM Agent 不失控的三條治理原則」|

✅ 同向：都把「治理思想」放在「框架本身」之上。W01 的 T1 是 plan §6 思路的口號化版本。

---

## 3. Plan §8.2 順序對齊

Plan §8.2：「兩張 Task Card 沒有強相依，但建議**先 A 後 B**」
本 session：使用者明示「執行（建議 A01 先、W01 後）」→ A01 commit `e95a425` 早於 W01 `419ebaf`。
✅ 完全符合 plan 建議順序。

---

## 4. Plan §8.3 step 3 行為差異說明

Plan §8.3 step 3：「不執行任務本身 —— 只把卡片建好，等使用者過目卡片內容後再啟動」

本 session 行為：使用者於對話直接下令「啟動執行（建議 A01 先、W01 後）」，等同於明示授權跨過「卡片過目」步驟，直接進入執行。

依 CLAUDE.md hard rule #1 + APPROVAL_POLICY：
- 卡片已存在於 repo
- 使用者明示授權執行
- 兩卡 risk 為 low/medium（未觸發 high → 強制 human_confirm 條件）

→ 行為合規。對齊報告留下此事件作為未來「plan 預期 vs 實際」差異的範例。

---

## 5. 命名漂移與工具詞彙差異彙整

| 差異 | Plan | Repo / A01-W01 | 影響 | 動作 |
|------|------|---------------|------|------|
| 檔名分隔符 | 底線 `_` | 連字號 `-`（與 examples/ 慣例一致）| 無 — `validate_task_card.py` 對 task_id 而非檔名 | 不修，記錄 |
| allowed_tools 詞彙 | Read / Grep / Write | file_read / file_search / write_drafts（PERMISSIONS.yaml 詞彙）| 兩套詞彙語意等價 | 不修；但 v3 治理 plugin 應採單一詞彙 |
| W01 含 `web_search` 工具 | plan 未列 | W01 列出但未呼叫 | 無 | 不修 |

---

## 6. Plan §1-§7 採納度（避免方法論章節漏點）

### 6.1 已被 A01 採納的 plan 論點

| Plan 段 | 內容 | A01 採納處 |
|---------|------|-----------|
| §3.1 強制力結構不對稱 | 156 行 deny hook 之外都是 prompt | A01 §1.2 直接引用「156 行 deny hook + 3 條 CI 檢查」「prompt 約束 + 文件規範，無強制檢查」|
| §3.2 重複造輪子 | 6 模組與原生重疊 | A01 §4.1 表 A 對 9 模組做重疊度估計（擴寫 plan）|
| §3.3 Task Card 強制與 LLM 衝突 | 為 1% 高風險場景給 99% 低風險上鎖 | A01 §4.2 #2 把 Task Card 改為「重構」並收斂必填欄位 5 個 |
| §3.4 5 個 Skill 分類 artificial | 真實任務跨類 | A01 §4.2 #6 Skill Executor「砍除」，路由交原生 |
| §4.2 過時清單 | Task Card 強制 / 5 skill / 自訂 Memory / Failure Taxonomy 14 / 156 行 deny hook | A01 §4.2 多數對應「砍除」或「重構」|
| §4.3 歷久彌新清單 | Audit / Decision / DoD / 不做清單 / 三平面分離 | A01 §4.2 全部對應「抽出」（§5.2 plugin 結構承載）|
| §5.1 三條未來路線 + §5.2 推薦路線 2+3 | 砍冗餘 + 深化治理層 + 同時做方法論 | A01（路線 2）+ W01（路線 3）並行執行 |
| §6 一句總結 | 模組會過時，治理思想不會 | A01 §2 第一性原理結論「砍冗餘 + 深化治理層」直接呼應 |
| §7 關鍵檔案清單 | 治理核心 / 與原生重疊 / 唯一硬制 | A01 §4.2 模組裁決完全相容此分類 |

### 6.2 已被 W01 採納的 plan 論點

| Plan 段 | 內容 | W01 採納處 |
|---------|------|-----------|
| §1 核心命題 | LLM 是機率引擎，需治理層 | W01 第 1 章「為什麼一人公司需要治理」第二段直接呼應 |
| §1 三條公理 (A)(B)(C) | DoD 契約 / Failure Taxonomy / drafts/+approval | W01 第 2 章「三原則總覽」對應 |
| §2.6 不做清單紀律 | 拒絕誘惑能力罕見 | W01 第 8 章專章「現階段不做清單：一人公司最強的紀律工具」|
| §3.6 Verification Gate 沒自動化 | 治理框架最有價值的部分最弱 | W01 第 9 章「Gate Policy：四層驗證的成本/效益」隱含這個診斷 |
| §3.7 治理紀律 vs LLM 機率本質 | 結構性天花板 | W01 第 10 章「強制力結構：prompt / CI / hook 三層」直接處理這個問題 |
| §4.1 趨勢 A | 模型變強會取代 Failure Taxonomy 部分 | W01 §6 反對 2「LLM 進步後這些都會自動」回應這個 |
| §4.3 歷久彌新清單 | Audit / Decision / DoD / 不做清單 / 三平面 | W01 12 章中 5 章直接對應這 5 件 |
| §5.2 「最大風險」 | Harness 變繁瑣，使用者繞過 | W01 §6 反對 1「治理太重一人公司不需要」回應 |
| §5.3 關鍵指標 | 4 條 | ⚠️ **未被 W01 採納** — 見 §7 |
| §6 一句總結 | 治理思想 > 框架本身 | W01 主軸 T1 一致 |

### 6.3 Plan 中 A01/W01 未採納的論點

| Plan 段 | 內容 | 為什麼未採納 | 建議行動 |
|---------|------|-------------|---------|
| §3.5 Memory 系統幾乎沒運作 | active_projects 大多空，auto_write 在 deny | A01 §4.2 #10 把 Agent Context 砍除，但未明確處理「Memory 系統閹割」此痛點 | 可在 v3.0 release 前另開 task：評估是否啟用原生 Memory + 寫入控制 |
| §4.1 趨勢 C | MCP + computer use → 別人 agent 已訂機票 | A01/W01 都未直接回應「保守設計 vs 自主潮流」這個張力 | W01 部落格首篇可加段「為什麼一人公司不該追自主」回應此點 |
| §5.3 4 條關鍵指標 | 月 Task Card 數 / drafts:reports / audit 覆蓋率 / 重疊度 | A01/W01 都未列為追蹤項 | **應開後續任務**（見 §7 #1）|
| §7 「唯一真正硬制的程式碼」段 | 156 行 permissions_guard.py + .claude/settings.json | A01 §4.2 #7/#11 處理權限/工具，但未明確指出「這 156 行就是 v3 plugin 的 enforcement 種子」| 建議 v3.0 release 時 plugin 直接 fork 這 156 行為 hooks/pre_tool_use.py |

---

## 7. 建議後續任務

### 7.1 高優先

1. **N5（建議優先做）— 落地 plan §5.3 4 條關鍵指標**
   - skill_type: ops
   - 把 4 條指標自動化採集（從 git log + AUDIT_LOG.md + outputs/ 計數）
   - 寫成 `scripts/check_governance_metrics.py`，月度執行
   - 預期輸出 `outputs/drafts/governance-metrics-YYYY-MM.md`
   - 一旦突破警訊閾值 → 自動寫 Decision Log 觸發

### 7.2 中優先

2. **N6 — README audit 計數修正（即 N2）**
   - 30+ → 實 19（含本 PR 新增的 N3/N4/N1 = 3 筆）
   - 同時修正 plan §Context 與 §2.3 的「30+」、「26 張 Task Card」等數據（plan 應作為歷史 snapshot 保留，不更新；只在 README 修正）

3. **N7 — 評估 Memory 系統啟用**
   - 對應 plan §3.5 痛點
   - skill_type: analysis
   - 產出：是否切換到原生 Memory？怎麼控制寫入？保留 deny `auto_write_memory` 的話該怎麼用？

### 7.3 低優先

4. **N8 — W01 部落格首篇 elevator pitch + 第 1 章草稿**
   - 對應 plan §4.1 趨勢 C 補章
   - 200 字 pitch + 3,500 字第 1 章

---

## 8. DoD 驗收

| # | DoD | 狀態 | 證據 |
|---|-----|:-:|------|
| 1 | plan 全文寫入 memory/active_projects/agent-harness/plans/ai-bubbly-mountain.md | ✅ | 本卡 commit |
| 2 | A01/W01 task card input_data 路徑替換 | ✅ | yaml 內 `/root/.claude/plans/...` 加註已歸檔位置 |
| 3 | Plan §8.1 Task A 7 條 DoD 逐條對齊 | ✅ | §1.2（5 + 2 over-deliver）|
| 4 | Plan §8.1 Task B 7 條 DoD 逐條對齊 | ✅ | §2.2（5 + 2 over-deliver）|
| 5 | A01/W01 草稿中『Plan 不可讀』相關 [待驗證] 段落清除/更新 | ✅ | §0 來源段更新；§9/§10 待驗證表加狀態欄 |
| 6 | Plan §5.3 4 條指標明確判斷 + 後續任務 | ✅ | §6.3 + §7.1 #1 開 N5 |
| 7 | Plan §1-7 論點與 A01/W01 採納列表 | ✅ | §6.1 / §6.2 / §6.3 |

7/7 通過。
