# 四層 AI Engineering 對照分析：agent-harness 優缺點與改善計劃

- Task Card：20260711-A01（skill_type: analysis）
- 日期：2026-07-11
- 輸入：datasciencedojo「The 4 Layers of AI Engineering」概念圖（四層定義轉述於第二節）
- 證據等級標示：**[驗]**＝本次親自讀碼/實測驗證（附檔案:行號）；**[盤]**＝全 repo 盤點彙整（已抽查關鍵項）

## 結論與建議

agent-harness 已完整實作四層，且成熟度方向與多數專案相反：一般是內層（Prompt）強、外層（Loop）弱，本專案反而是 Harness／Loop 兩層制度最完整（有界驗證閉環、熔斷、災難演練），弱點集中在三個「宣稱與實作的接縫」——兩套 L4 風險 gate 語意分歧、context 預算宣稱與量測口徑不一致、memory 狀態快照過期。建議採**選項 C（報告＋P0 修正）**：三個落差都已驗證、修正面小、測試可鎖；P1 以後依 WIP 治理節奏分批開卡，不在本卡擴scope（review 佇列已積 17 張，人工審核是目前瓶頸）。

## 框架轉述（分析基準）

| # | 層次 | 圖中定義 |
|---|------|----------|
| 1 | Prompt Engineering | 直接輸入對話的精確措辭、指令、約束 |
| 2 | Context Engineering | 模型看到 prompt 前讀到的系統指令、參考檔案、對話歷史 |
| 3 | Harness Engineering | 路由工具、驗證輸出、自動重試，讓模型自我檢查的「程式碼」 |
| 4 | Loop Engineering | 明確目標與停止條件，讓系統自行 prompt→check→adjust，無需人在迴圈 |

## 四層對照

### L1 Prompt — 成熟

**優點**
- Task Card 把 prompt 約束結構化為 schema 驗證的 YAML（goal／DoD／allowed_tools／max_*，10 必填欄位），三層驗證：`system/validate_task_card.py`（runtime）、`scripts/check_spec_consistency.rb`（CI，Ruby↔Python 欄位 parity 有測試鎖）、`scripts/task_card_guard.py`（PreToolUse hook，fail-closed）。**[盤]**
- 5 個可路由 skill 皆有輸出格式規範＋好壞範例（`skills/*/SKILL.md` + `eval_examples.md`）。**[盤]**

**缺點**
- evals 只覆蓋 2/6 skill（`evals/` 僅 research、analysis 各 1 case）；LLM judge 未接 provider，僅結構性 rule judge。**[盤]**
- `retro` skill 不可路由（`validate_task_card.py` 的 `VALID_SKILLS` 不含）。**[盤]**
- 86 張卡 26 未結：done 60／review 17／in_progress 3／pending 6——review 佇列 17 張＝人工審核瓶頸。**[盤]**

### L2 Context — 制度完整，口徑有漏

**優點**
- 預算量化且 CI 強制：`scripts/check_context_budget.rb`（CLAUDE.md＋GLOBAL_RULES ≤3,000、SKILL.md ≤1,500 tokens，CJK-aware 估算），現值 1,568/3,000。**[驗]**
- 快取友善載入順序（穩定前綴先、可變後綴後）、PreCompact 持久快照、SessionStart 定向注入、大檔路徑引用。**[盤]**
- memory 三層制（短期自動／scratchpad 任務內／長期須人工確認），自動寫入長期記憶＝deny。**[盤]**

**缺點**
- **宣稱／量測口徑不一致**：`CLAUDE.md:24` 說 skill 上限「含 SKILL.md + eval_examples.md」，但 `check_context_budget.rb:22` 只量 `skills/*/SKILL.md`。照宣稱口徑實測 3/6 skill 已超標：analysis 2,029、retro 1,946、research 1,831（上限 1,500）。**[驗]** 本 session 實測 Skill 載入只注入 SKILL.md 本體，eval_examples.md 非執行期 context，故正確方向是修宣稱而非修內容。**[驗]**
- `memory/active_projects/agent-harness/context.md:32-37` 「目前狀態」快照停在 2026-06-09：寫 45 張卡／7 筆決策（D001–D007）／3 份報告，實際已是 86 張／8 筆（含 D008）／9 份。**[驗]**

### L3 Harness — 骨架完整，「執行當下」的強制有缺口

**優點**
- hooks 真實佈線（`.claude/settings.json`）：PreToolUse(Bash)→`permissions_guard.py`＋`failure_counter.py`；PreToolUse(Write/Edit)→`task_card_guard.py`＋`failure_counter.py`；Stop→`sync_derived.sh`＋`session_stop_checks.py`；SessionStart；PreCompact。**[盤]**
- `task_card_guard.py` fail-closed（壞輸入即擋）；deny 簽章由 `permissions_guard.py` runtime 阻擋；CI 12 類一致性檢查＋15+ 單元測試＋4 支 e2e；audit log 與 frontend `data.json` 自動衍生防漂移。**[盤]**
- `SECURITY.md` 誠實標註 enforcement 分層（L0 sandbox→L4 prompt 自律）與已知繞過面——治理誠實度罕見。**[盤]**

