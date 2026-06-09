# Harness 缺口補強計畫（依 20260609-001 差距分析報告）

- Task Card：`tasks/2026-06-09_harness-gap-remediation-plan.yaml`（task_id: 20260609-002，skill_type: analysis）
- 接力來源：`outputs/drafts/2026-06-09_harness-completeness-vs-fable5.md`（13 維度 rubric，✅7 / 🟡4 / ❌2）
- 狀態：草稿，待人工審閱。各補強項目執行前需逐項核准（見附錄 Task Card 草稿）

## 結論與建議

建議採**階段式補強（選項 B）**：R1（基準重評）→ Phase 1（R6 skills 原生註冊 + R2 evaluator subagent）→ Phase 2（R3 evidence-gated completion）→ Phase 3（R4 handoff + R5 操作者控制）。總工時 21–31 小時；若採兩個建議簡化（R3 v1 不做 read receipts、R5 的 steer 延後），可壓到 **16–22 小時**。排序理由：R1 最便宜且決定所有項目「自建 vs 採用原生」的走向；R6+R2 是純原生採用、風險最低、直接補掉官方認證的最強槓桿（builder/grader 分離）；R3 是唯一會「擋寫入」的 hook、依賴 R2 的 verdict 存在；R4/R5 只在 long-running/背景執行情境才回本——而報告已判定該情境目前未實現。全部完成後，rubric 預估從 ✅7/🟡4/❌2 升到 **✅11/🟡1（init.sh 延後）/❌0 ≈ 95%**。

設計總原則（呼應 NATIVE_OVERLAP 的 meta 原則）：**原生機制當載體，只自建政策邏輯**——evaluator 用 `.claude/agents/`、強制用 hooks、註冊用 native skills，不另造輪子。

## 總體選項比較

### 選項 A：全面補強（六項全做、不簡化）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高：rubric 升至 ~95%，五個缺口全閉 | 報告 #2/#3/#6/#8/#9 全數結構化解決 |
| 成本 | 21–31 小時 + 每任務多 ~1 個 evaluator subagent context（依 COST_POLICY 子代理隔離省 ~67%，可接受） | Plan 設計逐項工時加總 |
| 風險 | 中：R3 read receipts 與 R5 steer 是為「多小時無人自治」設計，現用型態下純摩擦 | 報告高風險假設：任務皆短任務、人工在場 |
| 可行性 | 高：全部有原生載體 + repo 既有 hook/CI 模式可循 | permissions_guard.py 架構直接套用 |
| 執行難度 | 中：R3 是唯一複雜項（8–12h，狀態管理） | 其餘各項 ≤6h |
| 預期回報 | 部分投資（receipts、steer）短期閒置 | 回本條件未到 |
| 一人公司適配度 | 中：一次吃下 31h 排擠本業任務 | M1 指標：月均 21 卡的產能 |

### 選項 B：階段式補強（建議）——R1 先行，P1 核心優先，R3 簡化 v1，steer 延後

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高：~90% 的選項 A 價值（兩個簡化各保留 ~80% 該項價值） | R3 v1 仍有 default-FAIL contract + done-gate + lint；只少 session 內讀取回執 |
| 成本 | **16–22 小時**，分 4 個 Task Card 分批吃 | 單批 ≤ 半天～1.5 天，不排擠本業 |
| 風險 | 低：每階段獨立 rollback（移除 settings.json 對應註冊即降級為建議性文件） | Plan 設計逐項 rollback 定義 |
| 可行性 | 高：同選項 A | 同上 |
| 執行難度 | 低-中：複雜度最高的 R3 被簡化，且排在 evaluator 落地之後 | 依賴順序正確 |
| 預期回報 | 高：P1 兩項直接消除「自評偏誤 + 自我宣告完成」這兩個官方點名的結構風險 | cwc「done 由 gate 強制」哲學 |
| 一人公司適配度 | **高**：增量交付、每階段可停損、與既有治理流程（一項一卡）完全相容 | ROUTING_RULES 複合任務拆分原則 |

