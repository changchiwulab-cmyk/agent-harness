# Task 20260424-O02 — Governance Docs Restructure Summary

## 執行結果
**DoD 8/8 通過。** 所有 spec / ruby test / YAML 檢查全綠。

## 變更清單

### 晉升（drafts → reports）
| 動作 | 來源 | 目標 |
|------|------|------|
| 新增 | — | `outputs/reports/token-calibration-v1.md`（含晉升標記區塊） |
| 修改 | `outputs/drafts/token-calibration-table-v1.md` | 檔尾加「已晉升為 reports/」回指 |
| 修改 | `system/COST_POLICY.md` | 校準係數章節資料來源路徑更新至 `outputs/reports/token-calibration-v1.md` |

### INTAKE_FLOW 主路調整
| 檔案 | 變更 |
|------|------|
| `system/INTAKE_FLOW.md` | 完全重寫：fast-path 升為預設主路；intake 模式降為 fallback；流程圖與說明順序重排 |

### WEEKLY_REVIEW 歸檔
| 動作 | 原路徑 | 新路徑 |
|------|--------|--------|
| `git mv` | `tasks/WEEKLY_REVIEW_TEMPLATE.md` | `tasks/archived/WEEKLY_REVIEW_TEMPLATE.md` |
| 路徑引用更新 | `system/RETRO_FLOW.md` | 指向新路徑 |
| README 結構圖 | 原 `WEEKLY_REVIEW_TEMPLATE.md` 條目 | 改為 `archived/` 資料夾說明 |

## 驗證輸出
```
scripts/check_spec_consistency.rb        → OK (exit 0)
ruby scripts/test_check_spec_consistency.rb → 14/14 pass, 43 assertions
ruby YAML parse loop                     → ALL_YAML_OK
```

## 引用一致性檢查
- `token-calibration-table-v1` 歷史引用（舊 Task Card、AUDIT_LOG、retro-2026-Q2-01）保留原樣 — 屬於歷史紀錄，不溯及追改
- `WEEKLY_REVIEW_TEMPLATE` 歷史引用同上
- 活性引用（COST_POLICY、RETRO_FLOW、README）全部指向新路徑 ✅

## 延伸觀察
- 未來如有更多模板 deprecated，皆應走 `tasks/archived/` 或 `system/archived/` 模式
- INTAKE_FLOW 重寫後 skill_type 判斷路徑未變，ROUTING_RULES.md 無需同步修改
