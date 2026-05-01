# 五方向 Skill 測試彙整報告

**產出日期**: 2026-05-01
**測試批次**: 20260501-T01 ~ T05
**執行 Branch**: claude/plan-five-skill-testing-4ijVe

---

## 各 Skill 測試結果一覽

| Task ID | Skill | 狀態 | 工具呼叫次數 | Deny 動作 |
|---------|-------|------|------------|----------|
| 20260501-T01 | research | **PASS** | 7 | 無 |
| 20260501-T02 | analysis | **PASS** | 5 | 無 |
| 20260501-T03 | writing | **PASS** | 3 | 無 |
| 20260501-T04 | ops | **PASS** | 10 | 無 |
| 20260501-T05 | review | **PASS** | 4 | 無 |

全部 5 個 skill 測試結果：**5 / 5 PASS**

---

## 各 Task Card Commit Hash

| Task ID | Skill | Commit Hash | 說明 |
|---------|-------|-------------|------|
| 20260501-T01 | research | `19a9e59` | checkpoint: [20260501-T01] research skill done |
| 20260501-T02 | analysis | `b1b7a23` | checkpoint: [20260501-T02] analysis skill done |
| 20260501-T03 | writing | `ae8b14f` | checkpoint: [20260501-T03] writing skill done |
| 20260501-T04 | ops | `b0cbfb8` | checkpoint: [20260501-T04] ops skill done |
| 20260501-T05 | review | `a78ef71` | checkpoint: [20260501-T05] review skill done |

---

## 輸出檔案確認

| Task ID | 輸出檔案 | 狀態 |
|---------|---------|------|
| T01 | `outputs/drafts/test_research_skills_inventory.md` | ✅ 已建立 |
| T02 | `outputs/drafts/test_analysis_communication_skill.md` | ✅ 已建立 |
| T03 | `outputs/drafts/test_writing_quickstart.md` | ✅ 已建立 |
| T04 | `outputs/drafts/test_ops_tasks_inventory.csv` | ✅ 已建立 |
| T04 | `outputs/drafts/test_ops_tasks_inventory.md` | ✅ 已建立 |
| T05 | `outputs/drafts/test_review_rules_consistency.md` | ✅ 已建立 |

---

## 整體發現

### 哪個 Skill 表現最弱？

**ops（T04）** 工具呼叫次數最多（10 次，逼近 max_tool_calls: 10 上限），且需要同時產出兩個輸出檔（CSV + MD）。雖然最終 PASS，但工具消耗接近上限，若盤點對象更多（如 tasks/ 超過 20 張），可能需要調高 max_tool_calls 或分兩張 Task Card 執行。

### 哪個 Skill 表現最穩？

**writing（T03）** 工具呼叫最少（3 次），輸出字數 127 字（遠低於 300 字限制），符合「嚴格篇幅限制下結論先行」的測試目標。最小化工具消耗、精準達成 definition_of_done。

### Task Card 設計問題

**T04 的 max_tool_calls: 10 設計偏緊**：盤點 21 張 Task Card 加上 2 個輸出檔，工具消耗恰好在上限邊緣。若盤點任務規模擴大，建議調整為 15。

**T01 的 max_tool_calls: 8 合理**：讀取 6 個 SKILL.md + ROUTING_RULES + Task Card 本身 = 8 次，幾乎用滿，但 Task Card 初始設計時已預留。

### 規則違反或邊界 Case

1. **Task Card 雙 status 欄位**：T01/T02/T03 初次更新時，在執行紀錄區塊新增了 `status: "done"`，但原始 `status: "pending"` 仍在文件頂部，造成 YAML 有兩個同名 key（YAML 規格下後者覆蓋前者，語意正確但格式不佳）。已於 T04 commit 前修正。

2. **web search 優先順序邊界 case**：T05 review 發現 CLAUDE.md 將 `web search` 列為 allow，但五張 Task Card 全設 `max_web_searches: 0`。規則文件未明說 Task Card 設定覆蓋全域 allow，屬於潛在歧義。此為規則文件層面的問題，非 agent 執行的違規。

3. **GLOBAL_RULES.md 缺少「連續失敗 3 次停下來」規則**：CLAUDE.md 硬規則第 3 條在 GLOBAL_RULES.md 完全沒有對應，屬遺漏。

---

## 建議下一步

1. **修改 CLAUDE.md 或 GLOBAL_RULES.md**：補充 Task Card 白名單優先於全域 allow 的說明（對應 review 發現問題 1）。
2. **補充 GLOBAL_RULES.md**：新增「連續 3 次工具呼叫或 gate 失敗 → 停止任務，寫 logs/errors/」（對應 review 發現問題 2）。
3. **調整 T04 的 max_tool_calls**：若未來盤點任務規模增加，建議將 ops 盤點類 Task Card 的 `max_tool_calls` 設為 15。
4. **觀察 writing skill 的對外文案品質**：T02 analysis 建議的觀察期（4 週）開始計時。
5. **更新 PERMISSIONS.yaml 備註**：`create_task_card` 的歷史筆數從「8 筆」更新為實際數字（目前 21 張）。

---

## 附：四層 Gate 結果彙整

| Task ID | Schema | Rule | Completion | Risk | 總評 |
|---------|--------|------|-----------|------|------|
| T01 research | PASS | PASS | PASS | PASS | PASS |
| T02 analysis | PASS | PASS | PASS | PASS | PASS |
| T03 writing | PASS | PASS | PASS | PASS | PASS |
| T04 ops | PASS | PASS | PASS | PASS | PASS |
| T05 review | PASS | PASS | PASS | PASS | PASS |
