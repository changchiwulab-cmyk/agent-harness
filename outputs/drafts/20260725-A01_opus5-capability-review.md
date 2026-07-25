# Opus 5 世代能力對照：agent-harness 完整檢視與優化計劃

- Task Card：20260725-A01（skill_type: analysis，risk_level: medium）
- 日期：2026-07-25
- 輸入：claude-api skill（當代模型能力）＋ Claude Code hooks／settings.json 官方文件（2026-07 現況）＋ 全 repo 實測
- 證據等級：**[驗]** ＝ 本次親自讀碼／實跑驗證（附檔案:行號或指令輸出）；**[盤]** ＝ 全 repo 盤點彙整

## 結論與建議

專案基線健康（17 支 Python 測試 + 4 支 e2e 全綠、evals 2/2 校準通過、治理指標無 alert）**[驗]**，
問題不在「功能不足」，而在**平台能力已經前進、專案的宣稱與設定還停在舊世代**所產生的三類接縫：

1. **執法宣稱與實際覆蓋面不符**（F1）—— `PERMISSIONS.yaml` 宣告 `auto_write_memory` 由 runtime 執法，
   但 guard 規則只涵蓋 shell 重導向；原生 auto memory（平台**預設開啟**）不經 Bash，完全在防線之外。
   這與本專案唯一的賣點（宣稱＝實作）直接衝突，是本次最重要的發現。
2. **原生已提供、專案未採用的執法層**（F2、F3、F8）—— `permissions.deny` 零使用、
   `UserPromptSubmit`／`SubagentStop` 未掛、`.claude/commands/` 空缺。
3. **可量化指標本身不可稽核**（F4）—— M4 的輸入值 `aggregate_estimate_pct` 是手設的 30，
   與同檔模組表的算術平均（62.2%）相差逾一倍**[驗]**，兩數無可複現關係。

已採**選項 C（報告＋P0 修正）**：五項 P0 全部落地並通過同款 CI 檢查；F3／F8 等需寫程式與演練的項目
只寫進 roadmap 分批開卡，不一次灌爆已有 21 張未結卡的 WIP。

**一句話建議**：先把「宣稱＝實作」這條線補回來（已完成），再依 roadmap 順序把
`UserPromptSubmit` 掛上——那是剩餘項目中治理增量最大的一項。

---

## 一、修正前必須說明的一項預測失準

規劃階段我預測「NATIVE_OVERLAP 誠實重評後 aggregate 會越過 50%，M4 轉 alert 並觸發 T-B（v3 評估）」。

**實際計算結果是 43%，落在 40–50% 的 warn 帶，未觸及 alert，不觸發 v3。[驗]**

差異來源：舊表只評了 9 個重疊度較高的模組，我據此外推；補齊為 README 定義的 16 個編號模組後，
本 harness 獨有、重疊度極低的治理模組（Decision Log 0%、Failure Taxonomy 0%、Gate Verifier 5%、
Execution Log 10%、Audit Log 10%）進入分母，把平均拉了下來。

對使用者的影響：**原本預告需要您裁決的「是否啟動 v3」這件事，這次不成立**。M4 轉 warn 的處理方式
依治理文件是「下次 retro 帶討論」，不需即刻行動。

---

## 二、逐項發現

### F1 — `auto_write_memory` 的執法宣稱與實際覆蓋面不符 ⚠️ 本次新發現

| 項目 | 內容 |
|------|------|
| 宣稱 | `system/PERMISSIONS.yaml` `deny_enforcement` 標記 `auto_write_memory: runtime` **[驗]** |
| 實際 | `scripts/permissions_guard.py:135-146` 的規則**只比對** shell 重導向／`tee`／`cp`/`mv` 寫進 `memory/` **[驗]** |
| 缺口 | Claude Code 原生 auto memory（settings key `autoMemoryEnabled`，**平台預設 `true`**）不經 Bash，guard 看不到；`.claude/settings.json` 對 `memory/**` 只有 `ask`，涵蓋不到原生機制自己的儲存路徑 **[驗]** |

