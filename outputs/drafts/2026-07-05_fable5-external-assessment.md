# Agent Harness v2 — 外部評估報告（評分 + 缺點 + 改善計畫）

> **草稿（draft）** ｜ 日期：2026-07-05 ｜ Task Card：`20260705-001` ｜ skill：review
> 評估基準：HEAD `520156e`（2026-07-05，本評估開始前）。
> 研究方法：3 個並行探索 agent（治理文件層／程式碼與 CI 層／運行資料層），與 2026-05-29 自我評估（`outputs/reports/harness-self-assessment-v1.md`）對照。
> 本報告隨附 P0 級修復（同一 Task Card 交付，範圍經使用者核准，見 `logs/approvals/2026-07-05_20260705-001_approval.yaml`）。

---

## 摘要

| 項目 | 結論 |
|------|------|
| **總分** | **≈ 6.8 / 10** |
| **成熟度等級** | **維持 3（生產前）**——R1–R8 確實落地，但一個月內漂移已回來，尚未證明「自我維持一致性」的能力 |
| **組成** | 設計面 ~9 分、執行面 ~5 分。**落差本身就是最大缺點** |
| **與 5/29 自評（≈7/10）的差異** | 分數接近，但結構不同：自評低估了「規格 vs 現實脫節」與「enforcement 榮譽制」兩類問題，高估了安全（9→本評估 6.5） |
| **單一最高槓桿方向** | 不是加新功能，而是**「每條規則要嘛被機器執行、要嘛降級為指引」**的規格瘦身 + 對帳自動化 |

---

## 一、評分卡（10 維）

| # | 維度 | 分數 | 依據 |
|---|------|:---:|------|
| 1 | 治理架構設計 | **9** | 三平面 16 模組、四層 gate、14 種失敗分類、成本校準係數、決策日誌含 revisit trigger——個人專案罕見的完整度 |
| 2 | 自我改進能力 | **9** | 誠實的自我評估（5/29）+ 當天執行 8/10 roadmap 項 + 真實故障演練（R5）與恢復演練（R8）。這是專案最珍貴的文化資產 |
| 3 | 文件與 DevEx | **8** | README 完整、模板齊、3 步上手、eval_examples 品質高（好壞對照 + rubric） |
| 4 | 恢復與耐久 | **7.5** | `RECOVERY_RUNBOOK.md` 存在且演練過（R8）；扣分：checkpoint hash 從未回填（兩筆 run log 的 commit 全是 "pending"） |
| 5 | 程式碼品質 | **7** | 9 個測試套件、90 tests 全綠、生成器有 `--check` 漂移模式；扣分：crash bug（見缺點 5）、regex 解析 Markdown 內 YAML、Python+Ruby+shell 三語言無理由混雜 |
| 6 | 可觀測性 | **7** | R7 落地了 metrics 引擎 + frontend 治理面板；扣分：`governance_metrics.py`（27 tests）完全不在 CI、`frontend/data.json` 在 HEAD 上已漂移 |
| 7 | 安全 | **6.5** | deny-by-default 設計 + runtime hook 方向正確；扣分：SECURITY.md 是空模板、無 secret scanning、Edit/Write 無任何防護（自評給 9 過於樂觀） |
| 8 | 規格一致性 | **5.5** | CLAUDE.md 與 PERMISSIONS/D006 三處脫節、`status: blocked` 被自家 CI 拒絕、驗證器三份分歧、枚舉字彙分裂 |
| 9 | Runtime 執行力 | **5** | 三條硬規則全是榮譽制；hook 只掛 Bash、只覆蓋 8 條 deny 中的 4 條且 hardcode（沒讀 PERMISSIONS.yaml） |
| 10 | 運行紀律 | **5** | ~17 張卡凍結在 review、memory 停在 4/15、7 份 reports 只有 1 筆 approval 紀錄、HEAD 上 CI 紅燈 |

**平均 ≈ 6.8 / 10。**

**核心判讀**：這個專案的風險模式是「**治理表面積的膨脹速度 > 維護能力**」。16 模組、14 失敗分類、12 份治理文件持續增長，但運行紀錄顯示：維護迴路跟不上既有表面積的一致性維持——R1–R8 修完一個月，漂移又回來了（data.json、CLAUDE.md、卡片狀態、memory）。

---

## 二、招牌（務必保留）