### 選項 C：不做（維持現狀）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 零增量；維持 75–80% 完整度 | 報告結論 |
| 成本 | 0 小時 | — |
| 風險 | **隱性升高**：報告的「低風險」評價建立在「短任務 + 人工在場」假設上；Fable 5（今日發布）支援數天級自治，使用型態大概率會演進，屆時 #2/#3 缺口直接變高風險 | 報告高風險假設第 1 條 |
| 可行性 | 高（什麼都不用做） | — |
| 執行難度 | 無 | — |
| 預期回報 | 負：NATIVE_OVERLAP 基準同時過期（5/9 評估早於 Fable 5），M4 訊號失真，可能持續投資該拆除的元件 | 報告高風險假設第 2 條 |
| 一人公司適配度 | 低：與「在可控範圍內穩定完成任務」的框架使命矛盾——自評偏誤是當下就存在的品質風險，不是未來風險 | CLAUDE.md 使命宣言 |

**判定：選項 B。** 選項 C 唯一站得住的部分是 R4/R5 的延後性——這已被 B 的階段設計吸收。

---

## 補強項目明細

> 以下實作設計經 Plan 子代理逐檔驗證 repo 現況（hook 註冊格式、validator 行為、CI 步驟、schema 消費者），檔案路徑與機制皆錨定實際程式碼。

### R1 — NATIVE_OVERLAP 基準重評（gate 項，最先做）

**skill_type: research ｜ 工時 2–3h ｜ 風險趨近零（純資料）｜ rollback：git revert**

| 維度 | 評估 |
|------|------|
| 價值 | 高：決定 R2–R6 每項「自建 vs 採用 vs 不做」；修復 M4 訊號失真 |
| 成本 | 2–3h，純讀寫，無程式碼 |
| 風險 | 近零。若新值落 40–50% 區間 M4 轉 warn——這是預期訊號，記入 decision log，不壓制 |
| 可行性 | 高：governance_metrics M4 閾值是資料驅動，改數值不會弄壞 CI（test 用自己的 tmp fixtures，已驗證） |
| 執行難度 | 低 |
| 預期回報 | 立即：本計畫各項的架構選擇都引用它 |
| 一人公司適配度 | 高：本來就是季度例行 + Fable 5 主版本發布雙觸發條件都已成立 |

實作：
- 改 `system/NATIVE_OVERLAP.yaml`：`reviewed_on` 更新；9 個既有模組對 Fable 5 世代 Claude Code 重新打分（原生 subagents、Stop/SessionStart/PostToolUse hooks、native skills 自動載入、/goal、agent teams、數天級自治）；**為即將自建的元件預先建檔打分**——Evaluator（原生 subagents ~90%）、Completion verify-gate（hook 載體原生、政策邏輯自建 ~40%）、Handoff（Stop/SessionStart + memory ~60%）、Operator controls（hooks ~70%）
- 產出 `outputs/drafts/` 重評紀錄（research 格式）+ `memory/.../decisions/` 新增 D008：逐 R 項的 build-vs-adopt 裁決
- 若 `check_decision_revisit.rb` 有決議被翻成 DUE → 走 RETRO 流程處理，不改 tracker

不做的後果：所有後續項目的架構選擇失去依據；M4 持續失真。

### R2 — Fresh-context evaluator subagent（builder/grader 分離）

**skill_type: ops ｜ 工時 3–4h ｜ 風險低（純增量）｜ rollback：刪 agent 檔 + revert GATE_POLICY**

| 維度 | 評估 |
|------|------|
| 價值 | 最高：閉掉 rubric #3 + #9 兩個維度；官方認證「最強槓桿」（對抗自評偏誤） |
| 成本 | 3–4h + 每次 completion 驗證多一個子代理呼叫（fresh context，依 COST_POLICY 子代理隔離反而省 context） |
| 風險 | 低：唯一失敗模式是 evaluator 過嚴造成 NEEDS_WORK 迴圈 → 以 2 輪上限 + 升級人工解（與「連續失敗 3 次就停」硬規則一致） |
| 可行性 | 高：`.claude/agents/*.md` 原生機制；`skills/*/eval_examples.md` 直接變 few-shot 校準材料（已付過成本的資產再利用） |
| 執行難度 | 低-中：主要是 GATE_POLICY 文字手術 + agent prompt 設計 |
| 預期回報 | 即時：下一個任務的 completion_check 就換軌 |
| 一人公司適配度 | 高：審查不再吃 owner 的時間，且裁決可稽核（verdict 進 run log） |