**缺點**
- 關鍵 runtime 合規仍在 prompt 自律側：allowed_tools 白名單**不在呼叫當下擋**（僅事後有 run log 才稽核，而 run log 多數情形非必填）；`failure_counter.py` 熔斷是硬的、但計數靠 agent 主動 `--record`；注入偵測器 `check_untrusted_content.py` 沒掛任何 hook、不掃真實輸出。**[盤]**
- `permissions_guard.py` fail-open（壞輸入放行）與 `task_card_guard.py` fail-closed 並存，防線強度不對稱；無 PostToolUse hook。**[盤]**

### L4 Loop — 最強的一層，但有已驗證的實作缺陷

**優點**
- `system/VERIFICATION_LOOP.yaml` 有界閉環：全域迭代上限 3、四終態（pass／hard_stop／escalated／exhausted）、帳本 schema 對齊 EXECUTION_LOG_SCHEMA。**[盤]**
- 三重停止條件成體系：連續失敗 3 次熔斷（`failure_counter.py`）、同任務 3 次批准請求→暫停（APPROVAL_POLICY）、schema 失敗重試 1 次即停。`RECOVERY_RUNBOOK.md` 4 災難場景含 2 次實測演練；logs 有真實 failed run（R5 演練）。**[盤]**

**缺點（本卡 P0 標的）**
- `scripts/gate_check.py:212-225` `gate_risk` 對高風險卡**空路徑 fail-open**（`paths=[]`→`bad=[]`→回 PASS「confined to drafts/」），且用**子字串**比對（`foo/outputs/drafts/x` 會誤 PASS）。**[驗]**
- `scripts/verification_loop.py:178-186` `check_risk` 語意相反：**前綴精確**比對、空路徑 **fail-closed**、但**不看 run_log 實際落點**。同一張卡兩套驅動器可能給出相反判定。**[驗]**
- 閉環帳本尚未在真實任務產生（僅 e2e drill 證明）；「驗證」已程式化但「修正」半邊仍人工；熔斷是全域跳閘非按卡。**[盤]**

### 與圖定位的差異（設計選擇，非缺陷）

圖對 Loop 的定義是「無需人在迴圈」。本專案刻意把人留在迴圈：對外動作只出草稿、ask 級動作要人工確認、批准不設 timeout 不自動放行。這是一人公司治理的核心設計（可復原／可審計優先於全自動），不應照圖「補齊」全自動；可補的是**有界自主維運迴圈**——排程跑 metrics／retro digest 這類唯讀彙整，輸出仍進 drafts/ 等人看（見 P2）。

## 選項比較（如何回應這些落差）

### 選項 A：不做（維持現狀）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 0 | 落差持續存在 |
| 成本 | 0 | — |
| 風險 | 中高：兩套 gate 對同一張高風險卡可能判定相反，稽核結論不可信任；預算宣稱失真侵蝕「可量化」的核心價值 | gate_check.py:212 vs verification_loop.py:178 **[驗]** |
| 可行性 | 高（什麼都不用做） | — |
| 執行難度 | 無 | — |
| 預期回報 | 負（缺陷會隨卡片數放大） | 高風險卡今後增加時觸險機率上升 |
| 一人公司適配度 | 低：治理框架的可信度是唯一賣點 | — |

### 選項 B：只出分析報告

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中：缺口被記錄、可排program | 報告本身 |
| 成本 | ~2 小時 | 分析已完成 |
| 風險 | 中：已驗證的 fail-open 缺陷繼續留在 main；報告會過期 | 同選項 A |
| 可行性 | 高 | — |
| 執行難度 | 低 | — |
| 預期回報 | 中偏低：知而不修 | — |
| 一人公司適配度 | 中：又多一份待辦文件，review 佇列已 17 張 | tasks/ 狀態分佈 **[盤]** |

### 選項 C：報告＋P0 修正（✅ 本卡採用）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高：三個接縫落差一次對齊，宣稱恢復可信 | P0 全部已驗證存在 |
| 成本 | ~4 小時（本 session 內） | 修正面小：2 支 script＋1 行 CLAUDE.md＋1 段 context.md＋測試 |
| 風險 | 低：fail-open→fail-closed 是收緊；parity 測試鎖住兩套一致；CI 同款檢查回歸 | 測試矩陣見 roadmap P0-1 |
| 可行性 | 高：全部在本 repo、無外部依賴 | — |
| 執行難度 | 低中：gate helper 抽取＋測試案例矩陣 | — |
| 預期回報 | 高：高風險卡的 L4 判定從「可能誤 PASS」變成確定 fail-closed | — |
| 一人公司適配度 | 高：一次 PR 可審完，不加 WIP | — |