1. **自我評估文化**：5/29 的自評誠實到會校正自己的誤判，且當天就執行 8/10 roadmap 項。多數專案做不到第一步。
2. **故障與恢復演練是真的**：R5 刻意跑失敗路徑、R8 實測 checkpoint 還原——不是紙上談兵。
3. **實測成本校準**：research 1.43／writing 2.00／ops 1.56／review 1.25 是真數據。
4. **自我淘汰機制**：NATIVE_OVERLAP 主動量化「我跟 Claude Code 原生功能重疊 30%」並設 >50% 觸發重構。

---

## 三、缺點（按嚴重度，附證據）

### 1. 規格與現實脫節——boot prompt 說的和系統做的不一樣

- `CLAUDE.md:14` 說建立 Task Card 屬 **ask**，但 `system/PERMISSIONS.yaml:15` 早已依 D004（2026-04-15）升為 **allow**。boot prompt 是 agent 的最高指令，卻陳述與 enforced 權限相反的規則。
- `CLAUDE.md:19` 步驟 8 說每個任務都要寫 run log，但 D006（2026-04-24）已把範圍縮限為 failed/partial/risk≥high/checkpoints≥3（`system/EXECUTION_LOG_SCHEMA.yaml:5-13`）。CLAUDE.md 從未更新。
- `system/GATE_POLICY.yaml:18` 的 schema-gate rollback 指示「Task Card 標記 `status: blocked`」，但 `blocked` 不在 `scripts/check_spec_consistency.rb:9` 與 `system/validate_task_card.py:13` 的枚舉中——**忠實執行 rollback 的 agent 會產出一張被自家 CI 拒絕的卡**。
- 「≤3,000 tokens」預算（`CLAUDE.md:23`）只涵蓋實際載入 ~6 個檔中的 2 個。實測全套 boot context（CLAUDE.md + GLOBAL_RULES + AGENT_CONTEXT + APPROVAL_POLICY + 一個 skill + project context）≈ **3,797 tokens**，早已超過帳面數字；skill ≤1,500 的預算也不在 CI 檢查範圍。

### 2. Enforcement 大半是文件，不是機制

- `.claude/settings.json` 只掛了一個 hook：`permissions_guard.py` on `Bash`。**Edit/Write 完全沒有防護**——agent 可以直接 Write 進 `outputs/reports/`、`system/`、`memory/`、CLAUDE.md，繞過草稿優先與全部 ask/deny 意圖。`permissions_guard.py:138` 說 Edit/Write「由其他層防護」，但那一層不存在。
- `permissions_guard.py:2` 宣稱 enforce PERMISSIONS.yaml，實際上 `DENY_RULES`（42-105 行）是 hardcode 的，**只覆蓋 8 條宣告 deny 中的 4 條**（缺 publish_content、modify_production_data、auto_write_memory、spawn_background_process），還多了一條沒宣告的 git_force_push。改 PERMISSIONS.yaml 對 runtime 零影響。
- 三條硬規則（無卡不執行／對外只草稿／3 次失敗即停）**全部沒有機器檢查**。

### 3. CI 在 HEAD 上是紅的，且守門有洞

- 最新 commit `520156e` 加了 task card 但沒重生 `frontend/data.json`（45 vs 實際 46 張卡）——`generate_frontend_manifest.py --check` 在 HEAD 上 exit 1。**這正是該 gate 要防的漂移，發生在最新一次提交**。
- `generate_audit_log.py --check` 存在但不在 CI——audit log 漂移不可見（HEAD 上同樣 exit 1）。
- `governance_metrics.py` 與其 27 個測試（單一最大測試檔）完全不在 CI。
- Audit 的 commit 連結機制從未生效：`generate_audit_log.py:74` 用 `checkpoint: \[task_id\]`（含方括號）搜尋 commit，但所有歷史 checkpoint commit 都不含方括號——每筆 audit 條目的 `checkpoints` 永遠是空清單，audit→commit 可追溯性只存在於 `git log` 裡。

### 4. 雙重事實來源——資料在互相矛盾