實作：
- 建 `.claude/agents/evaluator.md`：frontmatter `tools: Read, Grep, Glob`（**無 Write/Edit/Bash**，結構性唯讀，v1 不給 Bash——evaluator 審產出，跑 validator 仍是主 agent 的事）。Body 五要素：(1) 校準步驟——先讀 `skills/review/eval_examples.md` + 受審產出對應 skill 的 eval_examples；(2) 流程——讀 Task Card → 逐條 DoD → 在產出檔中找證據；(3) **default-FAIL 立場**：「找不到證據 = 該條 fail」；(4) 裁決格式——逐條表（條目/pass-fail/證據位置/缺什麼）+ 結尾機器可 grep 的 `VERDICT: PASS|NEEDS_WORK`；(5) 防迴圈——單任務最多 2 輪 NEEDS_WORK 後升級人工
- 改 `system/GATE_POLICY.yaml` completion_check：「pass/fail 裁決由 evaluator subagent 做出，main agent 轉錄、不得自評」；on_fail 加「NEEDS_WORK → 修正重送（≤2 輪）」。**維持四層 gate 結構不動**（EXECUTION_LOG_SCHEMA 的 gate_results、manifest 的 OVERVIEW_GATES、smoke test 都寫死四層——不可加第五層）
- 改 `system/EXECUTION_LOG_SCHEMA.yaml`：gate_results 下加選填 `evaluation: {verdict, evaluator, rounds}`（validator/manifest 只取固定欄位，加選填欄位零風險——已驗證）
- 改 `skills/review/SKILL.md:54`：把散文警告升級為結構指令「必須委派 evaluator subagent」；邊界釐清——review skill 仍負責跨 session/外部產出的路由型審查任務，evaluator agent 負責執行中的完成裁決
- 改 `ROUTING_RULES.md`（加一列）、`CLAUDE.md` 步驟 6（~10 tokens，預算餘裕 1,800）
- **前置順位項**：`system/APPROVAL_POLICY.yaml` 補觸發條件「修改 `.claude/`（hooks/agents/skills 註冊）→ human_confirm」——目前只覆蓋 `system/` 與 `skills/`，而 `.claude/` 是後續所有強制項的落點，先把這個治理洞補上
- 測試：`tests/e2e/test_evaluator_agent.py` 釘住 agent 檔存在、frontmatter 合法、tools 不含寫入類、body 含 `VERDICT:`；演練——對 eval_examples 的 bad 範本跑一次，預期 NEEDS_WORK，紀錄進 AUDIT_LOG + run log

不做的後果：rubric #3/#9 維持缺口；「自己審自己」繼續只靠 prompt 客氣話。

### R3 — Evidence-gated completion（default-FAIL contract + verify-gate hook）

**skill_type: ops ｜ 工時 8–12h（v1 簡化 ~6–8h）｜ 風險中（唯一擋寫入的 hook）｜ rollback：移除 settings.json 兩條註冊，contract 降級為 lint 文件**

| 維度 | 評估 |
|------|------|
| 價值 | 高：閉掉 rubric #2；「done」從自我宣告變結構強制——cwc 哲學的核心件 |
| 成本 | 全功能 8–12h；**v1 簡化 6–8h**（建議，見下） |
| 風險 | 全計畫最高誤擋風險：session 重啟後回執遺失（其實是 feature：新 session 必須重讀證據）、YAML 解析邊角（parse 失敗 fail-open + 警告，與 permissions_guard 一致）、contract 檔 Edit 摩擦（by design） |
| 可行性 | 高：完全沿用 permissions_guard.py 架構（stdin JSON → exit 2 = block）；**contract 放獨立檔案使兩個 validator 與 manifest 零改動**（已驗證兩者只認既有欄位） |
| 執行難度 | 中-高：全計畫唯一需要 hook 狀態管理的項目 |
| 預期回報 | 高但條件性：短任務人工在場時是保險，無人自治時是命脈 |
| 一人公司適配度 | 中-高：scope rule 把 45 張舊卡和短任務全部豁免，摩擦只落在該付的地方 |

