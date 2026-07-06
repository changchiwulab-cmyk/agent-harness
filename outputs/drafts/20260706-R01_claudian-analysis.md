# Claudian 專案分析（yishentu/claudian）

- Task ID：20260706-R01
- 日期：2026-07-06
- Skill：research
- 投入：5 web queries（3 輪，含 review 查證 2 次）/ ~1700 字
- 狀態：草稿
- 修訂：2026-07-06 依 PR #127 Codex review 查證，修正「無細粒度治理」過強結論（見高風險假設）

## 結論

Claudian 是一個 **Obsidian 桌面外掛，把 AI coding agent（Claude Code、Codex、Opencode、Pi）直接嵌進筆記 vault**，讓 vault 成為 agent 的工作目錄——讀寫、搜尋、bash、多步驟工作流開箱即用。它與 agent-harness 處在同一領域的**不同層**：Claudian 解「agent 的互動介面與多 provider 接入」，agent-harness 解「agent 的治理與可控性」，兩者互補而非競品。專案非常活躍（v2.0.27，每週多次發版）、社群基礎大（~13.7k stars、MIT），其 **provider adapter 分層、skill 雙層 scope、plan mode 明確狀態切換、對話 compact** 四項設計對 agent-harness 有直接借鑑價值。治理面的差異在層次：Claudian 有操作級執行時審批（`ApprovalManager`），但沒有任務級流程治理（Task Card / DoD / 稽核）——後者正是本專案的差異化所在。

## 已知事實

### 定位與核心功能

- README 自述：「An Obsidian plugin that embeds AI coding agents (Claude Code, Codex, Opencode, Pi, and more to come) in your vault.」（來源 2）
- 專案頁引言：「Your vault becomes the agent's working directory — file read/write, search, bash, and multi-step workflows all work out of the box.」（來源 1）
- 功能清單（來源 2）：
  - **Inline Edit**：選取文字或游標處 + 快捷鍵，直接在筆記內編輯，含 word-level diff 預覽
  - **Slash Commands & Skills**：輸入 `/` 或 `$` 呼叫可重用 prompt 模板 / Skills，分 user-level 與 vault-level 兩層 scope
  - **`@mention`**：輸入 `@` 引用 vault 檔案、subagent、MCP server 或外部目錄
  - **Plan Mode**：`Shift+Tab` 切換，先探索設計、後實作
  - **Instruction Mode（`#`）**：從聊天輸入補充自訂指令
  - **MCP Servers**：經 Model Context Protocol 接外部工具
  - **Multi-Tab & Conversations**：多分頁、歷史、fork、resume、compact（壓縮）

### 技術架構

- TypeScript 為主（~97%），esbuild 建置、Jest 測試、ESLint、Bun 套件管理（來源 1）
- `src/` 分層（來源 1）：`main.ts` 入口；`app/`、`core/`（runtime、providers、bootstrap）；`providers/`（Claude、Codex、Opencode、Pi 各自的 adapter）；`features/`（chat sidebar、inline-edit、settings）；`shared/`、`i18n/`、`utils/`、`style/`
- `src/core/security/` 含 `ApprovalManager.ts`——存在操作級執行時審批元件（來源 4，2026-07-06 查證）
- 需求（來源 2）：Obsidian v1.7.2+；僅桌面（macOS / Linux / Windows）；Claude provider 需本機安裝 Claude Code CLI + 訂閱或 API（或相容 provider）；Codex CLI / Opencode / Pi 為選配
- 隱私聲明（來源 2）：送往 API 的資料包含使用者輸入、附加檔案與圖片；本機僅存設定與 session metadata；「Claudian does not run telemetry beacons」

### 生態與活躍度

- ~13.7k stars、863 forks、MIT 授權、51 open issues、36 PRs（來源 1，2026-07-06 頁面快照）
- 最新版 v2.0.27（2026-06-29）；5–6 月間每週多次發版，主題涵蓋 Pi provider 整合、Codex 目錄導航、diff 渲染、建置可重現性（Node 版本鎖定）等（來源 3）
- 安裝管道：Obsidian Community Plugins、GitHub Release 手動安裝、原始碼建置（來源 2）

## 合理推論

