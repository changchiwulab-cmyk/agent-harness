# Recovery Runbook — 災難恢復程序（R8）

## 目的

當發生 **context 被重置 / session 中斷 / 任務中途崩潰 / 工作樹被破壞** 時，如何用 git checkpoint
＋執行紀錄把系統還原到「一致狀態」（consistent state）。

對應失敗模式（`system/FAILURE_TAXONOMY.yaml`）：
- **COORD-01**：Context 被重置 → 用 git checkpoint 重建
- **SPEC-03**：對話歷史遺失 → 從 Task Card + run log 重建任務狀態

本 runbook 是 `system/GATE_POLICY.yaml` 各層 `rollback` 定義的**操作companion**：gate 定義「失敗後要回到什麼狀態」，本文件定義「用什麼指令做到」。

## 恢復資料來源（依可信度排序）

| 來源 | 提供什麼 | 指令 |
|------|---------|------|
| git checkpoint commits | 最後一致的檔案狀態 | `git log --oneline --grep="checkpoint: <task_id>"` |
| Task Card（`tasks/`） | goal / definition_of_done / checkpoints 欄位（commit hash） | 直接讀檔 |
| `logs/runs/<RUN>.yaml` | 該任務的執行狀態、gate_results、最後階段 | 直接讀檔（若有寫） |
| `logs/approvals/*.yaml` | 待處理 / 已核准的批准（避免重複請求） | 直接讀檔 |
| `logs/AUDIT_LOG.md` | 任務最終狀態與產出路徑 | 直接讀檔 |
| `logs/.session_state.md` | PreCompact 壓縮前快照：未結 Task Card goal/DoD ＋最後 checkpoint | 直接讀檔（gitignored、可能過時，與 Task Card 交叉確認） |

## 場景與程序

### 場景 A — 工作樹被破壞（未 commit）｜最常見
任務中途把檔案改壞、但尚未 checkpoint。還原到最後一次 checkpoint（HEAD）：
```bash
git status --short                 # 確認哪些檔被動到
git checkout -- <file>             # 單檔還原
git checkout -- .                  # 全部未 commit 變更還原（謹慎）
```
→ **已於 2026-05-29 實測（見附錄）：單檔還原 ~5ms、byte-identical。**

### 場景 B — 需要某 checkpoint 的舊版本
```bash
git log --oneline --grep="checkpoint: <task_id>"   # 找該任務的 checkpoint
git checkout <commit> -- <file>                    # 取該版本到工作樹
```

### 場景 C — Context / session 在任務中途重置
1. 找最後 checkpoint：`git log --oneline --grep="checkpoint: <task_id>"`
2. 讀 Task Card：確認 goal / definition_of_done / 已完成到第幾個 checkpoint
3. 讀 `logs/runs/<RUN>.yaml`（若有）：確認 gate_results 與最後階段
4. 讀 `logs/approvals/`：確認是否有待處理批准（避免重複請求人工）
5. 從「最後 checkpoint 之後、尚未完成的子任務」**接續**執行——不要從頭重做。

### 場景 D — 整批變更要回滾（已 commit、未 push 或可重置）
```bash
git checkout <checkpoint>          # detached，檢視
git reset --hard <checkpoint>      # ⚠️ 丟棄其後所有變更，確認後再用
```
> `reset --hard` 屬高風險；deny 清單禁止 `rm` 類刪除，但 `git reset --hard` 由人工確認後才執行。

## 還原後一致性檢查（必跑）

```bash
git status --short                                   # 應乾淨（或僅剩預期變更）
ruby scripts/check_spec_consistency.rb               # schema / logs lint 通過
python3 scripts/generate_frontend_manifest.py --check  # data.json 無漂移
```
三者皆綠 = 回到一致狀態。

## 與 GATE_POLICY rollback 的對應

| Gate 失敗 | GATE_POLICY rollback | 對應本 runbook |
|-----------|---------------------|---------------|
| schema_check | 不產檔、Task Card 標 blocked | 場景 A（丟棄未 commit 產出） |
| rule_check | 撤銷未 checkpoint 變更（git checkout） | **場景 A** |
| completion_check | 產出標 partial、存 drafts/ | 場景 A + 保留 drafts |
| risk_check | 產出鎖 drafts/、Audit 標 risk_escalated | 不需檔案還原，只移動產出 |

---

## 附錄：首次恢復演練紀錄（2026-05-29，Task Card 20260529-010）

| 項目 | 值 |
|------|----|
| 演練場景 | A — 工作樹未 commit 破壞 → 從 checkpoint 還原 |
| checkpoint (HEAD) | `5e54eec` |
| 目標檔 | `outputs/drafts/2026-05-29_governance-data-analysis.md` |
| 指令 | `git checkout -- <file>` |
| 還原耗時 | **~5ms** |
| 驗證 | sha1 還原前後 **byte-identical**；`git status` 還原後**乾淨** |
| 結論 | 場景 A 恢復路徑**實測可用**；checkpoint 機制不再只是紙上設計 |

> 後續：場景 C（context 重置接續）建議在下次真實多階段任務中途實測一次，補齊「接續執行」的實證。