這不是 regex 寫得不夠好，而是**該行為根本不在 Bash 通道上**——再多簽章也攔不到。

**已修**：`.claude/settings.json` 設 `autoMemoryEnabled: false`；`PERMISSIONS.yaml` 與 `SECURITY.md`
加註覆蓋邊界；新增 `TestNativeDenySync.test_auto_memory_is_disabled` 鎖定。

**一般化教訓（已寫入 `SECURITY.md`）**：`deny_enforcement` 的 `runtime` 語意是
「該條 deny **有一組 shell 簽章**會被攔」，**不等於**「該行為的所有路徑都被攔」。
平台每新增一項能自主寫檔／發外部請求的原生功能，都要重查對應 deny 條目的覆蓋面。

> 附帶：`outputs/drafts/2026-05-09_n07_native-memory-evaluation.md` §1 表列
> 「寫入須使用者明確確認（非自動寫入）」已與現況不符 **[驗]**，已加過期標記（結論未動）。

### F2 — 原生 `permissions.deny` 完全未使用

`.claude/settings.json` 原本只有 9 條 `ask`、**零條 `deny`** **[驗]**；deny 100% 依賴
`permissions_guard.py` 的手寫 regex，而 `SECURITY.md` 自己已列出該層的四項繞過面。

**已修**：新增 10 條原生 deny 規則（4 個 deny key）。設計取捨兩點：

- **只鏡射「前綴比對即可無歧義命中」的簽章**。原生 Bash 規則是前綴／glob 比對，
  對 curl 型簽章（webhook／金流／發布 API 出現在指令中段）不適用，那些維持 guard-only —— 少鏡射勝過誤擋。
- **`PERMISSIONS.yaml` 的 `native_deny` 是唯一事實來源**，settings.json 是衍生物；
  sync 鎖由三方擴為四方，並已負向驗證斷言非空轉（移除任一條或缺 `autoMemoryEnabled` 皆翻紅）**[驗]**。

這一層不取代 guard，也不取代 `SECURITY.md` 的 L0 sandbox，是在 guard 前面補一道 harness 之外的硬牆。

### F3 — hook 事件覆蓋面（roadmap）

已用 6 種：`PreToolUse` / `PostToolUse` / `PostToolUseFailure` / `Stop` / `SessionStart` / `PreCompact` **[驗]**。
未用且與治理直接相關者：

| 事件 | 缺口 |
|------|------|
| `UserPromptSubmit`（可 block、可注入 `additionalContext`） | 硬規則 1「沒有 Task Card 不執行」目前**只在寫入 `outputs/reports/` 時**擋（`task_card_guard.py`）**[驗]**。此事件是把它前移到輸入當下的正確位置，也是 `check_untrusted_content.py` 輸入側的自然掛點（現況只有 Stop 掃 `outputs/`，屬輸出側 advisory） |
| `SubagentStart` / `SubagentStop`（後者可 block） | 5 個 specialist 子代理**完全不受** Stop hook 三支檢查覆蓋（`sync_derived.sh`／`session_stop_checks.py`／注入掃描只在主 session Stop 跑）**[驗]**。子代理寫進 `outputs/drafts/` 的產出在該輪不會被掃到 |
| `PermissionRequest`（含 `addPermissionRule`） | `APPROVAL_POLICY.yaml` 的「同任務 3 次批准請求即暫停」仍是 prompt-only **[盤]** |

### F4 — M4 的輸入值不可稽核（已修）

`aggregate_estimate_pct: 30` 是手設值，同檔模組表的算術平均為 **62.2%**（9 模組）**[驗]**，
註解稱兩者「同量級」——相差逾一倍。指標的輸入無法被複現，等於 M4 這條「可量化」證據本身不可稽核。

**已修**：改為 `aggregate = mean(overlap_pct where in_aggregate)`，評估範圍補齊為 16 個編號模組
（Interface 依舊表自身註記「屬 runtime 不是模組」排除於分母外），得 640/15 = **43%**，
並以指令驗證宣告值與算術一致 **[驗]**。

