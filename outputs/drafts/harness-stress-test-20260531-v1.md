# Agent Harness v2 深度測試觀察報告 — 正式報告（harness-stress-test-20260531-v1）

---

## 晉升標記

| 項目 | 內容 |
|------|------|
| **原始 draft** | `outputs/drafts/2026-05-31_harness-stress-test-observations.md` |
| **晉升日期** | 2026-05-31 |
| **晉升任務** | Task Card `20260531-002`（tasks/2026-05-31_promote-physical-ai-roadmap.yaml） |
| **審閱者** | 人工確認（使用者於本 session 回覆「是」核准晉升） |
| **資料來源** | logs/runs/RUN-20260531-001.yaml、logs/AUDIT_LOG.md、PR #92 review |
| **原始任務** | Task Card `20260531-001`（深度測試） |

### 後續追蹤
| # | 發現 | 狀態 | 追蹤 |
|---|------|:----:|------|
| F1 | 權限模型張力（執行任務無權修復 CI 紅燈） | ⏳ 待議 | 另立 Task Card 改 system/ 走 ask |
| F2 | 工具計數未分離 task/overhead | ⏳ 待議 | COST_POLICY 校正候選 |
| F3 | rate-limit 降級路徑（正向） | ✅ 驗證 | 已坐實 SEC-03 路徑 |
| F4 | research DoD 字數判定 | ⏳ 待議 | TASK_CARD_TEMPLATE / SKILL 校正候選 |

---

以下為原始草稿全文保留（除上方「晉升標記」為新增，其餘未變動）。

# Agent Harness v2 深度測試觀察報告

- 來源任務：Task Card `20260531-001`（Physical AI 進度表，research）
- 測試性質：首次完整 happy-path 高負載實證（與 R5 故障演練互補）
- 紀錄出處：`logs/runs/RUN-20260531-001.yaml`、`logs/AUDIT_LOG.md`、本 PR review
- 狀態：草稿（待晉升）

## 結論

以「產出 Physical AI 進度表」這個高負載真實研究任務當測試載荷，端到端壓測 harness：**四層 gate 全 pass、三個 checkpoint、執行紀錄/audit/批准三條紀錄路徑全部走過**，補上自評報告（harness-self-assessment-v1）點名的最大弱點「關鍵 happy-path 從未經真實高負載實證」。同時暴露 4 個值得處理的框架弱點，均非阻斷性。

## 四層 Gate 結果

| Gate | 結果 | 證據 |
|------|:----:|------|
| schema_check | ✅ pass | `validate_task_card.py` exit 0 + `check_spec_consistency.rb` OK |
| rule_check | ✅ pass | 任務工具全 ⊆ allowed_tools；無 deny 命中；web_search 5/5 未超 |
| completion_check | ✅ pass | 10 條 DoD：9 條 pass，#8 字數為「含表格達標」軟 pass |
| risk_check | ✅ pass | 輸出鎖 `outputs/drafts/`，未誤入 `reports/` |
| 迴歸保護 | ✅ pass | smoke + failure_drill 共 7 測試仍綠（未動 system/fixture）|

## 壓測發現（4 點，依優先序）

### F1 — 權限模型張力：執行任務無權自行修復 CI 紅燈（P1）
新增 Task Card + run log 必然造成 `frontend/data.json` 漂移，使 CI `validate-spec` 變紅；但研究任務的 `allowed_tools` 白名單不含改 `frontend/data.json` 的權限（屬 ask 級）。結果是「執行任務本身無法讓自己的 PR 轉綠」，須 ask 級人工介入重生 manifest。
**建議**：(a) 在 GATE_POLICY / PERMISSIONS 明文界定 manifest 重生之權限地位；或 (b) 讓研究類 Task Card 可選擇性納入「衍生檔重生」的受控動作。

### F2 — 工具計數模型未分離「任務工具」與「context 載入 / 驗證」（P2）
`actual_tool_calls=16` 超出 `max_tool_calls=12`，主因 context 載入的 `file_read` 與 harness 自身的 gate 驗證（validate / check_spec / e2e / manifest --check）都被算進去。這讓預算門檻容易誤報「超支」。
**建議**：COST_POLICY 區分 task-tool 與 overhead-tool，或將驗證器執行排除在 `max_tool_calls` 之外。

### F3 — rate-limit 降級路徑首次被真實外部限制觸發並正確處理（P3，正向）
第 5 次 `web_search` 觸 session rate limit（非 COST_POLICY 的 5 輪上限）。1 次失敗 < 3 次門檻 → 依 `logs/errors/2026-04-04` 前例不硬停，降級用既有 T03 + 訓練知識並標 `[待驗證]`（SEC-03 路徑）。
**建議**：run log 紀錄需可區分「budget 用罄」與「外部 rate limit」兩種成因（本次兩者恰好同時發生）。

### F4 — research 類 DoD 的「字數」判定與品質脫鉤（P3）
DoD 寫「~3500-5000 字（含表格）」；純 CJK prose 2975、含表格非空白 8961，判定模糊。
**建議**：研究類 DoD 改以「章節/主張覆蓋度」為主、字數為輔。

## cost-quality 資料點（留待下次 retro 校正 COST_POLICY）

- 投入：web_search 5（實得 4）、~47K token（rule_estimated），超 research 建議上限 32K 約 47%。
- 產出：全球矩陣（6 時段 × 5 子領域）+ 5 子領域事實 + 台灣三切入點 + 5 條敏感性假設 + 真實來源。
- 對照 T03（台灣 deep dive，~45K）：放寬預算換得的增量主要在「子領域廣度」與「敏感性結構」，與 T03 的「政策時序/敏感性/事件日曆」增量結論一致。
- **本次不改 COST_POLICY**，僅作資料點累積，待下次 retro（累積 5 筆或手動觸發）正式校正。

## 與既有測試的關係

- **smoke**（test_dummy_task_smoke）：驗四 gate 靜態契約。本任務補上其註解點名的弱點——真實 full happy-path 負載。
- **failure_drill**（test_failure_drill / RUN-20260529-003）：固定失敗路徑。本任務固定成功路徑，兩者合起來覆蓋 gate 的 pass / fail 兩面。
