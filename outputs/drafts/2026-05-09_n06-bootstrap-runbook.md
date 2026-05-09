# N06 bootstrap runbook — agent-governance v0.1.0

- Task: `20260509-N06`（DoD #1-#5/#7/#9 已完成；本 runbook 對應 #6/#8 + 真實 repo 建立）
- Decision Log: D007（agent-governance / Apache-2.0 / Private / 獨立 repo）
- 對象：使用者本人，在本機（具 `gh` CLI + agent-governance owner 推送權）執行
- 預期耗時：5–10 分鐘
- 失敗降版：刪除新建 repo + 還原本機 `~/work/agent-governance/`，agent-harness 不受影響（沒有任何切換動作在本 runbook 範圍）

> **本 runbook 只負責 bootstrap 外部 repo。** agent-harness 端 CLAUDE.md / `.claude/settings.json` 切換引用屬 ask 級權限，會由另一張 Task Card（已建立，見 §6）配合下個 PR 處理。

---

## 0. 前置檢查（30 秒）

> **2026-05-09 校正**：hooks 實際 12 tests（含 `test_rule_gate_rejects_string_allowed_tools`，原文 11 為手動點數錯誤），總計 26。下方數字已更新。

```bash
# (a) 你登入的 GitHub 帳號 / org 對 agent-governance 有 repo 建立權
gh auth status
gh api user -q .login   # 預期：你或 changchiwulab-cmyk org 成員

# (b) bootstrap 檔樹完整且通過 plugin 自有 tests
cd ~/path/to/agent-harness
ls outputs/drafts/agent-governance-bootstrap/   # 應看到 plugin.json README.md LICENSE CHANGELOG.md commands/ hooks/ schemas/ validators/ .github/
( cd outputs/drafts/agent-governance-bootstrap && python3 -m unittest hooks.test_hooks validators.test_validators -v )
# 預期：26 tests OK（hooks 12 + validators 14）
```

任一步失敗 → 停下來回報，不繼續。

---

## 1. 在 GitHub 建 private repo

```bash
gh repo create changchiwulab-cmyk/agent-governance \
  --private \
  --description "Governance layer for Claude Code: Task Card contracts, Audit Log, Decision Log, Gate Policy, Failure Taxonomy." \
  --license apache-2.0
```

> `--license apache-2.0` 會自動產生 LICENSE 檔，我們本機 LICENSE 內容一致，commit 時會直接覆蓋（或留新生成的；兩者都是 Apache-2.0 完整文本，不衝突）。
> 若 `gh repo create` 拒絕（撞名 / 權限），先 `gh repo view changchiwulab-cmyk/agent-governance` 確認狀態，再決定是否需要改 owner。

驗證：

```bash
gh repo view changchiwulab-cmyk/agent-governance --json visibility,isPrivate,licenseInfo
# 預期：{"visibility":"PRIVATE","isPrivate":true,"licenseInfo":{"key":"apache-2.0",...}}
```

---

## 2. Clone 空 repo + 搬入 bootstrap 檔樹

```bash
cd ~/work    # 或你習慣的工作目錄
gh repo clone changchiwulab-cmyk/agent-governance
cd agent-governance

# 從 agent-harness 的 drafts 搬入（含隱藏檔，不含 __pycache__）
rsync -av \
  --exclude='__pycache__' \
  ~/path/to/agent-harness/outputs/drafts/agent-governance-bootstrap/ ./
```

驗證：

```bash
ls -la
# 應看到：plugin.json README.md LICENSE CHANGELOG.md commands/ hooks/ schemas/ validators/ .github/

# README、LICENSE、CHANGELOG 應該是 bootstrap 版本（不是 gh repo create 自動生成的占位版）
head -5 README.md           # "# agent-governance"
head -3 CHANGELOG.md        # "# Changelog"
grep -c 'Apache License' LICENSE   # 應 >= 1
```

---

## 3. 跑 plugin 自身 tests + manifest sanity check

```bash
python3 -m unittest hooks.test_hooks -v
python3 -m unittest validators.test_validators -v
python3 -c "import json; json.load(open('plugin.json')); print('plugin.json OK')"
python3 -c "
import yaml; from pathlib import Path
for f in sorted(Path('schemas').glob('*.yaml')):
    d = yaml.safe_load(f.read_text())
    assert isinstance(d, dict) and ('required' in d or 'properties' in d), f
    print('OK', f.name)
"
```

