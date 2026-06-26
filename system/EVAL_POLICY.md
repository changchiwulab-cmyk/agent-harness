# 評測政策 EVAL_POLICY（v2.1 治理層硬化）

## 為什麼

「可量化」是本框架三原則之一（可恢復 / 可審核 / 可量化）。成本已由 `COST_POLICY.md`
以校準係數量化；但**輸出品質**一直只有 `skills/<type>/eval_examples.md` 的好/壞範例
（golden set），**沒有任何機制去「跑」它**。本政策讓 golden set 變成可執行的 regression，
把「可量化」從成本延伸到品質。

## 評什麼

1. skill 輸出對 golden set 的一致性（deterministic 規則）。
2. 對 Task Card `definition_of_done` 的逐條遵從（沿用 `GATE_POLICY.yaml` completion_check，不重造）。

## 怎麼評（兩層）

- **L1 deterministic（預設、必跑）**：規則化檢查，零外呼、可進 CI。
  由 `skills/<type>/rubric.yaml` 定義、`scripts/run_evals.py` 執行。
  check 類型：`required_heading` / `required_regex` / `forbidden_regex` / `heading_order` / `heading_nonempty`。
- **L2 LLM-as-judge（可選、不自動）**：deterministic 判不了的品質維度（論證強度、語氣）才用強模型評分。
  屬 `ask` 等級、人工觸發，本期**不接 CI**（避免外呼成本與評分不穩定）。對應 `MODEL_POLICY.md` 的 judge tier。

## rubric schema（`skills/<type>/rubric.yaml`）

```yaml
skill: research
pass_threshold: 0.8           # score ≥ 此值視為通過
checks:
  - id: section_conclusion
    type: required_heading
    token: "結論"
    desc: "必須有結論區段"
  # required_regex {pattern} / forbidden_regex {pattern}
  # heading_order {before, after} / heading_nonempty {token}
```

## 評分與不變式

- `score = 通過 check 數 / 總 check 數`；`score ≥ pass_threshold` → 通過。
- **regression 不變式**：同一 skill 的 good 範例必過、bad 範例必不過。違反即 CI 失敗。

## 何時評

- 改 `skills/` 或 `system/` 規則 → CI 跑 `run_evals.py` regression（防止改壞 golden set）。
- 季度 RETRO → 新增「eval」維度，看各 skill 通過趨勢（見 `RETRO_FLOW.md`）。
- 新增/修改 rubric → 走 `ask`（列 diff 後人工確認）。

## 落地對應（enforcement — 遵守 J5：每條規則對應一個檢查點）

| 元件 | 路徑 |
|------|------|
| Runner | `scripts/run_evals.py` |
| 單元測試 | `scripts/test_run_evals.py` |
| good>bad 不變式 e2e | `tests/e2e/test_eval_smoke.py` |
| rubric schema lint | `scripts/check_spec_consistency.rb` |
| CI 串接 | `.github/workflows/spec-consistency.yml` |
