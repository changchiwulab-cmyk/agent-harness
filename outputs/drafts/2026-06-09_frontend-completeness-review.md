# 審查報告：前端作業完整度（frontend/ 治理看板）

- **Task Card**：`20260609-R01`（skill_type: review, risk_level: low）
- **審查對象**：`frontend/`（`index.html` / `app.js` / `styles.css` / `data.json`）+ 產生器 `scripts/generate_frontend_manifest.py` + 對應 Task Cards
- **審查日期**：2026-06-09　**branch**：`claude/busy-ramanujan-4espn8`
- **基準快照**（加入本 review 卡前）：`data.json` = 45 tasks / 2 logs / 7 decisions

---

## 總體評估

**有條件通過。**

已交付的兩塊前端工作（Phase 0 baseline + R7 治理總覽面板）**對自身 DoD 完成度高（F01 11/11、R7 4/4）、且受 CI 漂移檢查保護、實測健康度全綠**。問題不在「已交付的品質」，而在「roadmap 完整度」：原規劃的 Phase 1–3 多數仍散落在尚未合併的 open PR 或未開工，且多張前端相關 PR 互相重疊，存在收斂風險。

審查另發現 1 處**文件與實況漂移（README/index.html 漏列 R7 面板）**，屬低風險，已於本任務一併修正。

| 維度 | 結論 |
|------|------|
| 已交付前端健康度 | ✅ 全綠（drift OK、4 tests 綠、5 panel 齊、CI 已掛護欄） |
| 已交付卡片 DoD | ✅ F01 11/11、R7 4/4（1 條機制不同但達標，見下） |
| roadmap 完整度 | ⚠️ 5 項規劃僅 2 項落地（Phase 0 + R7 ≈ 40%）；Phase 1 在途、Phase 2/3 未開工 |
| 文件一致性 | 🔧 README/index.html 漏列治理總覽面板 → 本次已修 |
| 治理風險 | ⚠️ 5+ 張前端 open PR 重疊（#77/#80/#94/#90/#81），需人工收斂 |

---

## 通過項

### A. 現況健康度（實測）
- **漂移檢查**：`python3 scripts/generate_frontend_manifest.py --check` → `OK`。
- **產生器單元測試**：`python3 scripts/test_generate_frontend_manifest.py` → 4 tests 綠（empty / multi-project / idempotent / drift）。
- **資料唯一源**：`frontend/manifest.js` 已移除；前端僅 `fetch('./data.json')`（`app.js:25`），無 YAML 解析。
- **5 個 panel 皆存在**（`index.html`）：Summary `#summaryCards`(22) / 治理總覽 `#overviewPanel`(26) / Task 清單 `#taskList`(32) / Decision Timeline `#timeline`(37) / Logs `#logBoard`(43)。
- **CI 護欄存在**：`.github/workflows/spec-consistency.yml:48-52`（frontend manifest tests + drift check）。
- **多 project 友善**：decisions glob = `memory/active_projects/*/decisions/*.yaml`（`generate_frontend_manifest.py:24`）。
- **XSS 防護**：所有渲染走 `escapeHtml()`（`app.js:5-13`）。

### B. 設計面做得好的地方
- `build_overview` 純由「已蒐集的 tasks+logs」計算（`generate_frontend_manifest.py:117-143`），不額外讀檔、root-parameterized、輸出 byte-identical → 漂移檢查可靠、成本低。
- 產生器輸出 `sort_keys=True` + 固定 `indent`（`:158`），確保 idempotent，CI 漂移檢查不會偽陽性。

---

## 必須修改

（審查時發現 1 項，屬低風險，**本任務已修正**）

- **[README.md:174-178 / index.html:12] 文件漏列 R7 面板**：`index.html` 已有「治理總覽」與 Summary 概況卡 5 個 panel，但 README「前端動態介面」段只列 3 個（Task 清單 / Logs / Decision Timeline），header 副標亦未含治理總覽 → 文件與實況漂移。
  **處置**：已更新 README panel 清單為 5 項並補述治理總覽內容；index.html 副標補「治理總覽」。`data.json` 重生、drift `--check` 綠。

---

## 建議修改（不在本任務範圍，列為後續）

- **[roadmap] Phase 1 收斂**：Gate/Approval/Failure 視覺化（F02）目前散在 **PR #77（Phase 1 error dashboard）/ #80（Phase 0 closure + hardening）**，建議擇一收斂後合併，避免雙軌。
- **[roadmap] Phase 2 Context Budget 儀表板**：尚未開工。`scripts/check_context_budget.rb` 已有資料源，可比照 R7 以既有 manifest 計算後新增 panel。
- **[roadmap] Phase 3 Decision Graph**：目前僅平面 Decision Timeline（`app.js:91-102`），尚無依賴關係圖；`decisions/*.yaml` 已有 `related_task` 欄位可作邊。
- **[治理] open PR 收斂**：前端相關 open PR 重疊（#94 workflow 視覺化頁、#90/#81 前後端對齊、#77/#80 F02），建議由人工排序合併順序，降低 rebase/conflict 成本。
- **[紀錄] F01 卡片 status**：`tasks/2026-04-27_frontend-platform-phase0.yaml` 產物齊備但 status 仍 `review`。**屬人工 merge 決策，本任務不自動翻 done**；待 Phase 0 正式併入 main 後再更新。

