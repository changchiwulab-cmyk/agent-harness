# CLAUDE.md — Harness Runtime Alignment 建議修改（草稿）

**狀態**：待人工確認
**來源 Task Card**：`20260420-002` Phase 4
**相關決策**：D006 (sub-agent scope)、D007 (tool registry closure)
**說明**：CLAUDE.md 屬 `ask` 權限（`modify_claude_md`），本檔為建議 diff，不直接套用。
沿用 `20260420-001` Phase 3 的模式（先產草稿、經使用者確認再套用）。

---

## 盤點結果（20260420-002 的四大 HIGH + MED 項目）

1. 工具命名抽象層與 Claude Code 實際工具無對應 → 已以 `system/TOOL_MAPPING.yaml` 解決
2. Agent / TodoWrite / Skill / ToolSearch / MCP 未在 PERMISSIONS 登錄 → 已在 PERMISSIONS.yaml 擴充
3. GitHub MCP 寫入未進 APPROVAL triggers → 已在 APPROVAL_POLICY.yaml 新增 3 條 trigger
4. sub-agent 使用與 context.md 規則衝突 → 已以 D006 精準化「multi-agent swarm」定義

上述 1–4 均不需要修改 CLAUDE.md。CLAUDE.md 本體需要的調整只剩下把「新規則指向哪裡」
讓 session 啟動時讀得到，以及補上幾處 runtime 事實（auto-compaction、Plan mode、sub-agent 邊界）。

---

## 建議變更（共 4 處）

### 變更 1 — 執行流程步驟 3 拆分、載入 TOOL_MAPPING（第 22 行）

```diff
- 1. 載入 Task Card → 2. 確認 goal + definition_of_done → 3. 載入 context（system/GLOBAL_RULES.md + system/AGENT_CONTEXT.yaml + system/APPROVAL_POLICY.yaml + system/MODEL_POLICY.yaml + 對應 skill + project context）→ 4. 執行 → 5. 每關鍵階段 git commit checkpoint → 6. 依 system/GATE_POLICY.yaml 逐層驗證（schema → 規則 → 完成 → 風險，含 rollback 定義）→ 7. 輸出到 outputs/ → 8. 依 system/EXECUTION_LOG_SCHEMA.yaml 寫執行紀錄到 logs/runs/ → 9. 寫 audit log
+ 1. 載入 Task Card → 2. 確認 goal + definition_of_done → 3a. 載入 context（system/GLOBAL_RULES.md + system/AGENT_CONTEXT.yaml + system/APPROVAL_POLICY.yaml + system/MODEL_POLICY.yaml + system/TOOL_MAPPING.yaml + 對應 skill + project context）→ 3b. 宣告本次使用模型（依 MODEL_POLICY.yaml 與 Task Card 的 model_override）→ 4. 執行（allowed_tools ⊆ PERMISSIONS 登錄；未登錄視為 deny，見 D007）→ 5. 每關鍵階段 git commit checkpoint → 6. 依 system/GATE_POLICY.yaml 逐層驗證（schema → 規則 → 完成 → 風險，含 rollback 定義）→ 7. 輸出到 outputs/ → 8. 依 system/EXECUTION_LOG_SCHEMA.yaml 寫執行紀錄到 logs/runs/ → 9. 寫 audit log
```

**理由**：
- 載入 `system/TOOL_MAPPING.yaml` 讓 agent 知道 framework snake_case ↔ Claude Code 實際工具的對應；
- 步驟 3 拆成 3a + 3b 把「模型宣告」明確化（對應第一輪建議，之前僅在 MODEL_POLICY.yaml 提及）；
- 步驟 4 補一句 D007 閉包原則提醒。

**Token 成本估算**：+30~40 tokens，3K 預算內 margin 充足。

---

### 變更 2 — 權限段補 sub-agent 邊界（第 15 行下方）

```diff
  - **allow**：讀取專案檔案、web search、寫草稿、寫 logs、git checkpoint
  - **ask**：修改 skills/、system/、memory/，建立 Task Card，寫正式報告
  - **deny**：刪除、外發、修改正式資料、自動寫入長期記憶、金流操作
+
+ > Sub-agent（Agent tool）限唯讀模式（Explore / Plan / general-purpose / claude-code-guide）；
+ > 禁止 sub-agent 寫入、commit、multi-agent swarm。詳見 D006 與 PERMISSIONS 的
+ > `sub_agent_readonly` (allow) / `sub_agent_with_write_access` (deny)。
```