### 選項 D：報告＋P0＋P1 全面開卡實作

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 最高（若全落地） | P1 六項見 roadmap |
| 成本 | +3–5 個工作天（P1 每項 0.5–1 天） | 涉 hook 新增、eval 建置、plugin parity |
| 風險 | 中高：單次大改動審核負擔重；WIP 從 26 再增 6+ 張 | review 佇列現況 **[盤]** |
| 可行性 | 中：技術可行，人力（審核）不可行 | 人工審核是既有瓶頸 |
| 執行難度 | 高 | — |
| 預期回報 | 高但延遲：多數 P1 項互相獨立，分批不損失價值 | — |
| 一人公司適配度 | 低：违反本專案自己的 WIP 教訓 | — |

## 改善 Roadmap

### P0（本卡執行，均已驗證存在）
1. **兩套 L4 風險 gate 語意統一＋fail-closed**：`gate_check.py` 抽共用 helper `output_in_drafts()`（前綴精確）；`gate_risk` 高風險＋宣告 location 空→FAIL；`verification_loop.check_risk` 共用 helper 並增看 `run_log.output_path`。測試矩陣：空 location 高風險→兩套皆 FAIL；`outputs/drafts-public/`→FAIL；`foo/outputs/drafts/`→FAIL；正常 drafts→PASS；run_log 落 reports/→FAIL；另加兩套判定一致的 parity 測試。
2. **Context 預算口徑對齊**：`CLAUDE.md:24` 改為只計執行期載入的 SKILL.md（eval_examples.md 屬 eval 資產不計入——本 session 實測 Skill 載入僅注入 SKILL.md）；`check_context_budget.rb` 增 eval_examples.md 的 advisory 輸出（不影響 exit code），維持漂移可見。否決替代案「把 eval 計入並修剪 3 個超標檔」：內容手術大、且與載入事實不符。
3. **memory 狀態快照同步**：`context.md` 「目前狀態」更新至 2026-07-11 現值（86 卡／D001–D008／9 報告）。

### P1（分批開卡，建議順序＝治理增量／成本比）
1. **allowed_tools 呼叫當下強制**（~1 天）：PreToolUse hook 讀 active task 卡的 allowed_tools，超白名單即擋——把 L2 rule gate 從事後稽核前移到執行當下，是最大單項治理增量。
2. **failure_counter 自動記錄**（~0.5 天）：PostToolUse hook 對工具錯誤自動 `--record`，消除「計數靠自律」缺口。
3. **注入偵測掛上**（~0.5 天）：`check_untrusted_content.py` 掛 Stop hook（advisory）或 CI 掃 `outputs/` 新增檔。
4. **evals 擴至 6/6＋LLM judge 接 provider**（~1 天）：品質保證從結構層升到語意層。
5. **plugin fork parity 測試**（~0.5 天）：N11 已蓋 2 條缺陷；剩餘 deny rules（5 vs 8）與必填欄位（6 vs 10）差異在建 repo 前補 parity 鎖。**[盤]**
6. **review 佇列治理**（~0.5 天）：governance_metrics 加 WIP aging 指標＋每週清理節奏，17 張 review 卡先清。

### P2（方向性）
- **有界自主維運迴圈**：Routine 排程跑 governance_metrics／retro digest（唯讀彙整→drafts/），對齊圖的 Loop 定義但保留人工批准邊界。
- 熔斷按卡分閘（保留全域閘做總開關）；run log fail-closed 視窗（cutoff 2026-07-10＋狀態閘）逐步放寬；verification_loop 帳本常態化到 medium+ 卡。

## 高風險假設

- **gate 收緊不誤傷既有卡**：fail-closed 後，任何高風險＋location 空的歷史卡會開始 FAIL。若存在此類卡，CI 可能轉紅——驗證方式：對全部 86 張卡跑一次 gate_check 回歸（本卡步驟 6）。若成立需先補卡再合併。
- **review 佇列有人力清理**：P1 分批節奏假設每週能消化 1–2 張；若不成立，P1 應再壓縮到只做前 2 項。
- **plugin 草稿樹短期內會建 repo**（D007 延後中）：若確定不建，P1-5 可降級為「刪除草稿樹」而非 parity 鎖。

## 待驗證

- 兩套 gate 統一後 CI 同款檢查全綠（本卡步驟 6 執行）。
- verification_loop 帳本首次在真實任務落地（本卡 run log 即為首例，RUN-20260711-A01）。
- LLM judge 接上 provider 前，evals 對輸出品質的保證僅限結構層——P1-4 驗證。

## 建議下一步

1. 本卡 P0 三項落地＋CI 同款驗證全綠（進行中）。
2. 合併本 PR 後，開 P1-1（allowed_tools 當下強制）單獨一張卡——最大治理增量。
3. 每週清 review 佇列 1–2 張；P1-2 之後各項依序單卡推進。
4. P2 自主維運迴圈待 P1-1／P1-2 落地後再評估（先有硬防線，再談自動巡檢）。
