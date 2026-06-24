# Agent Harness v2 → v3 遷移就緒度評估

> **草稿（draft）** ｜ 日期：2026-06-24 ｜ Task Card：`20260529-012`（R10）｜ skill：analysis ｜ risk：high
> 交付範圍：**只評估不遷移**。本文件不改任何 `system/` 模組檔、不建 v3 plugin、不翻 D003/D007 決策本體。
> 來源 roadmap：`outputs/reports/harness-self-assessment-v1.md` §五 R10。
> 對齊基準：`outputs/drafts/2026-05-09_v3_extraction_plan.md`（裁決）＋`system/NATIVE_OVERLAP.yaml`（重疊數據）。
> 審閱通過後可依 `RETRO_FLOW` 晉升至 `outputs/reports/`。

---

## 摘要

| 項目 | 結論 |
|------|------|
| **整體就緒度** | **未就緒（hold）** — 設計面已想清楚（extraction plan 完備），但三項關鍵假設（H1/H2/H3）未驗證，且 plugin 落地尚未發生 |
| **強制觸發點** | 未達。`NATIVE_OVERLAP.aggregate_estimate_pct = 30%` < 50% 閾值；D003 四項升級觸發條件亦全未達標 |
| **可立即下放（ready）** | Interface、Skill Executor、Agent Context — 與原生重疊高且已具備（N3 PoC 驗證 frontmatter） |
| **被卡住（blocked）** | Planner/Router（待 H1）、Permission（待 H2）、所有抽出件的 plugin home（待 H3） |
| **不可替代資產（必須保留/抽出）** | 校準表、FAILURE_TAXONOMY、Decision Log、Audit Log（＋Gate/Approval/Execution Log schema）— 原生完全不提供 |
| **建議** | 維持「只評估不遷移」。先補 H1/H2/H3 驗證與 analysis 校準樣本，再談 v2.5 過渡 |

**就緒度視角 vs extraction plan**：`2026-05-09_v3_extraction_plan.md` 回答「v3 該長怎樣」（裁決：砍/抽/重構/留）；本評估回答「**現在搬得動嗎、搬之前缺什麼**」（就緒度：ready/blocked + 缺口）。兩者互補，不取代。

---

## 一、就緒度判準

把 extraction plan 的四態裁決（砍除／抽出／重構／保留）映射為 R10 的**三態 + 就緒度**：

| R10 三態 | 定義 | 對應 extraction plan 裁決 |
|---------|------|--------------------------|
| **下放原生** | 原生已 first-class 且穩定，可移除 harness 對應件、改靠原生 | 多數「砍除」 |
| **並存** | 與原生部分重疊，但 harness 補了原生缺的維度（如 risk_level）；過渡期/長期保留薄層 | 多數「重構」 |
| **保留** | 原生**完全不提供**的治理資產；必須留下（並為抽出成獨立治理層的候選） | 全部「抽出」＋治理性「重構」＋git 慣例 |

| 就緒度 | 意義 |
|-------|------|
| **ready** | 前置條件已具備，可進入 v2.5 過渡 |
| **blocked** | 卡在某個未驗證假設或缺資料，需先解 |

---

## 二、逐模組三態裁決表

> 重疊數據取自 `system/NATIVE_OVERLAP.yaml`；裁決對齊 extraction plan §4.2；就緒度為本評估新增。