**理由**：D006 決定放寬為「允許唯讀 sub-agent」，但 CLAUDE.md 必須讓啟動時就知道這個邊界，
避免 agent 自行解讀「不做 multi-agent swarm」為「完全不用 sub-agent」（與第一輪任務已實際使用
Haiku sub-agent 的事實矛盾）。

---

### 變更 3 — Context 硬限制補 auto-compaction 共存說明（第 29 行）

```diff
  ## Context 硬限制

  - CLAUDE.md + GLOBAL_RULES.md ≤ 3,000 tokens
  - 單一 skill prompt (SKILL.md) ≤ 1,500 tokens；eval_examples.md 為按需載入參考材料，不計入
  - 只載入 Task Card 白名單內的工具
- - 長對話 20 輪後摘要壓縮
+ - 長對話 20 輪後摘要壓縮（Claude Code CLI 另有 auto-compaction；兩者並存，auto-compaction 後重要決策應已寫入 memory/ 或 logs/，不依賴 session 記憶跨輪保存）
  - 大型檔案用路徑引用，不全文貼入
```

**理由**：Claude Code CLI 自身在接近 context 上限時會做 auto-compaction（壓縮早期訊息），
這與 framework 的「20 輪摘要」規則為不同機制但目的類似。明文說明兩者並存且強調
「決策要持久化到 memory/ 或 logs/」，避免 agent 誤以為兩者互斥或在 compaction 後
找不到關鍵背景。

---

### 變更 4（選配）— Plan mode 等價於 draft-first 的註記（第 9 行三條硬規則之後）

```diff
  2. **對外動作只產出草稿。** Email、發文、資料更新一律先到 `outputs/drafts/`，等人工確認。
  3. **連續失敗 3 次就停下來。** 寫入 `logs/errors/` 並通知使用者，不要自己硬修。
+
+ > 註：Claude Code CLI 的 Plan mode / ExitPlanMode 是 runtime 層的 draft-first 等價物。
+ > 使用 Plan mode 規劃、提交計畫、待使用者核可後再執行，符合硬規則 2。
```

**理由**：第一輪未提及 Plan mode；本次在 AGENT_CONTEXT.yaml 的 `runtime_integrations`
已說明映射關係，但 CLAUDE.md 頂層三條硬規則是每 session 第一個載入的內容，
讓使用者與 agent 都直接看到對應關係，降低誤解。若想保持三條硬規則區塊精簡，
此變更可略過（AGENT_CONTEXT.yaml 已有完整說明）。

---

## Token 預算影響估算

| 項目 | 變更前 | 變更後 | 差異 |
|------|--------|--------|------|
| CLAUDE.md 行數 | 43 | 49–53 | +6 ~ +10 |
| CLAUDE.md tokens（估） | ~312 | ~360–395 | +48 ~ +83 |
| CLAUDE.md + GLOBAL_RULES.md | ~699 | ~747–782 | 仍遠低於 3K 上限 |

---

## 風險與緩解

| 風險 | 緩解 |
|------|------|
| 變更 4 讓三條硬規則區塊不夠精簡 | 變更 4 標為選配，可略過；AGENT_CONTEXT.yaml 有完整版 |
| 步驟 3 拆成 3a / 3b 讓執行流程顯得複雜 | 只多一行文字；TOOL_MAPPING.yaml 載入已是必要 |
| 權限段補 sub-agent 說明後長度超標 | 算過 token 後仍 <3K 總上限 |
| CLAUDE.md 與 AGENT_CONTEXT 重複 | CLAUDE.md 僅做「指向」；detail 留在 AGENT_CONTEXT，避免雙重維護 |

---

## 建議套用順序

1. 先套用 **變更 1、變更 2、變更 3**（直接對應本次 HIGH finding，無爭議）
2. 觀察 1 次真實任務後，決定是否套用 **變更 4**（Plan mode 註記）
3. 套用後在 CLAUDE.md 的 commit message 引用本草稿、D006、D007
