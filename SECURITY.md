# 安全政策 Security Policy

本專案是一人公司的 Agent 執行框架（prompt-as-code）。安全模型以「最小權限 ＋ 人工把關」為核心，實作於 `system/PERMISSIONS.yaml` 與執行期 hook。

## 安全模型

- **deny 清單（執行期強制）**：刪除、對外發送（email／訊息／發文）、發布內容、修改正式資料、金流、自動寫長期記憶、背景程序。由 `scripts/permissions_guard.py`（`.claude/settings.json` 的 PreToolUse hook）在每次 Bash 呼叫前以 regex 攔截，違反即 `exit 2` 阻擋。
- **ask 清單（需人工批准）**：修改 `system/`、`skills/`、`memory/`、寫正式報告、改 `CLAUDE.md`、安裝套件。批准紀錄寫入 `logs/approvals/`。
- **draft-first**：所有對外動作只產出草稿到 `outputs/drafts/`，等人工確認，不直接發布。
- **風險分級**：low／medium／high／critical → 對應 `auto_execute` 與 `approval_type`（見 `system/PERMISSIONS.yaml`）。
- **失敗熔斷**：連續失敗 3 次即停止並寫 `logs/errors/`（見 `system/FAILURE_TAXONOMY.yaml` SEC-03）。

## 威脅模型與防護邊界（20260710-003）

本節明文回答外部安全審視最常問的問題：**「這套 deny-list 擋得住什麼、擋不住什麼」**。核心結論：regex deny-list 是**事故預防**（防呆），不是**安全隔離**（防惡意）。

### 防線分層（由外而內）

| 層 | 機制 | 性質 | 失效模式 |
|---|---|---|---|
| 0 | 容器／VM／OS 層 sandbox | 真正隔離 — **不在本 repo 內**，屬部署決策 | 未部署則此層不存在 |
| 1 | `.claude/settings.json` permissions ask 規則 | 人工把關（system/、skills/、memory/、reports/ 的寫入） | 依賴 runtime 實作 |
| 2 | PreToolUse hooks（deterministic chokepoint） | `task_card_guard.py`：新正式報告需 active task 精確授權，輸入層 **fail-closed**（壞 stdin／例外 → block） | matcher 外的工具不經過 |
| 3 | `permissions_guard.py` regex deny-list | 輔助防線：攔明顯違規簽章（刪除／外發／金流／force-push），**fail-open** | 見下方「已知可繞過」 |
| 4 | Prompt 自律（CLAUDE.md／GLOBAL_RULES） | 最弱層，僅引導 | 模型不遵循即失效 |

### 已知且接受的繞過面（deny-list 的邊界）

以下路徑**可以**繞過第 3 層，屬已知、明文接受的邊界 — 防禦它們的正確位置是第 0 層 sandbox，不是更多 regex：

- 經直譯器間接呼叫：`python3 -c`、`node -e` 內發 HTTP
- shell 變數、alias、base64 等編碼／間接執行
- 未列入簽章的 API domain
- 透過 repo 內既有程式完成被禁止的行為

**不做** interpreter one-liner 的 regex 攔截：false positive 率不可控，違反「誤傷比漏抓更糟」原則（`permissions_guard.py` 檔內明文）。

### fail-open / fail-closed 的取捨（20260710-003 核定）

- **fail-closed**：`task_card_guard.py` 的輸入層（空 stdin／壞 JSON／未捕捉例外 → exit 2）。理由：matcher 只掛寫入類工具，正常 runtime 必送 JSON payload，收不到代表有看不見路徑的寫入呼叫；誤傷面有界。
- **fail-open**：`permissions_guard.py` 與 `failure_counter.py` 的輸入層。理由：Bash 是 99% 低風險路徑，為輔助防線 brick 整個 shell 得不償失。此行為由 `test_permissions_guard.py` 的測試明文鎖定，改動視為安全變更。
- **條件 fail-closed**：`gate_check.py`／`verification_loop.py` 對「risk≥high 且 status∈{done,review,failed} 且 date≥2026-07-10」的卡，缺 `logs/runs/` 執行紀錄直接 FAIL — 最需要稽核的資料缺失不再靜默通過（不追溯歷史卡）。

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
