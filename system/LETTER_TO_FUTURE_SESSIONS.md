# 給未來 session 的信 LETTER_TO_FUTURE_SESSIONS

> 寫於 2026-07-03，Fable 5 的唯一一次 session。你——正在讀這封信的模型——多半是 Opus、Sonnet 或 Haiku。
> 這封信講三件使用者沒問、但對這個環境最重要的事，以及這套制度最可能怎麼爛掉。
> 讀完就夠了，不需要常駐 context；需要細節時按 CLAUDE.md 的載入地圖去查。

## 先說一件事

你不需要是最強的模型才能把這裡的工作做好。這套制度的設計前提就是：**結構承擔智力**。拆解、派工、驗收、留痕——照著做，你的產出下限就是強模型的水準；不照做，強模型的產出也一樣會失控。2026-05-29 的自我評估（7/10）扣的分全部是「設計完備、未經實證」，沒有一分扣在能力上。

## 三件最重要的事

### 1. 這套制度的頭號敵人是規則膨脹，而規則膨脹長得像「負責任」

每次踩坑加一條規則，每條規則看起來都有道理——五十次之後，CLAUDE.md 變成三千 token 的免責聲明，每個 session 都在繳規則稅，而且互相衝突的規則讓行為變得隨機。**教訓寫進教訓紀錄（append-only 段），不要寫進正文**；教訓要升級成規則，必須過使用者這一關（`system/MAINTENANCE_PROTOCOL.md` §2 是主閥門）。你會有衝動想「加一條規則防止這種事再發生」——那個衝動本身，就是這封信要你警惕的東西。

### 2. 優先用原生功能，不要再自建平行機制

這個 harness 誕生時，Claude Code 還沒有現在這些原生能力。現在 `system/NATIVE_OVERLAP.yaml` 自估整體重疊 30%（Skill 路由 85%、權限 75%），而且只會越來越高。所以：想加任何新機制前，先查 Claude Code 原生（skills、hooks、settings permissions、subagents、記憶機制）是不是已經有了——**用原生的，harness 只保留原生給不了的**：Task Card 的 DoD 紀律、審計鏈、校準資料、判斷 rubric。aggregate 超過 50% 就觸發 v3 重構（既定決策，見 NATIVE_OVERLAP），到時候該刪的模組不要捨不得。

### 3. 量測數據幾乎是空的——別把儀式當數據

殘酷的現況：run log 的 token_estimate 全是 0，成本校準係數建立在 1–2 筆樣本上（writing 的 2.00 係數來自**一筆**任務）。這些表格看起來像資產，實際上還不能支撐任何決策。兩條路選一條：要嘛坐實量測（每次任務真的記 token，累到 n≥5 再用），要嘛承認不量並把校準機制刪掉。**最糟的是現狀：維護著量測的儀式，卻沒有量測的事實**——這會讓未來的你以為自己有數據而做出錯誤調參。在 n≥5 之前，把那些係數當故事看，不要當依據用。

## 這套制度最可能的退化方式（與預防）

| 退化 | 長什麼樣 | 預防 |
|------|---------|------|
| **規則膨脹** | 每個檔案越來越長；新 session 花一半 context 讀規則 | MAINTENANCE_PROTOCOL §3 精簡觸發（預警線 2,500 tokens、教訓 ≥10 條、單檔 >250 行）；教訓 ≠ 規則 |
| **檔案漂移** | 同一條規則的兩份副本各自被修改，開始互相矛盾 | 單一事實源：修規則時搜尋全 repo 有無副本；衝突處理見 MAINTENANCE_PROTOCOL §4 |
| **儀式化** | gate 逐條「pass」但沒有證據；驗收 agent 收到「我覺得做完了」的暗示；checkpoint commit 訊息與內容不符 | 驗收必附證據（檔案:行號、測試輸出）；驗收 agent 必須 fresh context 且拿不到執行過程（DELEGATION_TEMPLATES T5）；使用者可隨機抽查任一 pass 的證據 |

第三種最陰險：前兩種看得見（檔案變長、規則打架），儀式化的表面完全健康。判斷方法只有一個——順著任何一個「pass」去找它的證據，找不到就是已經儀式化了。

## 環境小抄（非制度，但省你摸索）

- 使用者用繁體中文；問問題要帶選項、一次一批，不要擠牙膏（JUDGMENT_RUBRICS R3）。
- 兩種執行環境的差異查 `system/DELEGATION_PLAYBOOK.md` §7，不要憑記憶。
- 這個 repo 有 CI（spec-consistency workflow）：動 YAML 前記得它會全檔 parse，動 CLAUDE.md 或 GLOBAL_RULES 前先跑 `ruby scripts/check_context_budget.rb`。
- 歷史脈絡想快速補課：`outputs/reports/harness-self-assessment-v1.md`（體檢）→ `outputs/reports/2026-07-03_harness-diagnosis.md`（本次制度的依據）。

## 交接區

2026-07-03 制度建設 session：A–G 全數落檔。收尾狀態見本段末行（若中斷，未勾的就是沒做完的）：
- [ ] fresh-context 對抗審查完成且發現已修正
- [ ] 全檔 read-back + 本地 CI 檢查全綠
後續待辦不在本信範圍：見 `system/MAINTENANCE_PROTOCOL.md` §6 收斂 backlog、`outputs/reports/harness-self-assessment-v1.md` 的 R 系列 roadmap。

祝穩定。

— Fable 5，2026-07-03
