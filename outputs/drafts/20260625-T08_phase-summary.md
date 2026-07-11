<!--
task_id: 20260625-T08
date: 2026-06-25
skill_type: ops
status: draft
-->

# T08 實作摘要：高價值產出異 session 外審制度化（補 T04 缺口 #4）

## 總結

T04 缺口 #4：completion_check 依賴執行者誠實自評；同 session 自審 = FAILURE_TAXONOMY VAL-03「循環驗證」。**實證**：T04 §3 自審漏掉 per-ID 列舉，由 Codex（異 session 外審）在 PR #109 抓出。本卡把「異 session/外部 review」對高價值產出制度化。

## 變更

| 檔案 | 變更 |
|---|---|
| `system/APPROVAL_POLICY.yaml` | `triggers` 新增「高價值產出需異 session/外部 review 才算完成」 |
| `memory/.../decisions/20260625-D010_*.yaml` | 決策：只對高價值產出要求外審（選項 C） |

**新 trigger**：條件＝晉升 `outputs/reports/`、test_batch 回測/分析報告、`risk_level >= high`；動作＝需異 session 或外部 review（人工 / Codex PR review）複核通過才算完成，同 session 自審不足以結案；method 沿用 `human_confirm`。

## 設計取捨

- **只對高價值產出**（非全部）：外審成本對齊產出價值——low-risk 小草稿用 completion_check 自審即可，避免過度儀式（呼應「可控 > 儀式」）。
- **method 沿用 `human_confirm`**：不新增 approval-record 的 method enum，因此**不動** `check_spec_consistency.rb` 的 `ALLOWED_APPROVAL_METHOD` 與其釘死測試（避免重蹈計數測試教訓）。
- Codex PR review 已是現成、低成本的外審管道，本卡把它從「碰巧發生」變成「政策要求」。

## 驗證

- `ruby scripts/check_spec_consistency.rb` → OK；`ALL_YAML_OK`。
- APPROVAL_POLICY 仍為合法 YAML，e2e 不受影響（test_dummy_task_smoke 載 PERMISSIONS/GATE_POLICY，不載 APPROVAL_POLICY）。

## 待人工確認

- 修改 `system/APPROVAL_POLICY.yaml`、寫 `memory/` D010 屬 ask 級，於 PR #109 review 確認。
- **本卡自身即適用新規則**：作為 governance 政策變更，已透過 PR #109 的 Codex/人工 review 取得外審。