---

## Roadmap 缺口表

規劃來源：`tasks/2026-04-27_frontend-platform-phase0.yaml`（context 段定義 Phase 0–3）+ 自我評估 R7。

| 項目 | 卡片 | 本 branch 狀態 | 對應 open PR | 缺口 |
|------|------|----------------|--------------|------|
| Phase 0 baseline（data.json/測試/CI 護欄） | `20260427-F01` | ✅ 產物齊備（card status 仍 review） | #80 hardening | 待人工 merge 決策 |
| R7 治理總覽面板 | `20260529-011` | ✅ done（經 #88 併入） | — | 無 |
| Phase 1 Gate/Approval/Failure 視覺化 | F02 | ⏳ 不在本 branch | #77、#80 | 在途，需收斂 |
| workflow 視覺化頁（人看圖/agent 讀結構） | — | ⏳ 不在本 branch | #94 | 在途 |
| 前後端任務資料自動對齊 | — | ⏳ 不在本 branch | #90、#81 | 在途 |
| Phase 2 Context Budget 儀表板 | — | ❌ 未開工 | — | 未排程 |
| Phase 3 Decision Graph | — | ❌ 僅平面 timeline | — | 未排程 |

**完整度估算**：規劃 5 大項（Phase 0–3 + R7）中，**已落地 2 項（Phase 0、R7 ≈ 40%）**，1 項在途（Phase 1），2 項未開工（Phase 2、3）。

---

## Definition of Done 逐條確認（已交付卡片）

### `20260427-F01` Phase 0 baseline — 11/11 通過

- [x] 1 generator 輸出 data.json（PyYAML 序列化，前端不解析 YAML）：通過 — `generate_frontend_manifest.py:61-64,157-158`、`app.js:25`
- [x] 2 app.js 改讀 ./data.json、移除 regex parser、保留篩選與 summary/timeline/log panel：通過 — `app.js:25,45-61`，三 panel 俱在
- [x] 3 manifest.js 移除：通過 — `frontend/` 已無此檔
- [x] 4 decisions glob 多 project 友善：通過 — `generate_frontend_manifest.py:24`
- [x] 5 新增 generator 測試 ≥3 case（空/多 project/idempotent）：通過 — `test_generate_frontend_manifest.py`（4 case）
- [x] 6 CI 漂移步驟：**通過（機制不同）** — DoD 原述「generate && git diff --exit-code」，實作改用 `--check` 模式（`spec-consistency.yml:52`），漂移偵測效果等價且更乾淨
- [x] 7 run_frontend.sh CLI（--no-generate/--help/--version/port）不變：通過 — `run_frontend.sh:5,13-20`
- [x] 8 README 前端段去 manifest、改述 data.json 與漂移：通過 — `README.md:179-184`（本次另補 panel 清單）
- [x] 9 validate_task_card exit 0 + pytest 綠 + spec-consistency 綠：通過 — 本次實測三者皆綠
- [x] 10 phase0-summary 草稿：通過 — `outputs/drafts/20260427-F01_phase0-summary.md` 存在
- [x] 11 AUDIT_LOG 新增 1 筆：通過 — `logs/AUDIT_LOG.md:672`

### `20260529-011` R7 治理總覽面板 — 4/4 通過

- [x] 1 build_overview（task 狀態/skill/風險 + run 狀態 + gate tally）、build() 輸出 overview：通過 — `generate_frontend_manifest.py:117-143,153`
- [x] 2 test_empty_repo 含 overview 空值、其餘測試綠：通過 — `test_generate_frontend_manifest.py:35-48` + 4 tests 綠
- [x] 3 index.html 治理總覽 section、app.js renderOverview 以 .cards 渲染、data.json drift 綠：通過 — `index.html:24-27`、`app.js:115-138`、drift OK
- [x] 4 全套 CI-equivalent 綠、未動 system/：通過 — 實測綠；`git diff` 未觸及 `system/`

---

## 本任務驗證紀錄

| 檢查 | 指令 | 結果 |
|------|------|------|
| Task Card schema | `python3 system/validate_task_card.py tasks/2026-06-09_frontend-completeness-review.yaml` | ✅ 通過 |
| Spec consistency | `ruby scripts/check_spec_consistency.rb` | ✅ OK |
| Frontend drift | `python3 scripts/generate_frontend_manifest.py --check` | ✅ OK |
| Generator tests | `python3 scripts/test_generate_frontend_manifest.py` | ✅ 4/4 |
| Context budget | `ruby scripts/check_context_budget.rb` | ✅ within limit |

**結論**：已交付前端工作健康、DoD 完整；roadmap 完整度約 40%，缺口集中在 Phase 1–3 與 open PR 收斂（屬後續排程，非本次範圍）。本次已修正唯一的文件漂移。
