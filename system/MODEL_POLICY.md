# 模型路由政策 MODEL_POLICY（v2.1 治理層硬化）

## 為什麼

`COST_POLICY.md` 早已把「模型路由」列為 v2 準備項，但標註**未實作**。本檔把它落地為明確
治理意圖：依任務性質分層選模，貴的模型只用在真正需要推理的地方。本檔只定「哪類任務該用哪
tier」，不自建 router runtime（避免與 Claude Code 原生/平台重複，見 `NATIVE_OVERLAP.yaml`）。

## 模型分層（2026-06 Claude 家族）

| Tier | 模型 ID | 用途 |
|------|---------|------|
| cheap | `claude-haiku-4-5` | 分類、抽取、格式檢查、路由判斷、deterministic eval 前處理 |
| standard | `claude-sonnet-4-6` | 一般 skill 執行（多數 research / writing / ops / review） |
| strong | `claude-opus-4-8` | 規劃、跨來源綜整、analysis 決策、高風險任務、gate 裁決、LLM-as-judge |
| creative | `claude-fable-5` | 視需求（敘事 / 長文創作），非預設 |

## skill_type → 預設 tier

| skill | 預設 tier | 升級時機 |
|-------|-----------|---------|
| research | standard | 需跨多來源綜整 → strong |
| analysis | strong | 決策 / Go-No-Go 本就需強推理 |
| writing | standard | 策略提案 / 高風險對外文件 → strong |
| ops | cheap | 純轉換 / 整理；涉及判斷 → standard |
| review | standard | 高風險審查 / gate 裁決 → strong |

規則：
- 路由判斷本身用 **cheap**。
- `risk_level >= high` → 一律至少 **standard**；gate 裁決與 LLM-as-judge 用 **strong**。

## Task Card 欄位

`TASK_CARD_TEMPLATE.yaml` 新增**可選** `model_tier`（cheap / standard / strong / creative）。
留空 = 依上表預設。屬建議，不強制（平台仍可覆寫）。

## 與原生重疊

`NATIVE_OVERLAP.yaml` 評估 Cost/模型選擇與平台 ~40% 重疊。本政策保留的是「治理意圖」
（哪類任務用哪 tier、何時升級），實際指派由人 / 平台執行——不重造 runtime。

## 落地對應與回看

`COST_POLICY.md`（成本基準互連）｜`TASK_CARD_TEMPLATE.yaml`（`model_tier` 欄）｜
`EVAL_POLICY.md`（judge = strong）。revisit：Claude 模型家族更新時（見 D009）。