| # | v2 模組 | 重疊% | extraction plan | **R10 三態** | 就緒度 | 缺什麼（blocked 原因）/ 依據 |
|---|---------|:----:|:----:|:----:|:----:|------|
| 1 | Interface | 100 | 砍除 | **下放原生** | ready | 本就是 runtime（CLI/web/IDE），非模組 |
| 2 | Task Card / DoD 契約 | — | 重構 | **保留** | ready | DoD 契約原生無；瘦身欄位即可，不阻塞 |
| 3 | Planner/Router (ROUTING_RULES) | 70 | 砍除 | **下放原生** | **blocked** | **H1 未驗**：原生 Skill 自動路由是否能全替代手動路由表 |
| 4 | Decision Log | — | 抽出 | **保留** | ready | 原生 memory 無結構化決策 schema（見 §三） |
| 5 | Context Manager (CLAUDE.md 規則段) | 50 | 重構 | **並存** | ready | 原生有 20 輪自動壓縮；token 硬上限仍需 CI 護欄（`check_context_budget.rb`），故並存 |
| 6 | Skill Executor (skills/) | 85 | 砍除 | **下放原生** | ready | N3 PoC 已驗 frontmatter 解析 + `.claude/skills/research` symlink |
| 7 | Tool Executor (allowed_tools) | 80 | 重構 | **並存** | blocked | enforcement 已在 `permissions_guard.py`；但 hook 仍需 Task Card `allowed_tools` 作輸入 → 與 settings.json 並存（隨 H2） |
| 8 | Gate Verifier (GATE_POLICY) | — | 抽出 | **保留** | blocked | 四層驗證+rollback 原生無；plugin home 待 H3 |
| 9 | Checkpoint (git commit) | 0 | 砍除 | **保留** | ready | 原生 0% 對應；是 git 慣例不是模組，續用即可（**與 plan「砍除」分歧，見 §四**） |
| 10 | Agent Context (AGENT_CONTEXT) | 60 | 砍除 | **下放原生** | ready | 內容併回 CLAUDE.md「邊界」段即可 |
| 11 | Permission (PERMISSIONS.yaml) | 75 | 重構 | **並存** | **blocked** | **H2 未驗**：settings.json allow/ask/deny 與 risk_level 維度能否正交組合 |
| 12 | Approval Policy | — | 重構 | **保留** | ready | draft_first/human_confirm 流程原生無；邏輯併入 Decision Log + Task Card workflow 但屬治理資產 |
| 13 | Cost Policy | 40 | 重構 | **並存** | blocked | 校準表＝資產須保留（§三）；行為段下放 CLAUDE.md。**analysis 校準 0 筆**，校準資料未完整 |
| 14 | Failure Taxonomy | — | 抽出 | **保留** | blocked | 14 類知識資產原生無；plugin home 待 H3 |
| 15 | Execution Log Schema | — | 抽出 | **保留** | blocked | 窄範圍 post-mortem schema 原生無；plugin home 待 H3 |
| 16 | Audit Log | — | 抽出 | **保留** | blocked | append-only + CI 格式檢查原生無；plugin home 待 H3 |

**統計（R10 三態）**：下放原生 **4**（#1,3,6,10）／並存 **4**（#5,7,11,13）／保留 **8**（#2,4,8,9,12,14,15,16）。
**就緒度**：ready **7**／blocked **9**。blocked 集中在兩處根因：**H1/H2 假設未驗**（#3,#11，連帶 #7）與 **plugin home 未建（H3）**（#8,#14,#15,#16，連帶 #13）。

---

## 三、不可替代的治理資產（必須保留 / 抽出）

R10 明確要求點出原生**完全不提供**、因此不可下放的資產。這四件是 v2 真正的護城河：

| 資產 | 位置 | 原生為何不提供 | 去向 |
|------|------|---------------|------|
| **校準表** | `system/COST_POLICY.md` §校準係數 + `outputs/reports/token-calibration-v1.md` | 平台 dashboard 只給原始 token 計數；**本專案實測、逐 skill 的校準係數**（research **1.43**／writing **2.00**／ops **1.56**／review **1.25**）是歷史回測產物，無法由原生產生 | 保留為 `outputs/reports/token-calibration-v*.md`（資產，非 policy） |
| **FAILURE_TAXONOMY** | `system/FAILURE_TAXONOMY.yaml` | 原生無失敗分類學；14 類 + 各自 mitigation 是可跨專案引用的知識資產 | 抽出為治理層 plugin 的靜態 YAML + Decision Log 引用欄位 |
| **Decision Log** | `memory/.../decisions/D001–D007` | 原生 memory 為自由文字；無 `decision_id/options_considered/revisit_trigger` 結構化 schema 與可掃描的回看機制（R4 `check_decision_revisit.rb`） | 抽出為治理層 plugin 主元件 |
| **Audit Log** | `logs/AUDIT_LOG.md`（`generate_audit_log.py` 自動產出 + CI 守格式） | 原生無任務後事實紀錄；append-only + 機器可校驗格式是可審計性的根 | 抽出為治理層 plugin 的 `/audit`，CI 檢查格式 |

> 共同點：這四件都**不依賴「一個 Harness」存在**，可獨立發布——正是 v3 治理層 plugin 的核心。下放原生會直接損失它們，因此在三態中一律標「保留」。
> 延伸：Gate Policy（#8）、Approval Policy（#12）、Execution Log Schema（#15）同屬原生不提供的治理件，一併保留。

---

## 四、與 extraction plan 的對齊與差異