實作核心設計：
- **Contract 檔**：新目錄 `logs/verification/`，每參與任務一檔 `YYYY-MM-DD_<task_id>_dod.yaml`：DoD 逐條 `{id, text, status: fail(預設), evidence: []}` + `evaluator_verdict`（接 R2）+ `override`（人工逃生閥，需 `approval_ref` 對得上 logs/approvals/）。**適用範圍規則**（仿 D006 先例）：`risk_level >= high`、`checkpoints >= 3` 或長任務才必須；**hook 只在 contract 檔存在時強制**——這就是誤擋防火牆
- **`scripts/verify_gate.py` 一檔兩模式**：
  - `--gate`（PreToolUse，matcher `Write|Edit`）三規則：(1) contract 檔的 pass 翻轉——Edit 一律擋（「contract 必須整檔 Write」，根除片段解析問題）；Write 時逐項驗證 `status: pass` 的 evidence 路徑存在 + 非空 [+ v2: 在本 session 讀取回執中]；(2) Task Card `status: done` 翻轉——有 contract 則要求全 pass + `evaluator_verdict: PASS`，無 contract 放行；(3) override 含 approval_ref → 放行 + 警告
  - `--record`（PostToolUse，matcher `Read`）：讀取回執寫入 `logs/verification/.receipts/`（gitignored）——**v2 才做**
- **哲學反轉要寫進 docstring**：permissions_guard 是 deny-list（誤擋比漏擋糟）；verify-gate 是 default-FAIL（接受摩擦換確定性）
- 配套：`system/VERIFICATION_PROTOCOL.md`（格式/語意/範圍/override/rollback 程序）、`check_spec_consistency.rb` 新 section lint contract 檔（pass ⇒ evidence 非空 ⇒ 路徑存在）、`test_verify_gate.py`（沿用 test_permissions_guard 的 run_main 模式 + settings.json 註冊釘住測試）、e2e 演練（無證據翻 pass → 被擋 → error log，仿 R5 failure drill 釘住）
- **建議採 v1 簡化先行**：先出三規則 + lint，**不做 read receipts**——80% 價值、零 hook 狀態、零 .gitignore 變動；等多小時自治場景出現再上 v2。此選擇在 Task Card 中標明請人工裁決

不做的後果：completion_check 維持「同一個 agent 自己說了算」；R2 的 verdict 沒有強制力（evaluator 說 NEEDS_WORK，main agent 技術上仍能標 done）。**R3 是讓 R2 長牙齒的項目。**

### R4 — 跨 session handoff（PROGRESS 協議 + commit-on-stop）

**skill_type: ops ｜ 工時 4–6h ｜ 風險低 ｜ rollback：移除 settings.json 兩條註冊，progress 檔降級為無害文件**

| 維度 | 評估 |
|------|------|
| 價值 | 中-高：閉掉 rubric #6 + #5 殘餘（commit-on-stop）；官方教材的字面核心件 |
| 成本 | 4–6h |
| 風險 | 低：自動 commit 污染 history（以固定前綴 + 只收 tracked 檔 + 限 in_progress 卡存在時觸發三重節制）；commit ≠ 過 gate ≠ done 要寫進協議文件 |
| 可行性 | 高：Stop/SessionStart 原生 hook events；progress 檔放 `logs/progress/`——`write_logs` 本來就是 allow 權限，零權限變更（放 memory/ 反而要人工確認，故不採） |
| 執行難度 | 低-中 |
| 預期回報 | 條件性：單 context window 任務用不到；任務變長立刻回本 |
| 一人公司適配度 | 高：被動保險，平時零摩擦 |

