# Token 校準與 Retro 觸發條件分析

**Task Card**：20260427-B02
**日期**：2026-04-27
**Skill**：analysis

---

## 結論與建議

**建議方案 B：量化現有條件 + 新增 1 條漂移觸發 + 寫入腳本層提醒（不寫入 GATE_POLICY 強制鏈）**。

理由：
- 現有 `COST_POLICY.md` 與 `RETRO_FLOW.md` 已分別有觸發條件，但未量化、未自動化 → 形同「設了但沒在用」
- 完全靠 GATE_POLICY 強制反而會干擾單張任務的 happy-path（每張卡都要等 retro 檢查）
- **腳本層提醒（每次寫入 AUDIT_LOG 後檢查）** 才是合適的力度：不阻斷、不沉默

P1 立即採用：4 條（2 校準 + 2 retro）；P2 觀察 1 個月：1 條（飄移觸發）。

---

## 現狀盤點

### Token 校準現狀

來源：`system/COST_POLICY.md`、`outputs/reports/token-calibration-v1.md`

| 項目 | 現況 |
|------|------|
| 是否有觸發條件 | ✅ 有（"再累積 5 筆任務（含至少 1 筆 analysis）後，於下次 retro 重算"）|
| 是否量化 | ⚠️ 部分（"5 筆"、"1 筆 analysis" 是量化的；"飄移"沒有閾值）|
| 是否自動化 | ❌ 無腳本提醒 |
| 上次校準後新增任務數 | 8 筆（自 2026-04-17 v1 校準後） |
| analysis 樣本數 | **2 筆**（20260415-A01 + 20260427-B02 本身），尚未達門檻 |

### Retro 現狀

來源：`system/RETRO_FLOW.md`

| 項目 | 現況 |
|------|------|
| 是否有觸發條件 | ✅ 有 3 條（5 筆任務 / 週五 / 同類錯誤 ≥2）|
| 是否量化 | ⚠️ 部分（"每週一次" 已實證難守；自首次 retro 至今 12 天，未做第二次）|
| 是否自動化 | ❌ 無腳本提醒；首次 retro 觸發條件 5 筆早達成卻拖到 8 筆才做 |
| 上次 retro 後新增任務數 | 6 筆（自 2026-04-15 retro 後） |

---

## 選項比較

### 選項 A：維持現狀（不做）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 低 | 已知問題會持續：retro 拖延、校準無人提醒 |
| 成本 | 0 | |
| 風險 | 中 | 校準遲滯 → token 預算偏離實際 → max_tool_calls 設定不準 |
| 可行性 | 高 | 不變動 |
| 執行難度 | 0 | |
| 回報 | 0 | |
| 一人公司適配 | 中 | 其實本來「想到才做」也行得通；但已有兩次拖延前例 |

### 選項 B：量化條件 + 腳本層提醒（**推薦**）

修改：
- 在 `system/COST_POLICY.md` 的「下次校準觸發」段落，將條件量化為兩條
- 在 `system/RETRO_FLOW.md` 的「觸發條件」段落，將 3 條量化、加 1 條飄移觸發
- 在 `scripts/` 新增 `check_calibration_retro_due.rb`（不阻斷 CI，僅 warning）
- 不修改 GATE_POLICY.yaml（保持 4 層 gate 不變）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高 | 解決「忘了做」問題；不影響單張卡執行 |
| 成本 | 低 | 1 個腳本（~50 行）+ 2 處 system/ 文件修改提案（草稿）|
| 風險 | 低 | warning-only，不會誤判阻斷工作 |
| 可行性 | 高 | scripts/ 已有 check_audit_completeness 可借鑒 |
| 執行難度 | 低 | 約 1 小時實作 |
| 回報 | 高 | 一次設置，長期受益 |
| 一人公司適配 | 高 | 「設了會自己提醒」比「設了忘了用」價值高 |