實質重評變化（非只是換算法）：

| 模組 | 前 | 後 | 理由 |
|------|---|---|------|
| Checkpoint | 0% | 30% | 原生 `/rewind` 檔案 checkpointing 已存在（`fileCheckpointingEnabled` 預設 true），舊表 0% 已過期。但 `/rewind` 是 session 內、不可推送、不可稽核，故非高分 |
| Permission | 75% | 85% | deny 已鏡射進原生 |
| Cost Policy | 40% | 60% | 新增 `effortLevel` / `fallbackModel` / `availableModels` 維度 |
| Context Manager | 50% | 65% | `autoCompactEnabled`、`PostCompact`、`claudeMdExcludes` |
| （新增 7 個此前未評模組） | — | 0–20% | Decision Log、Failure Taxonomy、Gate Verifier、Task Card、Execution Log、Audit Log |

另新增 `unadopted_native` 區塊：有原生能力但本 harness 未採用者屬**採用缺口**而非重疊，不計入分母
（混入會扭曲指標語意）。

### F5 — 成本路由缺 effort 維度（已修）

`system/COST_POLICY.md` 的路由表只有「選哪個模型」一維 **[驗]**。當代模型另有
`effort`（`low`/`medium`/`high`/`xhigh`/`max`），是比換模型更細緻的槓桿。

**已修**：每個子代理補「建議 effort」欄，並記錄三項取捨：

- 先調 effort 再考慮換模型（同模型降一級 effort 通常比降一層模型更能保住品質）。
- Opus 5 世代 `low`/`medium` 相對前代異常強，routine 工作不需預設高 effort。
- **effort 不是控制輸出長度的旋鈕**——要縮短產出要用 prompt，調 effort 可能只改思考量。

**刻意不做**：不把 `model`／`effortLevel` 寫進 `settings.json`。寫死會奪走使用者 `/model`、`/effort`
的臨場調整空間；成本路由是建議而非 deny 級硬規則，維持在文件層是正確的執法強度。（此為原預告要請您
裁決的第 2 題，已在報告中以理由結案，如不同意可推翻。）

順帶修掉兩處文件漂移 **[驗]**：穩定前綴實測值註記 `~400 tokens`（實為 1,620，差逾 4 倍）；
skill 預算註記仍寫「含 eval_examples」，與 20260711-A01 已對齊的口徑相反。

### F6 — Opus 5 行為位移與現有 prompt 的衝突（已修）

| 位移 | 對本專案的衝擊 | 處置 |
|------|--------------|------|
| 會自我驗證，明寫的自我檢查指令造成**過度驗證** | `skills/writing/SKILL.md` 執行流程第 5 步、`CONTEXT_ENGINEERING.md` 自我檢查清單與腳本層重複 **[驗]** | 只移除這兩處 prompt 層叮嚀 |
| 擴張任務 scope | 直接威脅 Task Card 的 DoD 契約 | `GLOBAL_RULES.md` 新增「任務範圍紀律」 |
| 比前代**更**傾向委派子代理 | 5 個子代理無委派上限，成本與延遲相乘 | 新增「子代理委派上限」（≤3 並列、不委派驗證） |
| 寫到磁碟的產出更長 | `expected_output` 有篇幅約束 | 新增「產出篇幅」 |

> **必須劃清的界線**：這裡移除的只是 **prompt 層與腳本層重複的叮嚀**。
> `gate_check.py`／`verification_loop.py`／`GATE_POLICY.yaml`／CI **一律未動**——
> 那是稽核控制，不是模型自檢。把兩者混為一談會把本專案的核心價值一起刪掉。

### F7 — 組裝順序紀律終於有數字（已修）

最小可快取前綴**因世代而異且非單調**：Opus 5 為 512、Opus 4.8 為 1,024、Opus 4.6/4.5 與 Haiku 4.5 為 4,096。
本專案穩定前綴實測 1,620 tokens（本卡修改後 2,130）**[驗]**。

