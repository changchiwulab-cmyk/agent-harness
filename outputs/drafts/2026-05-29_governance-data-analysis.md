# 治理數據分析 — Agent Harness v2（2026-05-29）

> **草稿（draft）** ｜ Task Card：`20260529-006` ｜ skill：analysis
> 本分析同時是 R3 的「analysis 成本校準樣本 #1」（自我評估 roadmap R3）。

## 結論

Harness 的治理儀表**整體健康**（governance_metrics M1–M4 全 ✅），但有三個結構性訊號值得在下次 RETRO 處理：(1) 任務組成高度偏 `ops`、`analysis` 嚴重不足；(2) 草稿晉升率偏低（draft:report ≈ 8:1）；(3) 失敗/批准紀錄本 session 才剛被「種下第一筆」，樣本仍稀薄。**沒有任何指標達到警戒，但成本校準與決策回看是當前最該補的兩塊資料債。**

## 一、數據（取自 repo 實況 + `scripts/governance_metrics.py`）

| 面向 | 數值 |
|------|------|
| Task Card 總數 | 39 |
| ├ 依 skill | ops 21（54%）｜ review 6（15%）｜ research 5（13%）｜ writing 4（10%）｜ **analysis 3（8%）** |
| ├ 依 status | review 19｜done 16｜in_progress 2｜pending 2 |
| Audit 覆蓋率（M3） | 33/35 = **94.3%** ✅ |
| 月新增（M1） | 2026-04=16、2026-05=23 ✅ |
| draft:report 比（M2） | 8.00（24:3）✅；版控追蹤 drafts .md = 33 / reports = 3 |
| 原生重疊（M4） | 30% ✅（< 40% warn 線） |
| logs/runs | 2（含本 session R5 首筆 `failed`） |
| logs/approvals | 1（本 session R1 首筆回填） |
| logs/errors | 2（S01 歷史 + R5 演練） |
| Decision Log | 7 筆，全 `active`，**0 筆曾被 revisit** |

## 二、發現

1. **技能組合失衡，analysis 是最薄的一環。** `ops` 佔 54%，`analysis` 僅 8%（3 張）。這直接解釋了 COST_POLICY 為何 analysis 校準樣本=0——不是沒記錄，而是**樣本基數太小**。決策支援類工作偏少，可能代表 Harness 目前多用於「執行/維運」而非「策略判斷」。

2. **草稿紀律強、但晉升選擇性高。** draft:report ≈ 8:1 代表「對外只產草稿」硬規則被切實遵守（健康）；但只有 3 份被晉升為正式報告，顯示晉升是高門檻、低頻事件。這本身不是問題，但意味 `outputs/reports/` 不適合當「成熟度」指標——草稿才是主要產物。

3. **失敗/批准可觀測性剛從 0 起步。** 本 session 之前，logs/runs 僅 1 筆 happy-path、logs/approvals 為空。R5/R1 後變成 runs 2、approvals 1、errors 2——**第一筆真實 `failed` 與第一筆批准紀錄都是本週才有的**。趨勢正確，但樣本仍不足以做統計。

4. **決策資料債：7 筆全 active、零回看。** D006（「累積 10 筆 runs 後檢視」）與 D001（「20+ 並行任務」）是僅有的兩個可量化觸發，目前皆未達標（runs=2、進行中任務=4）。其餘 5 筆為非量化觸發，需人工回看——但從未發生過。

## 三、建議（對應 roadmap）

| # | 建議 | 對應 |
|---|------|------|
| 1 | **下次 RETRO 重算 analysis 校準**：本卡貢獻樣本 #1（~16K）；連同現有 3 張 analysis 卡，可望湊到 COST_POLICY 要求的 ≥3 筆，正式補上 analysis 係數 | R3 收尾 / COST_POLICY |
| 2 | **建立決策回看機制**：7 筆決策零回看是治理盲點 | R4（本批次同時交付） |
| 3 | **持續累積失敗/批准樣本**：runs/approvals 各只 1–2 筆，建議後續真實任務確實寫入，讓觀測層有統計基礎 | R5/R6/R7 |
| 4 | 用 draft 數（非 report 數）當產出量指標；report 維持高門檻 | 指標定義 |

## 四、本分析作為成本樣本

- skill_type：`analysis`
- token 實測估計：**~16K**（讀取 audit/tasks/decisions + governance_metrics 輸出 + 綜整撰寫）
- 用途：COST_POLICY analysis 校準樣本 #1（係數 = actual_avg / 12K 預估；需累積 ≥3 筆後於 RETRO 計算）