預期全綠（hooks 12 + validators 14 + plugin.json + 4 schemas）。任一失敗 → 停下來，回報後再決定是否繼續。

---

## 4. 初次 commit + tag v0.1.0 + push

```bash
git add .
git status   # 確認 staged 內容（應該是全部 bootstrap 檔，gh repo create 預設只有 LICENSE 會被覆蓋）

git commit -m "$(cat <<'EOF'
chore: v0.1.0 skeleton bootstrap from agent-harness PR #69

- plugin.json: 5 commands / 4 schemas / 2 hooks / 2 validators
- hooks: pre_tool_use (deny-list runtime guard) + post_task_use (4-stage gate runner)
- validators: validate_task_card + check_audit_format (with tests)
- schemas: task_card / decision_log / execution_log / failure_taxonomy
- CI: hooks tests + validators tests + manifest sanity

Decision Log: agent-harness D007 (agent-governance / Apache-2.0 / Private / standalone repo)
EOF
)"

git tag -a v0.1.0 -m "v0.1.0 skeleton bootstrap"
git push -u origin main
git push origin v0.1.0
```

驗證：

```bash
gh release list --repo changchiwulab-cmyk/agent-governance   # tag 應在
gh run list --repo changchiwulab-cmyk/agent-governance --limit 3
# CI workflow 應觸發（push 到 main）
```

CI 跑完後再次驗證：

```bash
gh run watch --repo changchiwulab-cmyk/agent-governance
# 預期：Hook tests / Validator tests / sanity 全綠
```

CI 失敗的話最常見是 `pip install pyyaml` 之外漏 deps；先看 workflow log，必要時補 deps 後 amend commit + force push 到 main（你是唯一使用者，可接受）。

---

## 5. 從 GitHub 建 v0.1.0 release（選擇性）

private repo 內部用其實不需要 release page，但有 release 對下個 session 引用 plugin tag 比較直接：

```bash
gh release create v0.1.0 \
  --repo changchiwulab-cmyk/agent-governance \
  --title "v0.1.0 — skeleton bootstrap" \
  --notes-file CHANGELOG.md \
  --prerelease
```

`--prerelease` 是因為 v0.1.0 是內部驗證版，符合 D007 的「v0.2.0 stable 後再轉 public」決策。

---

## 6. 完成後的下一步

回到 agent-harness（這個 repo），開新 PR 完成 DoD #6 切換引用。對應 Task Card：

- `tasks/2026-05-09_harness-plugin-switch.yaml`（risk=medium，本 PR 一併建立）
- 該卡 DoD：CLAUDE.md 註明 plugin 依賴 + `.claude/settings.json` hook 路徑指向 plugin + agent-harness 自身 CI 在 plugin 缺席仍綠

完成切換後，agent-harness 的 `system/validate_task_card.py` / `scripts/permissions_guard.py` 會留作 fallback；雙寫漂移風險到 plugin v0.2.0 stable 後再做大清理（屬遷移卡，非本批）。

---

## 7. 中止 / 回滾

| 場景 | 動作 |
|------|------|
| §1 建 repo 後想取消 | `gh repo delete changchiwulab-cmyk/agent-governance --yes`（private 無外部影響） |
| §4 commit 但 CI 紅 | `git revert HEAD` 或在 main amend；private repo 容許 force push |
| §5 release 建錯 | `gh release delete v0.1.0 --yes && git tag -d v0.1.0 && git push origin :v0.1.0` |
| 整體想重來 | 刪本機 `agent-governance/` + `gh repo delete`，回到 agent-harness 原狀（沒任何 agent-harness 端動作，故乾淨） |

---

## 8. 不在本 runbook 範圍

- **agent-harness CLAUDE.md / settings.json 修改** — 屬 ask 級權限，需另一張 Task Card（已備）+ 你的核准。
- **plugin v0.1.x 後續修改** — bootstrap 後，plugin repo 自身的 issue/PR 在 agent-governance 內處理，不再由 agent-harness 代管。
- **轉 public** — 待 v0.2.0 stable，由 D007 revisit_trigger 觸發新決策。
