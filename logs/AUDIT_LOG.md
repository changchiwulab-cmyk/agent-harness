# Audit Log

每次任務的結構化欄位由 `scripts/generate_audit_log.py` 從 Task Card + git log 自動產生。
人工備註寫在「人工備註」區段，不會被覆蓋。

格式：YAML blocks 由生成器維護，依 `task_id` 倒序。

<!-- AUTO_AUDIT_BEGIN -->
```yaml
task_id: 20260716-P24
date: '2026-07-16'
skill_type: ops
goal: P2-4：verification_loop 帳本常態化——閉環帳本從「真實任務首例」推進為 medium+ 風險卡的常規要求，驗證閉環不再只在 e2e
  drill 裡活著
status: pending
risk_level: medium
approval_needed: true
output_path: system/VERIFICATION_LOOP.yaml
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260716-P23
date: '2026-07-16'
skill_type: ops
goal: P2-3：把「高風險缺 run log 即 FAIL」的 fail-closed 視窗（cutoff 2026-07-10＋risk≥high＋狀態閘）依實測誤擋數據逐步放寬到更低風險層級
status: pending
risk_level: medium
approval_needed: true
output_path: scripts/gate_check.py
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260716-P22
date: '2026-07-16'
skill_type: ops
goal: P2-2：failure_counter 熔斷按 task_id 分閘——連續失敗計數與熔斷改為 per-card 維度，保留全域閘做總開關
status: pending
risk_level: medium
approval_needed: true
output_path: scripts/failure_counter.py
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260716-P21
date: '2026-07-16'
skill_type: ops
goal: P2-1：建立有界自主維運迴圈——以排程定期跑 governance_metrics 與 retro digest 等唯讀彙整，輸出一律進 outputs/drafts/
  等人看，對齊 Loop 層定義但保留人工批准邊界
status: pending
risk_level: medium
approval_needed: true
output_path: outputs/drafts/p2-1_bounded-ops-loop-design.md
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260716-P16
date: '2026-07-16'
skill_type: ops
goal: P1-6：WIP 治理制度化——governance_metrics 新增卡片 WIP aging 指標（未結狀態停留天數與警戒線），並把「每週清 review
  佇列 1–2 張」節奏寫進治理文件
status: pending
risk_level: medium
approval_needed: true
output_path: scripts/governance_metrics.py
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260716-P15
date: '2026-07-16'
skill_type: ops
goal: P1-5：在 agent-governance plugin 草稿樹補 fork parity 鎖——deny rules（plugin 5 條 vs
  本體 8 條）與 Task Card 必填欄位（plugin 6 vs 本體 10）的差異，在建外部 repo 前以 parity 測試鎖定或收斂
status: pending
risk_level: low
approval_needed: false
output_path: outputs/drafts/agent-governance-bootstrap/validators/test_validators.py
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260716-P14
date: '2026-07-16'
skill_type: ops
goal: P1-4：evals 覆蓋 2/6 → 6/6 skill（writing／ops／review／retro 各補 ≥1 case 含 gold/bad
  校準對），並把 run_evals.py 的 LLM judge 從強制 fallback 接上真 provider——品質保證從結構層升到語意層
status: pending
risk_level: medium
approval_needed: true
output_path: evals/README.md
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260716-P13
date: '2026-07-16'
skill_type: ops
goal: P1-3：把 check_untrusted_content.py 從「有偵測器沒佈線」接上執行面——優先掛 Stop hook 以 advisory
  模式掃描 session 新增／修改的 outputs/ 檔案（不 block），次選 CI 掃 outputs/ 新增檔
status: in_progress
risk_level: medium
approval_needed: true
output_path: scripts/check_untrusted_content.py
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260716-P12
date: '2026-07-16'
skill_type: ops
goal: P1-2：新增 PostToolUse hook 對工具錯誤自動 failure_counter --record，把「連續失敗 3 次熔斷」的計數端從
  prompt 自律升為 runtime 自動——熔斷觸發不再依賴 agent 記得記帳
status: review
risk_level: medium
approval_needed: true
output_path: scripts/failure_counter.py
checkpoints:
- commit: b1694a5
  stage: --post-hook 自動計數實作＋兩事件佈線＋13 例新測試全綠（C1）
- commit: 090f457
  stage: SECURITY/PERMISSIONS/CLAUDE.md enforcement 措辭同步（C2）
- commit: f09e795
  stage: 回歸＋drill＋run log＋approval＋卡片收尾（C3）
actual_tool_calls: 38
result_summary: DoD 5/5。關鍵設計偏差（已核准）：官方 hooks 文件確認 PostToolUse 只在成功觸發、失敗走 PostToolUseFailure，故實作為兩事件同一工具範圍（Bash|Write|Edit|MultiEdit|NotebookEdit）——failure→--post-hook
  自動 --record、success→自動歸零（連續語意）；計數鍵取 active task（idle no-op）、is_interrupt 不記、達門檻
  exit 2 non-blocking 警告（攔阻仍由 PreToolUse --hook 專責，不回歸）。輸入層 fail-open（空 stdin／壞 JSON／未知事件／內部例外→不記數不
  block＋stderr 警告）13 例新測試鎖定（合計 25 例，隨既有 CI step 進 spec-consistency）；SECURITY.md fail-open
  章節＋PERMISSIONS enforcement 段＋CLAUDE.md 硬規則 3 同步（context budget ~1620/3000 綠）。手動
  drill：3 筆合成 failure→3/3→PreToolUse exit 2 攔阻→reset→成功歸零。存量卡零回填；全套 Python＋Ruby＋4
  e2e＋evals＋sync_derived --check 不回歸。verification_loop 閉環 outcome=pass（RUN-20260716-001、APR-20260716-001）。
completion_time: '2026-07-16'
```

```yaml
task_id: 20260712-P11
date: '2026-07-12'
skill_type: ops
goal: P1-1：把 Task Card 的 allowed_tools 白名單從事後比對（gate_check L2）抬到 PreToolUse 當下強制 —
  新增 scripts/allowed_tools_guard.py，於 Bash 與寫入類工具呼叫的當下比對 active 卡的白名單，越界即 block
status: review
risk_level: medium
approval_needed: true
output_path: scripts/allowed_tools_guard.py
checkpoints:
- commit: cc87854
  stage: Task Card 建立並綁定 active task（C0）
- commit: b49dc65
  stage: allowed_tools_guard 核心 + 28 例單元測試全綠（C1）
- commit: 5596d1e
  stage: hook 註冊 + PERMISSIONS/GATE_POLICY/SECURITY 同步 + CI step（C2）
- commit: 43a2c0b
  stage: Codex P2 修正 — reports/ 只認 write_reports 專屬 token（C4）
actual_tool_calls: 40
result_summary: DoD 5/5。scripts/allowed_tools_guard.py 於 Bash + Write|Edit|MultiEdit|NotebookEdit
  兩組 matcher 註冊，active 卡的 allowed_tools 當下強制（寫入路徑→gate_check L2 同詞彙、Bash→run_tests/bash），block
  訊息含所需工具與修復指引；idle 與 state 不可讀全放行、控制面（tasks/ state/ logs/、harness CLI、git）豁免、輸入層
  fail-open 各以測試鎖定並寫入 SECURITY.md；28 例單元測試 + CI step；PERMISSIONS enforcement 與 GATE_POLICY
  L2 同步；92 張存量卡零回填，全套既有測試（13 Python + Ruby 53 runs + 4 e2e + evals）不回歸。dogfood：未宣告的
  memory/ 寫入 exit 2。
completion_time: ''
```

```yaml
task_id: 20260712-O01
date: '2026-07-12'
skill_type: ops
goal: 把 main 上 17 張滯留 review 狀態的任務卡收斂：16 張工作已完成者翻 done，唯一未完成的 N06 翻回 in_progress，並補齊
  pre-cutoff approval 紀錄
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/20260712-O01_review-queue-clearance.md
checkpoints:
- commit: 69a6c70
  stage: review 佇列收斂 17→0（16 done + N06 in_progress）
actual_tool_calls: 16
result_summary: 'review 佇列 17→0。16 張已完成卡（result_summary/completion_time/產出俱全）status
  翻 done；20260509-N06（DoD 7/9、等帶外 bootstrap）翻回 in_progress；4 張 pre-cutoff approval_needed
  卡補批次 approval 紀錄（APR-20260712-001…004）。20260711-A01 留 PR #133 待合併後下輪收。已知落差記錄於收案摘要：R01
  缺 run log（不回填）、A01 翻 done 時需補 approval。'
completion_time: '2026-07-12'
```

```yaml
task_id: 20260711-A01
date: '2026-07-11'
skill_type: analysis
goal: 以「四層 AI Engineering」框架（Prompt/Context/Harness/Loop）對照 agent-harness，產出優缺點分析與
  P0–P2 改善計劃，並修復本次已驗證的三個 P0 落差
status: review
risk_level: low
approval_needed: true
output_path: outputs/drafts/20260711-A01_four-layer-alignment-analysis.md
checkpoints:
- commit: 035c9f5
  stage: 四層對照分析報告草稿完成
- commit: a8d7d90
  stage: L4 風險 gate 語意統一（前綴精確 + fail-closed + parity 測試）
- commit: 7001b6d
  stage: 預算口徑對齊 + memory 規模快照同步
actual_tool_calls: 61
result_summary: 四層對照分析報告落地 outputs/drafts/（四層優缺點含檔案:行號證據 + P0–P2 roadmap）；P0 三項修正完成：L4
  風險 gate 語意統一（fail-closed + parity 測試、全卡回歸 0 翻轉）、context 預算口徑對齊（CLAUDE.md 只計 SKILL.md
  + CI advisory）、memory 規模快照同步。待人工審核 PR。
completion_time: '2026-07-11'
```

```yaml
task_id: 20260710-004
date: '2026-07-10'
skill_type: ops
goal: 將人工核准的外部報告對比驗證分析（20260710-001）從 outputs/drafts/ 升格為 outputs/reports/ 正式報告
status: done
risk_level: medium
approval_needed: true
output_path: outputs/reports/20260710-001_external-review-verification.md
checkpoints:
- commit: 8045b35
  stage: dogfood（idle block / 綁定放行）+ 報告升格 + 四卡 done + 批准紀錄
actual_tool_calls: 8
result_summary: DoD 3/3。dogfood 實測：idle 寫 reports exit=2 被擋、--set 20260710-004 後 exit=0
  放行（guard v2 上線後首次實戰驗證）。報告升格至 outputs/reports/，diff 確認內容與核准草稿一致（僅補升格註記）。四張 20260710
  卡 done + 批准紀錄補齊。
completion_time: '2026-07-10'
```

```yaml
task_id: 20260710-003
date: '2026-07-10'
skill_type: ops
goal: 選擇性 fail-closed 化（task_card_guard 壞 stdin/例外、gate 高風險缺 run log 條件 FAIL），並在 SECURITY.md
  寫明防護邊界聲明 + permissions_guard 低誤判補強
status: done
risk_level: medium
approval_needed: true
output_path: scripts/task_card_guard.py
checkpoints:
- commit: 619e9a9
  stage: 三張 Task Card 建立並通過 validator（C0，與 001/002 共用）
- commit: 05e6c4e
  stage: task_card_guard 輸入層 fail-closed（空 stdin/壞 JSON/例外 → exit 2）（C5）
- commit: 6a88c5a
  stage: gate_check + verification_loop 缺 run log 條件 FAIL，共用 helper（C6）
- commit: c65c57d
  stage: permissions_guard wget 擴充 + SECURITY.md 威脅模型 + Stop hook gate 警告（C7）
actual_tool_calls: 22
result_summary: DoD 7/7。task_card_guard 輸入層 fail-closed（test_empty_stdin_allows 語意翻轉為
  expect block）；gate_check/verification_loop 以共用 run_log_required() 對 cutoff 起高風險結案卡缺帳判
  FAIL（不追溯歷史卡）；permissions_guard/failure_counter 維持 fail-open 且理由入 SECURITY.md 新威脅模型章節（防線分層表
  + 已知繞過面）；4 條網路規則擴 wget 簽名 rule_id 不變；session_stop_checks 對 active task 跑 gate_check
  警告（非 blocking）。本地 CI 全套綠。
completion_time: '2026-07-10'
```

```yaml
task_id: 20260710-002
date: '2026-07-10'
skill_type: ops
goal: 建立 active task 真相來源（state/active_task.yaml + CLI），並將 task_card_guard 授權模型從 basename
  比對升級為 normalized 完整路徑 + task_id + status 三段綁定
status: done
risk_level: medium
approval_needed: true
output_path: scripts/active_task.py
checkpoints:
- commit: 619e9a9
  stage: 三張 Task Card 建立並通過 validator（C0，與 001/003 共用）
- commit: 27d1ea3
  stage: active_task schema + CLI + lint 分支 + 測試 + CI step 同 commit 落地（C2）
- commit: 244ded5
  stage: task_card_guard v2 三段綁定 + 16 例測試 + 真實 repo dogfood（C3）
- commit: f3015cb
  stage: CLAUDE.md 執行流程 + PERMISSIONS.yaml enforcement 同步（C4，ask 路徑）
actual_tool_calls: 26
result_summary: DoD 5/5。state/active_task.yaml + SCHEMA + scripts/active_task.py（--set
  拒絕 done/failed 卡）；task_card_guard.evaluate() 改三段綁定（active task → 卡存活 → normalized
  精確路徑），封掉 stale authorization 與檔名巧合授權；check_spec_consistency.rb 專屬 schema 分支與檔案同
  commit；82 張存量卡零回填；dogfood 驗證 idle block / 路徑不符 block / 精確路徑放行。本地 CI 全套綠。
completion_time: '2026-07-10'
```

```yaml
task_id: 20260710-001
date: '2026-07-10'
skill_type: analysis
goal: 將外部第一性原理分析報告（7.2/10）的六大類指控逐條對照程式碼驗證結果（含檔案:行號證據），給出 P0 建議的接受/修改/駁回結論
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260710-001_external-review-verification.md
checkpoints:
- commit: 619e9a9
  stage: 三張 Task Card 建立並通過 validator（C0，與 002/003 共用）
- commit: a2a0146
  stage: 對比驗證報告草稿完成，落 outputs/drafts/（C1）
actual_tool_calls: 12
result_summary: DoD 5/5。六大類指控逐條對照程式碼證據（檔案:行號）：幾乎全數屬實；報告三處需修正（CI 為單一 job 的 steps、permissions_guard
  policy 讀取失敗已 fail-safe、failure_counter 觸發後為硬擋）。P0 採納結論：(a)(b) 接受、(c) 選擇性翻轉、(d) 降級為邊界聲明；含十項不做清單。草稿待人工核准後升
  outputs/reports/。
completion_time: '2026-07-10'
```

```yaml
task_id: 20260706-R01
date: '2026-07-06'
skill_type: research
goal: 分析 GitHub 開源專案 yishentu/claudian（Obsidian AI coding agent 外掛），優化整理後收進專案知識庫 memory/
status: done
risk_level: low
approval_needed: true
output_path: outputs/drafts/20260706-R01_claudian-analysis.md
checkpoints:
- commit: 314dd25
  subject: 'checkpoint: [20260706-R01] merge main 解衝突 + 生成檔重生'
- commit: 64696fa
  subject: 'checkpoint: [20260706-R01] 修正安全層描述：claudian 具 core/security/ApprovalManager'
- commit: b7a3b15
  subject: 'checkpoint: [20260706-R01] 執行紀錄回填 + audit log / manifest 重生成'
- commit: a876c3b
  subject: 'checkpoint: [20260706-R01] 知識庫條目與核准紀錄寫入'
- commit: c368642
  subject: 'checkpoint: [20260706-R01] 研究草稿完成'
- commit: b091a60
  subject: 'checkpoint: [20260706-R01] 任務卡建立'
actual_tool_calls: 9
result_summary: 'DoD 5/5 通過。3 web queries（2 輪）完成 claudian 分析：定位/功能/架構/生態/優劣勢 + 6 項可借鑑設計（含
  🔍 待評估標記）。草稿落 outputs/drafts/，精煉條目寫入 memory/.../references/claudian.md（新建 references/），approval
  record 補於 logs/approvals/。後續依 PR #127 Codex review 加查 2 次（src/core 樹）：claudian 實有
  core/security/ApprovalManager.ts，已修正草稿與記憶條目中「無細粒度治理」過強結論。'
completion_time: '2026-07-06'
```

