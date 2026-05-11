# Audit Draft — N12 Batch Merge PR #70 + #72 onto main

**Status：DRAFT — squash 結果已於 worktree 準備完成，待人工授權 force-push + retarget + squash merge**

**Task Card：** `tasks/2026-05-11_n12-batch-merge-70-72.yaml`
**準備日期：** 2026-05-11
**執行者：** Claude (agent-harness session)
**Risk level：** high（force-push + main 改動 + 跨 PR 拓樸重整）

---

## 1. 背景時序

| Step | 動作 | 結果 |
|---|---|---|
| 1 | 使用者最初授權「#69 → #70 → #72 → #71 全 squash」 | 批次 merge 計畫 |
| 2 | #69 squash merged 進 main | main HEAD = `974c4820d09bd63b76aa203d0a853edb14abd421` |
| 3 | 嘗試自動 squash-merge #70 與 #72 | GitHub `mergeable_state: dirty` 失敗（6 衝突，因為 #69 已帶入大量同檔修改） |
| 4 | Worktree 試算 squash | 確認 #72 = #70 + 1 commit，是 strict superset |
| 5 | 策略修正：skip #70（superseded），把 #72 squash 進 main | 本 audit 對應此修正方案 |

## 2. 涉及 commit SHAs

| Ref | SHA | 說明 |
|---|---|---|
| `origin/main` | `974c4820d09bd63b76aa203d0a853edb14abd421` | 已含 #69 squash |
| `origin/claude/setup-agent-governance-v0.1.0-87beH` (#70 head) | `e756959a5f7ae24fda2c998012cd5885d4c8cfcc` | 25 commits since branch base |
| `origin/claude/plugin-v0.1.0-hardening-codex-p1p2` (#72 head) | `0dd128f3e8a33568a4836a7bba0f1d6d55cd3dfd` | #70 + Codex P1+P2 hardening |
| Worktree squash result | `<not committed, signing infra blocked>` | Staged in `/tmp/wt-rebase-70` branch `squash-72` |

## 3. 衝突解析

| 檔案 | 策略 | 理由 |
|---|---|---|
| `outputs/drafts/agent-governance-bootstrap/hooks/post_task_use.py` | take theirs (#72) | #72 含完整 P1 (risk gate 無短路) + P2 (DoD type guard)；main 版尚無 |
| `outputs/drafts/agent-governance-bootstrap/hooks/test_hooks.py` | take theirs (#72) | #72 +2 regression tests cover P1+P2 |
| `outputs/drafts/agent-governance-bootstrap/CHANGELOG.md` | take theirs (#72) | #72 加 `[Unreleased]` 段記錄 hardening |
| `scripts/governance_metrics.py` | take theirs (#72) | #72 加強 audit log YAML 解析；保留 #69 已有 `load_task_cards` 嚴格 raise |
| `scripts/test_governance_metrics.py` | take theirs (#72) | #72 對應新 audit 解析的 +2 test |
| `frontend/data.json` | 重生 (`scripts/generate_frontend_manifest.py`) | manifest 自動產出，避免手動合衝突 |

**淨 diff：** 9 files changed, +546 insertions, -9 deletions

**ADDED 檔（main 上原本不存在）：**
- `outputs/drafts/2026-05-09_n06-bootstrap-runbook.md`（#70 unique，N06 bootstrap runbook）
- `tasks/2026-05-09_harness-plugin-switch.yaml`（#70 unique，N06b card）
- `tasks/2026-05-09_n11-plugin-hardening-codex-p1p2.yaml`（#72 unique，N11 card）

## 4. 驗證結果（全綠）

| Gate | 命令 | 結果 |
|---|---|---|
| Plugin hooks self-tests | `python3 -m unittest hooks.test_hooks` | 14/14 OK |
| Plugin validators self-tests | `python3 -m unittest validators.test_validators` | 14/14 OK |
| Governance metrics tests | `python3 -m unittest scripts.test_governance_metrics` | 21/21 OK |
| Task Card validation (N06b) | `python3 system/validate_task_card.py tasks/2026-05-09_harness-plugin-switch.yaml` | ✅ |
| Task Card validation (N11) | `python3 system/validate_task_card.py tasks/2026-05-09_n11-plugin-hardening-codex-p1p2.yaml` | ✅ |
| Spec consistency | `ruby scripts/check_spec_consistency.rb` | OK |
| Frontend manifest | `python3 scripts/generate_frontend_manifest.py --check` | OK: up to date |

## 5. 待人工執行步驟（signing infra 恢復後）

```bash
# (a) Force-push squash result 到 #72 head branch
cd /tmp/wt-rebase-70
git push --force-with-lease=claude/plugin-v0.1.0-hardening-codex-p1p2:0dd128f3e8a33568a4836a7bba0f1d6d55cd3dfd \
  origin squash-72:claude/plugin-v0.1.0-hardening-codex-p1p2

# (b) 透過 GitHub MCP 把 #72 base 從 #70 branch 改為 main
#     (update_pull_request: base="main")

# (c) Squash merge #72 進 main
#     (merge_pull_request: merge_method="squash")

# (d) Close #70 並留 comment 指 superseding squash commit SHA
#     (issue_write / pull_request_write: state="closed",
#      body="Superseded by PR #72 squash commit <sha>; all #70 content (N06 runbook + N06b card) included.")

# (e) 把本 audit draft 升正寫入 logs/AUDIT_LOG.md
```

## 6. Rollback 計畫

見 Task Card `tasks/2026-05-11_n12-batch-merge-70-72.yaml` § rollback。重點：

- Force-push 可逆（保留原 SHA `0dd128f` 於本 audit）
- Base retarget 可逆（直接 PATCH 回原 base）
- Squash merge 不可直接逆轉 → 需 `git revert <merged-sha>`，PR 無法 reopen
- #70 close 完全可逆

## 7. 已知遺留

- **PR #71** 尚未處理：待本 batch merge 進 main 後，PR #71 需 rebase。預期同樣有 plugin tree 衝突，另開 N13 card 處理。
- **Signing infra**：本 session `environment-runner code-sign` 持續回 400 `missing source`，未能確認服務是否已恢復。

---

**本草稿待 human 審核後升正至 `logs/AUDIT_LOG.md` 並寫入 `logs/runs/2026-05-11_n12.yaml`（依 `system/EXECUTION_LOG_SCHEMA.yaml`）。**
