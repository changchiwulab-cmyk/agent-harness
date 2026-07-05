# DELEGATION_TEMPLATES — 派工 prompt 模板

> 用法：複製對應模板，把 `【】` 填掉，作為 Agent tool 的 `prompt`。每份模板已含
> DISPATCH_POLICY §2 的三件套（目標動機/驗收條件/回報格式）。model 選擇依
> DISPATCH_POLICY §3；不確定就照模板預設值。subagent 看不到主對話——
> 填空時當作對方**什麼都不知道**，所有路徑、脈絡、術語都要寫全。

---

## T1 搜尋／定位

```
subagent_type: Explore ｜ model: 不指定（Explore 內建）｜ prompt 開頭註明搜索廣度：medium 或 very thorough
```

```text
【搜索廣度：medium / very thorough 二選一】
在【repo 路徑或目錄範圍】找出【要找的東西：定義/呼叫點/設定/慣例】。
背景：我在做【上游任務一句話】，需要這份清單來【結果的用途】。

驗收條件：
- 找到的每一項都給 檔案路徑:行號
- 說明你搜了哪些關鍵字/模式（讓我能判斷有沒有漏）
- 明確說「找完了」還是「可能有漏，因為【】」

回報格式：清單（路徑:行號＋一句說明），不要貼檔案原文。30 行以內。
```

## T2 實作

```
subagent_type: general-purpose ｜ model: "sonnet"（動核心架構改 "opus"）
```

```text
任務：在【repo 絕對路徑】實作【功能/修復，一句話】。
背景與動機：【為什麼做、上游 Task Card 的 goal、這段程式在系統裡的角色】。
先讀這些檔案理解慣例：【1–3 個代表性檔案路徑】。
限制：【不能動什麼／必須沿用什麼模式／PERMISSIONS deny 照常生效】。

驗收條件（做完自己先跑一遍）：
- 【具體行為：輸入 X 得到 Y】
- 測試綠：跑【測試指令，例：python3 scripts/test_xxx.py】並貼結果最後 3 行
- 不新增【lint/CI】錯誤：跑【檢查指令】

回報格式：改了哪些檔（路徑:行號範圍）＋每處一句為什麼＋測試輸出末 3 行。
不要貼完整 diff。若卡住超過 2 次嘗試：停下，回報你試了什麼、錯在哪、你的假設。
```

## T3 重構

```
subagent_type: general-purpose ｜ model: "sonnet"；跨模組介面重切 → "opus"
```

```text
任務：重構【目標範圍】，把【現況問題】改成【目標形狀】。
動機：【為什麼值得重構；誰會受益】。
不變式（重構後必須依然成立）：
- 【對外行為/介面 X 不變】
- 【測試全綠：指令】
先跑一次測試記錄基線，再動手；每完成一個安全步驟 git add（不 commit，由我 checkpoint）。

驗收條件：
- 測試基線與結束時輸出一致（貼兩者末 3 行對照）
- 【重複段落/耦合點】已消除：指出消除前後的位置（路徑:行號）
- 沒有為了過測試而改測試（若非改不可，單獨列出並說明）

回報格式：步驟清單（每步一句）＋檔案:行號對照表＋測試前後輸出。不貼原文。
```

## T4 研究

```
subagent_type: general-purpose ｜ model: "sonnet" ｜ 產出走 skills/research/SKILL.md 格式
```

```text
研究題目：【一句話問題】。
動機：【這答案會決定什麼】。
範圍與優先序：先查【內部：memory/、outputs/、指定檔案】，不足再 web search
（最多【2】輪，策略見 skills/research/SKILL.md）。
時間框架：資訊以【日期】後為準，舊資料標註年份。

驗收條件：
- 回答直接對題（不是綜述周邊）
- 每個事實主張附來源；推論標依據；沒查到的明說「沒查到」，不要編
- 產出按 research skill 格式分節：結論/已知事實/合理推論/待驗證/高風險假設/來源

回報格式：完整報告寫入【outputs/drafts/檔名.md】，回我：結論 3 行＋檔案路徑＋
最不確定的一點。
```

## T5 審查

```
subagent_type: verifier（DoD 驗收用）；一般品質審查 → general-purpose + model: "sonnet"
```

```text
審查對象：【產出檔案路徑】。
它宣稱完成的任務：【Task Card 路徑，或貼上 goal + definition_of_done】。
你沒有參與產出過程——這是刻意的，請以全新眼光審。

驗收條件（= 你的審查工作本身合格的標準）：
- definition_of_done 逐條標 pass / fail，每條附證據（引用 檔案:行號 或實跑輸出）
- 對 fail 條目：寫出「差距是什麼、補什麼才過」
- 跑 JUDGMENT_RUBRICS.md §5 可驗層 checklist（路徑存在性/數字重算/佔位符/格式慣例）
- 反向測試至少 1 個：找一個產出應答而未答的問題
- 若內容涉品味/策略（rubric 驗不了），明確標注「此部分僅驗至 rubric 層」

回報格式：逐條 pass/fail 表＋fail 差距說明＋反向測試結果。30 行以內。
不要客氣，fail 就是 fail；也不要沒根據地挑刺，每個 fail 都要有證據。
```

---

## 通用附註（每次派工前掃一眼）

- 派工後主對話**不要**同時自己做同一件事（浪費且會互踩檔案）。
- 同時派多個互不依賴的 subagent 是允許且鼓勵的（訂閱制，換時間）。
- subagent 失敗的處理走 DISPATCH_POLICY §5（升降級），重派前先補齊它缺的脈絡。
- 高風險判斷的第二意見/多答案評審寫法：把同一份 T4/T5 prompt 派給兩個獨立 agent
  （其中一個 model: "opus"），比對結論；分歧點就是需要人工裁決的點。
