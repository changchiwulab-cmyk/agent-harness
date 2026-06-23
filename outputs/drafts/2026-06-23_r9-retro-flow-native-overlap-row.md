# R9 草稿 — RETRO_FLOW.md「原生重疊回看」列（待人工確認）

> ✅ 已套用（2026-06-23，人工確認選項 1.2）：`system/RETRO_FLOW.md` 已加「原生重疊回看」列，
> `system/NATIVE_OVERLAP.yaml` 已加 `revisit_interval_days: 90`。本草稿保留為歷史備援。


> Task Card `20260623-001`（R9）｜skill: ops｜2026-06-23
> 本檔為 `system/RETRO_FLOW.md` 的提案 diff。改 `system/` 屬 **ask** 權限，先草稿、人工確認後才套用。

## 為什麼

R9 在 `governance_metrics.py` M4 加了：
- 季度 staleness 偵測（`reviewed_on` 逾 90 天 → warn）
- 重疊 > 50% → 明確建議產出 v3 就緒度評估（R10）

但 RETRO 節奏要「記得跑」這條檢查，才不會跟 R4 的決策回看一樣淪為「有欄位沒人看」。
R4 已在 §2 加「決策回看」一列；R9 在它正下方再加「原生重疊回看」一列，兩者同一 RETRO 節奏合流，**不另造流程**。

## 提案變更（§2 分析維度表）

在現有最後一列「決策回看」之後，新增一列：

```diff
 | 決策回看 | 有 decision 觸發 revisit 嗎？（跑 `scripts/check_decision_revisit.rb`） | 對應 Decision Log 的 status |
+| 原生重疊回看 | NATIVE_OVERLAP `reviewed_on` 過季了嗎？aggregate 跨閾值了嗎？（跑 `python3 scripts/governance_metrics.py` 看 M4） | `system/NATIVE_OVERLAP.yaml`（更新 `reviewed_on` + 逐模組 %）；>50% 觸發 R10 v3 評估 |
```

## 套用後預期

`system/RETRO_FLOW.md` §2 表格列數 6 → 7；「決策回看」「原生重疊回看」相鄰，RETRO 一次跑兩個 revisit 檢查。

## 連帶（可選）

`system/NATIVE_OVERLAP.yaml` 可加一行 `revisit_interval_days: 90` 把「每季度」量化、可覆寫；
不加則 `governance_metrics.py` 預設 90 天，行為一致。屬可選，亦為 `system/` 變更。
