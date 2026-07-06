# Claudian（yishentu/claudian）— 參考條目

- 更新日期：2026-07-06（同日依 PR #127 review 查證修正安全層描述）
- 完整分析：`outputs/drafts/20260706-R01_claudian-analysis.md`（Task 20260706-R01）
- 寫入核准：`logs/approvals/2026-07-06_20260706-R01_approval.yaml`

## 定位

Obsidian 桌面外掛，把 AI coding agent（Claude Code、Codex、Opencode、Pi）嵌進筆記 vault——vault 即 agent 工作目錄，讀寫 / 搜尋 / bash / 多步驟工作流開箱即用。與 agent-harness 是**同領域不同層**：它解「互動介面與多 provider 接入」，本專案解「治理與可控性」，互補非競品。

## 核心事實

| 項目 | 內容 |
|------|------|
| 技術 | TypeScript（~97%）、esbuild、Jest、Bun；Obsidian v1.7.2+，僅桌面 |
| 架構 | `src/providers/` 每個 agent 一個 adapter；`features/`（chat sidebar、inline-edit、settings）與 `core/` 分離 |
| 生態 | ~13.7k stars、MIT、v2.0.27（2026-06-29）、每週多次發版（2026-07 快照） |
| 依賴 | 需本機安裝各 agent CLI（如 Claude Code CLI + 訂閱/API） |
| 隱私 | 明列送 API 資料範圍；無 telemetry |

## 主要功能

Inline Edit（word-level diff 預覽）、Slash Commands & Skills（user / vault 雙層 scope）、`@mention` 引用檔案與 MCP、Plan Mode（Shift+Tab）、Instruction Mode（`#`）、多分頁對話（fork / resume / compact）。

## 對本專案可借鑑（詳見完整分析的評估表）

1. **Skill 雙層 scope**：global vs project 兩層 skill 組織 🔍 待評估
2. **Provider adapter 分層**：未來多模型時的低耦合接法 🔍 待評估
3. **對話 compact 一級功能化**：把「20 輪摘要壓縮」從規則變成可主動觸發的操作 🔍 待評估
4. **`@mention` 顯式引用**：可標準化 Task Card `input_data` 的引用語法 🔍 待評估
5. **資料流透明揭露**：SECURITY.md 可比照明列 agent 對外送出什麼 🔍 待評估

## 風險與限制

- 治理採**操作級執行時審批**：原始碼有 `core/security/ApprovalManager.ts`（已查證；bash 路徑驗證與命令黑名單為 review 指出 [待驗證]），README 未著墨。與本專案差異在治理層次：它是操作級即時審批（近似本專案 ask 層級的程式化實作），本專案是任務級流程治理（Task Card / DoD / 稽核）——差異化定位仍成立，但不可稱其「無治理」
- 僅桌面、依賴外部 CLI；發版節奏顯示核心貢獻者少，有 bus factor 風險（推論）
- 高 star 數不等於安全審計，引入前需獨立評估

## 來源

GitHub 專案頁 / raw README / releases 頁（2026-07-06 擷取，完整連結見分析草稿）
