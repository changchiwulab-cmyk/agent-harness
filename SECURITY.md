# Security Policy

## 適用版本

本專案為個人 Agent 治理框架，只維護 `main` 分支上的當前版本。

| 版本 | 支援 |
| ---- | ---- |
| v2（`main`） | ✅ |
| v2 之前 | ❌ |

## 回報安全議題

本專案不對外提供服務，攻擊面主要是「agent 在本機的行為邊界」。若發現以下類型的問題，請開 GitHub issue 並加上 `security` 標籤：

- `scripts/permissions_guard.py`（PreToolUse hook）的繞過方式
- `system/PERMISSIONS.yaml` 宣告與 runtime 行為不一致
- CI 驗證（`.github/workflows/spec-consistency.yml`）可被繞過的路徑
- 任何會導致秘密資訊進入 git 歷史的缺口

**回報時請勿在 issue 內貼上任何真實憑證、金鑰或個資。**

## 秘密與資料處理

- 秘密檔案由 `.gitignore` 排除（`*.env`、`*.key`、`*.pem`、`*.credentials`）。
- Agent 權限規則見 `system/PERMISSIONS.yaml`；runtime 執行層見 `scripts/permissions_guard.py`。
- 敏感路徑（`~/.ssh`、`/etc` 等）的存取邊界宣告於 `system/AGENT_CONTEXT.yaml`。

## 已知缺口（誠實揭露）

- Hook 只覆蓋 `Bash` 工具；`Edit`/`Write` 尚無 runtime 防護（改善計畫 P1 追蹤中）。
- `permissions_guard.py` 的 deny 規則為 hardcode，未涵蓋 `PERMISSIONS.yaml` 全部 deny 項。
- CI 尚無 secret scanning（改善計畫 P2 追蹤中）。