**沿用**：模組清單（16）、重疊百分比、§7 遷移路徑（v2.5→v3.0→v3.1→v3.2）、§9 待驗證 H1–H3、治理三件 + 失敗分類學的抽出定位。本評估不另立新裁決，只加「就緒度」軸。

**差異 / 校正**：

1. **Checkpoint（#9）三態分歧**：extraction plan 列「砍除」（理由：是慣例不是模組）。R10 從「能不能下放原生」角度看，原生對 checkpoint 重疊 **0%**，無從下放；它只是續用 git 慣例。故 R10 標 **保留（慣例）**，非下放。結論方向一致（都不為它建模組），僅標籤不同。

2. **extraction plan §4.2 統計筆誤**：原文寫「保留 0 / 砍除 5 / **抽出 6 / 重構 5**」。逐列點算實為 **砍除 5 / 抽出 5 / 重構 6**（抽出與重構數字互換）。不影響裁決，但建議晉升時順手更正。

3. **就緒度是新增軸**：extraction plan 把 H1/H2/H3 列為「待驗證」但未綁定到個別模組。R10 把它們**對應到具體 blocked 模組**（H1→#3、H2→#11/#7、H3→#8/#14/#15/#16），讓「卡在哪」可操作。

---

## 五、就緒度缺口清單（遷移前置條件）

對齊 extraction plan §7 遷移路徑與 §9 高風險假設，搬遷前必須先補：

| 缺口 | 對應 | 阻塞模組 | 解法（仍走各自 Task Card、drafts-first） |
|------|:----:|---------|------|
| G1 H1 未驗：原生 Skill 自動路由能否全替代 ROUTING_RULES | §9 H1 | #3 | 分支上做路由替代 PoC；不成立則 Planner/Router 由「下放」改「並存」 |
| G2 H2 未驗：settings.json 與 risk_level 能否正交 | §9 H2 | #11,#7 | 做 allow/ask/deny × risk_level 組合測試；不成立則 Permission 改「抽出」、hook 從 plugin 讀 risk |
| G3 H3 未驗：plugin 能否同掛 hook+skill+command | §9 H3 | #8,#14,#15,#16 | 待真正建 agent-governance repo（D007 bootstrap）後驗證；不成立則先 standalone CLI + 文件 |
| G4 analysis 校準 0 筆 | COST_POLICY §校準 | #13 | R3：累積 ≥3 筆 analysis 實測（**本卡即 1 筆 analysis**，可餵下次校準） |
| G5 v2.5 過渡未啟動 | §7.3 | 全部抽出件 | 雙寫 settings.json、skills 加 frontmatter、AGENT_CONTEXT 併入 CLAUDE.md；退出條件：連續 5 張新卡無摩擦 |

---

## 六、結論與觸發實際遷移的條件

**結論：維持「只評估不遷移」。** 整體未就緒——不是設計不足，而是 (a) 三項關鍵假設未實證、(b) 強制觸發點未達（重疊 30% < 50%、D003 四條件全未達）、(c) plugin home 尚未存在。下放原生只有 3–4 件 ready，其餘卡在 H1/H2/H3 與 plugin 落地。

**觸發實際遷移的條件（任一達成即重啟評估）**：
1. `NATIVE_OVERLAP.aggregate_estimate_pct` > 50%（強制重構觸發點）；或某單一模組重疊 + 原生穩定度使其維護變淨負擔。
2. D003 任一升級觸發條件持續 2 週以上（context 常超限 / 規則衝突 / 成本超 dashboard 上限 / 錯誤率上升）。
3. H1/H2/H3 全部驗證通過 **且** v2.5 過渡退出條件達成（連續 5 張新卡無摩擦）。
4. 出現第二個外部使用場景（plan §5.1）→ 觸發治理層獨立發布。

**下一步（皆各自開 Task Card）**：補 G1–G4 驗證/樣本 → 視結果啟動 G5 v2.5 過渡 → D007 bootstrap 建 plugin repo（驗 H3）。本評估只產草稿，**未修改任何 `system/` 模組檔**。

---

### 附：D003 / D007 回寫摘要

本卡依 R10 要求對兩筆決策加 readiness 交叉引用（**decision 本體不翻案，status 維持 active**）：
- **D003（v3 升級 hold）**：`revisit_trigger` 補「2026-06-24 R10 readiness：aggregate 仍 30% < 50%，維持 hold」+ 指向本檔。
- **D007（v3 plugin bootstrap）**：加 readiness 交叉引用（bootstrap 子題答案不變），指向本檔 §五 G3（H3 待 plugin repo 建立後驗證）。