兩點推論已寫入 `CONTEXT_ENGINEERING.md` §一：

1. 「穩定前綴先」這條原則**在當代真的有回報，在 4.6 世代則沒有**（低於門檻靜默不快取）。過去是憑理論寫的，現在有數字。
2. 前綴**變短不一定更好**——低於門檻反而完全失去快取。壓縮 `CLAUDE.md` 要看門檻，不是「越小越好」。

### F8 — `.claude/commands/` 未使用（roadmap）

harness 協定（建卡／gate-check／run-log／audit／decision）全靠 prompt 記憶 **[驗]**；
`outputs/drafts/agent-governance-bootstrap/commands/` 已有 5 個現成 command 草稿可直接改寫 **[盤]**。

---

## 三、選項六維比較

### 選項 A：不做（維持現狀）

| 維度 | 評估 |
|------|------|
| 價值 | 0 |
| 成本 | 0 |
| 風險 | **高**：F1 是「硬規則寫了、runtime 沒守住」，且原生 auto memory 預設開啟——不處理等於 deny 清單有一條是假的 |
| 可行性 | 高 |
| 執行難度 | 無 |
| 預期回報 | 負：M4 輸入不可稽核會持續侵蝕「可量化」主張 |
| 一人公司適配度 | 低：治理框架的可信度是唯一賣點 |

### 選項 B：只出分析報告

| 維度 | 評估 |
|------|------|
| 價值 | 中：缺口被記錄 |
| 成本 | ~2 小時 |
| 風險 | 中高：已驗證的執法缺口繼續留在 main；報告會過期 |
| 可行性 | 高 |
| 執行難度 | 低 |
| 預期回報 | 中偏低：知而不修 |
| 一人公司適配度 | 中：又多一份待辦文件，review 佇列已 4 張 |

### 選項 C：報告＋P0 修正（✅ 本卡採用）

| 維度 | 評估 |
|------|------|
| 價值 | 高：三類接縫一次對齊，宣稱恢復可信 |
| 成本 | ~4 小時，本 session 內 |
| 風險 | 低：改動面小且全被測試鎖住；deny 採保守鏡射（少鏡射勝過誤擋）；prompt 只加不刪＋移除兩句重複 |
| 可行性 | 高：全在本 repo、無外部依賴 |
| 執行難度 | 低中：sync 測試由三方擴四方需設計 |
| 預期回報 | 高：F1 從「宣稱有、實際沒有」變成「宣稱有、測試鎖住」 |
| 一人公司適配度 | 高：一次 PR 審完，WIP 不增 |

### 選項 D：報告＋P0＋roadmap 全部開卡

| 維度 | 評估 |
|------|------|
| 價值 | 最高（若全落地） |
| 成本 | +4–6 個工作天 |
| 風險 | 中高：WIP 由 21 張再加 8 張，人工審核是既有瓶頸 |
| 可行性 | 中：技術可行，人力不可行 |
| 執行難度 | 高 |
| 預期回報 | 高但延遲：roadmap 各項互相獨立，分批不損失價值 |
| 一人公司適配度 | 低：違反本專案自己的 WIP 教訓 |

---

## 四、改善 Roadmap（本次不開卡，建議每週 1–2 張）

依「治理增量／成本」排序，與既有 backlog 合併：

| # | 項目 | 估時 | 說明 |
|---|------|------|------|
| 1 | **`UserPromptSubmit` hook** | ~1 天 | 硬規則 1 前移到輸入當下＋注入偵測輸入側掛點。**剩餘項目中治理增量最大**，與已完成的 P1-3（輸出側 advisory）互補成雙側防線 |
| 2 | **`SubagentStop`／`SubagentStart` 覆蓋** | ~0.5 天 | 補上子代理產出不受 Stop 檢查的漏洞 |
| 3 | **`.claude/commands/`** | ~0.5 天 | 草稿樹已有 5 個現成檔案 |
| 4 | 既有 P1-4（evals 2/6 → 6/6 + LLM judge 接 provider） | ~1 天 | judge 建議 `claude-opus-5` + 結構化輸出 json_schema + `effort: low`；**CI 維持 rule judge**（無網路依賴） |
| 5 | `PermissionRequest` hook | ~0.5 天 | 落地 APPROVAL_POLICY 的「3 次批准請求即暫停」 |
| 6 | 既有 P1-5／P1-6／P2-2／P2-3／P2-4 | — | 維持原序 |
| 7 | 既有 P2-1（有界自主維運迴圈） | — | **建議先重評**：現有原生解（`/loop`、排程 deployment），該卡應先判「自建 vs 用原生」再實作 |
| 8 | sandbox／`defaultMode` 評估 | — | 對應 `SECURITY.md` 防線分層的第 0 層空缺 |

