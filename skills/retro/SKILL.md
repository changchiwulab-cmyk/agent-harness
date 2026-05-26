---
name: retro
description: 週期性回顧 skill — 蒐集執行數據、分析五維模式、產出改善草稿、列出晉升與歸檔候補。觸發場景：累積完成 ≥5 個任務、發生 2 次以上同類錯誤，或使用者手動請求。輸出：outputs/drafts/retro-[日期].md。
---

# Retro Skill

## 用途
週期性回顧與系統調適。

核心問題：這批任務學到了什麼？哪些規則需要調整？

與 review 的差異：review 審查單一輸出的品質，retro 審查整批任務執行的**系統性模式**。

## 觸發條件
（依 system/RETRO_FLOW.md）
- 累積完成 ≥5 個任務（從 `logs/AUDIT_LOG.md` 計算，上次 retro 截止點起）
- 發生 2 次以上同類錯誤
- 使用者手動請求

## 執行流程

### 1. 資料蒐集
讀取（必讀）：
- `logs/AUDIT_LOG.md` — 期間全部紀錄
- `logs/errors/` — 錯誤紀錄
- `outputs/reports/retro-*.md` — 最近一份，作為對照基準

選讀（若有）：
- `logs/approvals/` — 核准紀錄
- `system/COST_POLICY.md` — 預算基準

### 2. 五維分析

| 維度 | 核心問題 | 建議更新對象 |
|------|---------|------------|
| 成本 | 每種任務類型實際 token 消耗？超出 COST_POLICY 預算幾次？ | COST_POLICY.md |
| 錯誤 | 哪類錯誤最頻繁？比率是否上升？ | FAILURE_TAXONOMY.yaml |
| 流程 | 哪個步驟最常卡住或被跳過？ | 對應 SKILL.md |
| 權限 | 哪些 ask 每次都被立即 approve？（畢業候選） | PERMISSIONS.yaml |
| 品質 | DoD 夠具體嗎？積壓在 drafts/ 待晉升的報告有幾份？ | TASK_CARD_TEMPLATE.yaml |

每條發現**必須附 task_id** 作為證據，不能只說「感覺上」。

### 3. 輸出草稿
產出 `outputs/drafts/retro-[YYYY-MM-DD].md`（見輸出格式）。

### 4. 停下等待
草稿完成後**不執行任何修改**，等使用者確認：
- 哪些建議採納 → 另開 Task Card
- 哪些 drafts 晉升為 reports
- 哪些專案封存
- 是否需建立新技能或自動化

## 輸出格式

```markdown
# Retro [YYYY-MM-DD]

## 數據摘要
- 涵蓋期間：
- 任務總數 / 完成 / 失敗 / 部分 / 待執行：
- 錯誤次數 + 類型分布：
- Token 消耗（與 COST_POLICY 基準對照）：

## 五維發現

### 成本
### 錯誤
### 流程
### 權限
### 品質

## 建議修改清單
（格式：[HIGH/MED/LOW] 修改內容 → 目標檔案：段落/行，依據：task_id）

## 待人工確認
- Draft → Report 晉升候補：
- 專案封存候補：
- 新技能 / 自動化建議：
```

## 品質標準
- 每條建議附 task_id（無法引用就標 [推論]）
- 修改建議具體到檔案名 + 段落
- 不自動改任何系統檔案
- token 消耗估計要與 COST_POLICY 表格對照，不能空白
