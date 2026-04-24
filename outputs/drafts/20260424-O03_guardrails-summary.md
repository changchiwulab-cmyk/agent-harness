# Task 20260424-O03 — Engineering Guardrails Summary

## 執行結果
**DoD 9/9 通過。** 新增 context budget CI；Execution Log Schema 做出 Narrow Scope 決策並文件化。

## 變更清單

### 新增 CI 護欄
| 檔案 | 內容 |
|------|------|
| `scripts/check_context_budget.rb` | 加總 CLAUDE.md + GLOBAL_RULES.md 字元數 / 4（CJK 友善），超 3K → exit 1 |
| `scripts/test_check_context_budget.rb` | 8 runs / 11 assertions，涵蓋空檔、ASCII、CJK、邊界四捨五入 |
| `.github/workflows/spec-consistency.yml` | 新增 `Context budget check` step（先跑 test，再跑 check） |

### 當前預算狀態
```
CLAUDE.md               ~312 tokens
system/GLOBAL_RULES.md  ~242 tokens
TOTAL                   ~554 tokens (budget 3000)
```
餘裕 ~2,446 tokens（使用率 18.5%）。

### Execution Log Schema 收斂決策
- **選項**：A. Enforce ／ B. Deprecate ／ C. Narrow Scope
- **決定**：C（Narrow Scope）
- **觸發條件**（寫入 logs/runs/ 的情境）：
  1. `status = failed`
  2. `status = partial`
  3. `risk_level >= high`
  4. `checkpoints >= 3`（多階段複雜任務）
- **其餘**：happy-path 任務僅寫 AUDIT_LOG 即可

### Decision Log
| 檔案 | 內容 |
|------|------|
| `memory/active_projects/agent-harness/decisions/20260424-D006_execution-log-scope.yaml` | 結構化決策紀錄，含三選項對照、風險、重檢觸發條件 |

### 修改
| 檔案 | 變更 |
|------|------|
| `system/EXECUTION_LOG_SCHEMA.yaml` | 檔頭加「使用範圍」段落，明列 4 種觸發條件，引用 D006 |

## 驗證輸出
```
scripts/check_spec_consistency.rb            → OK (exit 0)
ruby scripts/test_check_spec_consistency.rb  → 14/14 pass, 43 assertions
scripts/check_context_budget.rb              → OK (~554 / 3000 tokens)
ruby scripts/test_check_context_budget.rb    → 8/8 pass, 11 assertions
ruby YAML parse loop                         → ALL_YAML_OK
```

## 延伸觀察
- char/4 對純 CJK 內容是「過度低估」（Claude/GPT tokenizer 實測 CJK 常 1 char ≈ 1 token）。目前估值 554 vs 預算 3000 餘裕充足，粗估已夠；未來若逼近上限，可換成更精確的 tokenizer-based 估算
- D006 設有 revisit_trigger：未來 2 筆 failed/partial 任務未寫 runs/ → 升級為 enforce
