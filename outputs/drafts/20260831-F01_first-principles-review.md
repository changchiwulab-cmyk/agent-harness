# 第一性原理檢視：agent-harness 該往哪裡優化

- Task Card：20260831-F01（skill_type: ops，risk: medium）
- 日期：2026-08-31
- 證據標示：**[驗]**＝本次親自跑過指令／讀碼驗證　**[盤]**＝全 repo 盤點

---

## 結論

**這個專案不缺治理，缺的是讓已建立的治理變便宜。**

現行 roadmap（20260711-A01 的 P1-4〜P2-4，共 10 張卡）方向一致：再加一道 gate。
但同一份報告自己的結論是「人工審核是瓶頸」。往瓶頸上加閘是負貢獻——
這是本次檢視最主要的分歧點，也是四條工作線的共同判準。

三個第一性原理提問與答案：

| 提問 | 答案 | 推論 |
|---|---|---|
| 這套系統為何存在？ | 讓一人公司穩定產出商業價值，不是讓治理完整 | 98 張卡中 63 張在維護框架自己；框架成了自己的客戶 |
| 瓶頸在哪？ | 人工審核（專案自己的結論） | 優化目標＝**降低每單位價值的人工審核成本**，不是增加防線 |
| 平台已原生做了什麼？ | 唯一答案來源 NATIVE_OVERLAP.yaml **逾期 114 天** | 四項原生能力完全未採用而無人察覺 |

---

## 九項已驗證證據

| # | 發現 | 證據 |
|---|------|------|
| F1 | **框架變成自己的客戶**：98 張卡中 63 張 `skill_type: ops`（框架自身維運） | `grep skill_type tasks/20*.yaml` **[驗]** |
| F2 | **系統停擺一個月**：M1 指標 2026-08 = 0 張卡 → warn | `governance_metrics.py --today 2026-08-31` **[驗]** |
| F3 | **原生重疊度評估逾期 114 天** → M4 warn | `check_native_overlap_freshness.py` 回 STALE **[驗]** |
| F4 | **allow 層是空頭支票**：PERMISSIONS.yaml 宣告 9 項 allow，但 settings.json 無 `permissions.allow` 段，執行時照樣跳確認 | `system/PERMISSIONS.yaml:6-15` vs `.claude/settings.json` **[驗]** |
| F5 | **原生 deny 第 1 層不存在**：8 條 deny 只靠 `permissions_guard.py`（自承 fail-open 的「輔助防線」） | `SECURITY.md:22-24`、`PERMISSIONS.yaml` deny_enforcement **[驗]** |
| F6 | **retro 是幽靈 skill**：有合格 frontmatter（845 tokens）、列在 ROUTING_RULES，卻同時被 `VALID_SKILLS`／`ALLOWED_SKILL`／`.claude/skills/` 三處排除 → 建卡即失敗、原生不載入 | `validate_task_card.py:24`、`check_spec_consistency.rb:11`、`ls .claude/skills/` **[驗]** |
| F7 | **注入防護裝在錯誤的一側**：`INPUT_GUARDRAILS.md` 規範輸入，但偵測器掛 Stop hook 掃 `outputs/`（產出**之後**）。原生 `UserPromptSubmit` 鉤點未用 | `.claude/settings.json` hooks 段 **[驗]** |
| F8 | **草稿墳場**：M2 = drafts/reports 76/9 = 8.44，78 個草稿多數未晉升 | governance_metrics M2 **[驗]** |
| F9 | **每日工作流全靠散文重推**：CLAUDE.md 的 9 步流程每 session 由模型重新推導；`.claude/commands/` 目錄不存在 | `ls .claude/` **[驗]** |

### 一個順帶測到的護欄邊界（非缺陷，但值得記錄）

