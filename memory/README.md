# Memory 使用規則

## 結構

```
memory/
  user_prefs.md          ← 指標檔，實際偏好存於 ~/.claude/memory/
  active_projects/       ← 進行中專案的持久 context
    [project_name]/
      context.md         ← 該專案的背景、目標、限制
      decisions/         ← 該專案的結構化決策紀錄（用 tasks/DECISION_LOG_TEMPLATE.yaml 格式）
      references/        ← 該專案的參考資料
```

> **Decision Log 說明**：重要決策不再用自由格式 decisions.md，改用結構化 YAML。
> 每筆決策一個檔案，格式見 `tasks/DECISION_LOG_TEMPLATE.yaml`。
> 檔名格式：`YYYYMMDD-D###_決策簡述.yaml`。寫入前需人工確認。

## Memory 邊界（與外部系統）

| 存放位置 | 存放內容 |
|---------|----------|
| `~/.claude/memory/` | 使用者偏好、跨專案通用框架（Claude Code 全域） |
| `~/ai-os/` | 跨工具狀態層（ChatGPT ↔ Claude Code 交班、AI OS 級決策） |
| `agent-harness/memory/` | **僅限** agent-harness 任務執行 context（active_projects/） |

**決策記錄分層：**
- 跨工具 / AI OS 策略決策 → `~/ai-os/decision_log.md`（DEC-XXX 格式）
- agent-harness 任務內決策 → `memory/active_projects/[project]/decisions/`

## 兩層記憶規則

### 短期記憶（自動）
- 當前 session 的對話歷史
- 由 Claude Code 自動管理
- Session 結束後不自動保留
- 需要保留的內容 → 明確寫入檔案

### 長期記憶（需人工確認）
- SOP、模板、已驗證知識、客戶背景
- 存放在 memory/ 下
- **寫入前必須經人工確認**
- 不自動把對話內容寫入長期記憶
- 定期審查（建議每月一次），清除過時內容

## 寫入流程

1. Agent 識別出值得長期保存的資訊
2. 整理成結構化格式
3. 提議寫入位置與內容
4. **等待人工確認**
5. 確認後才寫入

## 禁止事項

- 不自動把每次對話都存入 memory
- 不把暫時的推論當永久事實儲存
- 不儲存敏感個資（密碼、金鑰、身分證號）
- 不在 memory 中儲存大量原始資料（用路徑引用）
