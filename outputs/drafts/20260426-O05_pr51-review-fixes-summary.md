# 20260426-O05 — PR #51 Codex Review 修正摘要

**任務**：修正 PR #51 兩條 Codex review comment。
**狀態**：done
**完成日期**：2026-04-26

## 變更項目

| # | 動作 | 檔案 | 摘要 | 對應 review |
|---|------|------|------|------|
| 1 | edit | `system/RETRO_FLOW.md` | 資料蒐集步驟改為當季 `AUDIT_LOG_<YYYY>-Q<n>.md`（索引見 `AUDIT_LOG.md`），跨季 retro 含上一季分檔 | P1 (logs/AUDIT_LOG.md:4) |
| 2 | edit | `system/COST_POLICY.md` (×2) | analysis 校準係數列改為「—（樣本 1，待 ≥ 3）」；任務級預算列備註修正為符合 SOP 第 3 條 | P2 (system/COST_POLICY.md:81) |
| 3 | edit | `outputs/drafts/20260426-A01_kb-tool-selection.md` | 校準資料表改為「原始觀測比例 1.17（未生效）」，明示與 COST_POLICY 一致 | 連帶 P2 |

## DoD 比對

| # | 條件 | 結果 |
|---|------|:----:|
| 1 | RETRO_FLOW 改指季度分檔 | ✅ |
| 2 | COST_POLICY analysis 列符合 SOP fallback | ✅ |
| 3 | CI 三檢全綠 | ✅ |
| 4 | AUDIT_LOG_2026-Q2.md 新增 1 筆 | ✅ |

DoD 4/4 通過。

## 審閱觀點

兩條 Codex review 皆 valid，指出本次優化內部三組檔案間的一致性漏洞：

- **P1**：分檔變更的下游影響（RETRO_FLOW）未追到底，是 ops 任務的常見遺漏
- **P2**：「同一 commit 同時寫入 SOP 與違反 SOP 的數據」屬於明顯自相矛盾，違反我自己寫的「SEC-04 幻覺驅動行動」緩解措施

兩項皆採用 review 建議方向（修檔而非調整 SOP），因為 SOP 本身合理（單樣本不應決定預算）。

## 後續

- 下次校準 SOP 觸發時自動處理 analysis（現累積 1 筆，待 ≥ 3）
- 之後 ops 卡涉及檔案分檔/重構時，加入「下游引用 grep 檢查」步驟（待後續 retro 時提案）

## 校準資料

- 預估 tokens：~6K
- 工具呼叫：file_read ×2、file_edit ×4、bash ×2
- ops 上限 19K，本卡符合預算
