# 歐盟 AI Act 2026 落地時程與對非歐盟中小企業/一人公司的合規衝擊（Standard）

- Task ID：20260620-X03
- 日期：2026-06-20
- Skill：research
- 投入：3 tool calls / 2 web searches / ~1,450 字
- 狀態：草稿（workflow 測試批次 X03・政策/法遵領域）

## 結論

歐盟 AI Act 的核心衝擊不在「歐盟境內」，而在它**比照 GDPR 的域外效力**：只要你的 AI 系統投放歐盟市場、在歐盟內被使用，或**其輸出被歐盟境內的人使用**，即使你在台灣、沒有歐盟實體、沒有歐盟伺服器，仍落入適用範圍。對一人公司而言有兩個好消息與一個壞消息：好消息是 (1) 2026 年 5 月 7 日的「Digital Omnibus」臨時協議把**高風險（Annex III）義務從 2026-08 延到 2027-12**，爭取了緩衝；(2) AI Act 對 SME/新創設有**比例原則與較低罰則上限**。壞消息是**透明度義務（Article 50）仍從 2026-12-02 生效**，而多數一人公司的 AI 應用（聊天機器人、生成內容）正落在這一塊——這才是 2026 年底最該優先處理的合規點，而非遙遠的高風險分類。

**對一人公司的務實優先序：先做透明度標示（低成本、近期生效）→ 確認自己不踩禁用實務 → 高風險義務按 2027-12 時程從容準備。**

## 已知事實

### 分階段適用時程（2025–2028 關鍵里程碑）

- **2025-02-02**：禁用實務（prohibited practices）與 AI 素養義務已生效 — 出自 SIG / Trilateral Research
- **2025-08-02**：通用型 AI（GPAI）義務開始適用 — 出自 Legiscope / Trilateral
- **2026-08-02（原定）**：高風險系統義務原訂生效；但依 **2026-05-07 Digital Omnibus 臨時協議，Annex III 高風險系統延後至 2027-12-02** — 出自 Legiscope / Tredence
- **2026-12-02**：Article 50 透明度義務適用（生成式/互動式 AI 的標示義務）— 出自 Tredence
- **2027-12-02**：Annex III 高風險系統義務（延後後的新生效日）— 出自多來源交叉
- **2028-08-02**：嵌入受規管產品（Annex I）的高風險 AI 義務 — 出自 SIG / Tredence

> 註：時程因 Digital Omnibus 簡化案而變動，落地日仍可能再調整，屬流動狀態。

### 域外效力與罰則

- AI Act 適用於**任何**將 AI 投放歐盟市場、在歐盟提供服務，或**其 AI 輸出被歐盟境內使用**的組織，與總部所在地無關（刻意比照 GDPR 域外效力）— 出自 Modulos / Annexa / Afriwise
- 罰則區間 €7.5M–€35M，或全球年營業額 1%–7%（最高 €35M 或 7%，高於 GDPR）— 出自 Tredence / Decodethefuture
- SME/新創享**比例原則**，部分情形罰則上限有調降 — 出自 Tredence / Quantamix

## 對「非歐盟中小企業/一人公司」最相關的 3 項風險點

1. **透明度義務（Article 50，2026-12-02 生效）最先咬到一人公司**
   生成式/互動式 AI 必須讓使用者知道在與 AI 互動、AI 生成內容須可標示。一人公司常見的 AI 客服、AI 文案、AI 生成圖文若服務觸及歐盟使用者，這是最近期、最實際的義務。

2. **域外效力＝「沒有歐盟實體也跑不掉」**
   只要產品在歐盟市場上架（如上架歐盟可購買的 SaaS / App / GPT store），或輸出被歐盟用戶使用，即屬適用對象。一人公司容易誤以為「我不在歐盟所以無關」，這是最大認知盲點。

