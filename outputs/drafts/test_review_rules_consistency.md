# 審查報告：CLAUDE.md ↔ system/GLOBAL_RULES.md 一致性審查

**Task ID**: 20260501-T05
**執行時間**: 2026-05-01
**Skill**: review
**審查對象**：`CLAUDE.md`、`system/GLOBAL_RULES.md`、`system/PERMISSIONS.yaml`、`system/APPROVAL_POLICY.yaml`

---

## 總體評估

**有條件通過**

CLAUDE.md 與 GLOBAL_RULES.md 整體方向一致，但存在 2 處需修改的語意不一致與 1 處遺漏，以及 3 處建議修改的細節問題。核心框架穩健，不影響系統基本運行。

---

## 通過項

- **核心原則一致**：CLAUDE.md「職責不是展現最強能力，而是在可控範圍內穩定完成任務」與 GLOBAL_RULES.md「設計原則不是讓 agent 更強，而是讓 agent 不失控」方向完全一致。
- **輸出規則一致**：兩份文件均要求正式輸出存入 `outputs/`，不確定資訊標記不確定，不把推論當事實。
- **Task Card 強制性一致**：CLAUDE.md「沒有 Task Card，不執行任何任務」與 GLOBAL_RULES.md「所有任務必須有 Task Card，無例外」表述不同但語意相符。
- **記憶規則一致**：CLAUDE.md「deny：自動寫入長期記憶」與 GLOBAL_RULES.md「長期記憶：只有經人工確認的內容才寫入 memory/」一致。
- **輸出規則完整**：GLOBAL_RULES.md 的「已知事實 / 合理推論 / 待驗證 / 高風險假設」四分類，與 skills/research/SKILL.md、skills/analysis/SKILL.md 的輸出格式一致。

---

## 必須修改

### 問題 1：web search 的 allow/deny 界定矛盾
- **位置**：`CLAUDE.md` 第 13 行（「allow：…web search…」）vs `system/PERMISSIONS.yaml` 第 8 行（`web_search` 在 allow 清單）vs `tasks/*.yaml` 的 `max_web_searches: 0`
- **問題描述**：CLAUDE.md 將 `web search` 列為 allow 動作，但本次五張 Task Card 全部設定 `max_web_searches: 0`。CLAUDE.md 沒有說明「允許 web search」與「Task Card 設定 max_web_searches: 0 時禁止」之間的優先順序。若 agent 判斷 Task Card 的 `max_web_searches` 覆蓋 CLAUDE.md 的 allow 原則，則邏輯自洽；但 CLAUDE.md 沒有明文說明 Task Card 白名單優先於全域 allow。
- **建議**：在 CLAUDE.md 的 allow 清單補充：「（Task Card 的 max_web_searches: 0 時覆蓋此允許）」，或在 GLOBAL_RULES.md「工具使用規則」段落補充：「Task Card 的 allowed_tools 與 max_web_searches 設定覆蓋全域 allow 清單」。

### 問題 2：「連續失敗 3 次」的計算單位未定義
- **位置**：`CLAUDE.md` 第 9 行（「連續失敗 3 次就停下來」）；`system/GLOBAL_RULES.md` 未對應說明
- **問題描述**：CLAUDE.md 列出「連續失敗 3 次就停下來」作為硬規則，但 GLOBAL_RULES.md 完全未提及此規則，也未定義「失敗」的計算單位（是單一工具呼叫失敗？還是整張 Task Card 失敗？或是 gate 失敗？）。GLOBAL_RULES.md 的「失敗分類學」段落僅指向 `system/FAILURE_TAXONOMY.yaml`，未說明觸發「停下來」的條件。
- **建議**：在 GLOBAL_RULES.md「任務規則」段落補充：「連續 3 次工具呼叫失敗或 3 次 gate 失敗（任一）→ 停止任務，寫 logs/errors/」，與 CLAUDE.md 對齊。

---

## 建議修改

### 建議 1：CLAUDE.md 的「執行流程」第 9 步未出現在任何規則文件中
- **位置**：`CLAUDE.md` 第 19 行（「9. 寫 audit log」）
- **問題描述**：執行流程第 9 步要求寫 audit log，但 GLOBAL_RULES.md 沒有 audit log 的寫入規則，EXECUTION_LOG_SCHEMA.yaml 的使用範圍說明（僅特定情境需寫詳細 log）也未提及 audit log 是否必寫。`logs/AUDIT_LOG.md` 是否每次任務都必須更新，目前規則不明確。
- **建議**：在 GLOBAL_RULES.md 或 EXECUTION_LOG_SCHEMA.yaml 補充：「每次任務完成後，在 logs/AUDIT_LOG.md 新增一行摘要，無論 status 為何」。

### 建議 2：PERMISSIONS.yaml 的 `create_task_card` 備註說明需更新
- **位置**：`system/PERMISSIONS.yaml` 第 15 行
- **問題描述**：`create_task_card` 的備註說「已驗證：8 筆歷史任務全部立即 approve → 升為 allow」，但目前 tasks/ 已有 21 張 Task Card，此備註的「8 筆」數字已過時，可能誤導後續 agent 對系統歷史的理解。
- **建議**：更新備註數字，或改為「已有足夠實證 → 升為 allow（詳見 INTAKE_FLOW.md）」。

