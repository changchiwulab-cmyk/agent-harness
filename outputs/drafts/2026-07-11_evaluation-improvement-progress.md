# 專案評分缺點 — 改進進度檢視與優化執行（2026-07-11）

> 草稿（draft）｜ Task Card：`20260711-001` ｜ skill：ops
> 方法：全面查證四份評分/診斷文件的每項缺點在 main（e7f9738）與 in-flight PR 上的實際狀態，
> 落地未動工的制度對策，執行 triage 已核定的 PR 收斂。範圍經使用者於 session 內確認（全選）。

---

## 一、評分系譜與本次檢視基準

| 日期 | 文件 | 評分 | 落點 |
|------|------|:----:|------|
| 2026-05-29 | 自我評估 v1 | ≈7/10（Level 3） | `outputs/reports/harness-self-assessment-v1.md`（已合併） |
| 2026-06-23 | v3 就緒度評估 | 7.6/10（結論：不遷移） | `outputs/drafts/2026-06-23_v3-readiness-assessment.md`（已合併） |
| 2026-07-05 | **外部評估報告** | **≈6.8/10**（設計 ~9／執行 ~5） | PR **#126**（未合併，已 dirty） |
| 2026-07-06 | **架構診斷**（triage） | 定性：最大缺點=無整合平面 | `outputs/reports/2026-07-06_pr-backlog-triage-and-architecture-diagnosis.md`（#129 已合併） |
| 2026-07-10 | **外部報告驗證** | 外部評 7.2/10，指控幾乎全數屬實 | PR **#130**（未合併，clean） |

三份最新文件的共同判讀：**設計完備、執行脫節**——「文件宣稱的控制力高於 runtime 實際能保證的控制力」，
且治理只覆蓋 session 之內，跨 session 的收斂機制（整合平面）為零。

## 二、統一缺點台帳（每項標狀態）

圖例：✅ 已上 main ｜ 🔧 本次完成 ｜ 🚧 in-flight PR ｜ ❌ 未動工 ｜ 🗳 待使用者決策

### 6.8 報告六大缺點

| # | 缺點 | 狀態 | 證據 |
|---|------|------|------|
| 1 | 規格與現實脫節（CLAUDE.md vs D004/D006、blocked 枚舉、token 預算帳面不實） | 部分✅／🚧 | D004/D006 的 CLAUDE.md 同步已由 #122 隨 #129 落地；`blocked` 枚舉修復仍只在 #126；token 預算誠實化（P2-2）未動工 |
| 2 | Enforcement 大半是文件不是機制 | 部分✅／🚧 | #96 落地 gate_check/failure_counter/task_card_guard（隨 #129 上 main）；#130 補 fail-closed + active task 綁定（review 中）；P1-1（guard 讀 PERMISSIONS.yaml、補 4 條 deny）仍 ❌ |
| 3 | CI 在 HEAD 紅且守門有洞 | ✅／🔧 | #103 auto-align、governance metrics tests 已在 CI；**但 CI 本體自 06-20 因重複 workflow_dispatch key 整條零 job 死掉——本次已修**（同 #130 修法） |
| 4 | 雙重事實來源（卡片凍結 review、audit 與卡片矛盾、memory 凍結） | 部分✅／❌ | AUDIT_LOG 改由 task card 導出（單一事實源）；memory context 已由 #129 更新；**P1-2 狀態對帳 CI 未動工**，26 張未結卡仍在 |
| 5 | 驗證邏輯三份分歧 | 部分✅／🔧 | #76 型別防護已隨 #129 上 main；**P0-c 空 YAML crash 本次回移植修復**；Ruby/Python 雙驗證器並存（P1-3 收斂）未動工 |
| 6 | 安全表面未完成 | 部分✅／🚧 | SECURITY.md 已為真實政策；#130 補威脅模型章節（review 中）；secret scanning / LICENSE / CHANGELOG（P2-5）未動工 |

### 07-06 架構診斷「無整合平面」對策（本次主戰場）

| 對策 | 狀態 | 本次動作 |
|------|------|---------|
| 執行流程第 10 步（PR 合併/明確關閉才算終結） | 🔧 | CLAUDE.md 流程加第 10 步 + GLOBAL_RULES 任務規則一條；context budget 仍綠（~1585/3000） |
| governance_metrics 加 open-PR 數量/齡期 + 警戒線 | 🔧 | 新 M5：count>10→alert（驗收基準）、count>5 或最老>30 天→warn、無資料→no_data；資料由新 workflow `governance-metrics.yml` 排程以 GITHUB_TOKEN 抓取餵入 `--pr-json`；data.json 不帶 M5（byte-identical drift 約束）；13 個新測試 |
| INTAKE 開卡前 in-flight 查重 | 🔧 | `scripts/check_inflight.py`（advisory：tasks goal/slug + remote 分支 + open PR 標題三來源）+ 16 個測試 + INTAKE_FLOW fast-path 前置步驟；冒煙實測命中本卡 |
| data.json 改 CI 產生不入庫 | 替代路線✅ | #103 的「入庫＋auto-align」已落地；物理衝突面仍在但由 CI 自動收斂壓制。維持現狀，不再改（成本>效益） |
| AUDIT_LOG 改 per-run + 彙總 | 替代路線✅ | 已改「per-task 卡為源＋單檔彙總生成」；與修法原意等效的部分（可再生、不手寫）已達成 |
| 驗收：open PR ≤ 10 | 🔧 | 75 → 21 →（本次收斂後）**4**：#90、#124、#126、#130，全部屬「需人工決策」類 |
| 驗收：run_evals.py 只有一份 / 無兩組 R11-R14 | ✅ | #118 勝出版本在 main；#121 重編號後無撞號 |