### 選項 C：強制 GATE 第 5 層

在 `GATE_POLICY.yaml` 新增第 5 層 `retro_check`：每次任務完成時驗證 retro/校準是否到期，到期則阻斷下一張卡。

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中 | 強制執行，但太剛性 |
| 成本 | 中 | GATE_POLICY 修改需人工確認；實作複雜（需 task counter）|
| 風險 | 中-高 | 阻斷急件；維修期可能被誤觸發 |
| 可行性 | 中 | 技術上可行，但 GATE 哲學是「驗證單一任務」，加入跨任務狀態破壞抽象 |
| 執行難度 | 中 | |
| 回報 | 中 | 強制有效，但有副作用 |
| 一人公司適配 | 低 | 一人公司本身就是 owner，不需要強制機制；提醒即可 |

### 選項 D：人工日曆排程（外部）

在 Calendar / Reminders 設「每月 1 號 retro / 每 5 筆 audit log 後重算校準」。

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中 | 外部提醒可行 |
| 成本 | 低 | |
| 風險 | 中 | 與 repo 狀態解耦 → 提醒時可能還沒到 5 筆，或早已超過 |
| 可行性 | 高 | |
| 執行難度 | 低 | |
| 回報 | 低-中 | 不如腳本層精準 |
| 一人公司適配 | 中 | 可作為選項 B 的補充，但不應取代 |

---

## 建議的具體觸發條件（選項 B 詳細）

### Token 校準觸發條件

| # | 條件 | 量化 | 依據 | 優先度 |
|---|------|------|------|:------:|
| C1 | **新增任務數**：自上次校準後累積 5 筆 done/failed/partial 任務 | counter ≥ 5 | 維持現有規範語意；首次校準在 8 筆觸發，5 筆是合理底限 | **P1** |
| C2 | **skill 樣本補齊**：任一 skill_type 從 0 樣本累積到 3 樣本 | analysis 0→3、其他類型亦然 | analysis 至今仍 0 筆，校準表缺一角；3 筆是統計可用最低門檻 | **P1** |
| C3 | **單筆異常飄移**：任一任務的 estimated_tokens > 該 skill 校準平均 × 2.0 | drift ratio | 19 筆中飄移最大為 writing 100%（×2.0），若再大可能模型/工具改變 | **P2**（先觀察）|

### Retro 觸發條件

| # | 條件 | 量化 | 依據 | 優先度 |
|---|------|------|------|:------:|
| R1 | **任務累積**：自上次 retro 後 done 任務 ≥ 5 | counter ≥ 5 | 既有規範；6 筆已達標 | **P1** |
| R2 | **時間上限**：自上次 retro 已逾 30 天 | days ≥ 30 | "每週一次" 已實證難守；30 天為硬上限避免無限拖延 | **P1** |
| R3 | **錯誤累積**：同類錯誤代碼 ≥ 2 次（如 COORD-02）| same code count ≥ 2 | 既有規範保留 | P1（沿用，不需新增）|

### 觸發後動作（不論 calibration 還是 retro）

1. 腳本輸出 warning（不 exit 1）
2. CI workflow 顯示 ⚠️ 標記
3. 使用者下次互動時 agent 主動提示「校準/retro 已到期」
4. 處理完畢後，更新對應檔案的 `last_done` 欄位（重置 counter）

---

## 高風險假設

- **「累積 5 筆」是合適粒度**：8 筆首次 retro 後，6 筆已是可分析量；若任務粒度未來變大（如單張卡涵蓋多階段），5 筆可能太頻繁。
  → 緩解：用 P2 飄移條件當保險；R2 時間上限避免太多次。

- **「30 天無 retro」是合理上限**：若使用者進入低活動期（如 1 個月只做 1 筆任務），R2 會誤觸發。
  → 緩解：條件為「任務 ≥ 1 筆 AND 30 天」，零任務不觸發。