實作：
- `logs/progress/<task_id>.md` 內容契約：目前步驟/下一步/未決問題/動過的檔/最後 checkpoint hash；每次 checkpoint 與停止前寫，**重啟先讀**
- `scripts/handoff_hooks.py` 一檔兩模式：`--on-stop`（Stop hook）——working tree dirty 且存在 in_progress 卡才 `git add -u`（只收 tracked，**絕不掃 untracked**，防垃圾/機密入庫）+ commit `checkpoint: <task_id> commit-on-stop 自動兜底`；**永遠 exit 0**（Stop hook 不得阻止停止）。`--on-start`（SessionStart hook）——偵測到 in_progress 卡 + progress 檔即注入 additionalContext「先讀 logs/progress/<id>.md 再續作」——把「重啟先讀」從散文變結構，這是對 doc-only 協議的關鍵升級
- 配套：`system/HANDOFF_PROTOCOL.md`、CLAUDE.md Checkpoint 段加一行、`RECOVERY_RUNBOOK.md` 場景 C 把 progress 檔列為第一還原來源、EXECUTION_LOG_SCHEMA 加選填 `progress_log`、`test_handoff_hooks.py`（tmp git repo fixtures：tracked-only、clean tree 不動作、永不非零退出）、kill-session 演練入 runbook 附錄

不做的後果：rubric #6 維持缺口；session 中斷後的接力靠人腦重建。

### R5 — Kill-switch + steer（執行中操作者控制）

**skill_type: ops ｜ 工時 3–4h（steer 延後則 ~2h）｜ 風險低 ｜ rollback：移除 settings.json 一條註冊**

| 維度 | 評估 |
|------|------|
| 價值 | 中：閉掉 rubric #8 缺口的「執行中」半邊（事前 approval 已完整） |
| 成本 | 3–4h；每次工具呼叫多一次 `os.path.exists` stat，可忽略 |
| 風險 | 低：殘留 AGENT_STOP 卡死後續 session（block 訊息直接寫明解法 + runbook 新場景 E） |
| 可行性 | 高：PreToolUse 不設 matcher = 攔所有工具 |
| 執行難度 | 低 |
| 預期回報 | 條件性最強的一項：人工在場時 Esc 就是 kill-switch；**steer 在背景執行存在前近乎冗餘** |
| 一人公司適配度 | kill-switch 高（保險便宜）；steer 中-低（建議延後並記 decision log） |

實作：
- `scripts/operator_controls.py`（PreToolUse，全工具）：(1) kill-switch——`AGENT_STOP` 存在即 exit 2 擋下一切工具呼叫；**自我保護特性**：agent 想 `rm AGENT_STOP` 的那次 Bash 呼叫本身就被本 hook 擋掉（注意：單靠 permissions_guard 會放行 plain `rm`，有 pinned test 為證）；與 R4 協同——Stop hook 不是工具呼叫，硬停時 commit-on-stop 照樣兜底；agent 仍可輸出文字總結。(2) steer——`STEER.md` 存在且 sha256 異於已 ack hash 時擋一次、把全文嵌入 block reason、寫回 ack hash 後放行（一次性確定注入，零迴圈）
- settings.json PreToolUse 順序：operator_controls（最便宜的 stat）→ permissions_guard（Bash）→ verify_gate（Write|Edit）
- `AGENT_STOP`、`STEER.md` 進 .gitignore（操作者建立，永不入庫）
- 配套：`system/OPERATOR_CONTROLS.md`、runbook 場景 E、`test_operator_controls.py` + 註冊釘住測試、mid-task 演練
- **建議**：kill-switch 全做；steer 作為同卡 30 分鐘附加項或明確延後 + decision log——報告自己的風險框架支持延後

不做的後果：執行中只能靠中斷 session 止損；對現用型態影響小，對背景執行是盲飛。

### R6 — Skills 原生註冊（frontmatter + symlinks）

**skill_type: ops ｜ 工時 1–2h ｜ 風險極低 ｜ rollback：刪 symlink、剝 frontmatter**

