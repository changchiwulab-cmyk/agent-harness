# 20260426-O01 — Skill / Routing / Lifecycle 治理條款補完摘要

**任務**：補完 retro-2026-Q2-01 已建議但未落地的三項治理條款。
**狀態**：done
**完成日期**：2026-04-26

## 變更項目

| # | 動作 | 檔案 | 摘要 |
|---|------|------|------|
| 1 | edit | `skills/research/SKILL.md` | 新增「Web search 策略」段：精準優先、保留 1 輪備用、SEC-03 對照 |
| 2 | edit | `system/ROUTING_RULES.md` | 新增「量化拆分閾值」段：DoD ≥ 8 / max_tool_calls > 25 / token > 校準上限 ×1.5 / 檔案 > 8 |
| 3 | create | `outputs/LIFECYCLE.md` | 三態（drafts/reports/archived）晉升與棄用 SOP，含現有 6 份草稿狀態盤點 |
| 4 | create | `outputs/archived/.gitkeep` | 啟用 archived 目錄 |
| 5 | edit | `tasks/2026-04-26_skill-routing-lifecycle-tuning.yaml` | Task Card 本身 |

## DoD 比對

| # | 條件 | 結果 |
|---|------|:----:|
| 1 | research/SKILL.md 新增 web search 策略段 | ✅ |
| 2 | ROUTING_RULES 新增量化拆分閾值 | ✅ |
| 3 | outputs/LIFECYCLE.md + archived/ | ✅ |
| 4 | 6 份草稿在 LIFECYCLE.md 內標記狀態 | ✅ |
| 5 | spec-consistency / yaml-parse / context-budget 全綠 | ✅ |
| 6 | AUDIT_LOG 新增 1 筆 | ✅ |

DoD 6/6 通過。

## 注意

- 三項條款源自 retro-2026-Q2-01 採納清單與 P2 優化建議，本卡為合併執行（同 ops skill、同治理層級）。
- LIFECYCLE.md 將被後續 Card B 引用作為 outputs/templates/ 對外交付樣板的銜接點。
- 任務摘要類檔案（`*-summary.md`）正式定義為「終態」，不晉升、不棄用。

## 校準資料

- 預估 tokens：~12K
- 工具呼叫：file_read ×3、file_edit ×3、file_write ×2、bash ×3
- ops 校準係數參考值（1.56）：實測落在 19K 預算內
