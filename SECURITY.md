# Security Policy

本專案為「一人公司 Agent Harness」執行框架。安全模型不以「修補漏洞」為主軸，而是**控制 agent 的執行權限與外部副作用**。請依下列政策回報問題。

## 三條硬規則（節錄自 CLAUDE.md）

1. **沒有 Task Card，不執行任何任務。** 需求必須先轉成 `tasks/*.yaml`，確認 goal + definition_of_done 後才執行。
2. **對外動作只產出草稿。** Email、發文、資料更新一律先到 `outputs/drafts/`，等人工確認。
3. **連續失敗 3 次就停下來。** 寫入 `logs/errors/` 並通知使用者，不要自己硬修。

完整啟動規則見根目錄 [`CLAUDE.md`](./CLAUDE.md)。

## 權限模型

所有動作分三層：`allow` / `ask` / `deny`，明細見 [`system/PERMISSIONS.yaml`](./system/PERMISSIONS.yaml)。重點：

- **絕不允許**：刪除檔案、自動發送 email / 訊息、發布內容、修改正式資料、金流操作、自動寫入長期記憶、啟動背景程序
- **需人工確認**：修改 `system/`、`skills/`、`memory/` 長期知識、寫入 `outputs/reports/`
- **直接允許**：讀檔、web search、寫 `outputs/drafts/`、寫 `logs/`、git checkpoint

風險等級對應審批方式見 [`system/APPROVAL_POLICY.yaml`](./system/APPROVAL_POLICY.yaml)。

## 回報方式

請依問題性質選擇：

| 問題類型 | 回報窗口 |
|---------|---------|
| 規則衝突或 agent 越界（觀察到 deny 動作被執行） | 開 GitHub Issue，標籤 `policy-violation` |
| Schema / Task Card / 驗證腳本錯誤 | 開 GitHub Issue，標籤 `validator` |
| 框架設計層的安全建議 | Pull Request 對 `system/` 檔案 + Decision Log 提案 |
| 機敏內容外洩疑慮（含 token、credentials 出現在 logs/ 或 outputs/） | **私下** 透過 repo owner 直接聯絡，勿在 Issue 公開 |

## 回應節奏

- 一般 Issue：依使用者實際工作節奏回覆，無 SLA
- 敏感回報（最後一列）：收到後 7 天內初步回覆

## 已知限制

- 本框架不提供加密、認證或網路層防護
- 機敏資料保護依賴 `.gitignore` 與 `outputs/drafts/` 工作流；請勿將 secrets 放入 `tasks/` 或 `memory/`
- Web search 與外部工具呼叫仍受底層 LLM 平台政策約束

---

*更新日期：2026-04-27（Task Card 20260427-A01）*