```yaml
task_id: 20260706-F01
date: '2026-07-06'
skill_type: ops
goal: '修復 PR #76 兩條 Codex review 指出、且仍存在於 main 的缺陷：metric_m4 型別防護與 validate_task_card
  DoD 字串型別檢查'
status: done
risk_level: low
approval_needed: false
output_path: scripts/governance_metrics.py
checkpoints:
- commit: 227e2da
  subject: 'checkpoint: [20260706-F01] 修復 PR #76 review 指出的 M4 型別防護與 DoD 字串檢查'
actual_tool_calls: 6
result_summary: 'DoD 4/4 通過。metric_m4 增型別防護（bool/非數值 → 結構化 alert，不再 TypeError）；validate_task_card
  DoD 項目改 isinstance(item, str) 並回報實際型別。回歸測試 +3（governance 29 全綠、plugin validators
  15 全綠），本地 CI 全套通過。取代擱置的 PR #75 中對應修復。'
completion_time: '2026-07-06'
```

```yaml
task_id: 20260702-R04
date: '2026-07-02'
skill_type: ops
goal: '修復 PR #122 Codex review 三項發現：audit generator 對 squash merge 的決定論、guard 的 &
  分隔符與引號路徑繞過'
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260702-R04_codex-review-fixes-summary.md
checkpoints:
- commit: dc87573
  stage: 任務卡 + 批准紀錄
- commit: 319077a
  stage: guard 補 ampersand 分隔符與引號 memory 路徑
- commit: b65b81e
  stage: audit generator 改卡片優先
actual_tool_calls: 12
result_summary: DoD 6/6 通過。Codex 三項發現全修：generator 卡片優先（squash 模擬下 --check 綠）、guard
  擋分隔符 ampersand 與引號 memory 路徑；guard 26 測試、generator 8 測試全綠，12 個 smoke case 全對。
completion_time: '2026-07-02'
```

```yaml
task_id: 20260702-R03
date: '2026-07-02'
skill_type: ops
goal: CLAUDE.md 第 8 步對齊 D006 執行紀錄使用範圍；補完 4 個 skill 的原生註冊（frontmatter + symlink）
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260702-R03_docs-skill-registration-summary.md
checkpoints:
- commit: 2c1701e
  stage: CLAUDE.md 第 8 步對齊 D006 + 4 skill frontmatter + symlink + NATIVE_OVERLAP
actual_tool_calls: 8
result_summary: DoD 6/6 通過。CLAUDE.md 第 8 步加 D006 條件（預算 ~1216/3000）；4 個 SKILL.md frontmatter
  + symlink，5/5 註冊；新 skill 立即出現在 session 可用清單，原生載入驗證成功。
completion_time: '2026-07-02'
```

```yaml
task_id: 20260702-R02
date: '2026-07-02'
skill_type: ops
goal: 把 AUDIT_LOG 漂移檢查接進 CI、修正 GATE_POLICY 失真敘述、收斂雙驗證器欄位、補 skill token 預算守門
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260702-R02_ci-validators-alignment-summary.md
checkpoints:
- commit: 3d83ddd
  stage: 驗證器欄位收斂 + allowed_tools 守門 + parity 測試 + skill 預算檢查
- commit: faca132
  stage: 'CI 加 AUDIT_LOG 漂移檢查 + fetch-depth: 0'
actual_tool_calls: 14
result_summary: 'DoD 8/8 通過。REQUIRED_FIELDS 雙驗證器收斂為 10 欄 + parity 測試；allowed_tools
  47 卡全過；GATE_POLICY 敘述對齊；skill 預算逐檔守門；CI 補 drift check（含 fetch-depth: 0）。AUDIT_LOG
  於收尾統一重生。'
completion_time: '2026-07-02'
```

```yaml
task_id: 20260702-R01
date: '2026-07-02'
skill_type: ops
goal: 對齊 PERMISSIONS.yaml 與 permissions_guard.py：deny 清單雙向同步、docstring 誠實化、Edit/Write
  ask 層落地到 settings.json
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260702-R01_guard-permissions-alignment-summary.md
checkpoints:
- commit: 91277ad
  stage: deny 清單雙向同步 + guard docstring 誠實化 + 三方 sync 測試
- commit: 9055c77
  stage: settings.json 補 permissions.ask（延後至 system/skills 編輯完成後）
actual_tool_calls: 12
result_summary: DoD 7/7 通過。PERMISSIONS.yaml 敘述對齊 + git_force_push + deny_enforcement
  區段；guard 新增 3 條 runtime 規則；22 測試綠、10 smoke case 全對；settings.json permissions.ask
  落地。
completion_time: '2026-07-02'
```

```yaml
task_id: 20260701-004
date: '2026-07-01'
skill_type: ops
goal: 擴充 check_spec_consistency.rb：驗證 logs/approvals/*.yaml 的 linked_run 指向真實存在的 logs/runs/
  run_id，以及 logs/runs/*.yaml 的 task_id 指向真實存在的 Task Card
status: done
risk_level: low
approval_needed: true
output_path: scripts/check_spec_consistency.rb
checkpoints:
- note: 'checkpoint: 20260701-004 R12 referential integrity lint'
actual_tool_calls: 6
result_summary: check_spec_consistency.rb 新增 check_run_task_references() 與 check_approval_run_references()
  兩個純函式，驗證 run log↔Task Card、approval↔run log 的雙向 ID 參照。main 邏輯 section 4/5 順手蒐集 run_records/approval_entries，新增
  section 8 呼叫。test_check_spec_consistency.rb 新增 TestReferentialIntegrity（6 個測試，含正常/斷鏈各
  2 組），全綠（連同既有測試共 33 個）。對真實 repo 跑檢查：綠燈，現有 2 筆 run log 與 1 筆 approval 檔的參照皆合法。變更影響
  CI 行為，approval_needed=true（比照 R2/R11），本卡自己的批准紀錄見 logs/approvals/2026-07-01_20260701-004_approval.yaml。
completion_time: '2026-07-01'
```

```yaml
task_id: 20260701-003
date: '2026-07-01'
skill_type: ops
goal: 擴充 check_spec_consistency.rb：對 approval_needed=true 且 status=done/failed 的 Task
  Card，檢查 logs/approvals/ 是否存在對應 task_id 的批准紀錄，缺漏則 CI fail
status: done
risk_level: low
approval_needed: true
output_path: scripts/check_spec_consistency.rb
checkpoints:
- note: 'checkpoint: 20260701-003 R11 approval coverage cross-check'
actual_tool_calls: 9
result_summary: 'check_spec_consistency.rb 新增 check_approval_coverage() 純函式 + APPROVAL_COVERAGE_CUTOFF=2026-07-01（理由寫在程式碼註解：10+
  筆歷史缺口無真實來源可回填，故不追溯）。main 邏輯的 section 2/5 順手蒐集 task_records/approval_task_ids，新增
  section 7 呼叫該函式。test_check_spec_consistency.rb 新增 7 個測試，全綠（連同既有測試共 27 個）。對真實 repo
  跑檢查：綠燈，且證實抓到真實缺口（R1 自己的 20260529-004、R2 的 20260529-005 等 10+ 筆歷史任務缺批准紀錄，因 cutoff
  豁免不擋 CI）。變更影響 CI 行為，approval_needed=true（比照 R2），本卡自己的批准紀錄見 logs/approvals/2026-07-01_20260701-003_approval.yaml。追記（PR
  #121 review, Codex P2）：原本收集 approval_task_ids 時未篩 status，rejected/superseded 紀錄也會被誤判為已覆蓋，覆蓋率檢查形同虛設；已新增
  approved_task_ids() 純函式只採計 status=approved，並補 5 個測試（含 rejected-only 不覆蓋、approved
  覆蓋、混合紀錄）。全套檢查仍綠。'
completion_time: '2026-07-01'
```

```yaml
task_id: 20260701-002
date: '2026-07-01'
skill_type: ops
goal: 實測 RECOVERY_RUNBOOK.md 場景 C：任務中途模擬 context 重置後，只靠 git log --grep + Task Card
  + 進度檔重建狀態並正確接續（不重做、不跳過），把恢復路徑從紙上設計變成有實證的機制
status: done
risk_level: medium
approval_needed: true
output_path: system/RECOVERY_RUNBOOK.md
checkpoints:
- note: 'checkpoint: 20260701-002 R13 scenario C drill — step 1/3 (8ed849e)'
- note: 'checkpoint: 20260701-002 R13 scenario C drill — step 2/3 (0bc1a37)'
- note: 'checkpoint: 20260701-002 R13 scenario C drill — step 3/3 post-reset resume
    (442801f)'
actual_tool_calls: 11
result_summary: Scenario C 首次實測完成。以 tests/e2e/fixtures/scenario_c_progress.yaml 模擬
  3-checkpoint 任務，checkpoint 2 後模擬 context 重置：僅用 git log --grep + Task Card + 進度檔三個來源重建狀態，正確判斷『已完成
  1/2、下一步是 3』並接續，checkpoint 2→3 的 diff 驗證為純新增（未動 step 1/2 既有 notes）。結果寫入 system/RECOVERY_RUNBOOK.md
  新附錄，移除原本『建議下次實測』待辦註記。全套一致性檢查（spec consistency / frontend manifest drift / YAML parse）綠。system/
  變更（RECOVERY_RUNBOOK.md）待此分支的 PR review/merge，比照 R1/R2 模式。
completion_time: '2026-07-01'
```

```yaml
task_id: 20260701-001
date: '2026-07-01'
skill_type: ops
goal: 在前端看板新增 M2-M4 治理指標警示可視化，讓異常不再需要手動跑 governance_metrics.py 讀 markdown 才能發現
status: done
risk_level: low
approval_needed: false
output_path: frontend/app.js
checkpoints:
- note: 'checkpoint: 20260701-001 R14 governance alert UI (M2-M4 in dashboard)'
actual_tool_calls: 16
result_summary: governance_metrics.py 的 load_audit_task_ids/load_native_overlap 加
  root 參數（向下相容，既有 27 個測試全綠）；generate_frontend_manifest.py 新增 build_governance_alerts()
  重用 gm.metric_m2/m3/m4，overview.alerts 只含 M2/M3/M4（M1 因日期相依性明確排除，理由寫在 docstring）。前端新增治理警示
  section，app.js renderAlerts() 依狀態上色。新增 2 個測試類別（含日期無關性回歸測試）；test_empty_repo 更新期望值。data.json
  重生並通過 drift --check；Playwright 截圖確認 3 張綠色 ok badge 正確渲染（真實 repo 現況：M2/M3/M4 皆 ok）。未改
  system/。
completion_time: '2026-07-01'
```

```yaml
task_id: 20260630-G04
date: '2026-06-30'
skill_type: ops
goal: 為多/跨 session 任務補上結構化接續點 state/last_checkpoint.yaml，並接到 RECOVERY_RUNBOOK 與 CI
  schema lint
status: done
risk_level: medium
approval_needed: true
output_path: state/last_checkpoint.SCHEMA.yaml
checkpoints:
- note: 'checkpoint: 20260630-G04 cross-session resume state (G-D)'
actual_tool_calls: 8
result_summary: 新增 state/last_checkpoint.SCHEMA.yaml + 首個真實 resume 樣本（dogfood）；check_spec_consistency.rb
  擴充 state/*.yaml schema lint（跳過 SCHEMA/TEMPLATE）+ 測試常數；RECOVERY_RUNBOOK 場景 C 交叉引用
  state/ 為主動接續點。CI-equivalent 綠。system/ 變更待草稿 PR。
completion_time: '2026-06-30'
```

```yaml
task_id: 20260630-G03
date: '2026-06-30'
skill_type: ops
goal: 把 context 從『不可超的預算』升級為『可工程化的產物』：訂 context 組裝順序、JIT 檢索紀律、結構化工作筆記慣例
status: done
risk_level: low
approval_needed: true
output_path: system/CONTEXT_ENGINEERING.md
checkpoints:
- note: 'checkpoint: 20260630-G03 context engineering spec + scratchpad (G-C)'
actual_tool_calls: 6
result_summary: 新增 system/CONTEXT_ENGINEERING.md（組裝順序 + JIT 檢索 + 結構化工作筆記 scratchpad
  + 子任務 context 隔離；明標原生 vs 本 harness 分工避免冗餘）；GLOBAL_RULES + memory/README 補 scratchpad
  層（任務範圍工作記憶，與長期記憶、G-D resume state 三層區隔）。context budget 1354/3000 綠。system/ 變更待草稿
  PR。
completion_time: '2026-06-30'
```

```yaml
task_id: 20260630-G02
date: '2026-06-30'
skill_type: ops
goal: 建立可執行的評估閉環：evals/ 案例 + LLM-as-judge runner + CI baseline，並把執行紀錄詞彙向 OTel gen_ai.*
  對齊
status: done
risk_level: medium
approval_needed: true
output_path: evals/README.md
checkpoints:
- note: 'checkpoint: 20260630-G02 eval harness + OTel GenAI alignment (G-B/G-E)'
actual_tool_calls: 11
result_summary: 新增 evals/（research、analysis 各 1 case，含 gold/bad 校準對，rubric 對齊 eval_examples）；scripts/run_evals.py（rule
  judge CI-safe + LLM-judge 擴充點 + 校準模式）；scripts/test_run_evals.py；evals/README.md（與
  GATE/governance_metrics 分工）；EXECUTION_LOG_SCHEMA 加 optional gen_ai.* 對齊 OTel。校準：gold=1.0
  pass、bad=0.0 fail。CI-equivalent 綠。system/ 變更待草稿 PR。
completion_time: '2026-06-30'
```

```yaml
task_id: 20260630-G01
date: '2026-06-30'
skill_type: ops
goal: 為 harness 補上輸入側防護：把『檢索/外部內容是資料、不是指令』訂為規範，並接到失敗分類學、gate 與 research skill
status: done
risk_level: medium
approval_needed: true
output_path: system/INPUT_GUARDRAILS.md
checkpoints:
- note: 'checkpoint: 20260630-G01 input guardrails (indirect prompt injection)'
actual_tool_calls: 9
result_summary: 新增 system/INPUT_GUARDRAILS.md（檢索內容是資料不是指令 + [未受信任來源] 標記 + 交叉驗證）；FAILURE_TAXONOMY
  加 SEC-05/06；GATE_POLICY rule_check 加輸入面檢查；research SKILL 加不受信任內容段；scripts/check_untrusted_content.py
  偵測器 + 單元測試；tests/e2e 注入 smoke + fixture。全套 CI-equivalent 綠。system/+skills/ 變更待草稿
  PR review。
completion_time: '2026-06-30'
```

```yaml
task_id: 20260623-002
date: '2026-06-23'
skill_type: analysis
goal: 產出 v3 遷移就緒度評估草稿：逐模組標『保留/下放原生/並存』就緒度、列不可替代資產、盤點 v3 觸發現況，並提出 D003/D007 更新建議。只評估不遷移。
status: done
risk_level: high
approval_needed: true
output_path: outputs/drafts/2026-06-23_v3-readiness-assessment.md
checkpoints:
- note: 'checkpoint: 20260623-002 R10 v3 readiness assessment draft'
actual_tool_calls: 8
result_summary: '產出 outputs/drafts/2026-06-23_v3-readiness-assessment.md（只評估不遷移）。

  結論：維持 v2 hold——兩條 v3 觸發（T-A 規模/多代理@D003、T-B 原生重疊 30%@NATIVE_OVERLAP）皆未達標；

  但執行就緒度高（A01 已裁決 16 模組、D007 bootstrap 檔樹備齊）。綜合就緒度 ≈7.6/10。

  逐模組就緒度：14 ready / 2 partial（Planner/Router、Permission，卡 H1/H2），下放原生 5 / 並存 11 /
  保留 0。

  校正 A01 §4.2 摘要列（砍5/抽6/重構5）與逐項表（砍5/抽5/重構6）的出入，以逐項表為準。

  不可替代資產：token 校準表、Failure Taxonomy、Decision Log、Audit Log（+R7 可觀測性引擎建議併入）。

  D003/D007 更新以 proposed diff 呈現（只加註不改既有決策），實際套用屬 ask 待人工確認。

  識別 R11 候選：把 T-A 觸發也自動化，與 R9 的 T-B 偵測合流成單一 v3 觸發儀表板。

  '
completion_time: '2026-06-23'
```

