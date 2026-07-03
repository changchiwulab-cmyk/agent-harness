# 維護協議：弱模型如何安全更新 Harness 制度檔

日期：2026-07-02

## 結論

制度檔只能為三件事而改：降低重複錯誤、節省未來 token、降低風險。不能因為單次模型失誤或想把文字變漂亮就改制度。

## 可自行處理

- 新增 `outputs/drafts/` 草稿。
- 新增 `logs/runs/` 執行紀錄。
- 新增 `logs/errors/` 錯誤紀錄。
- 新增 `backups/YYYY-MM-DD/` 備份。
- 新增非正式分析檔，且不改既有制度規則。

## 修改前要問使用者，除非本輪已明確授權

- `CLAUDE.md`
- `system/PERMISSIONS.yaml`
- `system/GATE_POLICY.yaml`
- `system/COST_POLICY.md`
- `system/MODEL_ROUTING_POLICY.md`
- `system/JUDGMENT_RUBRIC.md`
- `system/MAINTENANCE_PROTOCOL.md`
- `memory/`
- `skills/`

## 禁止自行處理

- 刪除檔案。
- 對外發送或發布。
- 修改正式資料來源。
- 付款或金流動作。
- 把未驗證推論寫入長期記憶。

## 修改既有檔案流程

1. 讀取原檔。
2. 建立備份：`backups/YYYY-MM-DD/<original-path>.backup-before-<reason>.md`。
3. 說明為什麼要改。
4. 最小修改，不順手重構。
5. read-back 新檔。
6. fresh-context review。
7. 回報 changed files、backup path、verification、remaining risks。

做不到備份，就不能改既有檔案。

## 踩坑後寫回哪裡

單次錯誤寫到 `logs/errors/`。

可重複教訓寫到 `system/LESSONS_LEARNED.md`；若不存在，先建立草稿，等使用者確認後再納入正式規則。

長期偏好只在使用者明確確認後寫入 `memory/`。

## 教訓格式

```markdown
## YYYY-MM-DD — <lesson title>
Trigger:
Observed failure:
Rule to add:
Where it applies:
Positive example:
Negative example:
Review date:
```

## 何時精簡

- `CLAUDE.md` 超過 100 行。
- 任一制度檔超過 300 行。
- `system/LESSONS_LEARNED.md` 超過 30 則。
- 同一規則在 3 個以上檔案重複出現。
- 弱模型需要讀超過 3 個制度檔才能開始任務。

## Fresh-context review 必問

1. 規則有沒有互相打架？
2. 路徑、檔名、工具名有沒有錯？
3. 有沒有弱模型會誤讀的抽象語句？
4. 有沒有未驗證資訊被寫成事實？
5. 有沒有違反一人公司低維護成本原則？
