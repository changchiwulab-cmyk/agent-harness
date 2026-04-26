# PR Backlog Triage Summary — 2026-04-26

**Task Card**: `tasks/2026-04-26_pr-backlog-triage.yaml` (20260426-O03)
**Source**: deep-research-report-2.md 反向三 — PR sprawl 與重複提案
**Approval**: 使用者已確認 open PR 屬於「真 backlog」，授權主題式合併與激進關閉

## 執行結果

| 指標 | 進入時 | 收斂後 |
|---|---:|---:|
| Open PRs | 36 | 16（含 #53 本 PR） |
| 已關閉（superseded） | 0 | 21 |
| 重複主題群組 | 6 | 0（每組已收斂到單一 PR） |
| 需 owner 個別審查 | — | 14 |

報告原估 27 open，實際 36；經本次收斂 → 16（含本 PR）。距 DoD 目標（≤ 12）尚差 4，剩餘的全是「需 owner 個別審查」非「明顯重複」，不適合自動關閉。

## 關閉清單（21 PRs）

| Group | PRs | Superseded by | 理由 |
|---|---|---|---|
| **A1** analysis eval examples | #16 / #17 / #18 / #19 / #20 / #21 / #22 | PR #25 (merged 2026-04-15) | analysis skill 已正式註冊（`skills/analysis/SKILL.md` + `eval_examples.md`） |
| **A2** analysis skill_type docs | #38 / #39 / #40 / #41 | main + PR #25 | analysis 已在 PERMISSIONS / ROUTING / `check_spec_consistency.rb` ALLOWED_SKILL / TASK_CARD_TEMPLATE |
| **A3** analysis README/template wave | #46 / #47 / #48 | tasks/20260426-O02 (本 PR) | 本 PR 的 docs-parity-fix 已加 analysis 到 README skill_type list |
| **B1** workflow permissions autofix | #29 / #30 | #52 + tasks/20260426-O04 (本 PR) | 同一 alert，最新版 #52；本 PR #4 直接收斂 |
| **B2** validator tooling duplicates | #36 / #37 / #43 / #44 | #45 | 同 codex 主題、同 scope，#45 為最新更新版 |
| **B3** 五主題測試 v1 | #34 | #35 | #35 為 v2 改寫（branch `claude/five-themes-v2`） |

## 保留清單（active，需 owner 個別審查）

排除本 PR (#53)，剩 15 個 active PR。下表給每筆我的觀察與建議下一步。

| PR | 主題 | 我的判讀 | 建議下一步 |
|---|---|---|---|
| **#14** | leather ecommerce 市場研究 | 與一人公司主線無關，topic outlier | owner 決定：merge（若仍想保留 artefact）或 close |
| **#15** | 從 audit log rebuild 失蹤 drafts | 部分目的已被 20260417-O01 evidence-gap-filling 涵蓋；其餘 v2 drafts 是否仍需要待確認 | owner review，可考慮 close |
| **#23** | Elon-style 分析 | 歷史分析草稿，內容仍有參考價值 | owner 決定：merge 到 outputs/reports/ 還是 close |
| **#24** | Jobs-style 分析（branch off #23） | 同上；含一個已修的 skill_type validation regression（已被 main 的 `ALLOWED_SKILL` 修正吸收） | owner review，validation 部分已被吸收 |
| **#27** | 回應 PR #26 Codex P2 review | 修兩件具體事：vietnam-expansion frontmatter + evidence-gap-filling 補 bash 到 allowed_tools | owner verify 是否已在 main，未在則 merge |
| **#28** | 翻 4 張 2026-04-04 cards review→done | **真實有效** — main 上 S01/W01/RV01/O02 仍是 `status: "review"`，需 flip | **建議 merge**（先前我誤關，已重開） |
| **#31** | 集中化 PR-required CI checks（codex） | **與本 PR #5 (parity CI + audit gate) 直接重疊** | owner 等 #5 落地後決定：close 或挑選有用部分 |
| **#32** | Opus 4.7 相容性 | 結構性升級，含 MODEL_POLICY / TOOL_MAPPING / D006-007 | owner review；scope 大、值得獨立 merge |
| **#33** | 3 張治理 loop task cards | 純新增 task cards，低風險 | 建議 merge |
| **#35** | 五主題測試 v2 | 純測試資料 + audit entries | 建議 merge 或 close（測試資料用途決定） |
| **#42** | 大整合分支（4 卡 + 6 feature 分支） | 報告判讀 high-risk integration branch；含 partial / 已知 drift | owner 細審；建議拆細而非整體 merge |
| **#45** | Validator tooling（codex） | 重點是新增 `requirements-dev.txt` + Python unit tests | owner 決定是否引入 Python dev path（與目前純 Ruby + 一支 Python validator 取捨） |
| **#50** | 3 張產業測試 task cards | 純新增測試卡，低風險 | 建議 merge |
| **#51** | 2026-04-26 全面優化（5 卡 / 10 項建議） | **與本 PR (#53) 顯著重疊** — D007–D010 / outputs templates / AUDIT_LOG 季度分檔 / KB 工具選型 | **owner 必須決定**：本 PR 與 #51 何者為主，避免兩條線同時 merge 造成衝突 |
| **#52** | Workflow permissions autofix（最新版） | 與本 PR #4 直接重疊；本 PR 將直接修 main | 等本 PR merge 後 close |

## 已知重疊風險（需 owner 直接決定）

兩處與本 PR 平行軌道：

1. **#51 vs #53 (本 PR)** — 兩者都在做 2026-04-26 的優化。#51 的 scope 偏 governance 擴充（D007-D010、outputs templates、KB 選型），本 PR 的 scope 偏 P0 收斂（audit / parity / triage / permissions / CI gate）。差異夠大，理論上可並存，但 README / AUDIT_LOG / context.md 三檔會撞。**建議 owner 先 merge 本 PR 再 rebase #51**，因為本 PR 是 P0 收斂、#51 是擴充。

2. **#31 vs #5 (本 PR Task #5)** — 兩者都在加 PR-required CI checks。本 PR #5 採新增 audit completeness + docs parity 兩支 check 並接到既有 spec-consistency.yml；#31 採全新 workflow `pr-required-taskcard-checks.yml` + 移除舊 workflow + 加 `system/TOOLS_CATALOG.yaml`。後者 scope 大、改動既有 CI 結構。**建議 owner 等本 PR 落地後 close #31**（或挑出 TOOLS_CATALOG 部分另開卡）。

## 統計

- 收斂前：36 open
- A1+A2+A3 關閉：14
- B1+B2+B3 關閉：7
- 已關閉合計：21
- 收斂後 active（含 #53）：16
- 達成 DoD「open PR ≤ 12」：未完全達標（差 4，剩餘皆 needs-owner-review）

## 後續行動

- **本 PR 待完成**：#4 workflow permissions（merge 後可關 #52）/ #5 parity CI + audit gate（落地後 owner 可關 #31）
- **owner 待處理（建議優先順序）**：#28 → #33 → #50 → #35 → 然後 #14/#15/#23/#24/#27/#32/#42/#45/#51 個別決定