本次用 Bash heredoc 寫入含 `git push --force` **字串**的設定檔時，被
`permissions_guard.py` 當成真的要 force-push 而擋下 **[驗]**。
guard 分不出「執行該指令」與「檔案內容提到該指令」——這是 regex deny-list 的固有邊界，
與 SECURITY.md 已明載的「誤傷比漏抓更糟」取捨同源。不建議修（加豁免只會擴大繞過面），
但寫設定檔或文件時應改用檔案工具而非 shell heredoc。

---

## 本次落地

### 工作線 1：斜線指令（F9）— 把每日工作流從散文固化為指令

新增 `.claude/commands/` 五支，**只編排既有 script，不新增第二套驗證邏輯**：

| 指令 | 對應 CLAUDE.md 步驟 |
|---|---|
| `/task-new` | 1–2 建卡 → 驗證 → 綁定 active task |
| `/task-run` | 3–7 載入 context → 執行 → checkpoint → 驗證閉環 |
| `/task-close` | 7–9 gate → 執行紀錄 → 卡片回填 → 解除綁定 |
| `/queue` | 未結卡盤點 + WIP aging + keep/merge/kill 分流 |
| `/harness-check` | 全套本地回歸（CI 同款） |

CLAUDE.md 的 9 步敘述改為指向這三支，並註明**指令是固化不是特權路徑**——
不透過指令直接執行時，流程與約束完全相同。

### 工作線 2：注入偵測補輸入側（F7）

`check_untrusted_content.py` 新增 `--user-prompt-hook`：掃**使用者貼入的內容**，
這是注入最短的路徑，而原本的 `--stop-hook` 只看得到事後產出。兩側並存不互相取代。

語意刻意與既有 advisory 完全一致：永不阻斷、fail-open、乾淨時安靜、`(file, rule, sha)` 去重。
一個容易踩的細節已用測試鎖定：**UserPromptSubmit 的裸 stdout 會被併入 context**，
所以警告只能走 JSON `systemMessage`——advisory 訊息不該成為模型輸入的一部分。

測試 25 → 36 例；手動 drill 命中／隔離放行／去重／乾淨四路徑通過，殘留已清 **[驗]**。

### 工作線 3：規格漂移收斂（F6）與重疊度重評（F3）

**retro 四處對齊為 6**，並新增 `test_allowed_skill_matches_skills_directory`
直接對照 `skills/` 實際目錄——同類漂移下次由 CI 擋掉，不必靠人發現。
落地當下原生 skill 清單即出現 retro **[驗]**，`skill_type: retro` 的卡也通過 schema **[驗]**。

**NATIVE_OVERLAP 重評**（詳下節），M4 由 warn 轉 ok **[驗]**。

**ROUTING_RULES 31 → 22 行**：關鍵字對照表與各 skill 的 description 逐字重複，刪除。
兩份會漂移的真相來源不如一份。

**PERMISSIONS.yaml 誠實化**：新增 `allow_enforcement.status: declared_only`，
明載 allow 層目前是策略宣告而非 runtime 行為（F4）。修宣稱而非假裝已實作。

### 工作線 4：22 張未結卡分流（見下節）

---

## NATIVE_OVERLAP 重評

### 方法改了，不只數字改了

先前的 `aggregate_estimate_pct: 30` 是沒有算法的 baseline 數字，每季重評無從對照。
本次改為**可重現算式**：README 十六模組 `overlap_pct` 的算術平均，
**明確納入治理平面那 8 個 0% 的模組**——那正是本框架不可被原生取代的部分，
排除它們會讓 aggregate 失真成「執行平面重疊度」。

```
(100+0+85+0+50+95+80+0+0+60+85+0+40+0+0+0) / 16 = 37.2  →  37%
```

### 30% → 37%，但這是好消息

| 模組 | 舊 | 新 | 變動理由 |
|---|---|---|---|
| Skill Executor | 85 | **95** | 6/6 skill 原生註冊完成（本次補上第 6 個） |
| Planner/Router | 70 | **85** | 原生 description 路由實測有效；對照表已刪 |
| Permission | 75 | **85** | allow/ask/deny 三段皆可原生表達（待套用） |

