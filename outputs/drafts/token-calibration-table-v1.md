# Token 校準資料對照表 v1

> **用途**：作為 COST_POLICY「校準係數」章節（Stage 3 / B2）的資料依據。
> **資料來源**：`logs/AUDIT_LOG.md` 全部 8 筆任務紀錄（2026-04-04 ~ 2026-04-09）。
> **狀態**：草稿，待 Stage 3 晉升入 COST_POLICY.md 後再更新。

---

## 一、原始資料（自 AUDIT_LOG 抽取）

| task_id | skill_type | estimated_tokens | 備註 |
|---------|-----------|------------------|------|
| 20260404-R01 | research | 18K | web search 3/3 全用完 |
| 20260404-S01 | research | 25K | 第 3 次 web search 遇 rate limit |
| 20260404-W01 | writing | 20K | 承接 S01 研究 |
| 20260404-R02 | review | 12K | tools inventory 審查 |
| 20260404-RV01 | review | 18K | proposal v1 審查 |
| 20260404-O01 | ops | 10K | tools inventory 修正 |
| 20260404-O02 | ops | 15K | proposal v2 修正 |
| 20260409-001 | review | 0（未填） | 系統驗證任務，token 未實測 — **不納入統計** |

**有效樣本**：7 筆（扣除 20260409-001）

---

## 二、分組統計

| skill_type | 樣本數 | min | max | 平均（實測） | 建議上限 (×1.5) |
|-----------|:-----:|----:|----:|------------:|---------------:|
| research | 2 | 18K | 25K | 21.5K | **32K** |
| writing  | 1 | 20K | 20K | 20K   | **30K** |
| ops      | 2 | 10K | 15K | 12.5K | **19K** |
| review   | 2 | 12K | 18K | 15K   | **23K** |
| analysis | 0 |  — |  — |   —   | 待累積（維持 20K） |

---

## 三、校準係數（vs COST_POLICY 原預估）

`calibration_factor = actual_avg / initial_estimate`

| skill_type | 原預估 | 實測平均 | 校準係數 | 偏差百分比 |
|-----------|------:|--------:|--------:|----------:|
| research | 15K | 21.5K | **1.43** | +43% |
| writing  | 10K | 20K   | **2.00** | +100% |
| ops      | 8K  | 12.5K | **1.56** | +56% |
| review   | 12K | 15K   | **1.25** | +25% |
| analysis | 12K | —     | 待累積    | — |

**觀察**：
- 所有類型皆**超估**（實測 > 預估），無低估情況
- writing 偏差最大（+100%），可能因輸出長度浮動大
- review 偏差最小（+25%），相對準確
- analysis 樣本為 0，暫維持現狀

---

## 四、與 retro-2026-04-15 的一致性檢查

| 維度 | retro 記錄 | 本表 | 一致？ |
|------|-----------|------|:-----:|
| research 平均 | ~21.5K | 21.5K | ✅ |
| writing 平均 | ~20K | 20K | ✅ |
| ops 平均 | ~12.5K | 12.5K | ✅ |
| review 平均 | ~15K | 15K | ✅ |
| research 建議上限 | 32K | 32K | ✅ |
| writing 建議上限 | 30K | 30K | ✅ |
| ops 建議上限 | 19K | 19K | ✅ |
| review 建議上限 | 23K | 23K | ✅ |

**結論**：數字與 retro 完全一致，可安全用於 B2 校準係數章節。

---

## 五、建議使用方式（Stage 3 / B2 參考）

1. **建立 Task Card 時**：依該 skill_type 的 `calibration_factor`，將原預估乘上該係數作為警戒上限
2. **下次 retro 觸發條件**：再累積 5 筆任務後（含至少 1 筆 analysis 任務）
3. **校準更新**：下次 retro 重算平均與係數，覆寫本表，晉升版本號（v2）

---

## 六、已知限制

- **樣本小**：多數 skill_type 僅 1-2 筆，統計意義有限
- **token 估算粗糙**：AUDIT_LOG 的 `estimated_tokens` 為事後粗估，非實際計量
- **無 analysis 樣本**：校準係數缺一項，無法全面
- **不含長時間影響**：若工具升級、模型切換（Sonnet → Opus），係數需重估

---

*建檔時間：2026-04-17*
*Task Card：20260417-O01*
*資料依據：logs/AUDIT_LOG.md*