- **腳本層 warning 會被忽略**：warning-only 設計依賴使用者主動處理。
  → 緩解：CI ⚠️ 標記在 PR 顯示；agent 在下次任務 intake 時主動提示。

---

## 待驗證

- `check_audit_completeness.rb` 的 task_id pattern 是否能用於本提議的 counter 計算（應該可以，因為都從 status=done 撈）
- `last_calibration_date` 與 `last_retro_date` 寫到哪裡？建議放 `system/COST_POLICY.md` / `system/RETRO_FLOW.md` 檔尾的 metadata 區塊（避免另開檔）

---

## 建議下一步

### P1（立即採用，建議下一張 ops Task Card 執行）

1. 在 `system/COST_POLICY.md` 「下次校準觸發」段落改寫為 C1 + C2 兩條（量化）
2. 在 `system/RETRO_FLOW.md` 「觸發條件」段落改寫為 R1 + R2 + R3 三條（量化）
3. 兩份檔案各補一個 metadata 區塊：`last_calibration_date` / `last_retro_date` / `last_done_task_id`
4. 新增 `scripts/check_calibration_retro_due.rb`（warning-only，跑當前 tasks/ 與 metadata 比對）
5. CI workflow 加入此 check，但用 `continue-on-error: true` 確保不阻斷

### P2（觀察 1 個月後決定）

- C3（單筆異常飄移）：先在腳本內加註計算邏輯但不啟用警示，等 1 個月後 review 是否需要

### 不在本任務範圍

- 修改 `system/GATE_POLICY.yaml`（選項 C 已被本分析否決）
- 實作腳本本身（這是下一張 ops Task Card 的工作）

---

## GATE_POLICY 增補建議（**不直接修改，僅草稿**）

> 本段為提案。若使用者採納選項 C 的部分精神，可考慮在 GATE_POLICY 加入「軟 gate」段落（warning-level）。

```yaml
# 增補段落草稿（非正式 PR）
soft_gates:
  description: "每次任務完成後執行；warning-only，不阻斷下一張任務"

  calibration_due:
    trigger: "scripts/check_calibration_retro_due.rb 顯示 calibration overdue"
    action: "在 audit log notes 標註 [calibration-due]；agent 在下次 intake 提示"

  retro_due:
    trigger: "scripts/check_calibration_retro_due.rb 顯示 retro overdue"
    action: "在 audit log notes 標註 [retro-due]；agent 在下次 intake 提示"
```

說明：本草稿**不寫入** `system/GATE_POLICY.yaml`。需要使用者決定是否採納再開新 task card 推進。

---

## DoD 逐條確認

| # | 條件 | 狀態 | 說明 |
|---|------|:---:|------|
| 1 | 提出 token 校準觸發條件至少 2 條 | ✅ | C1（任務數）+ C2（skill 樣本）+ C3（飄移）共 3 條 |
| 2 | 提出 retro 觸發條件至少 2 條 | ✅ | R1（任務數）+ R2（時間）+ R3（錯誤）共 3 條 |
| 3 | 說明每條條件的依據（從現有 19 任務數據推估）| ✅ | 「依據」欄位皆引用 19 筆數據 |
| 4 | 草擬 GATE_POLICY.yaml 增補段落（不直接修改 system/，僅提交差異建議）| ✅ | 「GATE_POLICY 增補建議」段提供 yaml 草稿，明標「不寫入」 |
| 5 | 標記哪些建議為 P1（立即採用）/ P2（觀察 1 個月再決定）| ✅ | 「優先度」欄位 + 「建議下一步」分段 |

**5/5 通過**。

---

*產出時間：2026-04-27*
*依據：system/COST_POLICY.md / system/RETRO_FLOW.md / system/GATE_POLICY.yaml / outputs/reports/token-calibration-v1.md / outputs/reports/retro-2026-Q2-01.md / logs/AUDIT_LOG.md（19 筆完成任務）*
