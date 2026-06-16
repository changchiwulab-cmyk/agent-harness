# 模型路由 MODEL_ROUTING

落地 `COST_POLICY.md` §「模型路由規則（v2 準備）」（gap A3）。Task Card 的選填欄位
`model` 用來把不同難度的工作分流到對應等級的模型，兼顧成本與品質。

## 路由表

| 工作性質 | 建議 `model` | 對應模型 | 理由 |
|---------|:-----------:|---------|------|
| 分類、抽取、格式檢查、路由判斷 | `haiku` | Claude Haiku 4.5 | 結構化、低推理需求，最省 token |
| 一般執行（多數 ops / writing / review） | `sonnet` | Claude Sonnet 4.6 | 速度與品質平衡 |
| 規劃、推理、整合分析、編排 | `opus` | Claude Opus 4.8 | 高推理需求 |
| 最高難度推理 / 長鏈決策 | `fable` | Claude Fable 5 | 前沿推理上限 |

## 依 skill_type 的預設

未在 Task Card 指定 `model` 時，用下列預設（仍可被卡片覆寫）：

| skill_type | 預設 model |
|-----------|:----------:|
| research | sonnet |
| analysis | opus |
| writing | sonnet |
| ops | haiku |
| review | sonnet |
| orchestration | opus |

## 使用方式

- Task Card 的 `model` 為**選填**。留空 = 用 session 預設模型，不強制路由。
- 允許值（含別名）：`haiku` / `sonnet` / `opus` / `fable`，或完整 id
  `claude-haiku-4-5` / `claude-sonnet-4-6` / `claude-opus-4-8` / `claude-fable-5`。
- `system/validate_task_card.py` 會在 `model` 有值時校驗其值域。
- 與成本校準的關係：`COST_POLICY.md` 的校準係數仍依 skill_type 估算；模型路由是在
  該預算內進一步降本，不取代既有護欄。

## 邊界

- 路由判斷本身不應消耗大量 token（沿用 ROUTING_RULES 原則）。
- 高風險任務（risk ≥ high）不因省成本而降模型；品質優先。
