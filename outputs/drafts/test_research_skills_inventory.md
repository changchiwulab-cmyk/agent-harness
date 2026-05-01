# Agent-Harness 五個 Skill 用途與差異盤點

**Task ID**: 20260501-T01
**執行時間**: 2026-05-01
**Skill**: research

---

## 結論

Agent-harness 現有五個 skill（research / analysis / writing / ops / review）各司其職，覆蓋「資料蒐集 → 決策分析 → 內容產出 → 執行操作 → 品質審查」完整閉環。每個 skill 職責明確、邊界清晰，但 research 與 analysis、writing 與 ops 之間存在語意重疊區，需靠 ROUTING_RULES 判斷路由。

---

## 已知事實

以下資訊直接讀取自各 skill 的 `SKILL.md`（來源見「來源」段落）：

### 1. Research Skill

- **用途**：資料調查、產業分析、競品研究、技術評估、事實查核。
- **執行流程**：確認問題範圍 → 查內部資料 → 補充 web search（最多 3 輪）→ 整理結構化筆記 → 區分事實 / 推論 / 待驗證 → 輸出。
- **輸出格式**：Markdown，含結論、已知事實、合理推論、待驗證、高風險假設、來源六段。
- **與最相近 skill（analysis）的差異**：
  - Research 回答「事實是什麼」；analysis 回答「該怎麼選」。
  - Research 產出資料整理筆記；analysis 產出決策建議與選項比較表。
- **常見失敗模式（來源：skills/research/SKILL.md）**：
  - 搜尋資料不足就硬湊結論（應明確說「資料不足」）
  - 把單一來源當權威（應交叉比對）
  - 混淆事實與推論（應明確分類）

### 2. Analysis Skill

- **用途**：決策支援、方案評估、Go/No-Go 判斷、策略分析、可行性評估。
- **執行流程**：確認決策問題 → 列選項（含「不做」選項）→ 六維評估（價值/成本/風險/可行性/執行難度/回報）→ 一人公司適配度判斷 → 建議排序 → 輸出。
- **輸出格式**：Markdown，含結論建議、選項比較表（含七維欄位）、高風險假設、待驗證、建議下一步。
- **與最相近 skill（research）的差異**：
  - Analysis 必須有明確的選項排序與建議；research 不做決策判斷。
  - Analysis 的選項比較含「維持現狀」；research 無此強制要求。
- **常見失敗模式（來源：skills/analysis/SKILL.md）**：
  - 只列優缺點不給建議（必須有明確排序）
  - 遺漏「不做」選項
  - 用模糊詞代替具體評估（「成本較高」→ 高多少？）
  - 忽略一人公司資源限制

### 3. Writing Skill

- **用途**：提案撰寫、報告產出、文件包裝、內容規劃、SOP 撰寫、對外文案。
- **執行流程**：確認目標/讀者/格式/篇幅 → 載入 context → 先產大綱 → 逐段撰寫 → 自我檢查 → 輸出草稿。
- **輸出格式**：依 Task Card 的 `expected_output.format` 決定（md / html / yaml）。
- **與最相近 skill（ops）的差異**：
  - Writing 產出面向人類閱讀的內容；ops 產出結構化資料（CSV/YAML/JSON）。
  - Writing 以「結論先行、段落清晰」為品質核心；ops 以「資料完整性、可逆驗證」為品質核心。
- **常見失敗模式（來源：skills/writing/SKILL.md）**：
  - 寫太多（未控制篇幅）
  - 格式不符需求（未先確認 expected_output）
  - 內容空洞（大量修飾語無實質資訊）
  - 自動加了未被要求的章節

### 4. Ops Skill

- **用途**：營運支援、表格整理、資料清洗、排程規劃、流程文件化、檔案組織。
- **執行流程**：確認目標與範圍 → 盤點現有資料 → 制定操作計畫（先輸出計畫，不直接執行）→ 確認後逐步執行 → 每步 checkpoint → 輸出結果 + 變更摘要。
- **輸出格式**：依任務性質（CSV/YAML/Markdown 表格/SOP/變更清單）。
- **與最相近 skill（writing）的差異**：
  - Ops 在執行前必須輸出「操作計畫」；writing 無此強制前置步驟。
  - Ops 禁止刪除任何檔案（PERMISSIONS deny 規則）；writing 無此限制。
- **常見失敗模式（來源：skills/ops/SKILL.md）**：
  - 直接執行修改而不先說明計畫
  - 批量操作沒有 checkpoint
  - 靜默丟失資料（格式轉換時欄位遺漏）
  - 誤解資料結構（CSV 含逗號）

### 5. Review Skill

