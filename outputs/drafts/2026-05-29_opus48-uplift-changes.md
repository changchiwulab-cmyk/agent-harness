# Opus 4.8 優化 — 變更摘要

> 草稿｜task_id: 20260529-013｜skill: ops｜2026-05-29
> 對應計畫：檢視＋高槓桿實作 / 平衡遷移 / 四 lever 全做。批准紀錄：`logs/approvals/2026-05-29_20260529-013_approval.yaml`。

## Phase A — 品質修正

| 變更 | 檔案 |
|---|---|
| skill_type 補上 `analysis`（原僅 4 個） | `README.md`、`tasks/TASK_CARD_TEMPLATE.yaml`、`system/EXECUTION_LOG_SCHEMA.yaml` |
| 能力清單去重，改指向 PERMISSIONS 單一來源 | `system/AGENT_CONTEXT.yaml` |
| 失敗分類學不再重述摘要，只留指標 | `system/GLOBAL_RULES.md` |
| approval 紀錄來源權威釐清（approvals/ 為準，execution_log 為鏡像） | `system/APPROVAL_POLICY.yaml`、`system/EXECUTION_LOG_SCHEMA.yaml` |
| SECURITY.md 改寫為專案實況（deny-list/draft-first/風險分級/回報窗口） | `SECURITY.md` |
| writing 校準係數標 pending stabilization＋暫定天花板 40K | `system/COST_POLICY.md` |

## Phase B — Opus 4.8 能力升級

### B1 原生 Skills 自動路由
- 4 個 skill 補上一致 YAML frontmatter（`name`/`description`，含「用於 Task Card 執行階段」治理註記）：`skills/{analysis,writing,ops,review}/SKILL.md`；research 補上同註記。
- `.claude/skills/` 以**相對 symlink** 註冊 5 個 skill（research 既有；analysis/writing/ops/review 新增）。
- `system/ROUTING_RULES.md` 標註「原生 description 自動路由為主，本表為契約/後援」。

### B2 子代理＋模型成本路由（落地 COST_POLICY 早已設計的 v2 路由）
- 新增 `.claude/agents/{research,analysis,writing,ops,review}-specialist.md`，least-privilege `tools` ＋ per-agent `model`：ops→haiku、research/writing/review→sonnet、analysis→opus。
- `system/COST_POLICY.md` 模型路由段改標「已落地」＋子代理對照表。

### B3 Hooks 自動化治理
- `.claude/settings.json` 擴充：SessionStart（載 recovery context）、Stop（fail-open 漂移檢查）、PreCompact（保全治理狀態）；保留既有 PreToolUse deny-guard。
- 新增 `scripts/session_start_context.py`、`scripts/session_stop_checks.py`、`scripts/precompact_preserve.py`（全部 fail-open，永遠 exit 0）＋ `scripts/test_session_start_context.py`。
- 修正 plugin 草稿：`PostTaskUse`（非真實事件）→ `Stop`；`skills: []` → 補 5 個。

### B4 Prompt caching ＋ context
- `CLAUDE.md`：手動「20 輪摘要」→ 原生 auto-compaction＋PreCompact hook；新增 cache 友善載入順序。
- `system/FAILURE_TAXONOMY.yaml` SPEC-03 mitigation 同步更新。
- `system/COST_POLICY.md` context 量化表新增 prompt caching 列。

## CI／測試
- `scripts/check_spec_consistency.rb` 新增 section 7-9：skill frontmatter、`.claude/agents` frontmatter（含 model 合法性）、`.claude/skills` symlink 可解析。
- `scripts/test_check_spec_consistency.rb` 新增 `TestFrontmatterLint`（5 個 subprocess 測試）。
- `.github/workflows/spec-consistency.yml` 新增：Audit log drift check、Hook script tests。

## 保留不變的治理價值
風險分級（PERMISSIONS）、draft-first 批准、audit/execution log、失敗分類學、Task Card 契約、git checkpoint。原生只取代「怎麼做」，治理仍管「要不要做」。

## 驗證
見任務 DoD；本地與 CI 皆跑 `check_spec_consistency` / `check_context_budget` / `validate_task_card` / 各 `pytest` 與 e2e / `generate_*_manifest --check`。