```yaml
task_id: 20260623-001
date: '2026-06-23'
skill_type: ops
goal: 為 NATIVE_OVERLAP 加上季度 revisit 自動化：M4 加時間維度 staleness 偵測 + >50% 明確觸發 v3 評估建議，並於
  RETRO_FLOW 與 R4 決策回看同一節奏合流
status: done
risk_level: low
approval_needed: true
output_path: scripts/governance_metrics.py
checkpoints:
- note: 'checkpoint: 20260623-001 R9 task card - native-overlap quarterly revisit'
- note: 'checkpoint: 20260623-001 R9 M4 quarterly staleness + v3 trigger; wire metrics
    test into CI'
- note: 'checkpoint: 20260623-001 R9 apply system/ changes (RETRO_FLOW row + revisit_interval_days)'
actual_tool_calls: 12
result_summary: 'governance_metrics.py M4 加 today 參數（向後相容）：reviewed_on 逾 revisit_interval_days

  （NATIVE_OVERLAP 現設 90，可覆寫）→ details.revisit_due=true 且 ok 升 warn（不下調 alert）；

  pct>50 → details.v3_trigger=true，render 建議產出 v3-readiness-assessment.md（R10）。

  test_governance_metrics.py 加 11 案例（staleness/v3/render）並接入 CI（原本未跑）。

  本機跑：--today 2026-06-23 → M4 ok（45 天<90、30%<40%）；--today 2026-09-01 → M4 warn（115
  天>90）。

  system/ 變更（RETRO_FLOW「原生重疊回看」列 + NATIVE_OVERLAP revisit_interval_days）經人工確認（選項 1.2）後套用。

  全套 CI-equivalent 綠。

  '
completion_time: '2026-06-23'
```

```yaml
task_id: 20260620-001
date: '2026-06-20'
skill_type: ops
goal: 把線性的四層 GATE_POLICY 收斂成有界、會終止、可稽核的任務內驗證閉環，並提供可執行驗證驅動器與測試
status: in_progress
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260620-001_verification-loop-summary.md
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260609-001
date: '2026-06-09'
skill_type: ops
goal: 校正狀態漂移、硬化三條硬規則、自動化 GATE_POLICY 剩餘三層，把宣稱的治理變成可被腳本與 CI 驗證的治理
status: done
risk_level: medium
approval_needed: false
output_path: outputs/drafts/2026-06-09_optimization-summary.md
checkpoints:
- commit: 97c48da
  stage: 建立 Task Card（goal + DoD）
- commit: e2d8586
  stage: WS1 校正狀態漂移（context.md + README）
- commit: 5a5cbe7
  stage: WS3 gate_check.py 自動化四層 gate + 測試
- commit: 4ff03a6
  stage: WS2 task_card_guard + failure_counter 硬化三條規則 + 收口
actual_tool_calls: 0
result_summary: '三條工作線全數完成。WS1：context.md/README 同步至 2026-06-09 + self-assessment
  addendum。

  WS2：task_card_guard.py（reports/ 守門）+ failure_counter.py（失敗 halt）兩支 deterministic

  guard 註冊進 settings.json，PERMISSIONS/GATE_POLICY 補述強制點。WS3：gate_check.py 自動化

  GATE 四層。三支新元件共 32 單元測試並納入 CI。新增 decision log D008。

  v3 治理插件抽出不在本次範圍（D007）。

  '
completion_time: '2026-06-09'
```

```yaml
task_id: 20260530-H02
date: '2026-05-30'
skill_type: analysis
goal: 用 Opus 4.8 分析 H01 掃描結果並逐維度比對本專案，產出優勢/缺口/可採納建議
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/20260530-H02_harness-comparison-analysis.md
checkpoints:
- note: 'checkpoint: 20260530-H02 比對分析完成（9 維度表 + 6 條建議）'
actual_tool_calls: 7
result_summary: Opus 4.8 讀 H01 掃描 + 本 repo 設計面，產出 9 維度比較表（任務閘控/權限/gates/模型路由/記憶/可觀測性/eval失敗/context預算/多代理）+
  優勢/缺口/可採納，6 條檔案對應建議（P0×2,P1×2,P2×2）。最大缺口：observability/eval。
completion_time: '2026-05-30'
```

```yaml
task_id: 20260530-H01
date: '2026-05-30'
skill_type: research
goal: 用 Haiku 廣度掃描所有公開的 agent harness / agent 執行框架工程資料，產出結構化清單
status: done
risk_level: low
approval_needed: true
output_path: outputs/drafts/20260530-H01_harness-landscape-scan.md
checkpoints:
- note: 'checkpoint: 20260530-H01/H02 建立兩張 Task Card'
- note: 'checkpoint: 20260530-H01 fan-out 完成（Haiku 三 lane 發現 → 掃描草稿）'
actual_tool_calls: 11
result_summary: '3 個 Haiku 子代理（model: haiku）分三 lane（Anthropic生態/其他框架/最佳實踐+eval）web
  fan-out 共 ~9 次搜尋，Opus 4.8 彙整為 research 格式掃描，涵蓋 4 大類 ~30 條目；量化/未來版本/付費牆宣稱標 [待驗證]。'
completion_time: '2026-05-30'
```

```yaml
task_id: 20260529-013
date: '2026-05-29'
skill_type: ops
goal: 套用 Opus 4.8／Claude Code 原生能力優化 harness：原生 Skills、子代理＋模型成本路由、Hooks 自動化、prompt
  caching＋context，並補品質修正與 CI/測試
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/2026-05-29_opus48-uplift-changes.md
checkpoints:
- commit: 2dfecdb
  subject: 'checkpoint: [20260529-012] [20260529-013] Opus 4.8 完整檢視與優化'
actual_tool_calls: 40
result_summary: Phase A 品質修正 + B1–B4 原生升級（原生 skills+5 symlinks、5 子代理含模型路由、3 個 fail-open
  hooks、CLAUDE.md/COST_POLICY/FAILURE_TAXONOMY 更新），CI 擴充 frontmatter/symlint lint＋hook
  測試，全測試綠
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-012
date: '2026-05-29'
skill_type: review
goal: 對 Agent Harness v2 做完整檢視，疊加 Opus 4.8 原生能力視角，產出檢視＋優化路線圖草稿
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/2026-05-29_opus48-review-and-roadmap.md
checkpoints:
- commit: 2dfecdb
  subject: 'checkpoint: [20260529-012] [20260529-013] Opus 4.8 完整檢視與優化'
actual_tool_calls: 12
result_summary: 完整檢視＋Opus 4.8 優化路線圖草稿產出；列出 10 項不一致/缺口及修正位置與四 lever 排序、最高槓桿動作
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-011
date: '2026-05-29'
skill_type: ops
goal: 在前端看板新增『治理總覽』面板，呈現 task 狀態/skill/風險分佈、run 狀態與四層 gate 統計
status: done
risk_level: low
approval_needed: false
output_path: frontend/app.js
checkpoints:
- note: 'checkpoint: 20260529-011 R7 frontend governance overview panel'
actual_tool_calls: 9
result_summary: 前端新增『治理總覽』面板：manifest build_overview（由既有 tasks+logs 計算，root-parameterized）→
  data.json overview 鍵；test_empty_repo 同步更新；index.html + app.js renderOverview 以既有
  .cards 樣式渲染。frontend manifest 測試與 drift --check 綠。未動 system/。
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-010
date: '2026-05-29'
skill_type: ops
goal: 建立災難恢復 runbook（context 重置/工作樹破壞時如何用 checkpoint 還原），並實測一次 checkpoint 還原、與 GATE_POLICY
  rollback 交叉引用
status: done
risk_level: medium
approval_needed: true
output_path: system/RECOVERY_RUNBOOK.md
checkpoints:
- note: 'checkpoint: 20260529-010 R8 recovery runbook + restore drill'
actual_tool_calls: 8
result_summary: 新增 system/RECOVERY_RUNBOOK.md（4 場景 + 資料來源 + 一致性檢查 + GATE_POLICY rollback
  對應）。實測場景 A：破壞工作副本→git checkout 還原，~5ms、byte-identical、工作樹還原乾淨（附錄記錄）。GATE_POLICY
  加交叉引用。system/ 變更待草稿 PR review。
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-009
date: '2026-05-29'
skill_type: ops
goal: 擴充 governance_metrics.py，補上工作流層（gate 通過率/checkpoints）、業務層（每 skill 任務數/token/工具呼叫）、失敗分佈三類可觀測性指標，並產出觀測報告
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/2026-05-29_observability-metrics.md
checkpoints:
- note: 'checkpoint: 20260529-009 R7 observability metrics engine'
actual_tool_calls: 9
result_summary: governance_metrics.py 補三層可觀測性（工作流/業務/失敗）+ --observability flag + 7
  個新測試（含 --json 仍為 M1–M4 的回歸守門）。產出觀測報告草稿。未改 system/、未動 CI。前端『治理成熟度』面板刻意延後：接入需改 data.json
  schema（受 CI drift-check 與結構鎖定測試保護），風險高於本批價值，留作獨立乾淨變更——觀測數據已可由 governance_metrics
  --observability 取得。
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-008
date: '2026-05-29'
skill_type: ops
goal: 為 EXECUTION_LOG_SCHEMA 的 token_estimate 增加 source（資料來源/可信度）欄位，並在現有 run log 示範，讓
  run 級成本可信度可被標示與校準引用
status: done
risk_level: medium
approval_needed: true
output_path: system/EXECUTION_LOG_SCHEMA.yaml
checkpoints:
- note: 'checkpoint: 20260529-008 R6 execution-log token source field'
actual_tool_calls: 5
result_summary: EXECUTION_LOG_SCHEMA token_estimate 新增 source 欄（dashboard_measured/rule_estimated/not_recorded）；RUN-20260529-003
  示範 source=rule_estimated。system/ 變更待草稿 PR review。
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-007
date: '2026-05-29'
skill_type: ops
goal: 建立唯讀的決策 revisit 追蹤器，掃描 decision logs、對可量化觸發比對當前值並標記，納入 RETRO 流程
status: done
risk_level: low
approval_needed: true
output_path: scripts/check_decision_revisit.rb
checkpoints:
- note: 'checkpoint: 20260529-007 R4 decision revisit tracker'
actual_tool_calls: 7
result_summary: 新增 check_decision_revisit.rb（唯讀，量化觸發比對 + DUE/OK/MANUAL + --json）+
  單元測試（接入 CI）+ RETRO_FLOW 加決策回看列。本機跑：7 筆全列，D001/D006 量化評為 OK、其餘 MANUAL、DUE=0。RETRO_FLOW
  屬 system/ 變更，待草稿 PR review。
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-006
date: '2026-05-29'
skill_type: analysis
goal: 以一次真實的治理數據分析任務，產生 analysis skill 的首個成本實測樣本，並輸出可行動的治理發現
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/2026-05-29_governance-data-analysis.md
checkpoints:
- note: 'checkpoint: 20260529-006 R3 analysis cost sample (governance data analysis)'
actual_tool_calls: 7
result_summary: '產出治理數據分析草稿（39 task cards、audit 覆蓋 94.3%、draft:report≈8:1、logs runs2/appr1/err2、7
  決策 0 revisit）。貢獻 analysis 成本樣本 #1（~16K）。建議 RETRO 重算 analysis 校準（現有 3 張 analysis
  卡可一併納入）。未改 system/。'
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-005
date: '2026-05-29'
skill_type: ops
goal: 擴充 scripts/check_spec_consistency.rb，把 logs/runs、logs/approvals、logs/errors
  的 schema 納入 CI lint，守住 R1 定義的格式不漂移
status: done
risk_level: low
approval_needed: true
output_path: scripts/check_spec_consistency.rb
checkpoints:
- note: 'checkpoint: 20260529-005 R2 logs schema lint + unit tests'
actual_tool_calls: 8
result_summary: check_spec_consistency.rb 新增 3 段 logs schema lint（runs/approvals/errors，含枚舉與必填欄位、跳過
  TEMPLATE）+ test_check_spec_consistency.rb 新增枚舉常數測試。現有 logs 全通過。變更影響 CI 行為，待草稿 PR
  review/merge。
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-004
date: '2026-05-29'
skill_type: ops
goal: 為批准動作定義 schema 並回填首筆真實紀錄，讓 logs/approvals/ 有可解析格式、RETRO_FLOW §1 的核准資料源不再讀空目錄
status: done
risk_level: medium
approval_needed: true
output_path: logs/approvals/2026-04-09_20260409-001_approval.yaml
checkpoints:
- note: 'checkpoint: 20260529-004 R1 approval record schema + backfill'
actual_tool_calls: 8
result_summary: approval_record schema 寫入 APPROVAL_POLICY.yaml；APPROVAL_LOG_TEMPLATE.yaml
  + 首筆回填樣本（RUN-20260409-001 的 2 筆批准）建立；RETRO_FLOW 註記 schema 位置。system/ 變更待草稿 PR review/merge（approval_given
  待人工）。
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-003
date: '2026-05-29'
skill_type: ops
goal: '執行受控的 schema 失敗演練，首次在真實故障下坐實 logs/errors/ + logs/runs/(status: failed) 紀錄路徑，並固化為可重複的
  e2e 回歸測試'
status: done
risk_level: low
approval_needed: false
output_path: logs/runs/RUN-20260529-003.yaml
checkpoints:
- note: 'checkpoint: 20260529-003 R5 failure drill (errors/runs paths + e2e regression)'
actual_tool_calls: 9
result_summary: 首次坐實失敗路徑：broken fixture 經 validate_task_card 確實觸發 schema_failure→重試
  1 次→停；產出即時 error log（logs/errors/）+ status=failed 的 run log（logs/runs/，gate_results.schema_check=fail）；新增
  tests/e2e/test_failure_drill.py 並接入 CI。全套 CI 綠，未改 system/。
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-002
date: '2026-05-29'
skill_type: ops
goal: 將 outputs/drafts/2026-05-29_harness-self-assessment.md 依 RETRO_FLOW §5 晉升為 outputs/reports/harness-self-assessment-v1.md
status: done
risk_level: low
approval_needed: true
output_path: outputs/reports/harness-self-assessment-v1.md
checkpoints:
- note: 'checkpoint: 20260529-002 promote self-assessment to reports/'
actual_tool_calls: 6
result_summary: 依 RETRO_FLOW §5 晉升完成：outputs/reports/harness-self-assessment-v1.md（檔頭加晉升標記＋採納清單）；原草稿加回指保留。內容與
  draft 一致，未修改任何 system/ 檔。
completion_time: '2026-05-29'
```

```yaml
task_id: 20260529-001
date: '2026-05-29'
skill_type: review
goal: 對 Agent Harness v2 做雙軸（業界十維最佳實踐 + 自家馬鞍工程六原則）1-10 評分，盤點優缺點，並產出短/中/長期優化 roadmap（R1–R10）
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/2026-05-29_harness-self-assessment.md
checkpoints:
- note: 'checkpoint: 20260529-001 harness self-assessment (eval + optimization roadmap)
    draft'
actual_tool_calls: 14
result_summary: 綜合 ≈7/10，成熟度等級 3（生產前）。業界十維平均 7.2（安全 9 / 治理 9 為招牌，可觀測 6 / 耐久 6 為短板）；馬鞍工程六原則平均
  7.0（驗證集中化 9 最高，執行紀錄結構化 5 最低）。校正 3 項原始誤判。產出 R1–R10 roadmap，單一最高槓桿＝R5 故障演練。產出：outputs/drafts/2026-05-29_harness-self-assessment.md。未修改任何
  system/ 檔。
completion_time: '2026-05-29'
```

```yaml
task_id: 20260509-W01
date: '2026-05-09'
skill_type: writing
goal: 把 Harness v2 沉澱的治理思想（可恢復／可審計／可量化）轉寫成可發表的方法論大綱，適用於書、長文系列、課程三種形態
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/2026-05-09_methodology_outline.md
checkpoints:
- note: '419ebaf checkpoint: 20260509-W01 methodology outline draft + audit'
actual_tool_calls: 6
result_summary: DoD 7/7 通過。主軸命題 3 候選 + 推薦 T1（用契約取代信任）；12 章大綱（~40K 字），每章帶 Harness 實證；三形態取捨推薦先部落格→課程→書；與
  LangChain / Chip Huyen / Anthropic best practice 差異化定位；2 個讀者反對意見已預備回應。
completion_time: '2026-05-09'
```