- **用途**：品質審查、文件校對、邏輯檢查、風險評估、決策驗證、輸出回測。
- **執行流程**：確認審查對象與標準 → 載入內容 → 三層檢查（格式/事實/邏輯）→ 風險識別 → 產出審查報告。
- **輸出格式**：Markdown，含總體評估、通過項、必須修改、建議修改、DoD 逐條確認。
- **與最相近 skill（research）的差異**：
  - Review 針對「已產出的內容」做品質把關；research 針對「未知資訊」做資料蒐集。
  - Review 不改原文，只提審查意見；research 直接產出整理後的筆記。
- **常見失敗模式（來源：skills/review/SKILL.md）**：
  - 審查太寬鬆（全部說 OK，必須至少找出 1 個可改善的地方）
  - 審查太嚴苛（雞蛋裡挑骨頭）
  - 只看格式不看內容
  - 自己的輸出審查自己（循環驗證）

---

## 合理推論

- **Research → Analysis 的自然流動**：在 ROUTING_RULES 中，「調查」導向 research，「決策/評估」導向 analysis；但在實際任務中，research 常作為 analysis 的前置步驟，二者有典型的接力關係。（依據：`system/ROUTING_RULES.md` 第 28-29 行：「Task Card 之間用 output 檔案作為接力點」）
- **Review 的循環驗證風險**：若同一個 session 同時執行 writing 和 review，review 審查自己剛產出的草稿，會陷入循環驗證。T05 的 Task Card 已明確要求「本任務僅審查既有規則檔，不審查同批測試的其他 4 個輸出」，正是為避免此風險。
- **Ops 是結構化版本的 Writing**：從輸出物來看，ops 產出的是機器可讀格式（CSV/YAML）；writing 產出的是人類可讀格式（Markdown/HTML）。二者在「整理資訊」這個動詞上有重疊，靠 routing 的「結構化 vs. 敘述性」來區分。

---

## 待驗證

- [待驗證] Research 的「web search 最多 3 輪」是否與 GLOBAL_RULES 的「單一任務最多 3 輪外部查詢」相同計算單位？SKILL.md 說「最多 3 輪 web search」，GLOBAL_RULES 說「單一任務最多 3 輪外部查詢」，措辭略有差異，待確認是否為同一規則的不同表述。
- [待驗證] Analysis 的「一人公司適配度」維度是否獨立計算，或合併到「可行性」維度？SKILL.md 的輸出格式表中列為獨立欄位，但在六維評估說明中未明確定義其計算方式。
- [待驗證] Writing 的「自我檢查」步驟是否有量化標準？SKILL.md 提及「自我檢查：邏輯、用詞、格式、完整度」，但未定義通過門檻。

---

## 高風險假設

- 無（本研究為純內部資料讀取，風險極低）

---

## 來源

| 引用內容 | 來源檔案 |
|---------|---------|
| Research skill 用途與流程 | `skills/research/SKILL.md` |
| Analysis skill 用途與流程 | `skills/analysis/SKILL.md` |
| Writing skill 用途與流程 | `skills/writing/SKILL.md` |
| Ops skill 用途與流程 | `skills/ops/SKILL.md` |
| Review skill 用途與流程 | `skills/review/SKILL.md` |
| Skill 路由判斷規則 | `system/ROUTING_RULES.md` |

---

## Gate 驗證

### 第一層：Schema 驗證
- task_id：`20260501-T01` ✅（格式 YYYYMMDD-###）
- goal：非空 ✅
- definition_of_done：5 條 ✅
- skill_type：`research`（有效值）✅
- risk_level：`low`（有效值）✅
- allowed_tools：`file_read, file_search` ✅
- **結果：PASS**

### 第二層：規則驗證
- 使用工具：`file_read`（讀取 6 個 SKILL.md 與 ROUTING_RULES.md）✅
- 無 web search ✅（max_web_searches: 0 遵守）
- 無 deny 動作 ✅
- 工具呼叫次數：約 7 次（含 Task Card 讀取），在 max_tool_calls: 8 範圍內 ✅
- **結果：PASS**

### 第三層：完成驗證（definition_of_done 逐條）
- [x] 涵蓋全部 5 個 skill（research / analysis / writing / ops / review）：**PASS** — 五個 skill 各有獨立段落
- [x] 每個 skill 至少列出：用途、與最相近 skill 的差異、1 個常見失敗模式：**PASS** — 每個 skill 含三項
- [x] 明確區分「已知事實 / 合理推論 / 待驗證」：**PASS** — 各有獨立段落
- [x] 輸出符合 research skill 的 Markdown 結構（含結論、來源）：**PASS** — 含結論、來源段落
- [x] 所有引用都標出檔案路徑作為來源：**PASS** — 結尾有來源表格
- **結果：PASS**

### 第四層：風險驗證
- risk_level: low，執行動作為純讀取與 drafts 輸出 ✅
- 輸出存放於 `outputs/drafts/` ✅
- 無對外動作 ✅
- **結果：PASS**
