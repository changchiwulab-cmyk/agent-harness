# 可觀測性指標報告 — Agent Harness v2（2026-05-29）

> **草稿（draft）** ｜ Task Card：`20260529-009`（R7） ｜ skill：ops
> 由 `scripts/governance_metrics.py --observability` 採集（工具層之外的工作流層 / 業務層 / 失敗分佈）。

## 結論

自我評估點名「觀測只到工具層」。本批把觀測擴到**工作流層**與**業務層**後，立刻得到兩個可行動訊號：(1) **`review` 的平均 token 被一筆 ~120K 的多代理任務嚴重拉高**（34.8K），印證該筆當初標記「不納入校準」是對的；(2) 多個 skill 的實測平均明顯高於 COST_POLICY 原始預估，下次 RETRO 應整體上修。

## 一、工作流層（2 筆 run log）

- **status 分佈**：completed 1 / failed 1（R5 演練貢獻首筆 failed）
- **平均 checkpoints/run**：2.0
- **四層 gate 結果**：

| gate | pass | fail | not_run |
|------|:----:|:----:|:-------:|
| schema_check | 1 | 1 | 0 |
| rule_check | 1 | 0 | 1 |
| completion_check | 1 | 0 | 1 |
| risk_check | 1 | 0 | 1 |

> 解讀：唯一一筆 `fail` 是 R5 受控演練（schema_check 失敗即停，後續 gate `not_run`）——正是失敗短路行為的預期樣態。樣本仍小（2 筆），趨勢待累積。

## 二、業務層（每 skill，來源 AUDIT_LOG）

| skill | 任務數 | 平均 token | 平均工具呼叫 | vs COST_POLICY 預估 |
|-------|:-----:|:---------:|:-----------:|------|
| ops | 20 | ~14.9K | 12.0 | 預估 8K → 實測高 ~1.9× |
| review | 5 | ~34.8K ⚠️ | 9.2 | 受 ~120K 離群值拉高；剔除後 ≈13.5K，貼近 12K 預估 |
| research | 5 | ~23.6K | 4.8 | 預估 15K → 實測 ~1.57×（與 COST_POLICY 21.5K 一致） |
| writing | 4 | ~16.5K | 5.8 | 預估 10K → 實測 ~1.65× |
| analysis | 3 | ~16K | 8.7 | 預估 12K → 實測 ~1.33×（R3 樣本已納入） |

> **離群值警示**：`review` 的 ~34.8K 含一筆 `20260529-001` 自我評估（~120K，多代理研究型），當初已在 audit log 標「不宜併入 review 校準均值」。可觀測性層把它顯性化——這正是業務層觀測的價值：**離群值不再被平均數藏起來**。

## 三、失敗分佈（2 筆 error log）

| error_type | 次數 |
|------------|:----:|
| tool_failure | 1（S01：web search rate limit） |
| schema_failure | 1（R5 受控演練） |

> 目前無 rule_violation / timeout / unknown。樣本小，僅作基線。

## 四、建議（對應 roadmap / RETRO）

1. **下次 RETRO 整體上修 COST_POLICY 任務級預算**：ops/research/writing 實測平均皆顯著高於原預估（~1.6–1.9×）。analysis 已有樣本（R3）。
2. **review 校準需剔除多代理離群值**：建議 COST_POLICY 校準改用中位數，或明確排除標記為「多代理/研究型」的任務。
3. **工作流層樣本待累積**：gate 統計目前僅 2 筆 run；R8 之後與後續真實任務會補上更多 run log。
4. **前端面板（R7 延後項）**：本報告數據已可由 `governance_metrics.py --observability` 取得；接入 dashboard 需改 `data.json` schema（受 CI drift-check 保護），列為獨立乾淨變更。

## 五、採集方式

```
python3 scripts/governance_metrics.py --observability   # 三層指標 JSON
python3 scripts/governance_metrics.py                   # M1–M4 + 觀測段（markdown）
```