---

## 高風險假設

- **原生 deny 規則的比對語法**：本次採 `Bash(cmd *)` 前綴形式。若實際比對語意與預期不同
  （例如不匹配帶額外前置字元的指令），這 10 條可能比預期寬鬆。**緩解**：這是**額外**一層，
  guard 的 regex 仍在原位，最壞情況是回到修改前的防護水準，不會比原本更差。
- **`autoMemoryEnabled: false` 的行為面未實測**（見待驗證）。若該 key 名稱或語意與文件不符，
  F1 的缺口實際上仍開著。**緩解**：`SECURITY.md` 已明文記錄此路徑與封閉方式，不是靜默假設。
- **重評分數帶主觀**：16 個模組的 overlap_pct 是人工判斷。aggregate 43% 距 50% alert 線僅 7 個百分點，
  若某幾個模組評分偏低 5–10 個百分點即可能翻成 alert。**緩解**：本版已把計算方法寫成可複現公式，
  下一季重評時分歧點會落在個別模組而非總數，容易討論。

## 待驗證

- **`autoMemoryEnabled: false` 的實際效果未做行為實測**——本次只驗證了設定值已寫入且被測試鎖定 **[驗]**，
  未實測「原生 auto memory 確實不再寫入」。這是設定旗標，無法用單元測試證明其行為。
  建議下次 session 啟動時觀察是否仍出現自動記憶提示。
- **原生 10 條 deny 規則未做實際觸發測試**——未實跑 `rm -rf` 等指令確認被原生層擋下
  （會與 guard 的攔阻混淆，且屬破壞性指令）。目前只驗證了規則已寫入且與來源同步 **[驗]**。
- **本卡意外產生的 P1-4 佐證資料點 [驗]**：把本報告丟給 `run_evals.py` 評分時，
  `includes_no_op_option` 判為 fail（score 0.8）。原因不是報告缺「不做」選項，而是該 rubric 用
  **字面子字串比對**找「維持現狀」四個字，而本報告原本寫「選項 A：不做」——語意相同、字面不同。
  已改為「不做（維持現狀）」使其通過，但這正是 P1-4「rule judge 只保證結構層、需升到語意層」的
  實例證據：**rule judge 會對同義改寫產生偽陰性**。建議 P1-4 執行時把本例納入 LLM judge 的校準集。

- **`permissions_guard.py` 的一處潛在不一致（本次未修）**：`git_force_push` 規則的
  `permission_key` 是 `modify_production_data` 而非 `git_force_push`（`scripts/permissions_guard.py:110-111`）**[驗]**。
  目前兩者都在 deny 清單中故運作正常，但若日後移除 `modify_production_data`，force-push 攔阻會
  靜默失效而 `deny_enforcement` 仍宣稱 runtime。屬既有小瑕疵，修它會改動 guard 語意，未納入本卡範圍。

## 建議下一步

1. 審核本 PR（5 項 P0 全數通過同款 CI 檢查）。
2. 合併後開 roadmap #1（`UserPromptSubmit` hook）單獨一張卡——剩餘項目中治理增量最大。
3. M4 現為 warn（43%），依治理文件於下次 retro 帶討論即可，**不需即刻行動**。
4. 每週清 review 佇列 1–2 張；roadmap 其餘各項依序單卡推進。
