# Task 20260424-O01 — Cleanup & Validator Consolidation Summary

## 執行結果
**DoD 8/8 通過。** spec-consistency 全綠、ruby 測試 14 runs / 43 assertions / 0 failures、YAML 解析 OK。

## 變更清單

### 刪除（git rm，歷史保留）
| 檔案 | 刪除原因 |
|------|---------|
| `scripts/check_task_card_skill_type.py` | 僅檢查 skill_type 子集，已被 `check_spec_consistency.rb` 全量涵蓋 |
| `scripts/test_check_task_card_skill_type.py` | 上檔的測試，隨之移除 |
| `.github/workflows/task-card-skill-type-check.yml` | 與 spec-consistency.yml 重疊的 CI workflow |

### 修改
| 檔案 | 變更 |
|------|------|
| `.github/workflows/spec-consistency.yml` | 移除 Python setup、Python unit tests、Python skill-type check 三個 step（因已無 Python CI 目標） |
| `README.md` | 檢查段新增 `system/validate_task_card.py` 單張卡用法；新增「安全政策」段落引用 SECURITY.md |

### 驗證保留
| 工具 | 角色 |
|------|------|
| `scripts/check_spec_consistency.rb` | CI 主驗（目錄、schema、日期一致性、路徑） |
| `scripts/test_check_spec_consistency.rb` | 上檔的單元測試 |
| `system/validate_task_card.py` | 單張 Task Card CLI（開發者手動用） |

## 驗證輸出
```
scripts/check_spec_consistency.rb        → OK (exit 0)
ruby scripts/test_check_spec_consistency.rb → 14/14 pass, 43 assertions
ruby YAML parse loop                     → ALL_YAML_OK
```

## 延伸觀察
- `tasks/examples/sample-data/` 已驗證含 `contacts-raw-notes.md` 與 `vietnam-ai-tools-research-draft.md`，非空，無需處理（原 Task Card 估計有誤已於 DoD 更新說明）。
- CI workflow 由 2 條收斂為 1 條，PR 檢查清單同步精簡。
