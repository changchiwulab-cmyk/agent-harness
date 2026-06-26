# 上下文工程政策 CONTEXT_POLICY（v2.1 治理層硬化）

## 為什麼

context engineering 是 2026 業界公認 agent 可靠度的首要槓桿（Anthropic：刻意設計每次推論
所見的內容，讓任務更快、錯誤更少）。本框架原有的 context 規則散落在 CLAUDE.md（token 上限、
20 輪壓縮）、`COST_POLICY.md`（量化基準）與子代理隔離數字。本檔把它們**收斂成單一政策**，
並收斂 native-memory 決策（D008）。

## 1. Context 預算配置（單次推論該看到什麼）

四個來源，由重到輕刻意控制：

| 來源 | 規則 | 守門 |
|------|------|------|
| 系統指令 | CLAUDE.md + GLOBAL_RULES ≤ 3K（硬限制） | `scripts/check_context_budget.rb`（CI） |
| 工具定義 | 只載入 Task Card `allowed_tools` 白名單；按需 Tool Search（省 ~85%） | `COST_POLICY.md` 量化基準 |
| 範例 | skill `eval_examples.md` 取 2–3 個 canonical（few-shot，不全貼） | — |
| 訊息歷史 | 當前任務相關；超 20 輪壓縮 | 見 §2 |

單一 skill prompt ≤ 1.5K（硬限制）。

## 2. 壓縮（compaction）

長對話接近上限 → 摘要關鍵決策後開新 context；**必須保留**：Task Card goal/DoD、
checkpoint commit、pending approval。對應 `FAILURE_TAXONOMY` 的 SPEC-03 / COORD-01。

## 3. Just-in-time 取用（不要預載）

- 大型檔案用路徑引用，需要時才讀（不全文貼入 context）。
- `memory/` 與既有 `outputs/` 先查再 web search（成本意識，見 GLOBAL_RULES）。
- 工具用 Tool Search 按需載入，不一次塞滿工具定義。

## 4. 子代理 context 隔離

- 大型 fan-out 探索（掃多檔/多目錄）下放子代理，只回傳結論，省 ~67% context。
- 子代理屬唯讀探索：不改檔、不對外（對齊 `AGENT_CONTEXT.yaml` / `PERMISSIONS.yaml`）。

## 5. 記憶架構（native-memory 決策，見 D008）

- **短期**：當前 session，自動管理。
- **長期**：只有經人工確認才寫 `memory/`（沿用 GLOBAL_RULES；`PERMISSIONS` deny `auto_write_memory`）。
- **混合策略**：
  - 採用 Claude Code 原生 session 壓縮（已是 first-class，不自建）。
  - **不採用**原生「跨 session 自動記憶」——與「長期記憶需人工確認」硬規則衝突。
  - `memory/active_projects/` 結構保留為事實來源（人工策展 + Decision Log）。
  - 轉向觸發：若原生記憶提供「人工確認後才持久化」的 gate，再評估（D008 revisit_trigger）。

## 6. 落地對應

`check_context_budget.rb`（3K 硬限制）｜`ROUTING_RULES` / `INTAKE_FLOW`（任務拆分降 context）｜
`COST_POLICY.md`（量化基準）｜`AGENT_CONTEXT.yaml`（子代理邊界）｜`MODEL_POLICY.md`（分層選模）。