```yaml
task_id: 20260509-N11
date: '2026-05-09'
skill_type: ops
goal: 在 plugin v0.1.0 candidate 推上 agent-governance repo 之前，修掉 Codex 指出的 P1（risk gate
  在 output_path 缺席時被略過 → 治理破口）+ P2（gate_completion 對非字串 DoD 入項會 TypeError 崩潰）。屬 plugin
  tree 內部 hardening，不影響 agent-harness 端
status: in_progress
risk_level: low
approval_needed: false
output_path: outputs/drafts/agent-governance-bootstrap/hooks/post_task_use.py
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260509-N10
date: '2026-05-09'
skill_type: ops
goal: 在 N06 bootstrap 進行帶外手動執行的等待期間，修正 runbook 的 test 數量漂移並預製 N06b 切換用的 3 個產物草稿，把
  N06b PR 的決策面降到接近零
status: in_progress
risk_level: low
approval_needed: false
output_path: outputs/drafts/n06b-switch-preview/README.md
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260509-N09
date: '2026-05-09'
skill_type: ops
goal: 把 agent-harness 的 CLAUDE.md / .claude/settings.json 切換為引用 agent-governance plugin
  v0.1.0，同時保證 agent-harness 自身 CI 在 plugin 缺席時仍綠（fallback 路徑）
status: pending
risk_level: medium
approval_needed: true
output_path: outputs/drafts/2026-05-09_n06b-harness-plugin-switch.md
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260509-N08
date: '2026-05-09'
skill_type: writing
goal: 把 W01 第 1 章『為什麼一人公司需要 Agent 治理？』從大綱寫成可發佈的部落格首篇草稿，並附 elevator pitch（單獨可流通版）
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/2026-05-09_n08_w01-chapter-one-draft.md
checkpoints:
- note: '562a31b checkpoint: N6/N7/N8 task cards created'
- note: 'bff62c1 checkpoint: 20260509-N08 W01 elevator pitch + chapter 1 draft'
actual_tool_calls: 5
result_summary: DoD 7/7 通過。Elevator pitch ~180 字 + 第 1 章草稿 ~3,650 字（≥3,200 ✅）。實證引用
  20260404-S01（DoD 6/6 通過 + error_summary 第 3 次 web search rate limit），來源 logs/AUDIT_LOG.md
  第 575-594 行已比對。未引用對標（嚴格做法），章末 hook 自然導向第 2 章三原則總覽。
completion_time: '2026-05-09'
```

```yaml
task_id: 20260509-N07
date: '2026-05-09'
skill_type: analysis
goal: 評估是否在 agent-harness v2.x 啟用 Claude Code 原生 Memory，並產出明確 Go / No-Go / Conditional-Go
  建議與條件清單
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/2026-05-09_n07_native-memory-evaluation.md
checkpoints:
- note: '562a31b checkpoint: N6/N7/N8 task cards created'
- note: '7b79480 checkpoint: 20260509-N07 native memory evaluation -> Conditional-Go'
actual_tool_calls: 6
result_summary: DoD 7/7 通過。建議 Conditional-Go：4 條啟用條件（C1 寫入仍須人工確認；C2 namespace 限定；C3
  不走雲同步；C4 與 N6 plugin 相容）。比照 N3 Skills symlink 模式可避免雙寫漂移。後續候補 M1（PoC：symlink + namespace
  試點，risk=medium）+ M2（PERMISSIONS.yaml + plan §3.5 收斂，risk=medium）。
completion_time: '2026-05-09'
```

```yaml
task_id: 20260509-N06
date: '2026-05-09'
skill_type: ops
goal: 依 N4 skeleton 真正建立 agent-governance plugin repo（含 plugin.json / 5 commands /
  4 schemas / 2 hooks / 2 validators 的最小可運行版本），並把 agent-harness 切到引用該 plugin
status: in_progress
risk_level: high
approval_needed: true
output_path: outputs/drafts/2026-05-09_n06_v3-plugin-bootstrap.md
checkpoints:
- note: '562a31b checkpoint: N6/N7/N8 task cards created'
actual_tool_calls: 18
result_summary: "使用者明示核准 + D007 完成 4 子題決策。\n本 session 完成 DoD #1/#2/#3/#4/#5/#7（檔案在\
  \ outputs/drafts/agent-governance-bootstrap/）：\n  - plugin.json manifest（5 commands\
  \ / 4 schemas / 2 hooks / 2 validators 註冊）\n  - 5 slash command 介面契約 markdown（task-card\
  \ / audit / decision / run-log / gate-check）\n  - 4 schemas（task_card / decision_log\
  \ / execution_log / failure_taxonomy）\n  - 2 hooks（pre_tool_use 移植 permissions_guard.py\
  \ + post_task_use 4-stage gate runner）\n  - 2 validators（validate_task_card 移植 system/\
  \ + check_audit_format 新）\n  - hooks 5 unit tests + validators 13 unit tests（總 18，於本機執行\
  \ OK 至 cwd 出問題前）\n  - README（5 步 quick start）+ LICENSE Apache-2.0 + CHANGELOG 0.1.0\
  \ + CI workflow\n待下個 session 完成（受工具限制）：\n  - DoD #6 agent-harness CLAUDE.md / settings.json\
  \ 切換引用 plugin\n  - DoD #8 agent-harness 自身 CI 在 plugin 缺席仍綠（待 #6 完成後驗證）\n  - 實際\
  \ GitHub repo 建立 + git init 搬入 + push v0.1.0\nDoD #9 Decision Log D007 已完成於 memory/active_projects/agent-harness/decisions/。\n"
completion_time: ''
```

```yaml
task_id: 20260509-N05
date: '2026-05-09'
skill_type: ops
goal: 建立 governance metrics 自動採集腳本，月度執行 plan §5.3 4 條關鍵指標（task card 月新增數 / drafts:reports
  比 / audit 覆蓋率 / 原生重疊度），輸出報告 + 警訊狀態
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/governance-metrics-2026-05.md
checkpoints:
- note: '04d9ce8 checkpoint: 20260509-N05 governance metrics automation'
actual_tool_calls: 6
result_summary: DoD 8/8 通過。scripts/governance_metrics.py（M1-M4 採集 + markdown/JSON
  雙輸出 + warn/alert 分級退出碼）+ scripts/test_governance_metrics.py（15 個測試全綠）+ system/NATIVE_OVERLAP.yaml（M4
  人工 input）+ outputs/drafts/governance-metrics-2026-05.md（首份月度報告）。本月實跑：M1 04/05 月
  16+11 ok / M2 比 9.50 ok / M3 覆蓋 92.3% ok / M4 重疊 30% ok。不加進 CI 強制（人工月度觸發）。
completion_time: '2026-05-09'
```

```yaml
task_id: 20260509-N04
date: '2026-05-09'
skill_type: writing
goal: 起草 agent-governance plugin 的 manifest skeleton 設計文件，定義每個 command / hook / schema
  / validator 的介面契約，但不寫實作
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/2026-05-09_n04_governance-plugin-skeleton.md
checkpoints:
- note: '4900614 checkpoint: 20260509-N04 governance plugin skeleton'
actual_tool_calls: 5
result_summary: DoD 8/8 通過。skeleton 含：plugin.json manifest、5 slash command 介面契約、4
  schema 草案、2 hook 行為、2 standalone validator、README outline、v2→plugin 對照表、暫不做清單。確認
  A01 §4.2 的抽出 6 / 砍除 5 / 重構 5 → plugin 承載全部抽出 + 4 個重構，2 個重構留 user 端（CLAUDE.md + cost
  calibration）。
completion_time: '2026-05-09'
```

```yaml
task_id: 20260509-N03
date: '2026-05-09'
skill_type: ops
goal: 在分支上把 skills/research/SKILL.md 加上原生 Claude Code Skills frontmatter 並建立 .claude/skills/
  註冊路徑，輸出 PoC summary 評估 H1（原生自動路由能否取代 ROUTING_RULES.md）
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/2026-05-09_n03_skills-native-poc.md
checkpoints:
- note: '4c65a40 checkpoint: 20260509-N03 skills native registration PoC'
actual_tool_calls: 7
result_summary: DoD 7/7 通過。skills/research/SKILL.md 加 frontmatter（name + description
  151 字），原內容不刪改；.claude/skills/research → ../../skills/research symlink 建立（避免雙寫漂移）；H1
  結論：部分成立——routing 表可被取代，但「跨 skill 拆 Task Card」原則需保留至 CLAUDE.md。A01 §4.2 第 3 列「保留拆分原則寫進
  CLAUDE.md」恰好命中，不需修改裁決。Session 內無法現場驗證自動觸發，需新 session。
completion_time: '2026-05-09'
```

```yaml
task_id: 20260509-N02
date: '2026-05-09'
skill_type: review
goal: 修正 A01 草稿 §1.1 對『README 寫 30+』的錯誤歸因，更新為實際計數，並在 N1 對齊報告中註記 plan 的數據是 snapshot，不更新
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/2026-05-09_n02_audit-count-fix.md
checkpoints:
- note: 'c7d64a6 checkpoint: 20260509-N02 audit count fix'
actual_tool_calls: 4
result_summary: DoD 6/6 通過。事實核對：README 從無『30+』字樣（grep 證明），真正出處為 plan §Context + 兩張
  task card context 欄位。實際計數本 PR 前 18 筆 audit / 12 drafts / 2 reports / 6 decisions；本
  PR 後 23/17/2/6。修正 6 處：A01 §1.1 + §10、W01 §1.4 + 第 11 章 + §9、N1 §7.2。建立計數規則：snapshot
  文件不改（plan/task card context/DoD）、事實文件即時更新（drafts/）、規範文件不寫具體計數。Root cause：歸因推論未交叉驗證，對應
  SPEC-04 + VAL-03。
completion_time: '2026-05-09'
```

```yaml
task_id: 20260509-N01
date: '2026-05-09'
skill_type: review
goal: 把 ai-bubbly-mountain plan 寫進 repo（memory/active_projects/agent-harness/plans/），並對
  A01/W01 與 plan §8.1 Task A/B 做逐項對齊，產出對齊報告與 task card 清理
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/2026-05-09_n01_plan-alignment.md
checkpoints:
- note: 'a245f1e checkpoint: 20260509-N01 plan alignment'
actual_tool_calls: 6
result_summary: DoD 7/7 通過。Plan 已歸檔 repo（memory/active_projects/agent-harness/plans/ai-bubbly-mountain.md）；A01/W01
  與 plan §8.1 Task A/B 各 5/5 草案 DoD pass + 各 2 條 over-deliver；命名漂移（_ vs -）+ allowed_tools
  詞彙差異記錄但不修；plan §5.3 4 條關鍵指標 A01/W01 都未採納 → 建議開 N5 自動採集；plan §3.5 Memory + §4.1 趨勢
  C 也識別為未採納 → N7/N8 候補。
completion_time: '2026-05-09'
```

```yaml
task_id: 20260509-M01
date: '2026-05-09'
skill_type: ops
goal: 在 agent-harness namespace 試點原生 Memory（symlink 模式），實測 Claude Code 是否真支援指向 repo
  內路徑、寫入提示流程、token 預算影響
status: pending
risk_level: medium
approval_needed: true
output_path: outputs/drafts/2026-05-09_m01_native-memory-poc.md
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260509-A01
date: '2026-05-09'
skill_type: analysis
goal: 規劃 Harness v3 重構範圍：砍除與 Claude Code 原生重疊的模組，把治理三件（Audit / Decision Log / DoD
  / Failure Taxonomy）抽成可獨立發布的治理層
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/2026-05-09_v3_extraction_plan.md
checkpoints:
- note: 'e95a425 checkpoint: 20260509-A01 v3 extraction plan draft + audit'
actual_tool_calls: 12
result_summary: DoD 7/7 通過。16 模組裁決：保留 0 / 砍除 5 / 抽出 6 / 重構 5。治理層 plugin 邊界、發布形態取捨（Plugin
  → CLI → MCP）、v2 → v2.5 → v3.x 階段切換、4 個風險已列。Plan 檔此 session 不可讀，相關推論標 [待驗證]。risk=medium
  → drafts/ 等人工審閱後才動代碼。
completion_time: '2026-05-09'
```

```yaml
task_id: 20260502-T03
date: '2026-05-02'
skill_type: research
goal: 台灣 AI 產業深度報告：5-7 切片量化、政策法規、敏感性表、12 個月機會日曆
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/20260502-T03_taiwan-ai-industry-deep-dive.md
checkpoints: []
actual_tool_calls: 8
result_summary: DoD 全條通過。7 切片 + 量化財務 + 完整政策法規（AI 基本法 + PDPA + 補貼）+ 12 個月機會日曆 + 6 條敏感性假設
  + 顧問切入點 ROI 排序。5 web searches 補完政策時序、AI 伺服器 ODM、人才薪資、startup VC、事件日曆。cost-quality
  對照確認：5 search 比 3 search 多出『政策時序 / 敏感性分析 / 事件日曆』三項，這三項是顧問業務最直接的決策輸入。
completion_time: '2026-05-02'
```

```yaml
task_id: 20260502-T02
date: '2026-05-02'
skill_type: research
goal: 台灣 AI 產業標準研究：5 切片含本地 vs 國際玩家比較、成熟度與驅動力分析
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/20260502-T02_taiwan-ai-industry-standard.md
checkpoints: []
actual_tool_calls: 4
result_summary: DoD 全條通過。5 切片（半導體 / 邊緣 AI / SaaS / 醫療 / 金融）+ 政策補貼 funnel + 顧問切入點 5
  列舉。3 web searches 補完 T01 缺口（SaaS 玩家、政策金額、產業數據）。
completion_time: '2026-05-02'
```

```yaml
task_id: 20260502-T01
date: '2026-05-02'
skill_type: research
goal: 台灣 AI 產業快速掃描：3 切片 + 3 跨切片趨勢，1 小時內出 executive brief
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/20260502-T01_taiwan-ai-industry-quick-scan.md
checkpoints: []
actual_tool_calls: 2
result_summary: DoD 7/7 通過。3 切片（半導體 / 邊緣 AI IPC / 軟體 SaaS）+ 3 跨切片趨勢 + 3 來源 + 高風險假設
  2 條。1 web search 限制下 SaaS 段量化資料不足，明確標 [待驗證]，由 T02 補完。
completion_time: '2026-05-02'
```

```yaml
task_id: 20260502-A01
date: '2026-05-02'
skill_type: ops
goal: Phase A：補齊規則 enforcement 與觀測自動化（PreToolUse hook、audit log generator、e2e smoke
  test）
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260502-A01_phase-a-summary.md
checkpoints: []
actual_tool_calls: 33
result_summary: DoD 9/10 完成（第 9 條 audit_log entry 已 append；第 10 條 CI 待 PR push 驗證）。Local
  CI 全綠：spec consistency / context budget / frontend manifest tests + drift / permissions_guard
  11 tests / audit_log 5 tests / e2e smoke 3 tests。等人工 review 後合併。
completion_time: '2026-05-02'
```

```yaml
task_id: 20260427-F01
date: '2026-04-27'
skill_type: ops
goal: '收斂 PR #55 為前端平台的最小可審核 baseline：穩定 YAML 解析、防 manifest 漂移、補 generator 測試與 CI
  護欄'
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260427-F01_phase0-summary.md
checkpoints:
- commit: dc73980
  subject: 'checkpoint: [20260427-F01] phase 0 baseline 收斂'
actual_tool_calls: 25
result_summary: DoD 11/11 對應產物完成（CI 綠待 PR push 後驗證）。frontend 由 manifest.js 改為 PyYAML→data.json，drift
  check 進 CI；4 個 unit tests 全綠；多 project decisions glob 落地。等人工 review 後合併。
completion_time: '2026-04-27'
```

```yaml
task_id: 20260424-O03
date: '2026-04-24'
skill_type: ops
goal: 為 CLAUDE.md/GLOBAL_RULES 3K token 硬限制加 CI 檢查，並對 Execution Log Schema 落地率低做收斂決策
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260424-O03_guardrails-summary.md
checkpoints:
- commit: 3d54463
  subject: 'checkpoint: [20260424-O03] engineering guardrails'
actual_tool_calls: 14
result_summary: DoD 9/9 通過。新增 context budget CI 護欄（當前 ~554/3000，使用 18.5%）；Execution
  Log Schema 選 Narrow Scope，Decision Log D006 落地。所有 CI 檢查全綠。
completion_time: '2026-04-24'
```

