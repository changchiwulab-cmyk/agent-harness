# 調查報告：2026-04-04 組 7 個 expected_output 檔案缺失

> Task Card: `20260417-O02`（completeness-sweep）
> 建立日期：2026-04-17
> 狀態：調查完成，待使用者決策

---

## 1. 背景

完整度檢查發現 `outputs/drafts/` 目錄與 `tasks/2026-04-04_*.yaml` 宣稱的 `expected_output` 嚴重不一致。本報告釐清真相，不做修復動作。

---

## 2. 事實（已知）

### 2.1 本機檔案系統實況

`outputs/drafts/` 目錄僅有 **2 個實際檔案**（加 `.gitkeep`）：

| 檔名 | 大小 | 最後修改 |
|------|------|---------|
| `analysis-create-task-card-permission.md` | 3,453 bytes | 2026-04-17 06:32 |
| `retro-2026-04-15.md` | 4,570 bytes | 2026-04-17 06:32 |
| `.gitkeep` | 0 bytes | 2026-04-11 07:51 |

`outputs/reports/` 目錄：空（僅 `.gitkeep`）。

### 2.2 Task Card 宣稱的 7 個 expected_output

所有 7 張 2026-04-04 卡皆宣稱輸出到 `outputs/drafts/`：

| Task Card | expected_output.filename | 本機存在？ | git 歷史曾追蹤？ |
|-----------|--------------------------|-----------|-----------------|
| `20260404-R01` (tools-inventory-research) | `solo-company-tools-inventory.md` | ❌ | ❌（0 次 add） |
| `20260404-R02` (tools-inventory-review) | `tools-inventory-review-report.md` | ❌ | ❌ |
| `20260404-O01` (tools-inventory-fix) | `solo-company-tools-inventory-v2.md` | ❌ | ❌ |
| `20260404-S01` (ai-era-solo-business-strategy) | `ai-era-solo-business-strategy.md` | ❌ | ❌ |
| `20260404-W01` (ai-era-solo-business-proposal) | `ai-era-solo-business-proposal.md` | ❌ | ❌ |
| `20260404-RV01` (proposal-review) | `ai-era-solo-business-proposal-review.md` | ❌ | ❌ |
| `20260404-O02` (proposal-fix-v2) | `ai-era-solo-business-proposal-v2.md` | ❌ | ❌ |

驗證指令：
```bash
for fn in <上述檔名>; do
  git log --all --oneline --diff-filter=A -- "outputs/drafts/$fn" | wc -l
done
# 全部皆 0
```

### 2.3 `.gitignore` 實際內容

```
# macOS
.DS_Store

# 敏感檔案
*.env
*.key
*.pem
*.credentials
scripts/__pycache__/
```

**`outputs/drafts/` 未被 `.gitignore` 排除**。

### 2.4 既有 AUDIT_LOG 中的不實註記

`logs/AUDIT_LOG.md` 中 `task_id: "20260404-R01"` 的 notes 欄寫：

> "…outputs/drafts/ 因 .gitignore 不入版控，Task Card 狀態記錄在 YAML。"

此陳述與 2.3 的事實矛盾。

---

## 3. 合理推論

最可能的情境（按可能性排序）：

1. **artifacts 從未實際寫入檔案系統**：7 張 task card 的執行階段僅產出「概念摘要」寫進 `result_summary`，未實際執行 `file_write` 產出 markdown。這與 `actual_tool_calls: 3-6` 的低數值一致（寫作任務通常需 ≥ 8 工具呼叫）。
2. **artifacts 曾存在於本機但被清理**：較不可能。若如此，git 歷史中至少應有一次 `git add`（除非全程未 staged）。
3. **artifacts 存在於另一 workspace / 分支**：`git log --all` 涵蓋所有分支，無匹配紀錄，排除此情境。

`R01` 的 `.gitignore` 註記推測為誤記：可能作者看到 `outputs/drafts/.gitkeep` 前的空目錄狀態，誤以為被忽略；或與其他專案的慣例混淆。

---

## 4. 待驗證（需使用者確認）

下列事項超出本任務權限範圍，列出供使用者決策：

1. **7 張 task card 的 `status: done` 是否仍成立？**
   - 選項 A：維持 done，承認當時僅做到「口頭摘要」等級，`result_summary` 即為交付物。
   - 選項 B：降級為 `partial`（需先在 validator 加入此 status 值）。
   - 選項 C：重新執行 7 張任務，實際產出 markdown 檔案。

2. **是否需要補寫這 7 個 markdown 檔案？**
   - 使用者手上若有草稿，可以直接投放到 `outputs/drafts/`。
   - 若無，Option C（重新執行）會觸發大量 token + 工具呼叫（估 7 × 20K ≈ 140K tokens，高於 COST_POLICY.md 單任務 32K 上限甚多，需多張 task card 切分）。

3. **R01 AUDIT_LOG 的誤記如何處理？**
   - 本任務（A3）採「追加 correction note 不改寫歷史」作法。若使用者偏好直接改寫原句，需另授權（違反審計不可篡改原則）。

---

## 5. 高風險假設

- 假設 `actual_tool_calls` 數字可信。若該欄位亦是概念填寫、未反映真實呼叫，則「artifacts 未實際寫入」這個推論仍成立（反而更肯定）。
- 假設 git 歷史完整。若曾有 reset --hard 或 branch 被刪除，可能漏查；但本專案 commit 量小（< 10），此風險低。

---

## 6. 本任務不做

- 不降級任何 task card status
- 不補寫 7 個 markdown 檔案
- 不改寫既有 AUDIT_LOG 舊 entry

上述決策交付下一張 task card 處理。