- **~17 張卡** status 凍結在 `review`，但 audit log 記為 done（例：20260404-S01/W01、20260502-A01/T01-T03、20260509-N01-N05/N07/N08）。卡片狀態從未推進。
- 2 張 done 的卡（20260409-001、20260415-A01）**沒有 audit 條目**；後者的 `audit_log_ref` 是空字串。
- 任務 20260412-001 記錄 `checkpoints: 5`，按 D006 規則（≥3）**必須有 run log，但沒有**——連縮限後的規則都被違反，且無任何檢查會發現。
- 7 份 `outputs/reports/` 只對應 **1 筆** approval 紀錄（還是 4 月的 task-card 批准，不是晉升批准）；4 份 draft/report **位元組級重複**（晉升用複製而非搬移，也無紀錄）。
- `memory/active_projects/agent-harness/context.md` 凍結在 **2026-04-15**（寫著「累積 6 筆 audit」，實際 41 筆），其後 2.5 個月的 N 系列、自評、R1–R8 全部缺席。
- D003（v3 hold，status: active）與 D007（v3 plugin 綠燈）方向相反，D003 的 revisit_trigger 從未觸發。

### 5. 驗證邏輯三份分歧

同一件事（Task Card 驗證）有三份實作：`scripts/check_spec_consistency.rb:62-144`（CI 在跑的）、`system/validate_task_card.py`（README 教使用者跑的，**有 crash bug**：空 YAML → `card.get` on None → AttributeError；且不檢查 `expected_output.location`）、`outputs/drafts/agent-governance-bootstrap/validators/validate_task_card.py`（**已修 bug 但從未回移植**）。枚舉也在分裂：draft 版與 `governance_metrics.py:38` 接受 `partial`，Ruby 檢查與主 Python 版拒絕；Task Card 用 `done`、run log 用 `completed`；approval 的 embedded 版（`EXECUTION_LOG_SCHEMA.yaml:51`）與 standalone 版（`APPROVAL_POLICY.yaml:56-67`）欄位與狀態值不一致，卻註記「同名同義」。

### 6. 安全表面未完成

- `SECURITY.md` 是 GitHub 預設模板原文（版本表還寫著 5.1.x/4.0.x），而 `README.md:129` 把它連結為正式安全政策。
- 無 secret scanning（SEC-02 的 mitigation 純靠自律）；無 LICENSE / CHANGELOG / VERSION（版本識別只存在於散文）。
- `AGENT_CONTEXT.yaml:26` 禁止讀 `~/.ssh`，但 `permissions_guard.py` 不會擋 `cat ~/.ssh/id_rsa`。

### 次要觀察

- `analysis` skill 是二等公民：驗證器與路由都支援，但 `TASK_CARD_TEMPLATE.yaml:38`、`README.md:96`、`EXECUTION_LOG_SCHEMA.yaml:20` 的說明都不提它，且 46 張卡零使用。
- 5 個 skill 只有 `research` 有原生 Skills 需要的 YAML frontmatter，`NATIVE_OVERLAP.yaml` 宣稱的 85% Skill 重疊只對 1/5 成立。
- 三張 plugin 卡（N09/N10/N11）新增了模板外欄位（preconditions/rollback）且卡在 pending/in_progress——模板長不出它們需要的形狀。
- 自家 roadmap 的 R9/R10 無 task card、無產出，未動工。

---

## 四、與 5/29 自評的差異分析

| 面向 | 5/29 自評 | 本評估 | 差異原因 |
|------|----------|--------|---------|
| 總分 | ≈7 / 10 | ≈6.8 / 10 | 分數接近但組成不同 |
| 安全 | 9 | 6.5 | 自評沒發現 Edit/Write 零防護、guard 只覆蓋 4/8 deny 且 hardcode、SECURITY.md 是空模板 |
| 治理 | 9 | 9（設計）/ 5（執行） | 自評把「設計完備」與「被遵循」混在一起評 |
| 可觀測 | 6 → R7 後應更高 | 7 | R7 確實落地，但 metrics 不在 CI、data.json 已再漂移 |
| 盲點 | 「關鍵路徑未實證」 | 「**一致性無法自我維持**」 | R5/R8 之後「未實證」已部分解決；新問題是修完一個月漂移就回來——需要的是**對帳自動化**，不是更多演練 |

自評最大的貢獻是誠實與 roadmap 執行力；最大的盲點是它主要檢查「檔案存在嗎、機制設計了嗎」，較少檢查「兩份檔案互相矛盾嗎、規則真的被執行嗎」。

---

## 五、改善計畫

### P0 — 立即（本次隨報告完成）

