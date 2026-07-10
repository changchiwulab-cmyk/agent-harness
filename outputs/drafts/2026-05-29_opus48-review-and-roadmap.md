# Agent Harness v2 — 完整檢視 ＋ Opus 4.8 優化路線圖

> 草稿｜task_id: 20260529-012｜skill: review｜2026-05-29
> 疊加於 `2026-05-29_harness-self-assessment.md`（R1–R10），本檔只新增「原生能力遷移」這條軸與 Opus 4.8 優化路線圖，不重做既有評分。

## 總體評估

**結論：架構成熟、治理紮實，但有約 30% 自訂層與 Claude Code 原生能力重疊，且 `COST_POLICY` 早已設計的模型路由從未落地。** 本輪以「平衡遷移」優化：高重疊低治理價值的模組改用原生，保留原生缺乏的治理價值（風險分級、draft-first、audit、失敗分類學）。

| 軸 | 評分(1-10) | 說明 |
|---|---|---|
| 治理完整度 | 8 | 三平面十六模組、四層 gate、14 失敗模式、recovery runbook 完整 |
| 工具/CI 成熟度 | 7 | permissions_guard PreToolUse hook、12 關 CI、e2e gate 測試、frontend 漂移檢查 |
| 原生能力對齊度 | **4** | 仍手刻 router、手動 context 壓縮、模型路由未落地；skill frontmatter 不一致 |
| 資料/觀測完整度 | 4 | approvals 長期空置、token 多為 not_recorded、analysis 零成本樣本（沿用既有評估） |

## 原生能力遷移評分軸（本輪新增）

依 `system/NATIVE_OVERLAP.yaml` 的模組重疊度，給出遷移建議：

| 模組 | 原生重疊 | 本輪動作 | 取代 or 保留 |
|---|---|---|---|
| Skill Executor（skills/） | 85% | 統一 frontmatter＋`.claude/skills/` 註冊，靠 description 自動載入 | **改原生** |
| Planner/Router（ROUTING_RULES） | 70% | 降級為文件/後援；原生 description 自動路由為主 | **改原生** |
| Cost Policy（模型路由） | 40% | 用 `.claude/agents` 子代理落地 Haiku/Sonnet/Opus 分流 | **改原生＋保留校準資料** |
| Context Manager（20 輪摘要） | 50% | 改用原生 auto-compaction＋PreCompact hook 保全治理狀態 | **改原生** |
| Permission（PERMISSIONS） | 75% | 工具權限以 settings.json/PreToolUse 為主；**風險分級保留** | 混合 |
| Agent Context（AGENT_CONTEXT） | 60% | 去除與 PERMISSIONS 重複的能力清單，只留邊界/升級邏輯 | 瘦身 |
| Checkpoint（git） | 0% | 不動 | 保留 |
| Audit / Gate / Failure Taxonomy | — | 原生無對應，全數保留並用 hook 自動化 | **保留** |

## 對映既有 self-assessment（R1–R10）

| 既有 R 項 | 與本輪關係 |
|---|---|
| R1 approval 紀錄 schema＋首筆回填 | 本輪在 `logs/approvals/` 補首批正式紀錄（013 的核准） |
| R2 CI 涵蓋 logs/ | 本輪再擴充：skill/agent frontmatter lint |
| R6 token 來源標示 | 本輪以子代理隔離＋prompt caching 降本，回填留待下次 retro |
| R3 analysis 成本樣本 | 不在本輪範圍（需實跑 analysis 任務） |
| R7 觀測面板、R8 recovery 演練 | 已於 2026-05-29 完成；本輪用 SessionStart hook 把 recovery 自動化 |

## 不一致 / 冗餘 / 缺口清單（含修正位置）

| # | 問題 | 位置 | 修正 |
|---|---|---|---|
| 1 | skill_type 漏列 `analysis`（僅 4 個） | `README.md` L96、`tasks/TASK_CARD_TEMPLATE.yaml` L38、`system/EXECUTION_LOG_SCHEMA.yaml` L21 | 補成 5 個 |
| 2 | 能力清單與 PERMISSIONS 重複 | `system/AGENT_CONTEXT.yaml` `can_do`/`cannot_do` | 改為指向 PERMISSIONS，只留 refuse/escalate |
| 3 | 失敗分類學摘要重述 | `system/GLOBAL_RULES.md` L46-49 | 只留指標，不重述百分比 |
| 4 | approval 紀錄來源未釐清 | `APPROVAL_POLICY.yaml`、`EXECUTION_LOG_SCHEMA.yaml` | 加 cross-ref：approvals/ 為 source of truth |
| 5 | skill frontmatter 不一致（僅 research 有） | `skills/{analysis,writing,ops,review}/SKILL.md` | 補一致 frontmatter |
| 6 | 手動「20 輪摘要」與原生重複 | `CLAUDE.md`、`FAILURE_TAXONOMY.yaml` SPEC-03 | 改用原生 compaction＋PreCompact hook |
| 7 | 模型路由設計未落地 | `system/COST_POLICY.md` | 用子代理落地並標為已實作 |
| 8 | `SECURITY.md` 為 GitHub 樣板 | `SECURITY.md` | 改寫為專案實況 |
| 9 | writing 校準係數 2.00× 僅 1 筆未標風險 | `system/COST_POLICY.md` | 標 pending stabilization＋暫定天花板 |
| 10 | plugin 草稿用不存在的 `PostTaskUse` 事件 | `outputs/drafts/agent-governance-bootstrap/plugin.json` | 改對映真實事件 |

## 四個 Opus 4.8 lever 排序

1. **子代理＋模型成本路由**（最高槓桿，見下）
2. **原生 Skills 自動路由**（與 1 合一執行；移除手刻 router）
3. **Hooks 自動化治理**（把 prose 規則變程式強制：SessionStart 載 recovery、Stop 跑漂移檢查、PostToolUse 寫 audit）
4. **Prompt caching ＋ context**（常駐 system prompt 快取；原生壓縮取代手動摘要）

### 最高槓桿動作（keystone）

**把 5 個 skill 同時升級成「原生 Skill ＋ 對應子代理（含模型路由）」。** 單一動作即：
- 移除手刻 router（Router 70% 重疊歸零）
- 首次**落地** `COST_POLICY` 的模型路由＝實際降本（context 隔離估省 ~67%；ops 走 Haiku、analysis 走 Opus）
- 以最低風險、增量方式踏出 v3「bounded specialists」第一步

## 風險與張力（本輪如何處理）

1. **原生自動觸發 vs「沒有 Task Card 不執行」**：skill/子代理定義「怎麼做」非「要不要做」；descriptions 標注「Task Card 執行階段」，對外動作恆由 `permissions_guard.py` deny-list＋draft-first 把關。
2. **子代理自主 vs draft-first**：子代理 `tools` 不含對外動作、繼承 PreToolUse deny-guard、只產 draft；gate/approval 留主代理。
3. **CLAUDE.md token 預算**：移除手動壓縮 prose 抵銷新增；以 `check_context_budget.rb` 守住 ≤3,000。
4. **symlink 於 git 的脆弱性**：CI 加 symlink 可解析檢查。

## 本輪明確不做
- v3 完整 graph orchestration / bounded specialists 編排
- plugin 正式打包與 marketplace 發布（本輪僅修正 plugin.json 正確性）
- analysis 成本樣本回填、自動長期記憶擴寫、複雜 MCP 串接
