# O05 — CI 健檢：Task Card expected_output 存在性

- Task ID：20260503-O05
- 日期：2026-05-03
- 狀態：實作完成 + strict 上線（DoD 接受 CI 暫紅燈）

## TL;DR

新增 CI 健檢 `check_task_output_exists.py`：每張 status ∈ {done, review} 的 Task Card，其 `expected_output.location/filename` 必須在 working tree 中存在；缺失即 exit 1。已在 spec-consistency workflow 新增 step（緊接於 frontend manifest drift check 之後）。

首次上線即攔到 7 張漂移卡（4 張 AI-proposal + 3 張 tools-inventory），全部源自 pre-2026-04-11 的 `outputs/drafts/` gitignore 規則。其中 4 張將由 O04 archive 處理；3 張 tools-inventory 將由後續 A03 mini-Go/No-Go 處理。CI 在這段期間會持續 red，是預期行為（健檢確實在做事）。

## 實作摘要

### 程式碼

| 檔案 | 行數 | 用途 |
|---|---:|---|
| `scripts/check_task_output_exists.py` | 76 | 健檢主程式 |
| `scripts/test_check_task_output_exists.py` | 116 | 5 個 unit test cases |
| `.github/workflows/spec-consistency.yml` | +5 | 兩個新 step（tests + check）|

### 掃描範圍

- 包含：`tasks/20*.yaml`（頂層）
- 排除：`tasks/archived/`、`tasks/examples/`、所有非 `20*` 開頭檔
- 觸發 status：`done`、`review`
- 略過 status：`pending`、`in_progress`、`checkpoint`、`failed`
- 略過 format：`multi`（多輸出卡無法以單一路徑驗證）

### 規則邏輯（精簡版）

```
for each tasks/20*.yaml:
  if status not in {done, review}:        skip
  if expected_output.format == "multi":   skip
  target = location + filename
  if not target.exists():                 record missing

if any missing: print + exit 1
else:           print OK + exit 0
```

### Unit Test Cases

| Case | 預期 |
|---|---|
| status=done + 輸出存在 | 不被 flag |
| status=review + 輸出缺失 | 被 flag |
| status=review + 在 archived/ 目錄下 | 自動跳過（glob 不掃 archived/）|
| status=pending + 輸出缺失 | 自動跳過（不在 target status 內）|
| status=done + format=multi + 輸出缺失 | 自動跳過（多輸出卡）|

5/5 全綠。

## 首次上線結果（main HEAD）

```
FAIL: expected_output files missing for done/review Task Cards:
  - tasks/2026-04-04_ai-era-solo-business-proposal-review.yaml -> outputs/drafts/ai-era-solo-business-proposal-review.md
  - tasks/2026-04-04_ai-era-solo-business-proposal.yaml        -> outputs/drafts/ai-era-solo-business-proposal.md
  - tasks/2026-04-04_ai-era-solo-business-strategy.yaml        -> outputs/drafts/ai-era-solo-business-strategy.md
  - tasks/2026-04-04_proposal-fix-v2.yaml                      -> outputs/drafts/ai-era-solo-business-proposal-v2.md
  - tasks/2026-04-04_tools-inventory-fix.yaml                  -> outputs/drafts/solo-company-tools-inventory-v2.md
  - tasks/2026-04-04_tools-inventory-research.yaml             -> outputs/drafts/solo-company-tools-inventory.md
  - tasks/2026-04-04_tools-inventory-review.yaml               -> outputs/drafts/tools-inventory-review-report.md
```

7 張漂移全部源自 commit `f32ba4a` 之前 `.gitignore` 攔截 `outputs/drafts/` 的時期。

## 預期攔截場景（未來）

1. **新 .gitignore 規則誤攔輸出目錄** — drafts 路徑被加進 .gitignore 但忘記從追蹤中移除
2. **誤刪 draft 但忘了改 Task Card status** — 健檢會立刻 red CI
3. **Task Card 改 expected_output.filename 但檔名沒改** — schema 與 filesystem 對不齊
4. **歸檔流程漏改 status 或漏移檔** — 雖然 archived/ 會跳過，但若只改 status 不搬檔就會被 flag

## 與其他檢查的關係

| 檢查 | 負責 |
|---|---|
| `validate_task_card.py` | 單一 Task Card schema（欄位、值域）|
| `check_spec_consistency.rb` | 跨 spec 一致性（GLOBAL_RULES、PERMISSIONS、GATE 對齊）|
| `generate_frontend_manifest.py --check` | data.json 漂移（generator 與 source 對齊）|
| **`check_task_output_exists.py`（新）** | **schema 與 filesystem 對齊（Task Card 與 outputs 對齊）**|

四者互不重疊。

## 已知限制

- 對 `format: "multi"` 卡完全跳過 — 這類卡的多路徑輸出目前沒有 schema 化的驗證方式。後續若有需要，可擴 schema 為 `outputs: [{...}, {...}]` 列表後一併驗證
- 只查存在性、不查內容（不空檔、不格式正確）— 是設計取捨，避免與 schema validator 重疊
- Working tree 等同 git ref：未追蹤但實際存在的檔案會通過。若要更嚴格（必須 git 追蹤），可加 `git ls-files --error-unmatch`，但會增加 CI 時間且對開發中狀態不友善

## 後續

- O04（已開）archive 4 張 AI-proposal 後，CI 仍 red（3 張 tools-inventory 未處理）
- A03（待開）對 tools-inventory 三張做 mini-Go/No-Go，再決定 archive 或重產
- A03 完成、tools-inventory 處理完後，CI 預期回到全綠