+7 點全部來自**本框架主動採用原生**，不是原生功能長進來侵蝕本框架。
在這個情境下重疊度上升代表少維護一份重造品——是好事。37% 仍在 40% 警戒線下，
未觸發 v3 重構評估。

### 新增的一段：原生有什麼我們還沒用

舊表只回答「本框架有幾成被原生取代」，不回答「原生有什麼還沒採用」。
**第二個問題才是每季重評的實際價值**——五月到八月之間，下列四項有三項
處於完全未採用而無人察覺：

| 原生能力 | 採用狀態 | 說明 |
|---|---|---|
| 斜線指令 `.claude/commands/` | ✅ 本次採用 | 此前完全未用 |
| Hook 事件面 | ⚠️ 部分 | 已用 6 種；本次新增 UserPromptSubmit（待佈線）；未用 SessionEnd／SubagentStop／Notification |
| 子代理 `.claude/agents/` | ✅ 已採用 | 5 支成本路由子代理 |
| **Plugin 打包** | ❌ 未採用 | plugin 可一次打包 skills + commands + hooks + agents，是 v3 governance 抽取（D007）**比 fork repo + parity 測試更自然的載體** |

最後一項直接影響 P1-5 的判斷（見分流表）。

---

## 22 張未結卡分流

未結 22 張（含本卡）。**停留天數中位數 51 天，最久 136 天** **[驗]**。
狀態分佈：pending 13 / in_progress 5 / review 4。

判準：**keep**＝真正降低人工成本或補已驗證缺陷；**merge**＝與他卡或已完成工作重疊；
**kill**＝加的是「再一道 gate」但瓶頸在人工審核 → 淨負貢獻，或前提已不成立。

### keep（9 張）

| 卡 | 天 | 理由 |
|---|---|---|
| **20260424-E01** 電商產業機會 | 129 | ⭐ **佇列裡僅有的三張商業價值卡之一，且應該排最前面**。它們坐了四個月，同期出貨了 34 張框架自維護卡——這就是 F1 的具體樣貌 |
| **20260424-F01** 金融 AI 顧問提案 | 129 | ⭐ 同上 |
| **20260424-H01** 醫療 AI 可行性 | 129 | ⭐ 同上 |
| **20260711-A01** 四層對照分析 | 51 | DoD 已達成、有 result_summary 與 3 個 checkpoint。**這不是工作，是決策佇列** |
| **20260712-P11** allowed_tools 強制 | 50 | DoD 5/5 已達成，同上 |
| **20260716-P12** failure_counter 自動計數 | 46 | DoD 5/5 已達成，同上 |
| **20260716-P13** 注入偵測佈線 | 46 | DoD 5/5 已達成，同上 |
| **20260716-P14** evals 6/6 + LLM judge | 46 | P1 裡**唯一真正打瓶頸的一張**：把品質保證從結構層升到語意層＝用自動判定換人工閱讀 |
| **20260716-P21** 有界自主維運迴圈 | 46 | 排程跑唯讀彙整→drafts，人只讀摘要不必自己跑指令＝減少人工動作 |

> 四張 `review` 卡的工作全部完成、只差一句「可以」。**一次批次確認即可讓佇列少掉 4 張**，
> 這是投入產出比最高的一個動作。

### merge（8 張）