- **Provider adapter 模式是其擴充性核心**：`src/providers/` 每個 agent 一個 adapter + README 的「and more to come」，推論其把 CLI 差異隔離在 adapter 層，新增 provider 成本低。（依據：目錄結構 + 2.0.19 一版即完成 Pi 整合）
- **它是「介面層 harness」，治理停留在操作級**：功能圍繞互動體驗（diff 預覽、多分頁、@mention），治理面有 `ApprovalManager` 執行時審批但無 Task Card / DoD / 稽核類流程機制，推論其信任模型是「操作級即時審批 + 使用者監督」，與 agent-harness 的「任務級事前定義 + 事後稽核」互補。（依據：README 功能清單無治理條目 + 來源 4 的 security 模組）
- **發版節奏顯示單人或小團隊高速迭代**：週級多版 + patch 密集，推論維護依賴少數核心貢獻者，長期維護有 bus factor 風險。（依據：來源 3 發版頻率）

## 對 agent-harness 可借鑑的設計

依 research skill 盤點狀態標記（均為推論性質的評估建議，不直接改本專案）：

| 設計 | 說明 | 對應本專案 | 狀態 |
|------|------|-----------|------|
| Skill 雙層 scope | user-level vs vault-level 兩層 prompt 模板 | `skills/` 可考慮拆 global（跨專案）與 project（隨 memory/active_projects/ 走）兩層 | 🔍 待評估 |
| Provider adapter 分層 | agent CLI 差異隔離在 `providers/` adapter | 本專案目前綁 Claude；若未來多模型，adapter 介面是低耦合作法 | 🔍 待評估 |
| 對話 compact 一級功能化 | 壓縮對話成一級操作（compact） | 對應 CLAUDE.md「20 輪後摘要壓縮」——claudian 把它從規則變成可主動觸發的功能 | 🔍 待評估 |
| Plan mode 明確狀態切換 | 探索/設計與執行是兩個可切換的顯式狀態 | 本專案已有 Task Card 前置關卡，精神一致 | ✅ 推論已用 |
| `@mention` 顯式引用 | 用語法明確宣告 agent 可觸及的檔案 | 與「大型檔案用路徑引用」原則一致，可考慮標準化為 Task Card `input_data` 的引用語法 | 🔍 待評估 |
| 資料流透明揭露 | README 明列送出資料範圍 + 無 telemetry 聲明 | 可借鑑到 SECURITY.md：明列 agent 對外送出什麼、本機存什麼 | 🔍 待評估 |

## 待驗證

- stars / forks / issues 數字來自頁面摘要快照，未逐項核對 [待驗證]
- 「word-level diff」與 inline edit 的實作品質僅為 README 宣稱，未實測 [待驗證]
- Community Plugins 上架狀態未實際在 Obsidian 內確認 [待驗證]
- 貢獻者人數與 bus factor 推論未查 contributors 頁 [待驗證]
- `ApprovalManager` 的審批預設範圍；bash 路徑驗證與命令黑名單（PR #127 review 指出，未直接讀碼確認）[待驗證]

## 高風險假設

- **「vault 即工作目錄 + bash」的風險敞口取決於審批預設值**。初版曾假設「無細粒度權限治理」，經 PR #127 review 查證修正（2026-07-06）：原始碼存在 `core/security/ApprovalManager.ts` 執行時審批層。剩餘風險點縮小為：審批的預設範圍與覆蓋度（bash 路徑驗證、命令黑名單等由 review 指出，未直接讀碼確認 [待驗證]）；若使用者放行過寬，vault 含敏感資料時敞口仍大。
- **高 star 數 ≠ 安全性**：13.7k stars 反映受歡迎程度，不構成 code 品質或安全審計證據；引入前仍需獨立評估。

## 來源

1. https://github.com/yishentu/claudian — 專案頁（2026-07-06 擷取：描述、語言比例、stars/forks/issues、目錄結構）
2. https://raw.githubusercontent.com/yishentu/claudian/main/README.md — README 原文（功能、需求、安裝、隱私、授權）
3. https://github.com/yishentu/claudian/releases — 發版紀錄（v2.0.18–v2.0.27，2026-05~06）
4. https://github.com/yishentu/claudian/tree/main/src/core/security — security 模組目錄（2026-07-06 擷取，`ApprovalManager.ts`；查證動機來自 PR #127 Codex review）
