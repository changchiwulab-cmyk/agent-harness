# Context Engineering — 情境工程（M3）

> 把 Context Manager 從「token **預算**」升級為「情境**工程**」。
> 對齊 Anthropic *Effective context engineering for AI agents*：
> 重點不是「prompt 怎麼寫」，而是「**context 怎麼配置**才最可能產生期望行為」。

## 既有（保留）：context 預算

- `CLAUDE.md` + `GLOBAL_RULES.md` ≤ 3,000 tokens；單一 skill ≤ 1,500 tokens（CI: `check_context_budget.rb`）。
- 只載入 Task Card 白名單工具；大型檔案用路徑引用不全貼。

預算是「不要爆」；情境工程是「**配置得當**」。以下補後者。

## 1. Compaction 協定（壓縮）

- 觸發：長對話（CLAUDE.md 既定「20 輪摘要」）或原生自動壓縮。
- **要求**：壓縮不是黑箱。壓縮當下把關鍵狀態寫成可稽核的 **handoff note**
  （目標、已完成、未完成、下一步、關鍵決策），路徑記到 EXECUTION_LOG 的 `context_snapshot.note_path`。
- 連結失敗模式：直接緩解 `COORD-01`（context 被重置）、`SPEC-03`（對話歷史遺失）。

## 2. 結構化筆記（context 外記憶，filesystem-as-memory）

- 把「需要跨壓縮存活」的狀態寫到**檔案**而非只留在 context window
  （`memory/active_projects/<p>/notes/`、checkpoint commit、handoff note）。
- 對齊 Letta benchmark「filesystem 即具競爭力的記憶」。長期晉升走 `MEMORY_ARCHITECTURE.md` 的人工 gate
  （**session 內筆記 ≠ 自動長期記憶**，不違反 deny 規則）。

## 3. JIT 檢索（just-in-time retrieval）

- 預設**按需讀取**：先讀目錄/標題/摘要，需要時才讀全文；大型檔案以路徑 + 摘要引用。
- 把 GLOBAL_RULES 既有「能用檔案讀取就不 web search」「長文件摘要引用」整併為**檢索紀律**：
  寬探索（fan-out）優先交給唯讀子代理（見 `SUBAGENT_POLICY.md`），只回傳精煉摘要，省母代理 context。

## 4. Context-awareness（容量自覺）

- 工具呼叫累計 5 次 / 外部查詢 3 輪 → 既有 checkpoint 規則，本質就是容量自檢點。
- 進入長任務前，先估 context 佔用；逼近預算時主動 compaction + 寫 note，而非被動截斷。

## enforcement 點（符合 J5）

- `check_context_budget.rb`：boot prompt token 硬上限（既有）。
- `EXECUTION_LOG_SCHEMA.yaml` `context_snapshot`：長任務（checkpoints ≥ 3）記錄 compaction 與 note 路徑，供溯源。
- 失敗映射：COORD-01 / SPEC-03 的 mitigation 在此落地。

## 後續（另開卡）

- handoff note 範本化 + `logs/runs` schema lint 檢查長任務是否填了 `context_snapshot`。