| 維度 | 評估 |
|------|------|
| 價值 | 中：閉掉 rubric #11 殘餘；NATIVE_OVERLAP 模組 1（85%）的採用落地 |
| 成本 | 1–2h |
| 風險 | 極低：唯一注意點是原生自動觸發與 ROUTING_RULES 散文可能雙觸發——內容相同無害，但要在 NATIVE_OVERLAP 註記「ROUTING_RULES 冗餘度上升」餵下一輪 M4 |
| 可行性 | 高：research symlink 是已入庫先例 |
| 執行難度 | 低。**隱藏子任務**（盤點時發現）：4 個 SKILL.md 完全沒有 frontmatter——native 載入必需，所以是「補 frontmatter + 建 symlink」不只是連結 |
| 預期回報 | 即時：skill 自動觸發，省路由 token |
| 一人公司適配度 | 高 |

實作：4 檔 prepend frontmatter（`name:` = 目錄名、`description:` = 壓縮版用途 + 觸發條件含「Task Card 的 skill_type 為 X」，仿 research 格式）；4 條相對 symlink `.claude/skills/<name> -> ../../skills/<name>`；注意單 skill ≤1,500 token 限制（frontmatter 約 +60–80 tokens，CJK 計價下安全，但要手動驗一次）；`check_spec_consistency.rb` 加 section：每個 skills/ 目錄的 frontmatter 必須合法解析且 symlink 必須存在並解析正確。skills/ 修改觸發 APPROVAL_POLICY human_confirm——由該卡核准動作本身滿足。

不做的後果：4 個 skill 持續靠檔案引用載入，路由全靠散文表。

---

## 依賴關係與階段排序

```
R1（research，gate 項）──► 全部
Phase 1：R6（獨立、最小）＋ R2（獨立）
Phase 2：R3（依賴 R2——evaluator_verdict 要先存在才能接進 contract 與 done-gate）
Phase 3：R4（獨立）＋ R5（steer 的 ack 機制沿用 R3 的 hook 狀態先例，kill-switch 獨立）
```

每項 = 一張 Task Card（依 ROUTING_RULES 複合任務拆分原則），共 6 張，草稿見附錄。共同前置項（掛在第一張執行卡）：APPROVAL_POLICY 補 `.claude/` 觸發條件。

### 橫切設計風險（執行各卡時須對照）

1. `.claude/settings.json` 將從 1 條註冊長到 6 條，是無 schema test 的單點故障——建議在 R3 卡中做一個**合併的 `test_settings_hooks.py`**（釘住全部註冊），優於三個散落斷言
2. hook 輸出風格統一沿用 permissions_guard 的 `{"decision"}` + exit-2（exit code 是承重通道）；新版 `hookSpecificOutput` 格式記入 NATIVE_OVERLAP 當未來項
3. repo 級 CI 會 parse 所有 `*.yaml`——故意壞掉的測試 fixture 只能放 `tests/e2e/fixtures/`
4. `frontend/data.json` 本計畫零變更（沒動 Task Card 欄位；run log 加的是選填欄位）——但**任何演練產生真實 run log 後，同 commit 必須重生成 manifest**（20260609-001 已被咬兩次，commit 1e892f8 與 1192ce9 為證）
5. CLAUDE.md + GLOBAL_RULES 預算現用 ~1,197/3,000：全計畫只加 ~3 行指標行（~30 tokens），協議細節全放 `system/*.md`

## 高風險假設

- **「使用型態將演進到 long-running」**：R3 v2（receipts）、R4、R5 的回本都押在這上面。若一年後仍是純短任務 + 人工在場，這三項是過度工程——但 Phase 設計讓你可以在 Phase 1 後停損，沉沒成本上限 ~7h。
- **「evaluator 不會系統性過嚴/過鬆」**：2 輪上限防迴圈，但若 eval_examples 校準材料本身偏誤，裁決會繼承偏誤。緩解：R2 演練用已知 good/bad 範本驗收；每月 RETRO 抽查 verdict 與人工判斷的一致率。
- **「原生機制穩定」**：`.claude/agents/`、Stop/SessionStart hooks 的行為若隨 Claude Code 版本變動，強制層會靜默失效。緩解：R3 卡的 settings.json 釘住測試 + 每季 NATIVE_OVERLAP 重評本來就會碰到。

