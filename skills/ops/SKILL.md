# Ops Skill

## 用途
營運支援、表格整理、資料清洗、排程規劃、流程文件化、檔案組織。

## 執行流程
1. 確認操作目標與範圍（從 Task Card 取得）
2. 盤點現有資料與檔案狀態
3. 制定操作計畫（先輸出計畫，不直接執行）
4. 確認計畫後逐步執行
5. 每個修改步驟都 checkpoint
6. 輸出結果 + 變更摘要

## 操作原則
- 修改前先備份（git commit）
- 批量操作前先在小範圍測試
- 檔案操作只在 project 目錄內執行
- 不刪除任何檔案（deny 規則）
- 結構化輸出優先（YAML、CSV、JSON）

## 輸出格式
依任務性質：
- 表格整理 → CSV / YAML
- 排程規劃 → Markdown 表格
- 流程文件 → Markdown SOP
- 檔案組織 → 變更清單 + 新結構說明

## 品質標準
- 資料完整性不能損失
- 格式轉換後可逆驗證
- 變更有完整紀錄
- 輸出可被後續任務直接使用

## 常見失敗模式
- 直接執行修改而不先說明計畫 → 必須先輸出操作計畫
- 批量操作沒有 checkpoint → 每 N 步存一次
- 靜默丟失資料（格式轉換時欄位遺漏）→ 轉換後比對欄位數
- 誤解資料結構（CSV 欄位含逗號）→ 先確認 delimiter 與 encoding

## 特定程序：月度治理指標健檢

每月人工觸發（非自動排程），步驟如下：

**1. 執行採集腳本**
```bash
python3 scripts/governance_metrics.py
```
輸出至 `outputs/drafts/governance-metrics-[YYYY-MM].md`。

**2. 解讀 4 條 KPI（依 system/NATIVE_OVERLAP.yaml 閾值判定）**
| 指標 | warn 閾值 | alert 閾值 |
|------|----------|-----------|
| M1：月新增 Task Card 數 | < 3 | < 1 |
| M2：drafts:reports 比 | > 15 | > 25 |
| M3：audit 覆蓋率 | < 80% | < 60% |
| M4：原生重疊度（每季 review） | > 40% | > 60% |

**3. 決定後續行動**
- 全綠：無需動作，在 notes 記錄「月度健檢通過」
- warn：在 retro 草稿中標記，下次 retro 重點追蹤
- alert：立即開一張 Task Card 調查根因，不等 retro

**4. 更新 M4 原生重疊度**（僅每季一次）
手動更新 `system/NATIVE_OVERLAP.yaml` 後重跑腳本。
