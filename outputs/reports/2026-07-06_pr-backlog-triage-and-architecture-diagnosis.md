# Open PR 積壓分析 + 架構最大缺點診斷（2026-07-06）

> 正式報告 ｜ 產出方式：全量實測（非抽樣）｜ 對應收斂 PR：本報告所在 PR
> 方法：抓取全部 75 個 open PR（#14–#124），以 `git merge-tree` 逐一實測與 main 的衝突，
> 再模擬「按時間序連續合併」找出互撞點；比對各 PR 檔案足跡找重複工作。

---

## 一、實測結果（核心數據）

- 分析當下 main 停在 #112 合併；**75 個 open PR，最舊 #14（2026-04-11）已積壓近 3 個月**。
- 對 main 個別測試：舊 PR（#14–#87 段）29 個衝突；#89 之後 35 個「個別乾淨」。
- **連續合併模擬**：只有 12 個 PR 能按序全綠 → `#15 #27 #28 #35 #50 #52 #64 #73 #74 #85 #86 #91`。
  其餘每一個都在前一個合併後開始互撞，衝突點高度集中：
  **`frontend/data.json`（生成物入庫）與 `logs/AUDIT_LOG.md`（單檔 append）**，
  其次 CLAUDE.md / README / TASK_CARD_TEMPLATE。
- 重複工作實證：
  - **#113 #115 #116 #117 #118 五個 PR 各自實作了同一個 `scripts/run_evals.py` + 測試**
    （「架構補齊」同題五做，2026-06-26 ~ 06-30 五天內）；#114 是同題的純規劃版。
  - **#123 vs #124**：兩天內兩次「Fable 5 制度化」重寫 CLAUDE.md + system 核心，
    連封存路徑都不同（`system/_archive/` vs `archive/pre-fable5/`）。
  - **#105 vs #121**：兩組互不相識的「R11–R14」，治理編號系統碰撞。
  - **#98 / #107 ⊂ #106**：R9、R10 各自單獨做了一次，又被 #106 合做一次。

## 二、75 個 PR 處置決定（五類）

### A. 依序合併（12 個，已本地驗證連續全綠後執行）
`#15 #27 #28 #35 #50 #52 #64 #73 #74 #85 #86 #91`
合併後由本收斂 PR 重生成 `data.json` / `AUDIT_LOG.md`，維持 CI 綠。

### B. 高價值工程 PR — 逐一合入收斂分支（2026-07-07 執行結果）
實際整合順序與結果（全部經完整 CI 等價套件驗證後合入 #129 分支）：
1. **#103** 衍生產物自動對齊 ✅
2. **#96** state drift + 硬規則 runtime 化 ✅（+修 fixture：main 的 validator 已要求 max_tool_calls）
3. **#122** 文件實作對齊 ✅（+修 #122 三條新 deny 規則缺 permission_key、匯入即 crash 且不啟用的問題）
4. **#100** 驗證閉環 ✅（+修 3 個 drill fixture 同類 schema 落後問題）
5. **#106** R9+R10 ✅（NATIVE_OVERLAP 的 stale_after_days 與 revisit_interval_days 兩 key 並存，各供其 script 使用）
6. **#89** Opus 4.8 檢視 ✅（GLOBAL_RULES 失敗模式數以 taxonomy 實數為準；4 個 skill 描述取較豐富版）
7. **#118** G-A 輸入防護 + G-B eval runner ✅（FAILURE_TAXONOMY 增至 17 種含 SEC-05/06；check_spec_consistency 補 state/ resume 驗證段）
8. **#121** R11/R12 批准覆蓋率 + 參照完整性 ✅（其 section 編號與既有 7-10 撞號，重編為 11/12）

**#105 不合併**（見 C 類新增列：與 #96 同目標重複實作，#96 勝出）。
整合過程共修 5 處測試破裂，全部同一類根因：**PR 個別對舊 main 是綠的，main 前進後共用的 validator 變嚴，fixture/接線落後**——正是「無整合平面」缺點的微觀重演。
**#124 合併前需使用者明確確認**（重寫 CLAUDE.md = 改 harness 開機行為，屬 `ask`）。