## 待驗證

- Fable 5 世代 Claude Code 是否已內建完成驗證機制（若有，R3 從「自建」降為「設定」）：R1 重評時查 code.claude.com docs 確認
- evaluator subagent 在此 repo 的實際 token 成本：R2 演練時實測，回填 COST_POLICY（analysis 校準係數同步建立——本計畫即第一筆 analysis 樣本）
- 單 skill 1,500 token 限制在加 frontmatter 後的實際餘裕：R6 執行時用 check_context_budget 的估算公式逐檔驗

## 建議下一步

1. **審閱本計畫**，特別裁決兩個簡化選項：R3 v1（不做 read receipts）、R5 steer 延後
2. 核准後依附錄草稿實例化 R1 的 Task Card（research，2–3h）——它 gate 其他一切
3. R1 完成 → 實例化 Phase 1 兩卡（R6 + R2，合計 4–6h，一個下午）
4. Phase 1 演練通過 → R3；R3 穩定跑兩週 → Phase 3
5. 全部完成後跑一次 mini 差距複評（對照 20260609-001 的 13 維度表），驗證 ~95% 的預估

---

## 附錄：後續執行用 Task Card 草稿

> 依 20260609-002 DoD 約定：草稿嵌入本文件，**不直接建檔**；經人工核准後再實例化到 `tasks/`（屆時填入實際日期與 task_id，並同 commit 重生成 manifest）。

### 卡 1：R1 基準重評

```yaml
task_id: "YYYYMMDD-R1"
status: "pending"
goal: "對 Fable 5 世代 Claude Code 重評 NATIVE_OVERLAP 九模組 + 預建補強元件評分，產出 build-vs-adopt 裁決"
definition_of_done:
  - "NATIVE_OVERLAP.yaml 九模組重打分 + reviewed_on 更新 + 四個新元件列入"
  - "重評紀錄輸出 outputs/drafts/（research 格式，逐模組附證據）"
  - "decisions/ 新增 D008：R2-R6 逐項 build-vs-adopt 裁決"
  - "若 aggregate 變動跨越 40%/50% 閾值，M4 影響與因應記入 D008"
expected_output: {format: "md+yaml", location: "outputs/drafts/", filename: "native-overlap-reeval-fable5.md"}
risk_level: "low"
approval_needed: true   # 修改 system/ 屬 ask
allowed_tools: ["file_read", "web_fetch", "web_search", "file_write_drafts", "file_write_logs", "git_checkpoint"]
skill_type: "research"
```

### 卡 2：R6 skills 原生註冊

```yaml
task_id: "YYYYMMDD-R6"
status: "pending"
goal: "為 analysis/writing/ops/review 四個 skill 補 YAML frontmatter 並建 .claude/skills/ symlink，完成原生註冊"
definition_of_done:
  - "四檔 frontmatter 合法（name=目錄名、description 含觸發條件），單檔 token 估算 ≤1,500"
  - "四條相對 symlink 建立且解析正確"
  - "check_spec_consistency.rb 新增 skills 結構 lint + 測試案例，CI 綠"
  - "NATIVE_OVERLAP 註記 ROUTING_RULES 冗餘度變化"
risk_level: "low"
approval_needed: true   # 修改 skills/ + .claude/ 屬 ask
allowed_tools: ["file_read", "file_write_skills", "file_write_logs", "git_checkpoint"]
skill_type: "ops"
```

### 卡 3：R2 evaluator subagent

