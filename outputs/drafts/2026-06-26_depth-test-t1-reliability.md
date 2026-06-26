# 深度測試研究 T1 — 可靠性／故障恢復

> **草稿（draft）** ｜ 日期：2026-06-26 ｜ Task Card：`20260626-001` ｜ skill：research
> 方法：實證探測（唯讀執行 harness 自帶 validator + git 唯讀指令）。探針 fixture 暫存 scratchpad，未進 `tasks/`，未修改任何 `system/`。
> 對應自我評估弱點：可靠性 7「設計完備、未經實證」、耐久性 6。

---

## 結論

harness 的可靠性**呈現明顯的分層落差**：**Schema 層（第一道 gate）已達生產級實證**——多種破壞模式（8/9 fixture）全數被 `validate_task_card.py` 正確攔下、且 R5 已在真實故障下走完「重試 1 次 → 停 → 寫 error/run log」閉環。但**其餘三道 gate（rule / completion / risk）仍是「契約釘樁 + LLM 推理」，從未在真實故障下被獨立坐實**：`tests/e2e/test_dummy_task_smoke.py` 自承四層 gate 是 *in-process 模擬*，僅 `schema_check` 真正 shell out 到實際 validator。恢復面則健康：22+ 個 checkpoint commit（量測時點數，隨後續 commit 持續增加）可被 `git log --grep` 尋回、工作樹乾淨、`RECOVERY_RUNBOOK` 場景指令實跑可用。

一句話：**「失敗 → 恢復」閉環在 schema 維度已坐實，但「四層 gate 全在真實故障下正確 on_fail」目前對 3/4 層仍是假設而非事實。**

---

## 已知事實（實證探針結果）

### 1. 多失敗模式 Schema 探測（`system/validate_task_card.py`，9 個 scratchpad fixture）

| 失敗模式 | exit | 攔截依據 |
|---|:--:|---|
| M1 缺 goal | 1 | 缺少必填欄位：goal |
| M2 空 definition_of_done | 1 | 缺少必填欄位 + 至少一條 |
| M3 非法 skill_type=marketing | 1 | skill_type 無效 |
| M4 非法 risk_level=extreme | 1 | risk_level 無效 |
| M5 缺 expected_output.format/filename | 1 | 兩欄不能為空 |
| M6 非法 status=shipping | 1 | status 無效 |
| M7 多重失敗（同時 5 缺） | 1 | 一次列出全部缺漏 |
| M8 非合法 YAML | 1 | YAML 解析失敗 |
| CONTROL 合法卡 | 0 | ✅ 通過 |

→ **8/9 破壞 fixture 正確拒絕、control 正確通過**。schema_check 跨「缺欄／空值／值域／格式／解析」全失敗類別穩健，且多重失敗會**一次列全**而非只報第一條。**超越 R5**（R5 只實證單一 multi-field fixture）。

### 2. 四層 Gate 的「實證 vs 模擬」真相

- `GATE_POLICY.yaml` schema_check `on_fail` =「重試 1 次修正，仍失敗 → 停 + 寫 logs/errors/」——**R5（`RUN-20260529-003`, status=failed）已在真實故障下走完此路徑**。
- `tests/e2e/test_dummy_task_smoke.py` docstring 明載：四層 gate「simulated in-process here … the real Claude Code runtime performs them via natural-language reasoning」。即：
  - `schema_check`：**真 shell out** 到 `validate_task_card.py` → 已實證。
  - `rule_check` / `completion_check` / `risk_check`：以**測試本地重實作**釘住契約（含 `test_high_risk_output_in_reports_fails_risk_gate` 反例），但執行期由 LLM 推理執行，**未在真實故障下獨立坐實**。
- `rule_check` 的 **deny 子集**在 runtime 由 `permissions_guard.py` hook 強制——此部分有 runtime 證據（見 T2：32/43 危險命令正確 block）。

### 3. FAILURE_TAXONOMY 14 種覆蓋表（已實證／僅設計）