```yaml
task_id: 20260424-O02
date: '2026-04-24'
skill_type: ops
goal: 將 token-calibration-table 晉升為治理 artifact，調整 INTAKE_FLOW 主路為快速路徑，正式歸檔 WEEKLY_REVIEW_TEMPLATE
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260424-O02_restructure-summary.md
checkpoints:
- commit: d63ef06
  subject: 'checkpoint: [20260424-O02] governance docs restructure'
actual_tool_calls: 12
result_summary: DoD 8/8 通過。token-calibration 晉升至 reports/；INTAKE_FLOW 重寫以 fast-path
  為主路；WEEKLY_REVIEW_TEMPLATE 歸檔至 tasks/archived/；所有活性引用同步更新。CI 檢查全綠。
completion_time: '2026-04-24'
```

```yaml
task_id: 20260424-O01
date: '2026-04-24'
skill_type: ops
goal: 收斂重複的 task card 驗證器為單一事實來源，補 SECURITY 發現性，清理重複 CI
status: done
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260424-O01_cleanup-summary.md
checkpoints:
- commit: 33cf98f
  subject: 'checkpoint: [20260424-O01] cleanup & validator consolidation'
actual_tool_calls: 10
result_summary: DoD 8/8 通過。刪除 2 支冗餘 Python 腳本 + 1 條重疊 CI workflow；spec-consistency.yml
  收斂為純 Ruby；README 補 SECURITY 與單張卡 CLI 用法。所有本地 CI 檢查全綠。
completion_time: '2026-04-24'
```

```yaml
task_id: 20260424-H01
date: '2026-04-24'
skill_type: analysis
goal: 評估台灣醫療健康產業 AI 顧問服務的可行性，比較診所、醫美、長照三個子市場的進入機會
status: pending
risk_level: low
approval_needed: false
output_path: outputs/drafts/20260424-O05_healthcare-ai-feasibility.md
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260424-F01
date: '2026-04-24'
skill_type: writing
goal: 撰寫針對台灣中小型金融機構（信用合作社、保險代理、P2P 借貸平台）的 AI 顧問服務提案書
status: pending
risk_level: medium
approval_needed: true
output_path: outputs/drafts/20260424-O06_fintech-service-proposal.md
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260424-E01
date: '2026-04-24'
skill_type: research
goal: 研究台灣與越南電商產業現況與 AI 應用機會，識別一人顧問公司可切入的高價值服務缺口
status: pending
risk_level: low
approval_needed: false
output_path: outputs/drafts/20260424-O04_ecommerce-market-research.md
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260421-W01
date: '2026-04-21'
skill_type: writing
goal: 撰寫一份面向新使用者的 AI Agent 使用說明文件草稿（約 600 字）
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/ai-agent-usage-guide.md
checkpoints:
- note: 'checkpoint: 20260421-W01 writing 完成'
actual_tool_calls: 3
result_summary: 產出約 650 字的使用說明文件，含前言/快速開始/常見錯誤（3 項）/注意事項（4 項）四節，台灣商業顧問語氣，所有術語有說明。DoD
  4/4 通過。
completion_time: '2026-04-21'
```

```yaml
task_id: 20260421-V01
date: '2026-04-21'
skill_type: review
goal: 審查 system/GLOBAL_RULES.md 的完整性、一致性，找出潛在缺漏、矛盾或需強化的規則
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/global-rules-review-report.md
checkpoints:
- note: 'checkpoint: 20260421-V01 review 完成'
actual_tool_calls: 4
result_summary: 有條件通過。必須修改 2 項（M1 輸出路徑未區分 drafts/reports、M2 Checkpoint 格式分散），建議修改
  4 項（S1 Skill 路由引用、S2 記憶路徑、S3 高風險假設定義、S4 COST_POLICY 引用）。DoD 5/5 通過。
completion_time: '2026-04-21'
```

```yaml
task_id: 20260421-R01
date: '2026-04-21'
skill_type: research
goal: 調查一人公司（顧問型）常見的客戶開發方法與工具，整理可立即行動的策略清單
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/client-development-strategies.md
checkpoints:
- note: 'checkpoint: 20260421-R01 research 完成'
actual_tool_calls: 1
result_summary: 整理 4 大客戶開發管道（轉介紹/內容行銷/直接開發/策略合作），每管道含描述、適用場景、2-3 步驟、預期效果。已知事實/推論/待驗證三層標記。含優先行動建議。DoD
  4/4 通過。
completion_time: '2026-04-21'
```

```yaml
task_id: 20260421-O01
date: '2026-04-21'
skill_type: ops
goal: 掃描 tasks/ 目錄下所有 Task Cards，產出結構化的任務狀態摘要表
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/tasks-status-summary.md
checkpoints:
- note: 'checkpoint: 20260421-O01 ops 完成'
actual_tool_calls: 2
result_summary: 掃描 tasks/ 下 14 張 Task Cards（排除 2 個模板），產出 Markdown 表格含 task_id/date/status/skill_type/goal，依日期倒序，附統計摘要（狀態分佈/skill
  分佈/時間分佈）。DoD 4/4 通過。
completion_time: '2026-04-21'
```

```yaml
task_id: 20260421-A01
date: '2026-04-21'
skill_type: analysis
goal: 分析一人顧問公司從台灣進入越南市場的可行性，產出 Go / No-Go 建議與關鍵決策依據
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/vietnam-market-analysis.md
checkpoints:
- note: 'checkpoint: 20260421-A01 analysis 完成'
actual_tool_calls: 2
result_summary: Conditional Go 建議，3 選項六維評估完整（含「不做」選項），3 項支持依據、3 項反對依據，2 項高風險假設含條件變化說明，3
  項待驗證含驗證方式。DoD 5/5 通過。
completion_time: '2026-04-21'
```

```yaml
task_id: 20260417-W01
date: '2026-04-17'
skill_type: writing
goal: '補寫 2026-04-04 組 7 個 expected_output markdown，使 outputs/drafts/ 與 7 張 status:
  done task card 一致'
status: pending
risk_level: low
approval_needed: false
output_path: outputs/drafts/[7 files; see definition_of_done]
checkpoints: []
actual_tool_calls: 0
result_summary: ''
completion_time: ''
```

```yaml
task_id: 20260417-O06
date: '2026-04-17'
skill_type: ops
goal: 將 AUDIT_LOG.md 中三處 file_edit 工具名稱統一改為 file_write，與 Task Card allowed_tools 白名單一致
status: done
risk_level: low
approval_needed: false
output_path: logs/AUDIT_LOG.md
checkpoints:
- note: 'audit-log-normalized: 3 處 file_edit 改為 file_write，grep -c 結果 0，Gate checker
    通過'
actual_tool_calls: 3
result_summary: 'DoD 4/4 通過。

  - logs/AUDIT_LOG.md 3 處 tool_name: "file_edit" 全數改為 tool_name: "file_write"（影響 O04、O03、O02
  條目）

  - grep -c file_edit logs/AUDIT_LOG.md: 0 ✅

  - ruby scripts/check_spec_consistency.rb ✅

  - python scripts/check_task_card_skill_type.py ✅（19 cards）

  '
completion_time: '2026-04-17'
```

```yaml
task_id: 20260417-O05
date: '2026-04-17'
skill_type: ops
goal: 為 spec-consistency.yml 補入 workflow_dispatch 觸發器，使 CI 可在 Actions 啟用後手動觸發
status: done
risk_level: low
approval_needed: false
output_path: .github/workflows/spec-consistency.yml
checkpoints:
- note: 'workflow-dispatch-added: spec-consistency.yml on: 區塊補入 workflow_dispatch，兩支
    Gate checker 通過'
actual_tool_calls: 4
result_summary: 'DoD 5/5 通過。

  - .github/workflows/spec-consistency.yml on: 區塊補入 workflow_dispatch

  - 兩支 workflow 觸發器對齊（pull_request + workflow_dispatch）

  - ruby scripts/check_spec_consistency.rb ✅

  - python scripts/check_task_card_skill_type.py ✅（18 cards）

  '
completion_time: '2026-04-17'
```

```yaml
task_id: 20260417-O04
date: '2026-04-17'
skill_type: ops
goal: '回應 PR #26 的兩則 Codex P2 review 評論：修 vietnam-expansion frontmatter 檔頭順序、補 evidence-gap-filling
  任務卡的 bash 工具白名單'
status: done
risk_level: low
approval_needed: false
output_path: memory/archived_projects/vietnam-expansion/, tasks/, logs/見 DoD
checkpoints:
- note: 'pr26-review-fixes-complete: frontmatter 與 allowed_tools 修正完成，全數 Gate checker
    通過'
actual_tool_calls: 9
result_summary: 'DoD 7/7 通過。

  - memory/archived_projects/vietnam-expansion/context.md：frontmatter 移至 line 1，`#
  越南市場拓展專案 Context` heading 移至 frontmatter 後；Ruby YAML.safe_load 可正確解析 status / archived_date
  / revive_trigger

  - tasks/2026-04-17_evidence-gap-filling.yaml：allowed_tools 加入 `bash`，與該卡 actual_tool_calls
  記錄一致

  - ruby scripts/check_spec_consistency.rb ✅

  - python system/validate_task_card.py ✅（兩張卡皆通過）

  - python scripts/check_task_card_skill_type.py ✅（17 張卡）

  - ruby scripts/test_check_spec_consistency.rb ✅（14 runs, 0 failures）

  - python scripts/test_check_task_card_skill_type.py ✅（13 tests）

  '
completion_time: '2026-04-17'
```

```yaml
task_id: 20260417-O03
date: '2026-04-17'
skill_type: ops
goal: 為 COST_POLICY 加入校準係數章節，並將 WEEKLY_REVIEW_TEMPLATE 標注為 deprecated
status: done
risk_level: medium
approval_needed: true
output_path: system/, tasks/見 DoD
checkpoints:
- note: 'stage3-complete: COST_POLICY 校準係數與 WEEKLY_REVIEW deprecated 標記全部完成'
actual_tool_calls: 4
result_summary: 'DoD 7/7 通過。

  - system/COST_POLICY.md 新增「校準係數」章節（含 4 筆有實測的 skill 係數與使用方式）

  - tasks/WEEKLY_REVIEW_TEMPLATE.md 檔頭加入 DEPRECATED 標記，指向 RETRO_FLOW.md

  - system/RETRO_FLOW.md 觸發條件段落補註週期性觸發的歷史來源

  - spec consistency 與 task card 驗證皆通過

  '
completion_time: '2026-04-17'
```

```yaml
task_id: 20260417-O02
date: '2026-04-17'
skill_type: ops
goal: 修補完整度檢查揭露的兩類缺口：AUDIT_LOG 缺漏 2 筆、AUDIT_LOG 含事實錯誤註記；validate_task_card.py 不檢 Gate
  2 引用的 allowed_tools / max_tool_calls / expected_output.location 三欄位
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/investigation-2026-04-04-missing-artifacts.md
checkpoints:
- note: 'checkpoint: [20260417-O02] A1 調查報告完成、A2+A3 AUDIT_LOG 補登 + 更正、B1 validator
    擴充 3 檢查、B2 11 張 task card 全通過新版 validator'
actual_tool_calls: 13
result_summary: 'A1：確認 2026-04-04 組 7 個 expected_output 從未進 git 也不在本機；.gitignore 不實註記已查明。
  報告 outputs/drafts/investigation-2026-04-04-missing-artifacts.md。7 張卡 status 是否降級留待使用者決策。
  A2：AUDIT_LOG 追加 20260409-001 + 20260415-A01 兩筆補登。 A3：AUDIT_LOG 末尾新增 correction_note，不改寫舊
  entry。 B1：validate_task_card.py 增加 allowed_tools（list 非空）、max_tool_calls（正整數）、expected_output.location（非空）三項檢查。
  B2：11 張現存 task card 全部通過新版 validator（含本卡）；TEMPLATE 如預期因空欄位失敗，檢查有效。 後續待辦：7 張卡 status
  決策 + 補寫 7 個 artifact（另開 task card）。

  '
completion_time: '2026-04-17'
```

```yaml
task_id: 20260417-O02
date: '2026-04-17'
skill_type: ops
goal: 將 retro-2026-04-15 晉升為正式 report，並封存 vietnam-expansion 專案
status: done
risk_level: medium
approval_needed: true
output_path: outputs/reports/, memory/archived_projects/, system/, memory/見 DoD
checkpoints:
- note: 'stage2-complete: retro 晉升、vietnam 封存、RETRO_FLOW 更新，consistency 通過'
actual_tool_calls: 7
result_summary: 'DoD 7/7 通過。主要產出：

  - outputs/reports/retro-2026-Q2-01.md（含晉升標記與採納清單）

  - outputs/drafts/retro-2026-04-15.md 檔尾加回指

  - system/RETRO_FLOW.md 新增第 5 步「晉升至 reports/」

  - memory/archived_projects/vietnam-expansion/（git mv 保留歷史）

  - memory/README.md 補 archived_projects 段落

  附帶修正：tasks/examples/ 兩個 example Task Card 的 input_data 路徑更新為 archived_projects/

  '
completion_time: '2026-04-17'
```

```yaml
task_id: 20260417-O01
date: '2026-04-17'
skill_type: ops
goal: 將 2026-04-04 四張已完成但停留 review 狀態的任務卡 status 推進到 done，使之與同日 tools-inventory ×
  3 的終態一致
status: done
risk_level: low
approval_needed: false
output_path: tasks/2026-04-04_*.yaml (4 files modified)
checkpoints:
- note: 'checkpoint: [20260417-O01] 四張卡 status review→done 完成'
actual_tool_calls: 8
result_summary: 四張 2026-04-04 卡（S01/W01/RV01/O02）status 由 review 翻轉為 done。validator
  對四張皆通過，其他欄位未動。現 2026-04-04 共 7 張卡全部 done，狀態一致。
completion_time: '2026-04-17'
```

```yaml
task_id: 20260417-O01
date: '2026-04-17'
skill_type: ops
goal: 填補 retro-2026-04-15 發現的三項證據空白：Error Log 範例、Decision Log D005、Token 校準資料表
status: done
risk_level: low
approval_needed: false
output_path: logs/errors/, memory/active_projects/agent-harness/decisions/, outputs/drafts/見
  DoD
checkpoints:
- note: 'stage1-complete: 三檔案產出完成，spec consistency 通過'
actual_tool_calls: 4
result_summary: '三份檔案全部產出，DoD 5/5 通過。

  - logs/errors/2026-04-04_20260404-S01_error.md（含「歷史重建/非阻斷」檔頭標註）

  - memory/active_projects/agent-harness/decisions/20260415-D005_intake-fast-path.yaml

  - outputs/drafts/token-calibration-table-v1.md（含校準係數與 retro 數字一致性檢查）

  '
completion_time: '2026-04-17'
```

```yaml
task_id: 20260415-A01
date: '2026-04-15'
skill_type: analysis
goal: 評估是否應將 create_task_card 從 ask 升為 allow，給出有依據的建議排序
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/analysis-create-task-card-permission.md
checkpoints: []
actual_tool_calls: 0
result_summary: 建議升為 allow（條件：已驗證 8 筆全 approve）。已執行：PERMISSIONS.yaml + APPROVAL_POLICY.yaml
  更新，D004 Decision Log 補建。
completion_time: '2026-04-15'
```

```yaml
task_id: 20260412-001
date: '2026-04-12'
skill_type: ops
goal: 重建 2026-04-04 因 .gitignore 遺失的 4 份草稿檔案，依原始 Task Card 及 Audit Log 紀錄忠實還原內容
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/（4 個檔案，見 DoD）
checkpoints:
- note: '33f92a9: Task Card 建立'
- note: 'd59ff9a: 重建 solo-company-tools-inventory-v2.md'
- note: 'f3ce3d5: 重建 ai-era-solo-business-strategy.md'
- note: '4a10b73: 重建 ai-era-solo-business-proposal-v2.md'
- note: '0c02ab4: 重建 ai-era-solo-business-proposal-review.md'
actual_tool_calls: 13
result_summary: DoD 6/6 通過。重建 4 份草稿：(1) 工具盤點 v2：7 大類別、25+ 工具、四態格式；(2) 策略研究：5 大商業模式、台越市場機會、12
  月執行路徑；(3) 策略提案 v2：含定位宣言、服務菜單、ICP、競爭優勢、12 月計畫（M1-M3 修正+S1）；(4) 審查報告：有條件通過、3 必須修改、6
  建議、DoD 7 條確認。
completion_time: '2026-04-12'
```

