# EXECUTION_LOG → OpenTelemetry GenAI 對照（M6）

> 把既有 `EXECUTION_LOG_SCHEMA.yaml` 的欄位**鬆對齊** OpenTelemetry GenAI semantic conventions
> （vendor-neutral `gen_ai.*` span/metric），為未來可攜性（接 Langfuse / Phoenix / 任何 OTel backend）鋪路。
> **不引入** runtime SDK 依賴或複雜 MCP——只做 schema 對照。對齊 2026 業界 trace/observability 標準。

## 為什麼

`governance_metrics.py`（R7）已有工具/工作流/業務層指標，但**沒有 trajectory/trace 級**紀錄，
也沒對齊任何標準 vocabulary。本檔定義對照表，讓 EXECUTION_LOG 的 `trace` 區塊未來可機械轉成 OTel span。

## 對照表

| EXECUTION_LOG（trace[]） | OpenTelemetry GenAI | 說明 |
|--------------------------|---------------------|------|
| `run_id` | trace_id（root span） | 一次任務 = 一條 trace |
| `trace[].step` | span 序 | 每步一個 child span |
| `trace[].type` | `gen_ai.operation.name` | tool_call / reasoning / subagent |
| `trace[].tool` | `gen_ai.tool.name` | 工具名 |
| `trace[].tokens` | `gen_ai.usage.input_tokens` / `output_tokens` | 該步 token |
| `trace[].latency_ms` | span duration | 延遲 |
| `trace[].outcome` | span status（ok/error） | 結果 |
| `skill_type` | `gen_ai.agent.name`（自訂屬性） | 路由的 skill |
| `token_estimate.source` | （自訂屬性）量測來源 | dashboard_measured / rule_estimated |

> 註：OTel GenAI conventions 多為 experimental，且預設**不擷取內容**以避免 PII 外洩——
> 與本框架「敏感資料不進 context、外部資料標 `[外部未驗證]`」一致。

## 範圍與後續

- **本輪**：只定 schema（EXECUTION_LOG `trace` 區塊）+ 本對照表。
- **後續（另開卡 M6-b）**：`run_evals.py` / `governance_metrics.py` 可選輸出真實 OTel span（OTLP exporter），接 Langfuse/Phoenix（皆 OSS、可自架，符合資料自主）。
- enforcement：`trace` 區塊為選填；填寫時由 logs schema lint 驗結構（延伸 R2）。