| ID | 失敗模式 | 狀態 | 證據 |
|---|---|---|---|
| SPEC-01 | 角色/目標違反 | 僅設計 | 無實證實例 |
| SPEC-02 | 步驟重複/迴圈 | 僅設計 | 迴圈/3-連續偵測從未被真實觸發紀錄 |
| SPEC-03 | 對話歷史遺失 | 部分實證 | `RECOVERY_RUNBOOK` 場景 + R8 checkpoint-restore drill |
| SPEC-04 | 不知何時停止 | 僅設計 | completion_check 契約釘樁，假完成未實證 |
| COORD-01 | Context 被重置 | 部分實證 | R8 災難恢復 drill 已演練 checkpoint 還原 |
| COORD-02 | 模糊需求硬做 | **已實證（正面）** | 本任務以 AskUserQuestion 澄清 3 決策再執行，即此模式的緩解實例 |
| COORD-03 | 目標偏離 | 僅設計 | — |
| COORD-04 | 忽略使用者輸入 | 僅設計 | — |
| VAL-01 | 假完成 | 僅設計 | completion_check 契約釘樁，未實證偵測 |
| VAL-02 | 驗證不完整 | 僅設計 | — |
| VAL-03 | 驗證判斷錯誤 | 僅設計 | — |
| SEC-01 | 未授權動作 | **已實證** | `permissions_guard.py` runtime hook（T2 實證）|
| SEC-02 | 資料洩漏 | 僅設計 | — |
| SEC-03 | 成本失控 | 部分實證 | R5 實證「schema 失敗即停」；3-連續-failure 計數未真實觸發 |
| SEC-04 | 幻覺驅動行動 | 僅設計 | 對外只草稿（設計），未在真實外部動作下測 |

→ **實證/部分實證 5 種、僅設計 9 種**。安全維度（SEC-01）與停止行為（SEC-03 之 schema-stop）證據最硬，其餘多為紙面設計。

### 4. 恢復資料源實跑（`RECOVERY_RUNBOOK` 唯讀驗證）

- `git log --oneline --grep="checkpoint:"` → **22 個 checkpoint commit 可尋回**（量測時點數，隨後續 commit 持續增加；最舊到本任務皆在）。
- `git status --short` → 工作樹乾淨（場景 A「未 commit 破壞」的還原基準存在）。
- runbook 列的恢復資料源（checkpoint commits / Task Card / run log / approvals / AUDIT_LOG）**全部實體存在且指令可跑**。

---

## 合理推論

- rule/completion/risk gate 在真實故障下「應」與 schema 同模式（停 + log），因共用同一 `on_fail`/`rollback` 框架；但**這是推論，無真實事件佐證**。
- 恢復**資料源可用**（指令能跑、commit 能尋回）**不等於恢復演練成功**；R8 已做過一次 checkpoint-restore drill，使 COORD-01/SPEC-03 從「純設計」升為「部分實證」。
- schema_check 一次列全缺漏的行為，降低了「修一條又撞下一條」的重試浪費——對 SEC-03 成本失控有正面作用。

## 待驗證

- `rule_check` 違規（任務使用 deny 清單工具）在真實 runtime 是否被擋並寫 error log？目前僅 permissions_guard 的 **shell-deny 子集**有 runtime 證據，**policy 級工具白名單**的執行期攔截未實證。
- `completion_check` 對「假完成」的偵測，在真實 LLM 判斷下的準確率（VAL-01）。
- SEC-03「連續失敗 3 次停」與 SPEC-02「連續 3 次相同動作停」的**計數器**從未在真實多失敗序列下被觸發紀錄。
- 「工作樹被破壞 **且** context 被重置」的雙重故障組合恢復（runbook 場景單獨驗過，組合未驗）。

## 高風險假設

- **「四層 gate 都會在真實故障下正確 on_fail」——此假設對 rule/completion/risk 三層成立與否，目前無實證；若 LLM 在壓力下略過某層，系統不會自知。** 這是可靠性最大的未坐實風險。
- 「恢復 runbook 在真實雙重故障下仍可用」未經演練。
- 「3-連續-failure 停止」假設 LLM 會正確計數——但計數器靠 LLM 自我追蹤，無外部強制 hook（對照 schema/deny 有腳本強制）。

## 建議（只提案，不就地修；各自應另開 Task Card 走 ask）

1. **R-T1a**：把 `rule_check`／`completion_check`／`risk_check` 從「in-process 模擬」升級為**真實故障演練**（仿 R5），各坐實一次 error/run log。單一最高槓桿＝rule_check 的 policy 級工具白名單攔截。
2. **R-T1b**：為 SEC-03/SPEC-02 的「連續失敗/重複計數」加一個**外部可觀測的計數紀錄**（寫 logs/），讓「3 次停」可被審計而非只靠 LLM 自律。
3. **R-T1c**：演練一次 runbook 雙重故障組合（工作樹破壞 + context 重置）。

---

## 來源

- `system/GATE_POLICY.yaml`、`system/FAILURE_TAXONOMY.yaml`、`system/RECOVERY_RUNBOOK.md`、`system/validate_task_card.py`
- `tests/e2e/test_dummy_task_smoke.py`（四層 gate 模擬契約）、`tests/e2e/test_failure_drill.py`、`logs/runs/RUN-20260529-003.yaml`（R5）
- 本任務探針輸出：9-fixture schema 探測表、`git log --grep="checkpoint:"`（22 筆）、`git status`（乾淨樹）
- 交叉引用：T2 安全研究（permissions_guard runtime 強制證據）