```yaml
task_id: 20260409-001
date: '2026-04-09'
skill_type: review
goal: 驗證 Agent Harness v2.0 所有新增組件的可用性與流程完整性
status: done
risk_level: low
approval_needed: false
output_path: logs/runs/20260409-001_system-validation.yaml
checkpoints:
- note: Batch 4 完成（3 新檔 + 2 修改）
- note: Batch 5 完成（1 新檔 + 2 修改）
- note: 'Gate 驗證通過，DoD #3 修正完成'
actual_tool_calls: 9
result_summary: 7/7 DoD 通過。初次驗證發現 FAILURE_TAXONOMY 漏 SEC-04，已補正。四層 Gate 全部 pass。
completion_time: '2026-04-09'
```

```yaml
task_id: 20260404-W01
date: '2026-04-04'
skill_type: writing
goal: 根據研究結果（20260404-S01），產出一份完整的一人公司 AI 時代策略提案，可直接用於自我規劃或向潛在合作方展示
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/ai-era-solo-business-proposal.md
checkpoints:
- note: 'checkpoint: [20260404-W01] AI 策略提案草稿完成'
actual_tool_calls: 4
result_summary: 完整策略提案草稿完成。定位宣言、服務菜單（4項）、台越雙市場 ICP、三方競爭對比、12 個月月度計畫、4 個風險對策、本週執行起點。DoD
  7/7 通過。
completion_time: '2026-04-04'
```

```yaml
task_id: 20260404-S01
date: '2026-04-04'
skill_type: research
goal: 分析 AI 時代一人公司最具長遠獲利潛力的商業項目，結合用戶背景（管理顧問、台灣+越南市場）提供可執行策略建議
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/ai-era-solo-business-strategy.md
checkpoints:
- note: 'checkpoint: [20260404-S01] AI 策略研究完成'
actual_tool_calls: 6
result_summary: 識別前 5 商業模式，最推薦 AI 顧問×產品化服務。台灣+越南市場機會、管理顧問差異化優勢、12 個月執行路徑均已輸出至草稿。
completion_time: '2026-04-04'
```

```yaml
task_id: 20260404-RV01
date: '2026-04-04'
skill_type: review
goal: 審查 ai-era-solo-business-proposal.md 的邏輯一致性、事實正確性、風險完整性，確認可作為正式使用的策略文件
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/ai-era-solo-business-proposal-review.md
checkpoints:
- note: 'checkpoint: [20260404-RV01] 提案審查報告完成'
actual_tool_calls: 3
result_summary: 有條件通過。3 個必須修改（數字矛盾 × 2、Retainer 交付差異未說明），6 個建議修改。修正 M1-M3 後可升格正式版本。
completion_time: '2026-04-04'
```

```yaml
task_id: 20260404-R02
date: '2026-04-04'
skill_type: review
goal: 審查工具盤點報告的完整性、邏輯一致性與一人公司適用性
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/tools-inventory-review-report.md
checkpoints:
- note: '65b3c8a: Task Card 建立'
- note: '（此 commit）: review 完成'
actual_tool_calls: 2
result_summary: 有條件通過。DoD 5 條中 3 通過、2 部分通過。發現 2 個必須修改（知識管理類別缺失、採用狀態不一致），3 個建議修改。
completion_time: '2026-04-04'
```

```yaml
task_id: 20260404-R01
date: '2026-04-04'
skill_type: research
goal: 調查並整理一人公司運作所需的工具清單，按功能分類並評估現有採用狀況
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/solo-company-tools-inventory.md
checkpoints:
- note: '65b3c8a: Task Card 建立'
- note: '（下一個 commit hash）: research 完成'
actual_tool_calls: 3
result_summary: 整理 6 大工具類別（AI/專案管理/通訊/財務行政/行銷/自動化），共 20+ 工具，依採用狀態分類。已知事實 6 項，合理推論
  4 項，待驗證 6 項。
completion_time: '2026-04-04'
```

```yaml
task_id: 20260404-O02
date: '2026-04-04'
skill_type: ops
goal: 根據審查報告 RV01 的 3 個必須修改項，修正提案數字矛盾並補充 Retainer 交付差異，產出 v2 正式版
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/ai-era-solo-business-proposal-v2.md
checkpoints:
- note: 'checkpoint: [20260404-O02] 提案 v2 修正完成'
actual_tool_calls: 3
result_summary: M1/M2/M3 全部修正，S1 採納，另補強台灣 ICP 主次分離、越南渠道語言策略、風險 3 品牌時間成本、競爭優勢描述精準化。v2
  輸出完成。
completion_time: '2026-04-04'
```

```yaml
task_id: 20260404-O01
date: '2026-04-04'
skill_type: ops
goal: 修正 20260404-R02 review 發現的 2 個 must-fix 問題，完成工具盤點報告定稿
status: done
risk_level: low
approval_needed: false
output_path: outputs/drafts/solo-company-tools-inventory-v2.md
checkpoints:
- note: '（此 commit）: Task Card 建立 + v2 報告輸出完成'
actual_tool_calls: 4
result_summary: '修改項目清單：

  1. 新增「6. 知識管理」類別：Obsidian / Notion / Mem.ai / Readwise Reader / agent-harness memory/
  共 5 個工具，含採用狀態、月費估算、一人公司適用性評估

  2. 全 7 個類別採用狀態統一為四態格式（✅已用 / ✅推論已用 / 🔍待評估 / ❌不適用），移除所有自由文字描述

  3. 各類別補充已知事實 / 合理推論 / 待驗證標記

  4. 輸出：outputs/drafts/solo-company-tools-inventory-v2.md

  注意：原 v1 草稿因 .gitignore 未存磁碟，v2 依 Task Card context + audit log + memory/ 重建

  '
completion_time: '2026-04-04'
```
<!-- AUTO_AUDIT_END -->

## 人工備註

```yaml
- task_id: ""
  date: ""
  skill_type: ""           # research / analysis / writing / ops / review
  goal: ""                 # 一句話
  status: ""               # done / failed / partial
  model_used: ""           # claude-sonnet-4-20250514 等
  tools_called:            # 實際呼叫的工具清單
    - tool_name: ""
      call_count: 0
  checkpoints: 0           # checkpoint 次數
  approval_needed: false
  approval_given: false
  output_path: ""          # 輸出檔案路徑
  error_summary: ""        # 如有錯誤，簡述
  estimated_tokens: ""     # 預估 token（粗略即可）
  notes: ""                # 其他備註
```

---

## 紀錄（依時間倒序）

<!-- 新紀錄加在這裡 -->

```yaml
- task_id: "20260701-004"
  date: "2026-07-01"
  skill_type: "ops"
  goal: "R12（R2 補強）：跨檔案參照完整性 lint（run↔Task Card、approval↔run）"
  status: "done"
  model_used: "claude-sonnet-4-6"
  tools_called:
    - tool_name: "file_read"
      call_count: 3
    - tool_name: "file_write"
      call_count: 2
    - tool_name: "bash"
      call_count: 4
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "scripts/check_spec_consistency.rb"
  error_summary: ""
  estimated_tokens: "~14K"
  notes: "R1/R2/R5/R7 補強計畫 R12。新增 check_run_task_references()/check_approval_run_references() 雙向 ID 參照檢查（純函式）。test_check_spec_consistency.rb 新增 6 個測試（正常/斷鏈各半），全綠（共 33）。真實 repo 現有參照皆合法、無誤報。修改 scripts/ 影響 CI 行為，比照 R2/R11 approval_needed=true，批准紀錄見 logs/approvals/2026-07-01_20260701-004_approval.yaml（本次會話 plan-mode 核准）。"
```

---

```yaml
- task_id: "20260701-003"
  date: "2026-07-01"
  skill_type: "ops"
  goal: "R11（R1 補強）：批准覆蓋率交叉檢查"
  status: "done"
  model_used: "claude-sonnet-4-6"
  tools_called:
    - tool_name: "file_read"
      call_count: 4
    - tool_name: "file_write"
      call_count: 2
    - tool_name: "bash"
      call_count: 5
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "scripts/check_spec_consistency.rb"
  error_summary: ""
  estimated_tokens: "~16K"
  notes: "R1/R2/R5/R7 補強計畫 R11。新增 check_approval_coverage() 純函式，檢查 approval_needed=true 且 status=done/failed 的 Task Card 是否有對應 logs/approvals/ 紀錄。發現真實缺口：10+ 筆歷史任務（含 R1/R2 自己）從未有批准紀錄，因無真實來源可誠實回填，改用 cutoff=2026-07-01 只管未來、不追溯歷史。test 新增 7 個，全綠（共 27）。approval_needed=true（比照 R2），批准紀錄見 logs/approvals/2026-07-01_20260701-003_approval.yaml。"
```

---

```yaml
- task_id: "20260701-002"
  date: "2026-07-01"
  skill_type: "ops"
  goal: "R13（R5 補強）：執行 Scenario C（context 重置接續）恢復演練"
  status: "done"
  model_used: "claude-sonnet-4-6"
  tools_called:
    - tool_name: "file_read"
      call_count: 5
    - tool_name: "file_write"
      call_count: 4
    - tool_name: "bash"
      call_count: 6
  checkpoints: 3
  approval_needed: true
  approval_given: true
  output_path: "system/RECOVERY_RUNBOOK.md"
  error_summary: ""
  estimated_tokens: "~15K"
  notes: "R1/R2/R5/R7 補強計畫 R13。RECOVERY_RUNBOOK.md 附錄明確標註 Scenario C 從未實測，本卡補上：以 tests/e2e/fixtures/scenario_c_progress.yaml 模擬 3-checkpoint 任務，checkpoint 2 後模擬 context 重置，僅靠 git log --grep + Task Card + 進度檔三個來源重建狀態並正確接續（diff 驗證為純新增，未重做 step 1/2）。四個恢復場景（A/B/D 既有、C 本次）皆已有實測證據。修改 system/，approval_needed=true，批准紀錄見 logs/approvals/2026-07-01_20260701-002_approval.yaml（本次會話 plan-mode 核准）。"
```

---

```yaml
- task_id: "20260701-001"
  date: "2026-07-01"
  skill_type: "ops"
  goal: "R14（R7 補強）：前端 M2-M4 治理警示可視化"
  status: "done"
  model_used: "claude-sonnet-4-6"
  tools_called:
    - tool_name: "file_read"
      call_count: 6
    - tool_name: "file_write"
      call_count: 6
    - tool_name: "bash"
      call_count: 5
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "frontend/app.js"
  error_summary: ""
  estimated_tokens: "~18K"
  notes: "R1/R2/R5/R7 補強計畫 R14。governance_metrics.py 的 load_audit_task_ids/load_native_overlap 加可選 root 參數（向下相容）；generate_frontend_manifest.py 新增 build_governance_alerts() 重用 M2/M3/M4（M1 因日期相依性明確排除，理由見程式碼註解，避免破壞 data.json 的 CI drift-check 決定性）。前端新增治理警示 section + 顏色 badge，Playwright 截圖確認正確渲染。新增/更新測試全綠。未動 system/。"
```

---

```yaml
- task_id: "20260623-002"
  date: "2026-06-23"
  skill_type: "analysis"
  goal: "R10：v3 遷移就緒度評估（只評估不遷移，對齊 A01，提出 D003/D007 加註）"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 5
    - tool_name: "create_output_files"
      call_count: 3
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "outputs/drafts/2026-06-23_v3-readiness-assessment.md"
  error_summary: ""
  estimated_tokens: "~17K"
  notes: "roadmap R10（最後一項策略層）。結論：維持 v2 hold——T-A（D003 規模觸發）+ T-B（NATIVE_OVERLAP 30% 重疊觸發）皆未達標；執行就緒度 ≈7.6/10（A01 裁決 + D007 bootstrap 已備）。逐模組 14 ready/2 partial，下放原生5/並存11/保留0。校正 A01 §4.2 摘要列計數出入。不可替代資產 4 類 + R7 引擎。D003/D007 以 proposed diff 加註（ask 待確認，故 approval_given=false）。識別 R11：T-A 觸發自動化與 R9 T-B 偵測合流。analysis skill 首筆樣本（補 R3）。"
```

---

```yaml
- task_id: "20260623-001"
  date: "2026-06-23"
  skill_type: "ops"
  goal: "R9：NATIVE_OVERLAP 季度 revisit 自動化（M4 staleness + v3 觸發 + 與 R4 RETRO 合流）"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 6
    - tool_name: "create_output_files"
      call_count: 6
  checkpoints: 3
  approval_needed: true
  approval_given: true
  output_path: "scripts/governance_metrics.py"
  error_summary: ""
  estimated_tokens: "~14K"
  notes: "roadmap R9（R1–R8 已完成）。M4 加 today 參數（向後相容）：reviewed_on 逾 revisit_interval_days（NATIVE_OVERLAP 設 90）→ revisit_due 且 ok 升 warn（不下調 alert）；pct>50 → v3_trigger，render 建議產出 v3-readiness-assessment.md（R10）。test 加 11 案例並接入 CI（原未跑）。system/ 變更（RETRO_FLOW『原生重疊回看』列 + NATIVE_OVERLAP revisit_interval_days）經人工確認（選項 1.2）。全套 CI-equivalent 綠。DoD 6/6。"
```

---

```yaml
- task_id: "20260529-011"
  date: "2026-05-29"
  skill_type: "ops"
  goal: "R7（前端）：治理總覽面板（task/run/gate 分佈接進 dashboard）"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 4
    - tool_name: "file_write"
      call_count: 5
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "frontend/app.js"
  error_summary: ""
  estimated_tokens: "~16K"
  notes: "R7 延後項補齊。manifest build_overview（由既有 tasks+logs 計算，無額外讀檔）→ data.json 新增 overview 鍵；唯一鎖定結構的 test_empty_repo 同步更新；index.html + app.js renderOverview 以既有 .cards 樣式渲染。frontend 測試 + drift --check 綠。未動 system/。R7 至此（引擎+報告+面板）完整。"
```

---

```yaml
- task_id: "20260529-010"
  date: "2026-05-29"
  skill_type: "ops"
  goal: "R8：災難恢復 runbook + checkpoint 還原實測 + GATE_POLICY 交叉引用"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 3
    - tool_name: "file_write"
      call_count: 3
  checkpoints: 1
  approval_needed: true
  approval_given: false
  output_path: "system/RECOVERY_RUNBOOK.md"
  error_summary: ""
  estimated_tokens: "~14K"
  notes: "R8。新增 system/RECOVERY_RUNBOOK.md（4 場景 + 資料來源 + 一致性檢查 + GATE_POLICY rollback 對應）。實測場景 A：破壞工作副本→git checkout 還原 ~5ms、byte-identical、還原後工作樹乾淨。GATE_POLICY 加交叉引用。修改 system/ 屬 ask，變更在草稿 PR #88 待 review/merge。"
```

---

```yaml
- task_id: "20260529-009"
  date: "2026-05-29"
  skill_type: "ops"
  goal: "R7：governance_metrics 補工作流/業務/失敗三層可觀測性 + --observability + 報告"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 6
    - tool_name: "file_write"
      call_count: 4
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/2026-05-29_observability-metrics.md"
  error_summary: ""
  estimated_tokens: "~22K"
  notes: "R7。governance_metrics.py 補三層可觀測性（工作流 gate 統計/業務每-skill token/失敗分佈）+ --observability flag + 7 新測試（含 --json 仍 M1–M4 回歸守門，27 測試全綠）。觀測立刻抓到 review 均值被 120K 多代理離群值拉高。未改 system/、未動 CI。前端面板刻意延後（避免 data.json schema/CI 風險）。"
```

---

```yaml
- task_id: "20260529-008"
  date: "2026-05-29"
  skill_type: "ops"
  goal: "R6：EXECUTION_LOG_SCHEMA token_estimate 增加 source（可信度）欄位 + 示範回填"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 2
    - tool_name: "file_write"
      call_count: 3
  checkpoints: 1
  approval_needed: true
  approval_given: false
  output_path: "system/EXECUTION_LOG_SCHEMA.yaml"
  error_summary: ""
  estimated_tokens: "~7K"
  notes: "R6。token_estimate 新增 source 欄（dashboard_measured/rule_estimated/not_recorded）；RUN-20260529-003 示範 source=rule_estimated。修改 system/ 屬 ask，變更在草稿 PR #88 待 review/merge。"
```

