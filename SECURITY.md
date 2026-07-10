# 安全政策 Security Policy

本專案是一人公司的 Agent 執行框架（prompt-as-code）。安全模型以「最小權限 ＋ 人工把關」為核心，實作於 `system/PERMISSIONS.yaml` 與執行期 hook。

## 安全模型

- **deny 清單（執行期強制）**：刪除、對外發送（email／訊息／發文）、發布內容、修改正式資料、金流、自動寫長期記憶、背景程序。由 `scripts/permissions_guard.py`（`.claude/settings.json` 的 PreToolUse hook）在每次 Bash 呼叫前以 regex 攔截，違反即 `exit 2` 阻擋。
- **ask 清單（需人工批准）**：修改 `system/`、`skills/`、`memory/`、寫正式報告、改 `CLAUDE.md`、安裝套件。批准紀錄寫入 `logs/approvals/`。
- **draft-first**：所有對外動作只產出草稿到 `outputs/drafts/`，等人工確認，不直接發布。
- **風險分級**：low／medium／high／critical → 對應 `auto_execute` 與 `approval_type`（見 `system/PERMISSIONS.yaml`）。
- **失敗熔斷**：連續失敗 3 次即停止並寫 `logs/errors/`（見 `system/FAILURE_TAXONOMY.yaml` SEC-03）。

## 敏感資料處理

- 敏感資料不進 context、不寫入 `outputs/`（FAILURE_TAXONOMY SEC-02）。
- 不存取本機敏感目錄（如 `~/.ssh`、`/etc`）。
- 輸出前檢查是否含憑證、金鑰、個資。

## 回報安全問題

本專案為單人維護。發現權限繞過、deny-list 漏洞或敏感資料外洩風險時：
- 開 GitHub issue（標題加 `[security]`），或私訊維護者。
- 請勿在公開 issue 貼出可被利用的繞過細節；先描述影響面，細節私下提供。

## 變更安全相關檔案

修改下列檔案視為高風險，須經 ask 批准並留 `logs/approvals/` 紀錄：
`system/PERMISSIONS.yaml`、`scripts/permissions_guard.py`、`.claude/settings.json`、`system/APPROVAL_POLICY.yaml`。