| 卡 | 天 | 併入哪裡 |
|---|---|---|
| **20260620-001** 驗證閉環 | 72 | 五條 DoD 的產物全部存在且已進 CI（`verification_loop.py`／測試／e2e drill／`VERIFICATION_LOOP.yaml`）**[驗]**——工作早已落地，卡片只是沒關。建議直接翻 done |
| **20260509-N06** plugin repo | 114 | ⬇ |
| **20260509-N09** 切換引用 plugin | 114 | ⬇ |
| **20260509-N10** runbook 修正 | 114 | ⬇ |
| **20260509-N11** plugin P1/P2 修正 | 114 | ⬇ |
| **20260509-M01** 原生 Memory 試點 | 114 | 五張全部卡在**同一個帶外動作**（D007 建 repo，已延後 114 天）。五張卡不是五件工作，是一個決策的五個下游。建議收成**一張 D007 決策卡**：建 repo、改走 plugin 打包、或明確放棄——決定後其餘自然收斂 |
| **20260716-P15** plugin fork parity | 46 | 前提已鬆動：重疊度重評指出 plugin 打包是比 fork + parity 測試更自然的載體。應併入上述 D007 決策，而非先蓋 parity 鎖 |
| **20260716-P16** WIP aging 指標 | 46 | 本卡已交付分流與 aging 數據（人工版）。**先讓佇列見底，再談自動量測**——佇列不會因為被量測而變短。若清完後仍需長期監控，再把指標接進 governance_metrics |

### kill（4 張）

| 卡 | 天 | 理由 |
|---|---|---|
| **20260417-W01** 補寫 7 個 markdown | 136 | 純補登陳年產出，沒有下游消費者。坐了 136 天沒人需要它，就是它不需要存在的證據 |
| **20260716-P22** 熔斷按卡分閘 | 46 | 全域熔斷可用，且**沒有觀察到誤跳閘的實例**。為假想問題增加維度。真的誤跳一次再開 |
| **20260716-P23** 放寬 fail-closed 視窗 | 46 | 放寬 fail-closed = 更多攔阻 = 更多人工介入，直接與瓶頸相反。且該卡自己說要「依實測誤擋數據」推進，而誤擋數據為零 |
| **20260716-P24** 閉環帳本常態化到 medium+ | 46 | M2 已顯示產物產出遠快於被閱讀（78 草稿 / 9 報告）。把帳本從「首例」推成「常規要求」＝每張 medium+ 卡多一份沒人讀的 YAML |

> **kill 不等於這些想法錯**，而是在人工審核是瓶頸的前提下優先序為負。
> 觸發條件成立時（誤跳閘、誤擋、稽核缺料真的咬到人）隨時可以重開。

### 分流後的樣子

```
現在：22 張未結（中位數停留 51 天）
批次確認 4 張 review + 關掉 20260620-001 + kill 4 張 →  13 張
D007 決策收斂 5 張 N/M 系列              →  9 張
其中 3 張是商業價值卡，應該排最前面
```

**不改任何卡片 status**——依指示只出建議，實際收斂等點頭。

---

## 尚待人工的一件事

`.claude/settings.json` 是 SECURITY.md §變更安全相關檔案明列的高風險檔，
本次依 draft-first（硬規則 2）產出完整替換草案：

**`outputs/drafts/20260831-F01_settings-permissions-proposal.json`**

四處差異，hooks 段除新增 UserPromptSubmit 外**逐字未動**（已程式比對驗證 **[驗]**）：

1. 新增 `permissions.allow`（42 條）——修掉 F4，讓宣告的 allow 真的免確認。
   刻意不含 `outputs/reports/**` 與 `memory/**`（兩者屬 ask）。
2. 新增 `permissions.deny`（24 條）——F5 的第 1 層。
   `rm` 只擋破壞性旗標，對齊 PERMISSIONS.yaml「單檔 rm 由模型層自律」的既有分寸，不擅自收緊策略。
3. `ask` 段補上 `.claude/settings.json` 與 `permissions_guard.py` 自身
   ——SECURITY.md 早已列為高風險，但先前沒有對應規則。
4. hooks 新增 `UserPromptSubmit`（模式已實作測試，36 例全綠，僅差佈線）。