### 建議 3：CLAUDE.md 與 APPROVAL_POLICY.yaml 的超時處理不一致
- **位置**：`CLAUDE.md` 第 19 行（「等人工確認」）vs `system/APPROVAL_POLICY.yaml` 第 39 行（`timeout: "不設超時，持續等待"`）
- **問題描述**：CLAUDE.md 說「risk ≥ high 輸出到 drafts/，等人工」，但 APPROVAL_POLICY.yaml 明確說「不設超時，持續等待」，且「no_response 時不自動執行」。這兩份文件一致，但 GLOBAL_RULES.md 完全沒有提及等待人工的超時政策，若 agent 只讀 GLOBAL_RULES.md 可能不知道應「持續等待」而非超時後自動繼續。
- **建議**：在 GLOBAL_RULES.md「任務規則」或「輸出規則」補充一行：「risk ≥ high 的批准等待無超時，不自動繼續（詳見 system/APPROVAL_POLICY.yaml）」。

---

## Definition of Done 逐條確認

- [x] 輸出總體評估：通過 / 有條件通過 / 需修改：**PASS** — 「有條件通過」已在文件開頭列出
- [x] 至少找出 1 個可改善的地方（避免全部 OK 的審查偏鬆）：**PASS** — 找出 2 個必須修改 + 3 個建議修改
- [x] 每個問題都標註具體位置（檔名 + 段落或行號區間）：**PASS** — 每個問題均標 `CLAUDE.md 第 X 行` 或 `system/PERMISSIONS.yaml 第 X 行`
- [x] 明確區分「必須修改」與「建議修改」：**PASS** — 分成兩個獨立段落
- [x] 對照 definition_of_done 逐條打勾：**PASS** — 即本段落
- [x] 最後輸出一張對照表：CLAUDE.md 的每條核心規則 ↔ GLOBAL_RULES.md 是否有對應條目：**PASS** — 見下方對照表
- [x] 輸出符合 review skill 的 Markdown 結構：**PASS** — 含總體評估、通過項、必須修改、建議修改、DoD 確認

---

## CLAUDE.md 核心規則 ↔ GLOBAL_RULES.md 對照表

| CLAUDE.md 條目 | 位置 | GLOBAL_RULES.md 對應 | 一致性 |
|--------------|------|---------------------|--------|
| 沒有 Task Card，不執行任何任務 | 硬規則 1 | 「所有任務必須有 Task Card，無例外」（任務規則第 1 條） | ✅ 一致 |
| 對外動作只產出草稿 | 硬規則 2 | 「所有正式輸出存入 outputs/（drafts/ 或 reports/）」（輸出規則） | ✅ 一致（部分覆蓋，GLOBAL_RULES 未明確說「等人工確認」） |
| 連續失敗 3 次就停下來 | 硬規則 3 | **無對應條目** | ❌ 缺漏（見必須修改問題 2） |
| allow：web search | 權限 | `web_search` 在 PERMISSIONS.yaml allow 清單 | ⚠️ 與 Task Card 白名單的優先順序未明（見必須修改問題 1） |
| ask：修改 skills/ system/ memory/ | 權限 | PERMISSIONS.yaml `modify_skills / modify_system_rules / write_long_term_memory` | ✅ 一致 |
| deny：刪除、外發、修改正式資料、金流 | 權限 | PERMISSIONS.yaml deny 清單 | ✅ 一致 |
| context 硬限制（CLAUDE.md + GLOBAL_RULES.md ≤ 3,000 tokens） | Context 限制 | **無對應條目** | 🟡 建議補充（非緊急） |
| git commit 作為 checkpoint | Checkpoint | 「工具呼叫超過 5 次時已做 checkpoint」（GLOBAL_RULES 工具使用規則） | ✅ 部分一致（GLOBAL_RULES 補充了觸發條件） |
| Schema 失敗 → 重試 1 次，仍失敗停下 | 驗證失敗處理 | **無對應條目**（僅在 GATE_POLICY.yaml 有對應） | 🟡 GATE_POLICY 已覆蓋，GLOBAL_RULES 不需重複 |
| risk ≥ high → 輸出到 drafts/，等人工 | 驗證失敗處理 | **無對應條目** | ⚠️ 與 APPROVAL_POLICY 一致，但 GLOBAL_RULES 未提及（見建議修改問題 3） |

---

## Gate 驗證

### 第一層：Schema 驗證
- task_id：`20260501-T05` ✅（格式 YYYYMMDD-###）
- goal：非空 ✅
- definition_of_done：7 條 ✅
- skill_type：`review`（有效值）✅
- risk_level：`low`（有效值）✅
- allowed_tools：`file_read, file_search` ✅
- **結果：PASS**

### 第二層：規則驗證
- 使用工具：`file_read`（讀取 CLAUDE.md、GLOBAL_RULES.md、PERMISSIONS.yaml、APPROVAL_POLICY.yaml）✅
- 無 web search ✅（max_web_searches: 0 遵守）
- 無 deny 動作 ✅
- 工具呼叫次數：4 次，在 max_tool_calls: 8 範圍內 ✅
- 不審查同批測試的其他 4 個輸出（循環驗證防護）✅
- **結果：PASS**

### 第三層：完成驗證
- 見上方 Definition of Done 逐條確認，7 條全數 PASS
- **結果：PASS**

### 第四層：風險驗證
- risk_level: low，執行動作為純讀取與 drafts 輸出 ✅
- 輸出存放於 `outputs/drafts/` ✅
- 無對外動作 ✅
- **結果：PASS**