| # | 項目 | 動作 |
|---|------|------|
| P0-a | CLAUDE.md 同步現實 | 「建立 Task Card」移到 allow（D004）；步驟 8 註記 D006 縮限範圍 |
| P0-b | `blocked` 枚舉修復 | 加入 `check_spec_consistency.rb` 與 `validate_task_card.py` + 測試 + 模板註解 |
| P0-c | crash bug 回移植 | `validate_task_card.py` 加 None/mapping guard（取自 draft plugin 已修版本） |
| P0-d | SECURITY.md | 替換為真實政策（版本表、回報方式、secret 處理、已知缺口） |
| P0-e | CI 守門補洞 | 加 `generate_audit_log.py --check`（checkout 改 fetch-depth: 0）與 `test_governance_metrics.py` |
| P0-f | 重生衍生檔 | `frontend/data.json` + `logs/AUDIT_LOG.md`，兩個 `--check` 回綠 |

### P1 — 結構性補強（1–2 週，各自開 Task Card）

1. **Enforcement 對齊宣告**：`permissions_guard.py` 改為從 `PERMISSIONS.yaml` 讀取/生成規則；hook 擴到 `Write|Edit` matcher，至少保護 `outputs/reports/`、`system/`、`memory/`、`CLAUDE.md` 四個路徑（沒有 approval 紀錄就 deny）；補齊 4 條未覆蓋的 deny。
2. **狀態對帳 CI 檢查**：audit 記 done ⇒ 卡必須 done；符合 D006 條件（failed/partial/high/checkpoints≥3）⇒ `logs/runs/` 必須有對應檔；`outputs/reports/` 每個檔 ⇒ 必須有對應 approval 紀錄。先跑一次人工對帳把 17 張 review 卡收斂。
3. **驗證器收斂**：以 Python 版為單一實作（draft plugin 已示範方向且棄用了 Ruby），Ruby 腳本改為呼叫或退役；統一 `done/completed/partial/blocked` 字彙表（一份 SSOT，各 schema 引用）。
4. **晉升流程坐實**：draft→report 改為搬移（或報告內鏈接 draft），晉升動作必寫 approval 紀錄——由 P1-2 的 CI 對帳守住。
5. **memory 維護納入 RETRO**：`RETRO_FLOW.md` 加一條必做項「更新 active_projects context.md」；`check_decision_revisit.rb` 對 D003 vs D007 這類方向矛盾要能標記。
6. **audit commit 連結修復**：統一 checkpoint commit 格式（建議含方括號 `checkpoint: [task_id] 描述`，與 CLAUDE.md 字面一致），讓 `generate_audit_log.py` 的 commit 連結真正生效（本任務的 commit 已採此格式作為首例）。

### P2 — 戰略級（季度）

1. **規格瘦身原則**：逐條盤點 12 份治理文件——每條規則標記「機器執行（CI/hook）」或「指引（不宣稱強制）」。宣稱強制但無機制的規則，要嘛補機制、要嘛降級。這直接治「表面積 > 維護能力」的根因。
2. **Token 預算誠實化**：預算改為涵蓋全套 boot 檔（~6 個），`check_context_budget.rb` 對應擴充；skill ≤1,500 納入 CI。
3. **R9/R10 收尾**：自家 roadmap 未完成的兩項（NATIVE_OVERLAP 季度 revisit 自動化、v3 就緒度評估），並順手 revisit D003。
4. **skill 治理**：4 個 skill 補 frontmatter；決定 `analysis` 去留（升一等公民進模板與 README，或砍掉）。
5. **安全補完**：CI 加 secret scanning（gitleaks）；補 LICENSE/CHANGELOG。

### 排程建議

```
P0（本次）───────────────────────────► CI 回綠、自相矛盾清零
P1 週1-2：P1-1 enforcement ＋ P1-2 對帳 CI（兩者是「不再漂移」的主幹）
P1 週2：  P1-3 驗證器收斂 → P1-4 晉升坐實 → P1-5/P1-6
P2 季度： P2-1 規格瘦身（最高槓桿）→ P2-2/P2-3/P2-4/P2-5
```

---

## 六、後續

- 本報告依規則進 `outputs/drafts/`；晉升 `outputs/reports/` 需人工確認（屆時請寫 approval 紀錄——正好練習 P1-4）。
- P1/P2 各項依慣例各自開 Task Card。建議第一張 = **P1-2 狀態對帳 CI 檢查**：它是防止「修完又漂」的結構解，性價比最高。