**套用步驟**：覆蓋 `.claude/settings.json` → 寫 `logs/approvals/` 紀錄 →
把 `PERMISSIONS.yaml` 的 `allow_enforcement.status` 改為 `runtime`、
`deny_enforcement` 有原生簽章者標 `native` → `SECURITY.md` 防線分層表第 1 層補上 deny →
`tests/e2e/test_input_guardrails.py` 加一條 UserPromptSubmit 佈線斷言（比照既有 Stop hook 斷言）。

---

---

## 驗證結果

| 項目 | 結果 |
|---|---|
| 四層 gate（`gate_check.py 20260831-F01`） | ✅ PASS（schema／rule／completion 全 pass，risk n/a） |
| 驗證閉環（`verification_loop.py`） | ⚠️ **escalated / human_gated** — 9 條 DoD 中 7 pass、2 依賴人工套用 settings.json。**不重試**：重試無法改變閘門條件 |
| Ruby 一致性 8 支＋YAML parse | ✅ 全綠 |
| Python 單元測試（含新增 11 例，25→36） | ✅ 全綠 |
| e2e 4 支＋evals | ✅ 全綠 |
| `sync_derived.sh --check` | ✅ 零漂移 |
| context budget | ✅ 1,703 / 3,000 |
| `check_native_overlap_freshness.py` | ✅ STALE → FRESH |
| governance_metrics M4 | ✅ warn → ok |
| 回歸紅線 | ✅ 存量卡零回填、`permissions_guard.py` 一行未動 |

閉環判為 `human_gated` 而非 `hard_stop` 是這次值得記錄的一點：
**驅動器正確區分了「修不好的失敗」與「等人的失敗」**，並據此建議不重試。
這是 A01 當時「閉環帳本尚未在真實任務產生」的第二個真實案例。

順帶發現一處介面不一致（未修，不在本卡範圍）：
`gate_check.py` 吃 **task_id**，`verification_loop.py` 吃 **檔案路徑**——
兩支同層驅動器的呼叫慣例不同，容易誤用。建議之後統一。

---

## 高風險假設

- **`permissions.allow` 會減少而非增加風險暴露**：allow 清單刻意只鏡射
  PERMISSIONS.yaml 既有宣告，未擴張任何權限；但一旦生效，寫 drafts／logs／tasks
  與 git checkpoint 將不再逐次確認。若使用者其實**依賴那些確認當作人工檢查點**，
  這個假設就錯了——套用後前兩週請留意是否有非預期寫入。
- **原生 deny 不會誤傷**：`curl`/`wget` 全面 deny 假設本 repo 無合法 HTTP 用途
  （已盤點：scripts 中無任何呼叫 **[驗]**）。若日後要接外部 API，需先改此清單。
- **kill 的四張不會回頭咬人**：前提是「沒有觀察到誤跳閘／誤擋」。
  若 P2-2／P2-3 的觸發條件實際發生過但沒被記錄，這個判斷會過於樂觀。

## 待驗證

- `permissions.allow` 生效後，人工確認次數是否真的下降（M 指標無此欄位，需人工感受兩週）。
- UserPromptSubmit advisory 的誤報率——ledger 已能以 `--stats` 分組統計，
  與 P13 的 Stop hook 誤報觀察合併看。
- 斜線指令是否真的被用。若兩週後仍走散文流程，代表指令設計不合手，該修指令而非怪流程。

## 建議下一步

1. **先做投報比最高的那一步**：批次確認 4 張 review 卡 + 關掉 20260620-001。佇列 22 → 17。
2. **套用 settings.json 草案**（上節四步）——這是本次唯一沒能自動落地的部分。
3. **執行 kill 4 張、merge 8 張**的分流。佇列 → 9 張。
4. **然後回去做生意**：E01／F01／H01 三張商業卡已經等了 129 天。
   框架已經夠好了，缺的是拿它產出價值。
5. D007 決策卡（建 repo vs plugin 打包 vs 放棄）——五張 N/M 系列的總開關。