### 7.2 報告（#130 驗證）P0 採納項

全部在 PR #130 內（status=review 待人工核准）：active task 綁定 + 精確路徑授權、選擇性 fail-closed、
防護邊界聲明入 SECURITY.md、CI dup-key 修復。**本分支僅重複其中 dup-key 修復一項**（同內容，merge 自動收斂），其餘不重疊。

## 三、本次執行明細（PR 積壓收斂）

- **關閉 17 個 PR**（依 triage #129 核定處置）：
  - D 類 15 個（#92 #93 #94 #95 #97 #99 #101 #102 #104 #108 #109 #110 #111 #119 #120）：
    46 份 `outputs/**` 報告檔已 salvage 進 `outputs/drafts/`（reports/ 路徑一律降落 drafts/——晉升需 approval，見 6.8 報告 P1-4）。
    #94 無報告檔（前端 workflow 視覺化功能 PR），如仍要此功能請另開卡。
  - `#105`：關閉（實作敗於 #96）。兩項 salvage 均經檢視後**跳過**：
    `20260620-D008` 與已合入的 `20260609-D008` 同題撞號（收入會製造編號衝突）；
    R14 README 表格描述的是敗選實作的 script 名（gate_runner/failure_tracker/write_guard，main 上不存在）。
    其「逐條規則標註強制力等級」的概念由 #130 的 SECURITY.md 防線分層表接手。
  - `#123`：關閉（被 #124 取代，同題重寫 CLAUDE.md 取新棄舊）。
- **#99/#101/#104 的 system/ 改動逐一過目，均不取**：
  - #99：runtime enforcement 相鄰工作（run_gates/session_recorder 等），已被 #96/#100/#121 的落地版取代。
  - #101：06-20 時點對 system/skills 的廣面微調，main 已前進（FAILURE_TAXONOMY 17 種、G 系列落地），套用會回退新內容。
  - #104：skill-evals 基建（run_skill_evals.py）＝「eval harness 五做」的第六做，#118 已勝出；其 L5 LLM-judge 構想已列 7.2 報告的不做清單（P1 觀察）。
- **防重複 key linter 評估後不加**：GitHub 解析器本身已在 PR 事件強制（引入 dup key 的 PR 當下紅 X）；
  workflow 內自檢救不了 workflow 自己（零 job 時不會跑）。06-20 事故根因是「紅 CI 照樣合併」的流程問題，
  由第 10 步 + M5 警戒線治本。

## 四、剩餘路線圖與待使用者決策

### 待使用者決策（🗳，依建議順序）

1. **合併 #130**（clean、CI 全綠、三張卡 gate PASS）：P0 hardening + CI 修復。建議最先。
2. **#124 明確確認**（重寫 CLAUDE.md = 改 harness 開機行為，屬 ask）：確認合入則同時關閉 #90（DISPATCH_POLICY 取代 workflow 路由）；否決則 #90 另行評估。
3. **#126 處置**：其 P0-a/P0-d 已被 #122 等取代、P0-c 本次已修，唯一仍缺的是 P0-b（blocked 枚舉）與評估報告本文。
   建議：重做為小 PR——只帶 `2026-07-05_fable5-external-assessment.md` 報告檔 + blocked 枚舉修復，其餘丟棄。
4. **草稿晉升**：本次 salvage 的 46 份中屬正式報告者（*-v1.md 等）如要晉升 `outputs/reports/`，請寫 approval 紀錄（正好練 P1-4）。

### 未動工項（建議各自開卡，依價值排序）

1. **P1-2 狀態對帳 CI**（6.8 報告首推）：audit done ⇔ 卡 done、D006 條件 ⇔ run log 存在、report ⇔ approval 紀錄；順帶收斂 26 張未結卡。
2. **P1-1 enforcement 對齊宣告**：permissions_guard 改讀 PERMISSIONS.yaml、補 4 條未覆蓋 deny（等 #130 合併後做，避免撞 guard 檔）。
3. **P1-3 驗證器收斂**：Ruby/Python 二選一、統一 done/completed/partial/blocked 字彙表。
4. **P2-1 規格瘦身**（最高槓桿）：12 份治理文件逐條標「機器執行」或「指引」。
5. P2-2 token 預算誠實化、P2-5 secret scanning + LICENSE/CHANGELOG。

## 五、本次驗證

- 本地全套：spec consistency（Ruby 測試 + 主檢查）、context budget（~1585/3000）、
  governance metrics 56 tests、check_inflight 16 tests、frontend manifest tests、
  `sync_derived.sh --check`、全 repo YAML parse、task_card_guard tests（未動、確認不連帶紅）。
- 端到端：push 後 Spec Consistency workflow 應**實際產生 job**（06-20 後首次）——dup-key 修復的唯一權威驗證。
- M5 實測：無 `--pr-json` → no_data 不炸；fixture 餵入 → count/oldest 正確。

## 六、一句話總結

三份評分共同指出的「執行面 ~5 分」缺口，本次補上其中**制度性最大塊**（整合平面 v0：終結定義、積壓指標、開卡查重）
並實際把積壓從 21 收斂到 4；剩餘缺口集中在 #130/#126 的合併決策與 P1-1/P1-2 兩張未開的卡。