---

```yaml
- task_id: "20260529-007"
  date: "2026-05-29"
  skill_type: "ops"
  goal: "R4：決策 revisit 追蹤器（唯讀掃描 + 量化觸發比對）+ 測試入 CI + RETRO_FLOW 整合"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 5
    - tool_name: "file_write"
      call_count: 4
  checkpoints: 1
  approval_needed: true
  approval_given: false
  output_path: "scripts/check_decision_revisit.rb"
  error_summary: ""
  estimated_tokens: "~12K"
  notes: "新增 check_decision_revisit.rb（唯讀；D001 並行任務數/D006 runs 數量化比對 → DUE/OK，其餘 MANUAL；--json）+ 單元測試（接入 CI）。本機跑 7 筆全列、DUE=0。RETRO_FLOW 加『決策回看』列屬 system/ ask、workflow 加測試步驟——皆在草稿 PR #88 待 review。"
```

---

```yaml
- task_id: "20260529-006"
  date: "2026-05-29"
  skill_type: "analysis"
  goal: "R3：治理數據分析（產出發現 + 貢獻 analysis 成本校準樣本 #1）"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 6
    - tool_name: "file_write"
      call_count: 2
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/2026-05-29_governance-data-analysis.md"
  error_summary: ""
  estimated_tokens: "~16K"
  notes: "R3。analysis skill 成本實測樣本 #1（~16K，COST_POLICY 原預估 12K → 初估係數 ~1.33，待累積 ≥3 筆於 RETRO 正式計算）。分析 39 task cards / audit 94.3% / draft:report 8:1 / logs runs2-appr1-err2 / 7 決策 0 revisit。未改 system/。"
```

---

```yaml
- task_id: "20260529-005"
  date: "2026-05-29"
  skill_type: "ops"
  goal: "R2：擴充 check_spec_consistency.rb，把 logs/runs、logs/approvals、logs/errors 納入 CI schema lint"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 6
    - tool_name: "file_write"
      call_count: 4
  checkpoints: 1
  approval_needed: true
  approval_given: false
  output_path: "scripts/check_spec_consistency.rb"
  error_summary: ""
  estimated_tokens: "~14K"
  notes: "新增 3 段 logs schema lint（runs 必填+status 枚舉 / approvals 必填+method+status 枚舉，跳過 TEMPLATE / errors 抽 yaml 驗 error_type 枚舉）+ 6 個單元測試。本機 CI 抓到並修正 error-log 讀檔的 US-ASCII 編碼 bug（改 UTF-8）。正反向測試皆通過。影響 CI 行為，待草稿 PR #88 review/merge（approval_given 待人工）。"
```

---

```yaml
- task_id: "20260529-004"
  date: "2026-05-29"
  skill_type: "ops"
  goal: "R1：定義 approval_record schema、建模板、回填首筆真實批准紀錄"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 5
    - tool_name: "file_write"
      call_count: 5
  checkpoints: 1
  approval_needed: true
  approval_given: false
  output_path: "logs/approvals/2026-04-09_20260409-001_approval.yaml"
  error_summary: ""
  estimated_tokens: "~13K"
  notes: "在 system/APPROVAL_POLICY.yaml 新增 approval_record schema（與 EXECUTION_LOG_SCHEMA approvals 對齊）+ APPROVAL_LOG_TEMPLATE.yaml + 回填 RUN-20260409-001 的 2 筆批准 + RETRO_FLOW 註記。修改 system/ 屬 ask：變更在草稿 PR #88，未 merge＝『列差異、等待確認』狀態，approval_given 待人工。"
```

---

```yaml
- task_id: "20260529-003"
  date: "2026-05-29"
  skill_type: "ops"
  goal: "R5 故障演練：實證 logs/errors/ + logs/runs/(status: failed) 失敗紀錄路徑 + e2e 回歸測試"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 5
    - tool_name: "file_write"
      call_count: 5
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "logs/runs/RUN-20260529-003.yaml"
  error_summary: ""
  estimated_tokens: "~12K"
  notes: "R5（自我評估 roadmap 單一最高槓桿）。演練本身成功（status: done）：以 tests/e2e/fixtures/broken_schema_task.yaml 觸發受控 schema_failure，首次在真實故障下填寫 logs/runs/RUN-20260529-003.yaml（status: failed, schema_check: fail）+ logs/errors/。新增 tests/e2e/test_failure_drill.py 並接入 CI（spec-consistency.yml）。未修改任何 system/ 檔。"
```

---

```yaml
- task_id: "20260529-002"
  date: "2026-05-29"
  skill_type: "ops"
  goal: "晉升自我評估草稿至 outputs/reports/（harness-self-assessment-v1.md）"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 2
    - tool_name: "file_write"
      call_count: 3
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "outputs/reports/harness-self-assessment-v1.md"
  error_summary: ""
  estimated_tokens: "~8K"
  notes: "依 RETRO_FLOW §5 晉升：reports/ 加晉升標記區塊（採納清單），原 draft 加回指。內容與 draft 一致，未修改 system/。寫 reports/ 屬 ask，使用者於本 session 明確核准。"
```

---

```yaml
- task_id: "20260529-001"
  date: "2026-05-29"
  skill_type: "review"
  goal: "Agent Harness v2 自我評估（雙軸 1-10）+ R1–R10 優化 roadmap"
  status: "done"
  model_used: "claude-opus"
  tools_called:
    - tool_name: "file_read"
      call_count: 12
    - tool_name: "web_search"
      call_count: 3
    - tool_name: "file_write"
      call_count: 2
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/2026-05-29_harness-self-assessment.md"
  error_summary: ""
  estimated_tokens: "~120K（含 2 探索 + 1 plan 子代理；屬多代理研究型任務，不宜直接併入 review 校準均值）"
  notes: "綜合 ≈7/10、成熟度 3。雙軸評分（業界十維均 7.2 / 馬鞍工程六原則均 7.0）。校正 3 項原始誤判：approvals 目錄其實存在（僅缺 schema）、CI 其實有跑一致性檢查、analysis eval 其實最長（真缺口是 analysis 成本樣本=0）。單一最高槓桿＝R5 故障演練。未修改任何 system/ 檔。"
```

---

```yaml
- task_id: "20260509-M01"
  date: "2026-05-09"
  skill_type: "ops"
  goal: "原生 Memory PoC 卡建立（symlink + namespace 試點）— N07 後續候補"
  status: "pending"
  model_used: "—"
  tools_called: []
  checkpoints: 0
  approval_needed: true
  approval_given: false
  output_path: "tasks/2026-05-09_native-memory-poc.yaml"
  error_summary: ""
  estimated_tokens: "—"
  notes: "risk=medium，依 N07 §7.1 建立。本 PR 僅含卡片本身，等使用者明示核准後另開 session 執行 PoC（symlink、寫入提示實測、token 預算量測、雙系統決策樹）。"
```

---

```yaml
- task_id: "20260509-N06"
  date: "2026-05-09"
  skill_type: "ops"
  goal: "v3 governance plugin bootstrap — 在 drafts/ 完整準備 plugin v0.1.0 檔樹（受工具限制無法直接建外部 repo）"
  status: "review"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 5
    - tool_name: "file_write"
      call_count: 14
    - tool_name: "file_edit"
      call_count: 4
    - tool_name: "bash"
      call_count: 8
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "outputs/drafts/agent-governance-bootstrap/; outputs/drafts/2026-05-09_n06_v3-plugin-bootstrap.md; memory/active_projects/agent-harness/decisions/20260509-D007_v3-plugin-bootstrap-decisions.yaml"
  error_summary: "本 session GitHub MCP 限定 agent-harness 單一 repo，無法直接建外部 agent-governance repo；DoD #6 (harness 切換引用 plugin) 與 #8 (CI 驗證) 留下個 session。"
  estimated_tokens: "~45K"
  notes: "使用者於 PR #69 明示核准 + 4 子題決策（D007）：repo=agent-governance / Apache-2.0 / Private / 獨立 repo。本 session 完成 DoD 7/9：plugin.json + 5 commands + 4 schemas + 2 hooks(8 tests) + 2 validators(13 tests) + LICENSE + README + CHANGELOG + CI workflow + D007。Plugin tests 25/25 pass。下個 session 5 步遷移指南見 outputs/drafts/2026-05-09_n06_v3-plugin-bootstrap.md §4。"
```

---

```yaml
- task_id: "20260509-N08"
  date: "2026-05-09"
  skill_type: "writing"
  goal: "W01 部落格首篇 elevator pitch + 第 1 章草稿（為什麼一人公司需要 Agent 治理？）"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 2
    - tool_name: "file_write"
      call_count: 1
    - tool_name: "file_edit"
      call_count: 1
    - tool_name: "bash"
      call_count: 1
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/2026-05-09_n08_w01-chapter-one-draft.md"
  error_summary: ""
  estimated_tokens: "~12K"
  notes: "Elevator pitch ~180 字（≤200 ✅）+ 第 1 章草稿 ~3,650 字（≥3,200 ✅）。實證引用 20260404-S01 已比對 logs/AUDIT_LOG.md 第 575-594 行原文。未引用 LangChain/Chip Huyen/Anthropic 任何句子（嚴格做法）。章末 hook 導向第 2 章三原則總覽。"
```

---

```yaml
- task_id: "20260509-N07"
  date: "2026-05-09"
  skill_type: "analysis"
  goal: "評估啟用 Claude Code 原生 Memory（plan §3.5 痛點）"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 4
    - tool_name: "file_write"
      call_count: 1
    - tool_name: "bash"
      call_count: 1
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/2026-05-09_n07_native-memory-evaluation.md"
  error_summary: ""
  estimated_tokens: "~10K"
  notes: "建議 Conditional-Go：4 條啟用條件（C1 寫入須人工確認；C2 namespace 限定，不接管 decisions/plans 結構化 YAML；C3 不走雲同步；C4 與 N6 plugin 相容）。比照 N3 Skills symlink 模式可避免雙寫漂移。後續候補 M1 PoC + M2 PERMISSIONS 收斂。3 項待驗證留至 M1 工具實測。"
```

---

```yaml
- task_id: "20260509-N05"
  date: "2026-05-09"
  skill_type: "ops"
  goal: "governance metrics 自動採集腳本 — 落地 plan §5.3 4 條關鍵指標"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 2
    - tool_name: "file_write"
      call_count: 4
    - tool_name: "file_edit"
      call_count: 2
    - tool_name: "bash"
      call_count: 3
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "scripts/governance_metrics.py; scripts/test_governance_metrics.py; system/NATIVE_OVERLAP.yaml; outputs/drafts/governance-metrics-2026-05.md"
  error_summary: ""
  estimated_tokens: "~14K"
  notes: "採集 4 指標 + warn/alert 分級。15 unit tests 全綠。本月實跑全 ok：M1 月 16/11 / M2 比 9.50 / M3 覆蓋 92.3%（2 卡漏 audit）/ M4 重疊 30%。M4 採人工 input（NATIVE_OVERLAP.yaml，每季 review）。不加進 spec-consistency CI；月度人工觸發。"
```

---

```yaml
- task_id: "20260509-N02"
  date: "2026-05-09"
  skill_type: "review"
  goal: "修正 audit 計數錯誤歸因（README 寫 30+ → 實際是 plan/task card context）並校正計數"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 1
    - tool_name: "file_search"
      call_count: 2
    - tool_name: "file_write"
      call_count: 2
    - tool_name: "file_edit"
      call_count: 8
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/2026-05-09_n02_audit-count-fix.md"
  error_summary: ""
  estimated_tokens: "~10K"
  notes: "事實核對：README 從無 30+ 字樣；真正出處為 plan §Context + task card context。本 PR 前實 18 筆 audit（A01 自寫 17 也偏少 1）。建立 snapshot/事實/規範三類文件的計數更新規則。Root cause：SPEC-04 + VAL-03（草稿引用未交叉驗證）。"
```

---

```yaml
- task_id: "20260509-N01"
  date: "2026-05-09"
  skill_type: "review"
  goal: "plan 歸檔 repo + A01/W01 與 plan §8.1 對齊報告 + 清除已解 [待驗證]"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 1
    - tool_name: "file_write"
      call_count: 2
    - tool_name: "file_edit"
      call_count: 6
    - tool_name: "bash"
      call_count: 1
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/2026-05-09_n01_plan-alignment.md; memory/active_projects/agent-harness/plans/ai-bubbly-mountain.md"
  error_summary: ""
  estimated_tokens: "~14K"
  notes: "A01 vs Task A: 5/5 + 2 over-deliver; W01 vs Task B: 5/5 + 2 over-deliver; 順序「先 A 後 B」符合 plan §8.2。Plan §5.3 4 條關鍵指標未被 A01/W01 採納 → 建議開 N5（governance metrics 自動採集）。命名漂移（_ vs -）與工具詞彙差異記錄但不修。"
```

---

```yaml
- task_id: "20260509-N04"
  date: "2026-05-09"
  skill_type: "writing"
  goal: "起草 agent-governance plugin manifest skeleton（介面契約，不寫實作）"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 2
    - tool_name: "file_write"
      call_count: 2
    - tool_name: "file_edit"
      call_count: 3
    - tool_name: "bash"
      call_count: 1
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/2026-05-09_n04_governance-plugin-skeleton.md"
  error_summary: ""
  estimated_tokens: "~16K"
  notes: "5 command + 4 schema + 2 hook + 2 validator 介面契約全部完成。L2「PostTaskUse hook 是否原生支援」標 [待驗證]。建議下一步：起 task card（risk=high，需人工核准）真正建立 agent-governance 獨立 repo。"
```

---

```yaml
- task_id: "20260509-N03"
  date: "2026-05-09"
  skill_type: "ops"
  goal: "PoC: skills/research/SKILL.md 加原生 Skills frontmatter + .claude/skills/ 註冊，驗證 A01 H1"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 3
    - tool_name: "file_write"
      call_count: 2
    - tool_name: "file_edit"
      call_count: 3
    - tool_name: "bash"
      call_count: 4
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "outputs/drafts/2026-05-09_n03_skills-native-poc.md"
  error_summary: ""
  estimated_tokens: "~12K"
  notes: "H1 部分成立：routing 表可由 frontmatter description 取代；但「跨 skill 拆 Task Card」原則屬 prompt 層工作流，需保留至 CLAUDE.md。A01 §4.2 裁決不需修改（已預寫此句）。symlink 路徑（.claude/skills/research → ../../skills/research）避免雙寫漂移。session 啟動時序：新 session 才能驗證自動觸發。"
```

---

```yaml
- task_id: "20260509-W01"
  date: "2026-05-09"
  skill_type: "writing"
  goal: "把 Harness 治理思想轉寫成方法論大綱（書／部落格／課程三形態）"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 4
    - tool_name: "file_search"
      call_count: 1
    - tool_name: "file_write"
      call_count: 1
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/2026-05-09_methodology_outline.md"
  error_summary: ""
  estimated_tokens: "~18K"
  notes: "12 章大綱、每章含實證案例、三形態取捨（推薦：部落格→課程→書）、與 LangChain/Chip Huyen/Anthropic 差異化、2 個反對意見預備回應。建立在 A01 的保留／抽出清單之上。Plan §8.1 Task B 對齊與 Chip Huyen ToC 比對標 [待驗證]。零 web_search（max_web_searches=3 全保留）。"
```

---

```yaml
- task_id: "20260509-A01"
  date: "2026-05-09"
  skill_type: "analysis"
  goal: "規劃 Harness v3 重構範圍：砍除與 Claude Code 原生重疊的模組，把治理三件抽成獨立治理層"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 9
    - tool_name: "file_search"
      call_count: 2
    - tool_name: "file_write"
      call_count: 1
  checkpoints: 1
  approval_needed: true
  approval_given: false
  output_path: "outputs/drafts/2026-05-09_v3_extraction_plan.md"
  error_summary: ""
  estimated_tokens: "~22K"
  notes: "規劃階段，不動既有代碼。16 模組裁決：保留 0 / 砍除 5 / 抽出 6 / 重構 5。治理層 plugin 邊界＋遷移路徑＋4 個風險已列。Plan 檔 /root/.claude/plans/ai-bubbly-mountain.md 此 session 不可讀，相關推論已標 [待驗證]。Risk=medium → drafts/ 等待人工審閱。"
```

---