### C. 重複系列 — 擇一保留
| 系列 | 保留 | 關閉 | 理由 |
|------|------|------|------|
| 架構補齊（eval harness 五做） | #118 | #113 #114 #115 #116 #117 | 五份 `run_evals.py` 只能活一份；#117 記憶層/Skill 註冊表差異點另開 task card |
| Fable 5 制度化 | #124（待確認） | #123 | 都重寫 CLAUDE.md，取新棄舊 |
| R9/R10 | #106 | #98 #107 | #106 = 兩者合集 |
| 模型路由 | 視 #124 決定 | #90（若 #124 合入） | DISPATCH_POLICY 取代 workflow 路由 |
| **硬規則 runtime 強制化（整合階段新發現）** | **#96** | #105 | 兩者並行實作同一目標：#96 = gate_check / failure_counter / task_card_guard；#105 = gate_runner / failure_tracker / write_guard。#96 已整合、測試綠、乾淨重用 validate_task_card；#105 視為被取代，其獨有的 `20260620-D008` 決策記錄 + R14 enforcement 文件可 salvage。**此重複在原 triage（個別對舊 main 測）未顯現，是整合階段才暴露的 in-flight 分支發散案例。** |

### D. 報告/測試類（15 個）— cherry-pick 報告檔進彙整、關閉原 PR
`#92 #93 #94 #95 #97 #99 #101 #102 #104 #108 #109 #110 #111 #119 #120`
（#99 #101 #104 帶 system/ 改動，逐一過目後決定。）

### E. 直接關閉（29 個：過時、已被 main 取代、或結構錯誤）
`#14 #23 #24 #31 #32 #33 #42 #45 #51 #53 #54 #56 #59 #60 #61 #62 #65 #66 #75 #76 #77 #78 #79 #80 #81 #82 #83 #84 #87`
- #76 是反向 PR（main → feature branch，0 檔變更）。
- Salvage：#14（電商市調系列 20 份草稿）、#83（台灣 AI 前瞻 2 份草稿）已隨本收斂 PR 收入 `outputs/drafts/`。

## 三、架構最大缺點

**治理只覆蓋 session 之內，完全沒有「整合平面」——跨 session 的狀態收斂機制是零。**

三平面十六模組管的全是「單一 session 內不失控」：Task Card 管開工、Gate 管驗證、AUDIT_LOG 管留痕。
但九步執行流程在「寫 audit log」就結束了，**沒有第 10 步「收斂回 main」**。
每個 session 產出一個 PR 後死掉，下個 session 從 main 重新出發、看不見 in-flight 的分支。結果：

1. **75 個 open PR 積壓三個月**，而 harness 的所有 metric（governance_metrics、gate 通過率、成本校準）
   都不量測「工作成果有多少 % 真的回到 main」。
2. **同題重做**：eval harness 做了 5 次、R9/R10 做了 2 次、Fable 5 制度化做了 2 次、R11–R14 編號撞車。
   Intake flow 沒有「開卡前先查 in-flight 分支」的 dedup 步驟。
3. **共享狀態的物理設計保證並行必撞**：`frontend/data.json`（生成物入庫 + CI 強制同步）和
   `logs/AUDIT_LOG.md`（全域單檔 append）是每條分支都必須改的檔案 → 任兩個並行 session 數學上必然衝突。
   實測 #89 之後 35 個 PR 兩兩互撞全在這兩檔。
4. **驗證自驗的盲區實例**：大量 PR 是 harness 自我分析報告，每份都說「設計完備 ≈7/10」，
   但沒有一份發現「產出根本沒有 landing 機制」——session 內部指標全綠，系統整體在發散。

### 對應修法
- **短期**：合 #103（衍生產物自動對齊）；評估把 `data.json` 改為 CI 產生、不入庫；
  AUDIT_LOG 改 per-run 檔 + 彙總生成。
- **制度**：執行流程加第 10 步「PR 合併或明確關閉才算任務終結」；
  `governance_metrics.py` 加 open-PR 數量/齡期指標與警戒線；
  INTAKE_FLOW 加開卡前 in-flight 分支查重。

## 四、驗收基準

- open PR 數 75 → ≤ 10（僅剩需人工決策者）。
- main 上 `run_evals.py` 只有一份；無兩組 R11–R14。
- 每個 Phase 後本地全綠：`check_spec_consistency.rb`、`generate_frontend_manifest.py --check`、
  `generate_audit_log.py --check`、全部單元/E2E 測試。
