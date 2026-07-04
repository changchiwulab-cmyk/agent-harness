# MODEL_ROSTER — 現役模型名冊與調度語法

> 用途：`DISPATCH_POLICY.md` 與 `DELEGATION_TEMPLATES.md` 引用的**唯一**型號事實來源。
> 模型世代更迭時**只改這一檔**（更新程序見文末），守則本身不用動。
> 最後查證：2026-07-04，對照 code.claude.com/docs（sub-agents、model-config 兩頁），非憑記憶。

## 現役別名與定位

| 別名（model 參數值） | 目前指向 | 定位 | 調度上的用法 |
|---------------------|---------|------|--------------|
| `haiku` | Haiku 4.5 | 最便宜最快 | 批次套用已解出的模式、格式轉換、簡單抽取 |
| `sonnet` | Sonnet 5 | 中堅 | 預設 subagent 工作馬：搜尋、實作、研究、驗收 |
| `opus` | Opus 4.8 | 最強常備 | 指揮官（主對話預設）；高難度子任務的升級目標 |
| `fable` | Fable 5 | Mythos 級，通常不可用 | 不要在守則裡依賴它；可用時見 HANDOFF_FABLE5 的待強模型清單 |
| `inherit` | 跟隨主對話 | — | 不指定時的預設；**守則要求顯式指定，不要用 inherit** |

其他合法值：完整 model ID（如 `claude-opus-4-8`、`claude-sonnet-5`）、`sonnet[1m]` /
`opus[1m]`（1M context，超大量讀取時用）、`best`（有 fable 用 fable，否則最新 opus）。

## effort（推理力度）

合法值：`low` / `medium` / `high` / `xhigh` / `max`。

- 設定位置：`.claude/agents/*.md` frontmatter 的 `effort:` 欄（覆蓋 session effort）。
- Agent tool **每次呼叫沒有 effort 參數**（只有 model 可以逐次覆寫）；要固定 effort
  就寫成 `.claude/agents/` 定義檔。
- 沒有 per-subagent 的 extended thinking 開關；subagent 繼承主對話的 thinking 設定。

## 調度語法（三個位置）

1. **Agent tool 逐次覆寫**：呼叫時帶 `model: "haiku" | "sonnet" | "opus"`。
   解析順序：env `CLAUDE_CODE_SUBAGENT_MODEL` ＞ 呼叫參數 ＞ agent 定義檔 frontmatter ＞ 主對話模型。
2. **Agent 定義檔**：`.claude/agents/名字.md`，frontmatter 支援
   `name` / `description`（必填）與 `tools` / `disallowedTools` / `model` / `effort` /
   `maxTurns` / `skills` / `memory` / `isolation` 等（完整清單見官方 sub-agents 文件）。
   放在 repo 內的 `.claude/agents/` 雲端 session 也吃；`~/.claude/agents/` 雲端**不吃**。
3. **Session 預設模型**：`.claude/settings.json` 的 `"model"` 鍵（本 repo 已釘 `"opus"`）。

## 本 session 環境可用的內建 subagent_type

`Explore`（唯讀搜索，回結論不回原文）、`Plan`（架構規劃）、`general-purpose`（全工具）、
`claude`（泛用）、`claude-code-guide`（查 Claude Code/API 官方文件）。
自訂：`verifier`（本 repo `.claude/agents/verifier.md`，fresh-context 驗收員）。

> 注意：內建清單可能隨平台版本變動。開新 session 時以系統提示裡實際列出的
> agent types 為準；發現與本表不符→依 MAINTENANCE_PROTOCOL 更新本檔。

## 更新程序（型號換代時）

1. 派 `claude-code-guide` agent 查 code.claude.com/docs 的 model-config 與 sub-agents 兩頁，
   拿到現行別名對應與 frontmatter 欄位清單（**不要憑訓練記憶寫**）。
2. 只改本檔的表格與「目前指向」欄；`DISPATCH_POLICY.md` 用別名寫成的規則不用動。
3. 若別名語意變了（例如 sonnet 能力大幅躍升），在 `memory/lessons.md` 記一筆，
   並依 `MAINTENANCE_PROTOCOL.md` 評估是否調整 DISPATCH_POLICY 的升降級門檻（屬「先問使用者」級）。
4. 檔頭「最後查證」日期更新。建議每季 retro 時順手複查（併入 RETRO_FLOW 的分析維度）。