```yaml
- task_id: "20260502-T03"
  date: "2026-05-02"
  skill_type: "research"
  goal: "台灣 AI 產業深度研究（Deep Dive）：7 切片 + 量化 + 政策 + 12 月日曆 + 敏感性分析"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "web_search"
      call_count: 5
    - tool_name: "file_read"
      call_count: 1
    - tool_name: "file_write"
      call_count: 1
  checkpoints: 0
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/20260502-T03_taiwan-ai-industry-deep-dive.md"
  error_summary: ""
  estimated_tokens: "~42K"
  notes: "Cost-quality 系列第 3 張（最高投入）。完整 7 切片含 AI 伺服器 ODM（鴻海/廣達/緯創）、國防 AI、量化財務數據；政策法規含 AI 基本法 2026-01-14 施行 + PDPA 2025-11 修法 + 5 大補貼程式；12 個月機會日曆（COMPUTEX/GTC/SEMICON）；6 條敏感性假設。對 T01/T02 cost-quality 結論：5 search 多出『政策時序 + 敏感性 + 事件日曆』，這三項對顧問決策最直接。"
```

---

```yaml
- task_id: "20260502-T02"
  date: "2026-05-02"
  skill_type: "research"
  goal: "台灣 AI 產業標準研究（Standard）：5 切片 + 政策補貼 + 顧問切入點列舉"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "web_search"
      call_count: 3
    - tool_name: "file_write"
      call_count: 1
  checkpoints: 0
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/20260502-T02_taiwan-ai-industry-standard.md"
  error_summary: ""
  estimated_tokens: "~24K"
  notes: "Cost-quality 系列第 2 張。3 web searches 補完 T01 缺口：本地 SaaS 玩家具名（Appier 唯一獨角獸 + Perfect/iKala/CyberLink/Kdan/Aiello/Trend Micro）、政府補貼具體金額（NT$46B/NT$310M/NT$100K/SBIR）、5 切片含醫療與金融。對顧問背景列舉 5 切入點（不評估 ROI）。"
```

---

```yaml
- task_id: "20260502-T01"
  date: "2026-05-02"
  skill_type: "research"
  goal: "台灣 AI 產業快速掃描（Quick Scan）：3 切片 executive brief，作為 cost-quality 對照基準"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "web_search"
      call_count: 1
    - tool_name: "file_write"
      call_count: 1
  checkpoints: 0
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/20260502-T01_taiwan-ai-industry-quick-scan.md"
  error_summary: ""
  estimated_tokens: "~9K"
  notes: "Cost-quality 系列第 1 張（最低投入）。1 web search 限制下 3 切片（半導體 / IPC 邊緣 AI / SaaS）+ 3 趨勢 + 2 高風險假設。SaaS 段資料不足明確標 [待驗證]，由 T02 補完。預算狀態 tool_calls 2/3、web_searches 1/1。"
```

---

```yaml
- task_id: "20260502-A01"
  date: "2026-05-02"
  skill_type: "ops"
  goal: "Phase A：補齊規則 enforcement 與觀測自動化（PreToolUse hook、audit log generator、e2e smoke test）"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 12
    - tool_name: "file_write"
      call_count: 9
    - tool_name: "file_edit"
      call_count: 4
    - tool_name: "bash"
      call_count: 8
  checkpoints: 0
  approval_needed: true
  approval_given: false
  output_path: "outputs/drafts/2026-05-02_project-completeness-analysis.md; outputs/drafts/20260502-A01_phase-a-summary.md; tasks/2026-05-02_phase-a-enforcement-and-observability.yaml; .claude/settings.json; scripts/permissions_guard.py; scripts/test_permissions_guard.py; scripts/generate_audit_log.py; scripts/test_generate_audit_log.py; tests/e2e/test_dummy_task_smoke.py; .github/workflows/spec-consistency.yml; frontend/data.json"
  error_summary: ""
  estimated_tokens: "~28K"
  notes: "Phase A of post-v2 第一性原理改善計畫。3 件事落地：(A1) PreToolUse hook 把 PERMISSIONS deny 改 runtime 攔截、(A2) audit log generator opt-in（不接管現有手寫紀錄，等待後續遷移卡）、(A3) e2e dummy task 跑 4 gate contract pinning。Local CI 全綠。Phase B/C 另開 task card。"
```

---

```yaml
- task_id: "20260427-F01"
  date: "2026-04-27"
  skill_type: "ops"
  goal: "收斂 PR #55 為前端平台的最小可審核 baseline：穩定 YAML 解析、防 manifest 漂移、補 generator 測試與 CI 護欄"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 8
    - tool_name: "file_write"
      call_count: 5
    - tool_name: "file_edit"
      call_count: 6
    - tool_name: "bash"
      call_count: 6
    - tool_name: "github_mcp"
      call_count: 4
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "scripts/generate_frontend_manifest.py; frontend/data.json; frontend/app.js; scripts/test_generate_frontend_manifest.py; .github/workflows/spec-consistency.yml; scripts/run_frontend.sh; README.md; outputs/drafts/20260427-F01_phase0-summary.md; tasks/2026-04-27_frontend-platform-phase0.yaml"
  error_summary: ""
  estimated_tokens: "~18K"
  notes: "Phase 0 of frontend platform plan. PR #55 baseline 收斂：YAML→data.json、多 project decisions glob、generator unit tests (4 cases)、CI 漂移檢查。frontend/manifest.js 移除。Phase 1 (Gate/Approval/Failure 視覺化) 另開 task card。"
```

---

```yaml
- task_id: "20260424-O03"
  date: "2026-04-24"
  skill_type: "ops"
  goal: "為 CLAUDE.md/GLOBAL_RULES 3K token 硬限制加 CI 檢查，並對 Execution Log Schema 落地率低做收斂決策"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 1
    - tool_name: "file_write"
      call_count: 5
    - tool_name: "file_edit"
      call_count: 4
    - tool_name: "bash"
      call_count: 4
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "scripts/check_context_budget.rb; scripts/test_check_context_budget.rb; .github/workflows/spec-consistency.yml; system/EXECUTION_LOG_SCHEMA.yaml; memory/active_projects/agent-harness/decisions/20260424-D006_execution-log-scope.yaml; outputs/drafts/20260424-O03_guardrails-summary.md"
  error_summary: ""
  estimated_tokens: "~14K"
  notes: "Stage 3 of C 全面優化。DoD 9/9 通過。context budget 首次量化（554/3000, 18.5%）；Execution Log 選 Narrow Scope 僅 failed/partial/high-risk/多 checkpoint 任務寫 runs/。Decision Log D006 為專案第 6 筆結構化決策。"
```

---

```yaml
- task_id: "20260424-O02"
  date: "2026-04-24"
  skill_type: "ops"
  goal: "將 token-calibration-table 晉升為治理 artifact，調整 INTAKE_FLOW 主路為快速路徑，正式歸檔 WEEKLY_REVIEW_TEMPLATE"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 2
    - tool_name: "file_write"
      call_count: 3
    - tool_name: "file_edit"
      call_count: 4
    - tool_name: "bash"
      call_count: 3
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "outputs/reports/token-calibration-v1.md; outputs/drafts/20260424-O02_restructure-summary.md; system/INTAKE_FLOW.md; system/COST_POLICY.md; system/RETRO_FLOW.md; tasks/archived/WEEKLY_REVIEW_TEMPLATE.md; README.md"
  error_summary: ""
  estimated_tokens: "~15K"
  notes: "Stage 2 of C 全面優化。DoD 8/8 通過。token-calibration 正式晉升（drafts→reports）；INTAKE_FLOW fast-path 升為預設主路；WEEKLY_REVIEW_TEMPLATE git mv 至 tasks/archived/。歷史引用保留，活性引用全部同步。"
```

---

```yaml
- task_id: "20260424-O01"
  date: "2026-04-24"
  skill_type: "ops"
  goal: "收斂重複的 task card 驗證器為單一事實來源，補 SECURITY 發現性，清理重複 CI"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 3
    - tool_name: "file_write"
      call_count: 2
    - tool_name: "file_edit"
      call_count: 3
    - tool_name: "bash"
      call_count: 2
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "outputs/drafts/20260424-O01_cleanup-summary.md; scripts/ (-2); .github/workflows/ (-1, ~1); README.md"
  error_summary: ""
  estimated_tokens: "~10K"
  notes: "Stage 1 of C 全面優化。DoD 8/8 通過。sample-data 發現非空已於 DoD 說明；Python CI step 全撤。spec-consistency / ruby tests / yaml parse 全綠。"
```

---

```yaml
- task_id: "20260417-O03"
  date: "2026-04-17"
  skill_type: "ops"
  goal: "為 COST_POLICY 加入校準係數章節，並將 WEEKLY_REVIEW_TEMPLATE 標注為 deprecated"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 1
    - tool_name: "file_edit"
      call_count: 4
    - tool_name: "bash"
      call_count: 2
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "system/COST_POLICY.md, tasks/WEEKLY_REVIEW_TEMPLATE.md, system/RETRO_FLOW.md"
  error_summary: ""
  estimated_tokens: "~10K"
  notes: "Stage 3 of optimization plan. 新章節數值與 token-calibration-table-v1.md 一致。DoD 7/7 通過，spec consistency 通過。"
```

---

```yaml
- task_id: "20260417-O02"
  date: "2026-04-17"
  skill_type: "ops"
  goal: "將 retro-2026-04-15 晉升為正式 report，並封存 vietnam-expansion 專案"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 4
    - tool_name: "file_write"
      call_count: 1
    - tool_name: "file_edit"
      call_count: 6
    - tool_name: "bash"
      call_count: 3
  checkpoints: 1
  approval_needed: true
  approval_given: true
  output_path: "outputs/reports/retro-2026-Q2-01.md, memory/archived_projects/vietnam-expansion/, system/RETRO_FLOW.md"
  error_summary: ""
  estimated_tokens: "~15K"
  notes: "Stage 2 of optimization plan. 使用者已於規劃階段核准四項決策。發現 examples/ 兩張 Task Card 引用舊路徑，一併修正。DoD 7/7 通過，spec consistency 通過。"
```

---

```yaml
- task_id: "20260417-O01"
  date: "2026-04-17"
  skill_type: "ops"
  goal: "填補 retro-2026-04-15 發現的三項證據空白：Error Log 範例、Decision Log D005、Token 校準資料表"
  status: "done"
  model_used: "claude-opus-4-7"
  tools_called:
    - tool_name: "file_read"
      call_count: 6
    - tool_name: "file_write"
      call_count: 3
    - tool_name: "bash"
      call_count: 2
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "logs/errors/2026-04-04_20260404-S01_error.md, memory/active_projects/agent-harness/decisions/20260415-D005_intake-fast-path.yaml, outputs/drafts/token-calibration-table-v1.md"
  error_summary: ""
  estimated_tokens: "~12K"
  notes: "Stage 1 of agent-harness optimization plan. DoD 5/5 通過。spec consistency check 通過。全 allow 權限範圍，無阻斷。"
```

---

```yaml
- task_id: "20260404-O02"
  date: "2026-04-04"
  skill_type: "ops"
  goal: "修正審查報告 M1-M3，產出提案 v2 正式版"
  status: "done"
  model_used: "claude-sonnet-4-6"
  tools_called:
    - tool_name: "file_read"
      call_count: 1
    - tool_name: "file_write"
      call_count: 2
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/ai-era-solo-business-proposal-v2.md"
  error_summary: ""
  estimated_tokens: "~15K"
  notes: "DoD 5/5 通過。M1 月 7-9 里程碑修正（NT$300-500K/月含構成明細）、M2 月 10-12 改為具體組合計算（NT$300K保底+Build均攤）、M3 Retainer 補充交付差異表、S1 Q1 假設說明。附加採納 S2/S3/S4/S5/S6 建議。"
```

---

```yaml
- task_id: "20260404-RV01"
  date: "2026-04-04"
  skill_type: "review"
  goal: "審查 ai-era-solo-business-proposal.md 的邏輯一致性、事實正確性、風險完整性"
  status: "done"
  model_used: "claude-sonnet-4-6"
  tools_called:
    - tool_name: "file_read"
      call_count: 2
    - tool_name: "file_write"
      call_count: 2
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/ai-era-solo-business-proposal-review.md"
  error_summary: ""
  estimated_tokens: "~18K"
  notes: "有條件通過。必須修改 3 項：月 7-9 里程碑數字矛盾、月 10-12 Retainer 月收區間矛盾、Retainer 三方案交付差異未說明。建議修改 6 項。DoD 7/7 通過（含條件）。"
```

---

```yaml
- task_id: "20260404-W01"
  date: "2026-04-04"
  skill_type: "writing"
  goal: "產出完整的一人公司 AI 時代策略提案（定位、服務菜單、ICP、競爭優勢、12 個月計畫、風險對策）"
  status: "done"
  model_used: "claude-sonnet-4-6"
  tools_called:
    - tool_name: "file_read"
      call_count: 2
    - tool_name: "file_write"
      call_count: 2
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/ai-era-solo-business-proposal.md"
  error_summary: ""
  estimated_tokens: "~20K"
  notes: "承接 20260404-S01 研究成果。DoD 7/7 全部通過。含服務菜單（Discovery/Build/Retainer/Workshop）、台灣+越南雙市場 ICP、三方競爭對比、月度行動計畫、4 個風險對策、本週執行起點。"
```

---

```yaml
- task_id: "20260404-S01"
  date: "2026-04-04"
  skill_type: "research"
  goal: "分析 AI 時代一人公司最具長遠獲利潛力的商業項目，結合用戶背景提供可執行策略建議"
  status: "done"
  model_used: "claude-sonnet-4-6"
  tools_called:
    - tool_name: "web_search"
      call_count: 2
    - tool_name: "file_read"
      call_count: 3
    - tool_name: "file_write"
      call_count: 1
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/ai-era-solo-business-strategy.md"
  error_summary: "第 3 次 web search 遭遇速率限制（rate limit），以前兩次搜尋結果及既有知識完成任務。DoD 6/6 全部通過。"
  estimated_tokens: "~25K"
  notes: "識別前 5 商業模式：AI顧問×產品化服務、AI Agent 自動化建置、垂直 AI SaaS、知識商品化、AI 培訓工作坊。針對台灣+越南雙市場及管理顧問背景提供具體建議。12 個月執行路徑已規劃。"
```

---

```yaml
- task_id: "20260404-O01"
  date: "2026-04-04"
  skill_type: "ops"
  goal: "修正 R02 must-fix：補充知識管理類別、統一採用狀態四態格式"
  status: "done"
  model_used: "claude-sonnet-4-6"
  tools_called:
    - tool_name: "file_read"
      call_count: 3
    - tool_name: "file_write"
      call_count: 1
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/solo-company-tools-inventory-v2.md"
  error_summary: ""
  estimated_tokens: "~10K"
  notes: "原 v1 草稿因 .gitignore 未入版控，v2 依 Task Card context + audit log + memory/ 重建。DoD 5/5 全部通過。新增知識管理類別（5 工具），7 大類別採用狀態全面統一四態格式。"
```

---

```yaml
- task_id: "20260404-R02"
  date: "2026-04-04"
  skill_type: "review"
  goal: "審查工具盤點報告的完整性、邏輯一致性與一人公司適用性"
  status: "done"
  model_used: "claude-opus-4-6"
  tools_called:
    - tool_name: "file_read"
      call_count: 2
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/tools-inventory-review-report.md"
  error_summary: ""
  estimated_tokens: "~12K"
  notes: "有條件通過。發現 2 個必須修改（知識管理類別缺失、採用狀態不一致），3 個建議修改。DoD 5/5 條有 3 通過、2 部分通過。Week 1 pipeline 驗證完成。"

- task_id: "20260404-R01"
  date: "2026-04-04"
  skill_type: "research"
  goal: "調查並整理一人公司運作所需的工具清單，按功能分類並評估現有採用狀況"
  status: "done"
  model_used: "claude-opus-4-6"
  tools_called:
    - tool_name: "file_read"
      call_count: 2
    - tool_name: "web_search"
      call_count: 3
  checkpoints: 1
  approval_needed: false
  approval_given: false
  output_path: "outputs/drafts/solo-company-tools-inventory.md"
  error_summary: ""
  estimated_tokens: "~18K"
  notes: "6 大類別 20+ 工具。web search 3 輪全部用完。outputs/drafts/ 因 .gitignore 不入版控，Task Card 狀態記錄在 YAML。"
```
