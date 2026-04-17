# Retro 回饋流程

## 目的

讓系統能從執行結果中學習，而不是永遠用相同的設定。

## 觸發條件

以下任一：
- 累積完成 5 個任務
- 每週一次（週五下班前）
- 發生 2 次以上同類錯誤

## Retro 流程

### 1. 資料蒐集
讀取以下內容：
- `logs/AUDIT_LOG.md`（最近一批紀錄）
- `logs/errors/`（錯誤紀錄）
- `logs/approvals/`（核准紀錄）

### 2. 分析維度

| 維度 | 問題 | 更新對象 |
|------|------|---------|
| 成本 | 每種任務類型實際花了多少 token？ | COST_POLICY.md 任務級預算 |
| 錯誤 | 哪類錯誤最常出現？比例有變嗎？ | GLOBAL_RULES.md 失敗分類學 |
| 流程 | 哪裡卡住最久？哪個步驟多餘？ | 對應 SKILL.md |
| 權限 | 哪些 ask 每次都被 approve？ | PERMISSIONS.yaml（畢業候選） |
| 品質 | definition_of_done 夠具體嗎？ | TASK_CARD_TEMPLATE.yaml |

### 3. 輸出

產出 `outputs/drafts/retro-[日期].md`，包含：
- 數據摘要
- 發現的模式
- 具體的建議修改（指向哪個檔案的哪個段落）
- 是否觸發 v2 升級條件

### 4. 執行修改

Retro 報告產出後：
- 使用者確認哪些建議要採納
- 修改對應的系統檔案（屬於 ask 權限）
- 記錄到 audit log

### 5. 晉升至 reports/

當 retro 草稿已由人工確認、建議已採納（或明確擱置）後：
- 複製 `outputs/drafts/retro-[日期].md` → `outputs/reports/retro-[季度-序號].md`
- 正式版檔頭加「晉升標記」區塊（晉升日期、審閱者、採納項目清單）
- 原 draft 檔尾加「已晉升為 reports/...」回指，保留歷史備援
- 寫 `reports/` 屬 ask 權限，需人工確認；建立新 Task Card 執行晉升任務

## 限制

- Retro 本身是一個 review 類型的任務，需要 Task Card
- 不自動修改系統檔案，一律先到 drafts/
- 修改系統規則需要人工確認
