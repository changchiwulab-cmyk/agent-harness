# 20260620-001 任務內驗證閉環 — 交付摘要（草稿）

> 狀態：待人工審核（risk_level: medium，改動 `system/` 與 `CLAUDE.md`，依 APPROVAL_POLICY 出草稿）
> Task Card：`tasks/2026-06-20_verification-loop.yaml`
> 計畫：`/root/.claude/plans/loop-compiled-metcalfe.md`

## 結論

把 `GATE_POLICY.yaml` 的四層驗證從**一次性線性管線**收斂成**有界、會終止、可稽核的閉環**
（驗證 → 修正 → 再驗證），並提供可執行驅動器 `scripts/verification_loop.py` 與完整測試，
讓「閉環本身」成為可被檢驗的工程。本地 9 項 CI-equivalent 檢查全綠。

## 設計重點

- **閉環不是每層都迴圈**：各 gate 的處置沿用 `GATE_POLICY.yaml` 既有 `on_fail` 語意——
  schema=`retry_fixable`（最多 1 次）、rule=`hard_stop`（不重試）、completion=`human_gated`、
  risk=`escalate`。
- **終止保證**：閉環必落在四個終態之一 `pass / hard_stop / escalated / exhausted`；非終態為
  `continue`（可修且預算未盡，agent 修正後 iteration+1 重驗）。
- **預算與硬規則對齊**：`max_iterations = min(Task Card.max_retries, 3)`，永不超過 CLAUDE.md
  「連續失敗 3 次就停下來」的硬上限；schema 另有自身上限（2 次嘗試）。
- **可稽核帳本**：每輪記 `{iteration, gate_results, first_fail, disposition, action}`，落地於
  `EXECUTION_LOG_SCHEMA.yaml` 新增的（向後相容）`verification_loop` 區塊。
- **重用優先**：schema_check 直接呼叫既有 `system/validate_task_card.py` 的 `validate()`；
  rule_check 讀 `system/PERMISSIONS.yaml` 的 deny 清單。未重造輪子。

## 變更清單

| 類型 | 檔案 | 說明 |
|---|---|---|
| 新增規格 | `system/VERIFICATION_LOOP.yaml` | 閉環演算法 / disposition / 終態 / 預算 / 帳本 schema |
| 修改規格 | `system/GATE_POLICY.yaml` | header 加閉環交叉引用（四層內容不動） |
| 修改規格 | `system/EXECUTION_LOG_SCHEMA.yaml` | 新增選用 `verification_loop` 區塊 |
| 修改規格 | `CLAUDE.md` | 第 6 步指向 `VERIFICATION_LOOP.yaml`（僅一行，context budget ~1208/3000） |
| 新增程式 | `scripts/verification_loop.py` | 可執行驗證驅動器（exit 0/1/2、`--json`） |
| 新增測試 | `scripts/test_verification_loop.py` | 22 項單元測試 |
| 新增測試 | `tests/e2e/test_verification_loop_drill.py` | 5 項 e2e（四終態 + ledger 形狀） |
| 新增 fixtures | `tests/e2e/fixtures/loop_*.yaml` | 4 個（放 tests/，避開 `tasks/**` CI glob） |
| 修改 CI | `.github/workflows/spec-consistency.yml` | 新增 2 個測試步驟 |
| 重新產生 | `frontend/data.json` | 反映新 Task Card（manifest 無漂移） |

## 驗證結果（實跑）

四個終態 + continue 全數實證：

```
iter1 broken card  → continue  | first_fail=schema_check | retry_fixable
iter2 fixed card   → pass      | gate_results 全 pass
rule violation     → hard_stop | first_fail=rule_check   | hard_stop
high-risk→reports/ → escalated | first_fail=risk_check   | escalate
iter3/3 still fail → exhausted | 不超過硬上限 3
```

本地 CI-equivalent 9 項全綠：context budget、frontend manifest（tests + drift）、permissions guard、
audit log、dummy smoke、failure-drill、verification-loop unit、verification-loop e2e、decision revisit。

## 使用方式

```bash
# 單輪驗證一張 Task Card（不夠的層會說明 next_action）
python3 scripts/verification_loop.py <task_card.yaml> [--completion pass,fail,...] \
    [--run-log logs/runs/RUN-*.yaml] [--iteration N] [--max-iterations M] [--json]
```

agent 在兩輪之間執行修正，然後以遞增的 `--iteration` 重新呼叫；`outcome` 欄位指示下一步。

## 待人工確認（ask 權限項）

- `system/*`（VERIFICATION_LOOP / GATE_POLICY header / EXECUTION_LOG_SCHEMA）與 `CLAUDE.md`
  的修改屬 `modify_system_rules` / `modify_claude_md`（ask 等級），請審閱 diff。
- 確認後可將本摘要自 `drafts/` 升級至 `outputs/reports/`（另開 promotion Task Card）。

## 待驗證

- 真實多輪任務尚未在正式 run 中產生 `verification_loop` 帳本（目前僅 e2e drill 證明）；
  建議下一個 high-risk/多階段任務實跑一次，把帳本寫進 `logs/runs/RUN-*.yaml`。