3. **高風險分類的舉證與文件負擔（2027-12 起）**
   若 AI 用於 Annex III 場景（招聘、信用評分、教育評量、關鍵基礎設施等），需符合風險管理、資料治理、日誌、人為監督、符合性評估與註冊——對單人團隊是沉重的文件工程。延期到 2027-12 給了準備時間，但若業務踩到這類場景，需提早設計。

## 合理推論（一人公司如何務實因應）

- **以「我的 AI 輸出會不會被歐盟人看到/用到」為第一道篩選**：若答案為否，多數義務暫不適用，避免過度合規消耗。
- **2026 下半年優先投資在「透明度標示」**：成本最低（多為 UI 文案與揭露頁），但生效最早（2026-12），CP 值最高。
- **避開高風險 Annex III 場景，或外包給已合規的平台**：一人公司自建招聘/信用評分類 AI 的合規成本不成比例，能用合規供應商就不要自建。
- **善用 SME 比例原則**：保留輕量文件（用途說明、資料來源、人為複核紀錄）即可顯著降低風險，不需企業級 GRC 系統。
- 此題與本 harness 哲學呼應：**「先界定範圍、再決定義務」就是 Task Card 的 definition_of_done 思維**——先問「這件事到底適不適用」，再投入。

## 待驗證

- Digital Omnibus 是否最終定案、延後日期是否再變（2026-05-07 為「臨時協議」，尚非最終法律文本）[待驗證]
- SME 比例原則的**具體**條件與罰則調降幅度（來源僅泛稱「caps may apply」，未見明確數字）[待驗證]
- Article 50 透明度義務對「純 B2B、輸出不直接面向歐盟自然人」的一人公司是否適用 [待驗證]
- 台灣主管機關是否有對應指引或互認安排 [待驗證]

## 高風險假設

- **「延期＝可以拖到 2027 再說」**：透明度義務 2026-12 仍生效；把所有準備都推到 2027 會錯過近期義務。延期只適用高風險分類，不是全面緩刑。
- **「一人公司太小不會被查」**：罰則以全球營業額百分比計，雖有 SME 上限，但「規模小＝不被執法」是危險假設；GDPR 已有對小型業者開罰的先例，AI Act 執法強度尚待觀察但不應假設零風險。
- **「輸出不在歐盟就完全免責」**：域外效力的判定（特別是 SaaS/API 透過第三方觸及歐盟用戶）比直覺複雜，邊界案例可能仍落入範圍。

## 來源

- [EU AI Act Deadlines 2026-2027: Compliance Calendar + Fines (Legiscope)](https://www.legiscope.com/blog/eu-ai-act-timeline-deadlines.html)（時效：2026）
- [EU AI Act Compliance Timeline 2025-2027 by Risk Tier (Trilateral Research)](https://trilateralresearch.com/responsible-ai/eu-ai-act-implementation-timeline-mapping-your-models-to-the-new-risk-tiers)（時效：2026）
- [EU AI Act 2026 Compliance Guide for US/Non-EU Companies (Tredence)](https://www.tredence.com/blog/eu-ai-act-compliance-guide-us-companies)（時效：2026）
- [Does the EU AI Act Apply to US Companies? Extraterritorial Scope (Modulos)](https://www.modulos.ai/blog/eu-ai-act-us-companies/)（時效：2026）
- [Extraterritorial Application of the EU AI Act — Non-EU Companies (Afriwise)](https://www.afriwise.com/blog/extraterritorial-application-of-the-eu-ai-act-what-non-eu-companies-should-know)（時效：2026）

## 執行紀錄

- web search：2 次（timeline/GPAI/high-risk dates；extraterritorial + SME impact）
- 工具呼叫：3 次（2 web_search + Write）
- 預算狀態：tool_calls 3/5、web_searches 2/3（未用滿，2 輪已足夠交叉比對）
- 限制：法規處於 Digital Omnibus 變動中，延後日期與 SME 細則均標 [待驗證]；非法律意見，僅供範圍評估參考

---

**End of X03**
