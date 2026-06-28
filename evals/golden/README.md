# Golden Set — 回歸錨點

依 `system/EVAL_POLICY.yaml` 的 `golden_regression` 規則，`cases.yaml` 列出**真實既有產出**
與其期望 verdict，作為品質回歸的錨點（對齊 2026 best practice：golden set 取自真實案例，非合成）。

## 規則

- `scripts/run_evals.py --check` 對每筆 `evals/results/*.yaml`：若其 `target` 命中某 golden case，
  該 result 的 `verdict` **不得低於** golden 的 `expected_verdict`（順序 fail < partial < pass），否則 CI 失敗。
- 沒有對應 result 的 golden case 為惰性錨點（不報錯），待日後評分時生效。

## 維護

- 每次把一份產出晉升為 `outputs/reports/` 前建議先評分，並視情況把它加為 golden 錨點。
- 錨點只收「已實際評分過」的案例，避免捏造 expected_verdict。
