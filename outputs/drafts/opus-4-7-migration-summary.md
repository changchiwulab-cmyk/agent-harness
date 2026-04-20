# Opus 4.7 相容性遷移摘要

**Task Card**：`tasks/2026-04-20_opus-4-7-compatibility.yaml` (`20260420-001`)
**日期**：2026-04-20
**狀態**：已完成（CLAUDE.md 草稿待人工確認）
**執行紀錄**：`logs/runs/20260420-001_opus-4-7-compatibility.yaml`

---

## 盤點結論

**整體相容（YELLOW）**：agent-harness v2 架構與 Claude Opus 4.7 無 API / schema / tool 衝突，只需微調。

---

## 完成事項

### Phase 1 — 立即（低風險、向後相容） ✓

| 項目 | 產出 | commit |
|------|------|--------|
| audit log 模型遷移註記 | `logs/AUDIT_LOG.md` 頂部加入遷移表，歷史 entries 不竄改 | `2140cbe` |
| 模型路由 policy | `system/MODEL_POLICY.yaml` 新檔：Opus 4.7 預設 + Sonnet 4.6 / Haiku 4.5 fallback | `2140cbe` |
| 專案 context footnote | `memory/active_projects/agent-harness/context.md` 加入 2026-04-20 狀態與 D005 引用 | `2140cbe` |

### Phase 2 — 強化 ✓

| 項目 | 產出 | commit |
|------|------|--------|
| CI 版本釘選 | 已自然滿足（ruby 3.2 / python 3.11 已 pin 於兩個 workflow） | — |
| D005 決策紀錄 | `memory/.../decisions/20260420-D005_opus-4-7-baseline.yaml`：部分覆寫 D002 的 token API 假設，保留 D002 原文 | `c0237c0` |
| COST_POLICY 更新 | 模型路由段落改指向 MODEL_POLICY.yaml；新增「Opus 4.7 觀測能力」段落（已知 / 待驗證 / 處置） | `c0237c0` |

### Phase 3 — 優化 ✓（CLAUDE.md 僅產草稿）

| 項目 | 產出 | commit |
|------|------|--------|
| analysis skill 載入規則 | `skills/analysis/SKILL.md` 頂部註明 eval_examples.md 為按需載入，釋出 token margin | `2778e51` |
| CLAUDE.md 建議 diff | `outputs/drafts/claude-md-opus-4-7-proposed-diff.md`：3 處建議（2 強烈建議 + 1 選配），未直接修改 CLAUDE.md | `2778e51` |

---

## 四層 Gate 驗證結果

| 層 | 結果 | 說明 |
|----|------|------|
| schema_check | pass | Task Card 通過 ruby + python 兩支 validator |
| rule_check | pass | 所有修改在 allowed_tools 白名單內；ask 級動作已取得人工批准 |
| completion_check | pass | 11 條 DoD 全通過（Phase 3 CLAUDE.md 僅產草稿符合「產出 diff 草稿到 outputs/drafts/」定義） |
| risk_check | pass | risk_level=medium 與實際動作一致；CLAUDE.md 修改鎖定在 drafts/ |

---

## 待人工確認項目

1. **CLAUDE.md 是否套用 `outputs/drafts/claude-md-opus-4-7-proposed-diff.md` 的建議**
   - 變更 1（新增 MODEL_POLICY 到載入清單）：強烈建議
   - 變更 2（澄清 skill prompt 邊界）：強烈建議
   - 變更 3（權限區塊下方註解）：選配
2. **CI 失敗處理**：PR #32 的 `validate-spec` 與 `check-task-card-skill-type` 在 2 秒內失敗，本地所有對應步驟通過。研判為 runner infra 問題，使用者已選擇忽略。若後續 PR 仍有同樣狀況，建議觀察是否為既有 flakiness。

---

## 檔案清單

**新增**
- `system/MODEL_POLICY.yaml`
- `memory/active_projects/agent-harness/decisions/20260420-D005_opus-4-7-baseline.yaml`
- `logs/runs/20260420-001_opus-4-7-compatibility.yaml`
- `outputs/drafts/claude-md-opus-4-7-proposed-diff.md`
- `outputs/drafts/opus-4-7-migration-summary.md`（本檔）
- `tasks/2026-04-20_opus-4-7-compatibility.yaml`

**修改**
- `logs/AUDIT_LOG.md`（新增遷移表）
- `memory/active_projects/agent-harness/context.md`（狀態 + 決策列表）
- `system/COST_POLICY.md`（模型路由段落 + Opus 4.7 觀測能力段落）
- `skills/analysis/SKILL.md`（頂部載入規則）

**未修改（草稿待審）**
- `CLAUDE.md`

---

## 下一步建議

1. 審閱本摘要與 `claude-md-opus-4-7-proposed-diff.md`
2. 若核可 CLAUDE.md 的變更 1、2，回覆後由 agent 直接套用（這次不再需要額外 Task Card，仍為本 Task Card scope 內）
3. 後續觀察 1–2 次真實 Opus 4.7 任務的執行狀況，再決定：
   - 是否套用變更 3
   - D002 的 token API 假設是否能正式解除（需實測 Claude Code CLI 內 per-turn token 觀測）
   - MODEL_POLICY 的 primary / fallback 是否需依實測調整
