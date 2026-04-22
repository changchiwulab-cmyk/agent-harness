# CLAUDE.md — Opus 4.7 baseline 建議修改（草稿）

**狀態**：待人工確認
**來源 Task Card**：`20260420-001` Phase 3.2
**說明**：CLAUDE.md 屬 `ask` 權限（`modify_claude_md`），本檔為建議 diff，不直接套用。

---

## 盤點結果

CLAUDE.md 共 40 行，**沒有**硬編碼的 model ID（實際上完全 model-agnostic），這是優點。
需要處理的只有兩類：
1. 執行流程的 context 載入清單中，漏了新增的 `system/MODEL_POLICY.yaml`
2. 「單一 skill prompt ≤ 1,500 tokens」語意模糊，實務上會連同 `eval_examples.md` 一起計算（analysis skill 已達 99.6%）

---

## 建議變更（共 3 處，diff 格式）

### 變更 1 — 執行流程新增 MODEL_POLICY（第 19 行）

```diff
- 1. 載入 Task Card → 2. 確認 goal + definition_of_done → 3. 載入 context（system/GLOBAL_RULES.md + system/AGENT_CONTEXT.yaml + system/APPROVAL_POLICY.yaml + 對應 skill + project context）→ 4. 執行 → 5. 每關鍵階段 git commit checkpoint → 6. 依 system/GATE_POLICY.yaml 逐層驗證（schema → 規則 → 完成 → 風險，含 rollback 定義）→ 7. 輸出到 outputs/ → 8. 依 system/EXECUTION_LOG_SCHEMA.yaml 寫執行紀錄到 logs/runs/ → 9. 寫 audit log
+ 1. 載入 Task Card → 2. 確認 goal + definition_of_done → 3. 載入 context（system/GLOBAL_RULES.md + system/AGENT_CONTEXT.yaml + system/APPROVAL_POLICY.yaml + system/MODEL_POLICY.yaml + 對應 skill + project context）→ 4. 執行 → 5. 每關鍵階段 git commit checkpoint → 6. 依 system/GATE_POLICY.yaml 逐層驗證（schema → 規則 → 完成 → 風險，含 rollback 定義）→ 7. 輸出到 outputs/ → 8. 依 system/EXECUTION_LOG_SCHEMA.yaml 寫執行紀錄到 logs/runs/ → 9. 寫 audit log
```

**理由**：D005 已把模型選擇提升為獨立 policy；不載入會導致 agent 在降級時缺乏 fallback chain 依據。新增一個檔案約 +300 tokens，3K 總預算內仍有 ~2.2K margin。

---

### 變更 2 — 澄清 skill prompt 的 token 預算邊界（第 24 行）

```diff
  ## Context 硬限制

  - CLAUDE.md + GLOBAL_RULES.md ≤ 3,000 tokens
- - 單一 skill prompt ≤ 1,500 tokens
+ - 單一 skill prompt (SKILL.md) ≤ 1,500 tokens；eval_examples.md 為按需載入參考材料，不計入
  - 只載入 Task Card 白名單內的工具
  - 長對話 20 輪後摘要壓縮
  - 大型檔案用路徑引用，不全文貼入
```

**理由**：原條文歧義導致 2026-04-20 盤點時將 analysis skill 計為 99.6%（= SKILL.md + eval_examples 合計）。澄清後：
- SKILL.md：~426 tokens（28% 使用率，有充足 margin）
- eval_examples.md：~1,068 tokens（僅在首次使用或輸出不穩時載入）

同步已在 `skills/analysis/SKILL.md` 頂部加入「載入規則」註解。

---

### 變更 3（選配）— 在「權限」區塊下方補 D005 註解

```diff
  - **allow**：讀取專案檔案、web search、寫草稿、寫 logs、git checkpoint
  - **ask**：修改 skills/、system/、memory/，建立 Task Card，寫正式報告
  - **deny**：刪除、外發、修改正式資料、自動寫入長期記憶、金流操作
+
+ > 模型選擇依 `system/MODEL_POLICY.yaml`（D005，2026-04-20）：預設 Opus 4.7，
+ > Sonnet 4.6 / Haiku 4.5 為 fallback。Task Card 可用 `model_override` 覆寫。
```

**理由**：讓載入 CLAUDE.md 的 session 第一眼就知道模型策略存在，減少每次都要主動去翻 MODEL_POLICY.yaml 的摩擦。但若想保持 CLAUDE.md 最精簡，此變更可跳過（MODEL_POLICY 已出現在變更 1 的載入清單中）。

---

## Token 預算影響估算

| 項目 | 變更前 | 變更後 | 差異 |
|------|--------|--------|------|
| CLAUDE.md 行數 | 40 | 41–44 | +1 ~ +4 |
| CLAUDE.md tokens（估） | ~272 | ~285–315 | +13 ~ +43 |
| CLAUDE.md + GLOBAL_RULES.md | ~659 | ~672–702 | 仍遠低於 3K 上限 |

---

## 風險與緩解

| 風險 | 緩解 |
|------|------|
| 變更 3 讓 CLAUDE.md 不夠精簡 | 變更 3 標為選配，可略過 |
| 載入 MODEL_POLICY.yaml 後若語法錯會卡住啟動 | 已驗證 YAML 可 parse；CI 的 YAML check 會持續驗證 |
| 「按需載入 eval_examples」是人工 discipline，agent 不會強制 | 本來就是，2026-04-15 RETRO 後可量測實際載入頻率再決定是否改強制 |

---

## 建議套用順序

1. 先套用 **變更 1、變更 2**（低爭議、直接解決盤點發現的問題）
2. 觀察 1–2 次真實任務後，決定是否套用 **變更 3**
3. 套用後在 CLAUDE.md 頂部 commit message 引用本草稿與 D005
