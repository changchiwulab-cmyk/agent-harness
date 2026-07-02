# 20260702-R01 摘要：guard / permissions 對齊（發現 #2 #3 #4 #5）

## 改了什麼

- **#2** `system/PERMISSIONS.yaml` shell_delete 敘述放寬為「rm -r/-f、rmdir、shred、find -delete 等高破壞性刪除（單檔 rm 由模型層自律）」，與 guard 實際攔截範圍一致（方向由使用者 2026-07-02 定案）。
- **#3** deny 清單雙向同步：
  - PERMISSIONS.yaml 補 `git_force_push`（原本只存在於 guard）。
  - guard 補 3 條 runtime 規則：`spawn_background_process`（nohup/setsid/disown/行尾 `&`，`&&` 不誤擋）、`auto_write_memory`（redirect/tee/cp/mv 寫入 memory/）、`publish_content`（curl 到 twitter/x/facebook/linkedin/medium/wp-json 發布 API）。
  - `modify_production_data` 無可靠 shell 簽名 → 新增 `deny_enforcement:` 區段標注每項 runtime|model，唯一 model 級即此項。
- **#4** guard docstring 改誠實描述：規則為手工對映，由 `test_permissions_guard.py` 的三方同步測試（deny ↔ deny_enforcement ↔ DENY_RULES）在 CI 交叉驗證；`PERMISSIONS_PATH` 由死變數轉為 sync 測試實際使用。
- **#5** `.claude/settings.json` 補 `permissions.ask`：Edit/Write 於 system/、skills/、CLAUDE.md、memory/、outputs/reports/ 需人工確認，鏡射 PERMISSIONS.yaml ask 清單。

## 驗證

- `python3 scripts/test_permissions_guard.py`：22 測試全綠（含 8 個新行為測試 + 4 個 sync 測試）。
- 10 個 stdin smoke case 全部符合規格（nohup/行尾 &/tee memory/redirect memory/publish API/force-push → block；單檔 rm/&&/讀 memory → allow）。
- 執行途中 guard hook 實際攔下一次含 `tee memory/` 字樣的指令 — runtime 生效的直接證據。

## Checkpoints

- 91277ad（guard + PERMISSIONS + 測試）
- 9055c77（settings.json，刻意延後至所有 system/skills/CLAUDE.md 編輯完成後）
