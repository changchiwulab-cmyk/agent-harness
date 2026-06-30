# 架構補齊驗證報告（2026-06-30）

> 對應 Task Card 20260630-005、Decision D008。草稿待人工確認後可晉升 reports/。

## 補齊內容總覽

| # | 缺口 | 落地 | 對標 2026 |
|---|------|------|-----------|
| 1 | 記憶層 v2 | `memory/episodes/` + `memory/playbook/`(5 skill) + 進場檢索 | 分層記憶 / context playbook |
| 2 | eval harness | `evals/` 5 rubric + 10 golden + `run_evals.py` | eval harness 評分每次變更 |
| 3 | 內容安全 | `system/SAFETY_POLICY.md` + `output_scan.py` | guardrails（輸入注入 / 輸出掃描）|
| 4 | 子代理契約 | `system/SUBAGENT_POLICY.md` + Task Card delegation | subagent context 隔離 |
| 5 | Skill 註冊表 | `skills/REGISTRY.yaml` + `validate_skill_registry.py` | SSOT / 一致性 |

## 設計原則遵循

- 寫記憶仍 ask、檢索 allow、`auto_write_memory` 維持 deny。
- 不引入向量庫、不引入外部依賴（關鍵字/標籤檢索）。
- 不違反 D006（不對小任務加 per-run trace）、不提前觸發 D003（v3/v4）。
- 全部沿用既有模式：規格 + schema + 薄 script + CI 測試。

## 驗證結果

### 新增單元測試（全綠）
- `test_memory_retrieve.py` — 7 passed
- `test_run_evals.py` — 9 passed
- `test_output_scan.py` — 8 passed
- `test_validate_skill_registry.py` — 5 passed

### 確定性檢查（全綠）
- `run_evals.py --check` — 10 golden，0 mismatch（good 100% / bad 0%）
- `build_memory_index.py --check` — 索引無漂移
- `validate_skill_registry.py` — REGISTRY ↔ skills/ 一致（5 skills）
- `output_scan.py outputs/` — 既有產出零誤判

### 既有管線不回歸（全綠）
- `check_spec_consistency.rb` — OK
- 全 YAML 可解析 — OK
- `check_context_budget.rb` — CLAUDE.md + GLOBAL_RULES ~1240 / 3000 tokens
- `generate_frontend_manifest.py --check` — data.json 已重生（50 tasks / 8 decisions）

### CI 接入
`.github/workflows/spec-consistency.yml` 新增 9 個步驟（4 測試套件 + 4 一致性檢查 + 1 掃描）。

## 端到端示意（進場檢索 → 評分 → 掃描）
```
memory_retrieve.py --skill research --keywords "web search,rate limit"
  → 撈出 PB-research-001 + episode E001（避免重蹈 rate-limit）
run_evals.py --score <草稿> --skill research
  → 量表評分，輔助 gate completion_check
output_scan.py <草稿>
  → 晉升前把關機密/個資
```

## 待人工確認事項
- 是否將本驗證報告晉升至 `outputs/reports/`。
- README 架構章節是否同步補上 v2.1 新元件（已於本批一併更新，請覆核）。
