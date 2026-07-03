# 模型路由映射說明（草稿）

> 狀態：草稿，待人工確認後晉升 `outputs/reports/`。
> 對應 Task Card：`20260530-W01`。真相來源：`system/MODEL_ROUTING.yaml`。

## 一、三層對應：tier → 模型 → 推理強度 → 子代理

| tier | 模型 id | reasoning_effort | 子代理（.claude/agents/） | 用途 |
|------|---------|------------------|--------------------------|------|
| `fast` | `claude-haiku-4-5-20251001` | （不設） | `fast-reader` | 快速讀取、搜尋、抽取、格式檢查、路由判斷 |
| `test` | `claude-sonnet-4-6` | high | `tester` | 跑測試、回測、逐條驗證、品質審查 |
| `strategy` | `claude-opus-4-8` | max | `synthesizer` | 統整、策略分析、決策、整合、規劃 |

## 二、使用者 3 分類 → skill_type → phase 的對應

使用者的 3 個分類與框架既有 5 個 skill 並非 1:1，對應如下：

| 使用者分類 | tier | 對應 skill_type | 對應 phase |
|-----------|------|-----------------|-----------|
| 快速讀取、搜尋 | `fast` | research（蒐集段）、ops | `explore` / `retrieve` |
| 測試 | `test` | review、實跑 `tests/`·`scripts/test_*` | `test` / `review` |
| 統整、策略規劃 | `strategy` | analysis、writing | `synthesize` / `plan` |

`by_skill_default`（未標 phase 時的預設）：
`research→fast`、`ops→fast`、`review→test`、`analysis→strategy`、`writing→strategy`。

## 三、同一張卡的不同階段用不同模型

兩種互補機制：

1. **資料層（宣告式）**：Task Card 的 `model_routing.phase_overrides`。
   例：一張 research 卡，讀取/搜尋用 Haiku、統整結論用 Opus：
   ```yaml
   skill_type: "research"
   model_routing:
     phase_overrides: { explore: fast, retrieve: fast, synthesize: strategy }
   ```
2. **執行層（sub-agent model 參數）**：實際跑時用 Agent/Task 工具的 `model` 參數派工——
   讀取/搜尋階段交給 `fast-reader`、測試交給 `tester`、統整/規劃交給 `synthesizer`。
   `MODEL_ROUTING.yaml` 是對照表，sub-agent 的 `model` 參數是「查表後帶上的值」。

> 框架原則「一卡一 skill、複合任務拆多張卡」（ROUTING_RULES）：嚴格做法是
> research→writing 拆兩張卡，天然落在 fast→strategy 兩 tier。`phase_overrides`
> 是給「單張卡內仍有明顯階段切換」時的輕量補充，兩者不衝突。

## 四、路由優先序（resolution_order）

1. Task Card `model_routing.override`（釘死 model id，最高優先）
2. Task Card `model_routing.tier`（顯式指定 tier）
3. 當前 phase → `routing.by_phase`
4. `skill_type` → `routing.by_skill_default`
5. `default_model`（`claude-opus-4-8`）

## 五、已知限制（高風險假設與待驗證）

- **`reasoning_effort`（high/max）為意圖宣告，非程式強制。** 本框架無自有 API 程式碼；
  `.claude/agents/` frontmatter 只能綁 `model`，無法 per-agent 設推理強度。實際強度由
  執行時（Claude Code CLI / sub-agent）決定。
- **dashboard 的 `task_model` 為「路由會指派的 tier」**（由 `skill_type` 經 `by_skill_default`
  衍生），非「實際跑過的模型」。實際模型看 `run_model`（來自 run log 的 `model_used`），
  目前多為 `unknown`，需新任務累積。
- **舊 51 卡 / 既有 log 不回填**：向後相容，舊 log 的 `model_used` 自由字串
  （`claude-opus` / `claude-opus-4-7` 等）先原樣呈現，不寫考古正規化邏輯。

## 六、來源

- `system/MODEL_ROUTING.yaml`（路由表真相來源）
- `system/ROUTING_RULES.md`（skill 路由 + 模型路由小節）
- `system/COST_POLICY.md`（模型路由原則）
- `.claude/agents/{fast-reader,tester,synthesizer}.md`（執行層綁定）
- `CLAUDE.md`（執行流程串接）
