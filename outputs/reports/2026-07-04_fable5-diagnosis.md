# Harness 快速診斷 — token 洩漏 / 失焦 / 易錯 前三名

> **正式報告** ｜ 日期：2026-07-04 ｜ Task Card：`20260704-F01` ｜ 作者：Fable 5 session（一次性）
> 定位：後續制度檔（DISPATCH_POLICY、JUDGMENT_RUBRICS、MAINTENANCE_PROTOCOL）的依據。
> 與既有自評（`outputs/reports/harness-self-assessment-v1.md`，7/10）互補：該報告評的是
> **治理設計的完備度**（可觀測、耐久、審計，R1–R8 已補）；本診斷評的是**每個 session
> 實際運行時的行為缺陷**——自評看不到的層面，因為它也是在同一種運行方式下寫出來的。

---

## 第 1 名（token 洩漏）：規則重複載入 ＋ 工具結果全文進主對話

### 症狀

**a. 制度層重複。** 同一條規則活在多個檔案裡，每個 session 重複載入、且會漂移：

| 重複對 | 證據 |
|--------|------|
| CLAUDE.md 權限段 ≈ PERMISSIONS.yaml 摘要 | 舊 CLAUDE.md 第 9–13 行 vs PERMISSIONS.yaml 全檔 |
| CLAUDE.md 執行流程段 ≈ GATE_POLICY + EXECUTION_LOG_SCHEMA 摘要 | 舊 CLAUDE.md 第 15–17 行 |
| AGENT_CONTEXT.yaml ≈ CLAUDE.md 自我描述 | NATIVE_OVERLAP.yaml 自標 60% 重疊 |
| GLOBAL_RULES 成本段 ≈ COST_POLICY 行為規則段 | 兩檔「能用檔案讀取就不 web search」等句近乎逐字重複 |
| ROUTING_RULES 路由表 ≈ 各 SKILL.md description | NATIVE_OVERLAP.yaml 自標 70% 重疊 |

**b. 運行層洩漏（更大宗、且無任何政策管）。** 主對話直接執行大量讀取——掃 repo、
讀長檔、web search——工具結果**全文**進入主對話 context。COST_POLICY 寫了「大型檔案用
路徑引用」，但這是提醒，不是機制；一個 Opus session 讀 10 個檔案做研究，50K token 的
原始材料就永久佔據 context，直到 compaction 把任務目標一起壓掉。

### 修法

1. **單一事實來源原則**：每條規則只活在一個檔案；其他位置只放一行指標。
   → 已執行：CLAUDE.md 重寫為路由層（見本次 commit），重複段落全刪。
2. **大量讀取隔離到 subagent**：主對話只進結論，原始材料留在 subagent 的
   拋棄式 context 裡。→ 制度化於 `system/DISPATCH_POLICY.md` §1（含具體觸發門檻）。

---

## 第 2 名（失焦）：模型調度層完全空白，指揮官下場做工

### 症狀

整個 harness 沒有任何檔案回答：什麼工作該派 subagent？派給哪個 model？用什麼 effort？
COST_POLICY 的「模型路由規則（v2 準備）」只有 3 行 stub；AGENT_CONTEXT.yaml 還停在
「單一代理」世界觀。結果是每個 session 的預設行為＝指揮官親自下場：自己 grep、自己讀檔、
自己改一批檔案。

失焦的機制很具體：主對話做完 20 次工具呼叫後，Task Card 的 goal 被稀釋在幾萬 token 的
中間產物裡。FAILURE_TAXONOMY 的 SPEC-03（對話歷史遺失）、COORD-03（目標偏離）記錄的
就是這個的下游症狀——但既有 mitigation 全是「提醒自己回頭看」型，沒有結構性防呆。
結構性的解法是讓主對話**根本不裝載**那些會稀釋目標的材料。

### 修法

1. `system/DISPATCH_POLICY.md`：六節調度守則（不下場觸發條件、派工三件套、
   model × effort 對照表、回報合約、升降級路徑、驗證不自驗）。
2. `system/MODEL_ROSTER.md`：查證過的可用型號與語法，型號更迭只改這一檔。
3. `system/DELEGATION_TEMPLATES.md`：五種任務型態的填空模板，把派工成本降到零思考。
4. 指揮官基準：**Opus 4.8**、訂閱制（派工的邊際成本近似固定，守則預設大方派工）。

---

## 第 3 名（易錯）：驗證自驗——執行者自己跑自己的 gate

### 症狀

GATE_POLICY 四層驗證（schema → rule → completion → risk）設計良好，但全部由**同一個
context 裡的同一個模型**執行。寫出「假完成」的 context 正是最不可能發現假完成的
context——它帶著「我已經做完了」的全部偏見去打勾。FAILURE_TAXONOMY 的 VAL-01（假完成）、
VAL-02（驗證不完整）、VAL-03（格式對就當內容對）佔全部失敗的 21%，根因都是這個。
CI 與 E2E 測試守得住 schema 和路徑，守不住內容品質。

弱模型接手後這個問題會放大：Sonnet/Haiku 的自驗比 Opus 更容易把「寫了字」當成「答了題」。

### 修法

1. **驗證不自驗**：DoD 驗收一律派 fresh-context subagent，不給它執行過程、只給
   Task Card 與產出路徑。→ `system/DISPATCH_POLICY.md` §6。
2. **驗法分型**：檔案落地用 read-back；程式碼用測試或實跑；高風險判斷加第二意見
   或多答案評審選優。→ `system/JUDGMENT_RUBRICS.md` §5。
3. **原生化**：`.claude/agents/verifier.md` 讓驗收員一個 Agent 呼叫就能啟動，
   降低「因為麻煩所以跳過」的機率。

---

## 誠實條款：這套制度的極限

拆解、驗證、fresh-context 驗收、多樣本評審，補得了**執行品質**——漏做、假完成、
格式錯、路徑錯、規則違反，這類問題弱模型照著檔案跑就能壓下去。

補不了的是**模糊題與品味判斷**：策略取捨、文案語感、客戶語氣拿捏、沒有明確判準的
設計決策。弱模型照 rubric 跑會產出「合格但平庸」的答案，而且**無法自知平庸**——
rubric 全過不代表東西好。

遇到這類任務時只有三條路（判準見 `system/JUDGMENT_RUBRICS.md` §3）：

1. **升級**：換更強的 model 重做該子任務（Opus，或把問題存入待強模型清單）。
2. **外部第二意見**：交使用者裁決，或用另一個獨立 context / 供應商互評。
3. **明說做不到**：輸出標注「此判斷超出可驗證範圍，建議人工」，不假裝 rubric 覆蓋了品味。

禁止第四條路：把品味題包裝成已通過驗證的完成品。

---

## 診斷方法備註

- 親自讀完 system/ 全部 14 檔、CLAUDE.md、README、skills 結構、CI workflow、
  scripts/ 檢查器、先前自評與 R1–R8 執行紀錄（git log 佐證）。
- model/effort 語法經 claude-code-guide agent 對官方文件（code.claude.com/docs）查證，
  非憑記憶；結果落於 `system/MODEL_ROSTER.md`。
- 本報告經計畫核准後直接寫入 `outputs/reports/`（write_reports 之人工確認
  ＝2026-07-04 plan approval，見 Task Card 20260704-F01 context 欄）。
