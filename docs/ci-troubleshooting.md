# CI Troubleshooting（PR 必過檢查）

本文件對應 `README.md` 的「設定 PR 必過檢查（GitHub）」段落，提供快速排查。

## 30 秒快速自檢

1. 最新 PR 是否有 `PR Required Taskcard Checks / required-checks`。  
2. Branch protection 是否套用到正確分支（通常是 `main`）。  
3. 本機是否先跑過：
   - `scripts/check_spec_consistency.rb`
   - `python3 scripts/check_task_card_skill_type.py`

## 常見失敗排查

- **找不到 check 名稱**：先確認 PR 已觸發過一次 workflow，回到 Branch protection 重新整理再勾選。  
- **有勾 required 但仍可 merge**：確認 protection rule 套用到正確分支，且未被其他較寬鬆規則覆蓋。  
- **PR 顯示 Pending 很久**：查看 Actions 頁面是否被並行限制、或 runner 佇列過長。  
- **本機通過但 CI 失敗**：先比對本機與 CI 的 Ruby/Python 版本是否一致（workflow 使用 Ruby 3.2 / Python 3.11）。

## CI 失敗標準回報模板（可貼 PR comment）

```md
### CI 檢查失敗回報

- PR: <PR 連結>
- Commit: <commit hash>
- Workflow: PR Required Taskcard Checks / required-checks
- 失敗步驟: <Run spec consistency check | Run task card skill_type check>
- 錯誤摘要:
  - <貼 1~3 行關鍵錯誤訊息>

### 本機重現結果
- `scripts/check_spec_consistency.rb`: <pass/fail>
- `python3 scripts/check_task_card_skill_type.py`: <pass/fail>

### 初步判斷
- 類型: <設定問題 / 規格問題 / 環境問題>
- 影響範圍: <僅此 PR / 全 repo>

### 建議處置
1. <立即修正項目>
2. <需要 reviewer 確認項目>
```

## CI Failure Report Template (English)

```md
### CI Check Failure Report

- PR: <PR link>
- Commit: <commit hash>
- Workflow: PR Required Taskcard Checks / required-checks
- Failed step: <Run spec consistency check | Run task card skill_type check>
- Error summary:
  - <paste 1-3 key error lines>

### Local reproduction
- `scripts/check_spec_consistency.rb`: <pass/fail>
- `python3 scripts/check_task_card_skill_type.py`: <pass/fail>

### Initial assessment
- Type: <configuration issue / spec issue / environment issue>
- Impact: <this PR only / repository-wide>

### Suggested actions
1. <immediate fix>
2. <items requiring reviewer confirmation>
```

## 一行版超短模板（Slack / LINE）

- 中文：`[CI失敗] Severity:<P0/P1/P2> PR:<連結> Commit:<hash> Step:<步驟> 結論:<設定/規格/環境> 需協助:<是/否>`  
- English: `[CI FAIL] Severity:<P0/P1/P2> PR:<link> Commit:<hash> Step:<step> Type:<config/spec/env> Need help:<yes/no>`

## 嚴重度標籤建議（P0 / P1 / P2）

- **P0（阻斷）**：主分支無法合併、或所有 PR 持續失敗（疑似 workflow / runner / 全域規則問題）。  
  - 建議：立即通知維護者，優先修復；必要時暫停非必要合併。  
- **P1（高）**：單一 PR 被阻斷，且短時間內無法自行修復（規格衝突、跨檔不一致）。  
  - 建議：同日內完成修復或提出可審核 workaround。  
- **P2（中）**：可快速修正的單點問題（例如工具名拼字、欄位遺漏、日期未更新）。  
  - 建議：修正後重跑檢查並更新 PR comment。

## 實填範例（P0 / P1 / P2）

- 送出前請先替換所有佔位符（PR 連結、commit hash、step、結論）。  
- 最小必填欄位（至少 4 項）：`Severity`、`PR`、`Commit`、`Step`。

- **P0 範例**  
  `[CI失敗] Severity:P0 PR:https://github.com/org/repo/pull/123 Commit:abc1234 Step:Run spec consistency check 結論:環境 需協助:是`  
  （情境：多個 PR 同時卡在同一 workflow，疑似 runner/平台異常）

- **P1 範例**  
  `[CI失敗] Severity:P1 PR:https://github.com/org/repo/pull/124 Commit:def5678 Step:Run task card skill_type check 結論:規格 需協助:否`  
  （情境：單一 PR 因跨檔 skill_type 不一致而阻斷）

- **P2 範例**  
  `[CI失敗] Severity:P2 PR:https://github.com/org/repo/pull/125 Commit:ghi9012 Step:Run spec consistency check 結論:設定 需協助:否`  
  （情境：allowed_tools 單字拼錯，修正後可快速通過）

## 回報品質檢查清單（Reviewer 30 秒版）

1. **可追溯**：是否包含 `PR`、`Commit`、`Step`（可直接定位問題）。  
2. **可判斷**：是否有 `Severity` 與「結論類型（設定/規格/環境）」。  
3. **可行動**：是否明確標示「需協助（是/否）」或下一步處置。

### PR comment checklist（可直接貼上）

```md
### CI Report Review Checklist
- [ ] 可追溯：含 `PR` / `Commit` / `Step`
- [ ] 可判斷：含 `Severity` + 問題類型（設定/規格/環境）
- [ ] 可行動：含「需協助」或下一步處置
```

### PR comment checklist (English)

```md
### CI Report Review Checklist
- [ ] Traceable: includes `PR` / `Commit` / `Step`
- [ ] Diagnosable: includes `Severity` + issue type (config/spec/env)
- [ ] Actionable: includes `Need help` or explicit next action
```