```yaml
task_id: "YYYYMMDD-R2"
status: "pending"
goal: "建立 fresh-context evaluator subagent 並把 GATE_POLICY completion_check 裁決權移交給它"
definition_of_done:
  - ".claude/agents/evaluator.md 建立：唯讀工具、eval_examples 校準、default-FAIL、VERDICT 格式、2 輪上限"
  - "GATE_POLICY completion_check / EXECUTION_LOG_SCHEMA evaluation 欄 / review SKILL.md:54 / ROUTING_RULES / CLAUDE.md 步驟 6 同步更新"
  - "APPROVAL_POLICY 補 .claude/ 觸發條件（共同前置項）"
  - "test_evaluator_agent.py 釘住唯讀契約，CI 綠"
  - "演練：對已知 bad 範本得到 NEEDS_WORK，verdict 入 run log；token 成本實測回填 COST_POLICY"
risk_level: "medium"    # 動 system/ 核心 gate 流程
approval_needed: true
allowed_tools: ["file_read", "file_write_system", "file_write_claude_dir", "file_write_logs", "git_checkpoint", "evaluator_subagent"]
skill_type: "ops"
```

### 卡 4：R3 evidence-gated completion（v1）

```yaml
task_id: "YYYYMMDD-R3"
status: "pending"
goal: "建立 default-FAIL DoD contract（logs/verification/）與 verify_gate.py PreToolUse hook，強制 done 翻轉須證據 + evaluator PASS"
definition_of_done:
  - "verify_gate.py --gate 三規則實作（contract Edit 全擋/Write 逐項驗證、done 翻轉 gate、override 逃生閥），仿 permissions_guard 架構"
  - "VERIFICATION_PROTOCOL.md + GATE_POLICY/EXECUTION_LOG_SCHEMA 同步 + spec_consistency 新 lint section"
  - "test_verify_gate.py 全場景 + 合併版 test_settings_hooks.py（釘住全部 hook 註冊）+ CI 步驟"
  - "e2e 演練：無證據翻 pass 被擋 → error log，仿 failure drill 釘住，manifest 同 commit 重生成"
  - "v1 範圍確認：不含 PostToolUse read receipts（v2 觸發條件寫入 protocol 文件）"
risk_level: "high"      # 唯一擋寫入的 hook；risk>=high 強制走完整 4-gate + run log
approval_needed: true
allowed_tools: ["file_read", "file_write_system", "file_write_claude_dir", "file_write_scripts", "file_write_logs", "git_checkpoint"]
skill_type: "ops"
```

### 卡 5：R4 handoff 協議

```yaml
task_id: "YYYYMMDD-R4"
status: "pending"
goal: "建立 logs/progress/ PROGRESS 協議與 handoff_hooks.py（commit-on-stop + session-start 注入）"
definition_of_done:
  - "handoff_hooks.py 兩模式：--on-stop（tracked-only、限 in_progress 卡、永遠 exit 0）、--on-start（additionalContext 注入）"
  - "HANDOFF_PROTOCOL.md + RECOVERY_RUNBOOK 場景 C 更新 + CLAUDE.md 一行"
  - "test_handoff_hooks.py（tmp git repo fixtures）+ CI 綠"
  - "kill-session 演練：自動 commit 兜底 + 重啟注入皆驗證，入 runbook 附錄"
risk_level: "medium"
approval_needed: true
allowed_tools: ["file_read", "file_write_system", "file_write_claude_dir", "file_write_scripts", "file_write_logs", "git_checkpoint"]
skill_type: "ops"
```

### 卡 6：R5 操作者控制

```yaml
task_id: "YYYYMMDD-R5"
status: "pending"
goal: "建立 operator_controls.py kill-switch（AGENT_STOP）；steer 依核准結果做或延後 + decision log"
definition_of_done:
  - "operator_controls.py PreToolUse（全工具）：AGENT_STOP 即全擋；hook 順序 operator→permissions→verify 落實"
  - "OPERATOR_CONTROLS.md + RECOVERY_RUNBOOK 場景 E + .gitignore 更新"
  - "test_operator_controls.py + CI 綠"
  - "mid-task 演練：halt → 移除 → 恢復，artifacts 入 logs/"
  - "steer 裁決已執行（做：一次性 ack 注入機制；不做：decision log 記延後條件）"
risk_level: "medium"
approval_needed: true
allowed_tools: ["file_read", "file_write_system", "file_write_claude_dir", "file_write_scripts", "file_write_logs", "git_checkpoint"]
skill_type: "ops"
```
