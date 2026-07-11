# AI 產業落地物理 AI（Physical AI）進度表（全球趨勢 + 台灣切入點）

- Task ID：20260531-001
- 日期：2026-05-31
- Skill：research
- 投入：web_search 5 次（4 成功 / 1 觸 rate limit）、~4600 字
- 狀態：草稿（執行中，僅供人工審閱，未晉升 reports/）
- 範圍：全球為主軸 + 台灣切入點；形式：時間軸(2023→2030) × 子領域矩陣

> **成熟度標記說明（沿用 skills/research/SKILL.md 語彙）**
> ✅ 已達成/商轉里程碑　🔍 研發或試點中（演進）　❌ 停滯或資料不足　（推）= 合理推論之未來預測，不確定性高

---

## 結論

物理 AI（Physical AI＝把 AI 從螢幕推進到能感知、推理並在真實世界行動的系統）在 2023→2026 走出一條清晰主曲線：**「模型先突破、硬體後追趕」**。2025 是公認的轉折年——具身基礎模型（VLA）與世界模型同時出現產品級里程碑，餵養了人形機器人與自駕的訓練資料引擎。當前五個子領域成熟度極不均衡：**自駕（robotaxi）是唯一已達規模化商業營收的子領域**（Waymo 每週 50 萬次付費載客）；**具身基礎模型與世界模型完成「技術元年」**（π0、GR00T N1、Cosmos、Genie 3）；**人形機器人剛跨入量產起步**（Tesla Optimus 2026-01 宣布量產，但 Musk 時程歷史性高估）；**工業協作機器人**則是成熟產業正被 VLA 重新定義。瓶頸正從「軟體/模型」轉向「硬體量產、成本與可靠度」。

對台灣與一人公司而言，最高確定性的槓桿是**「Physical AI 的算力地基」**（半導體 + AI 伺服器，台灣已壟斷），次級機會是**機器人本體零組件**（諧波減速機 / 伺服 / 感測，台灣有 Hiwin、Techman 等切入點）與**製造業 AI 落地陪跑**；模型層與人形整機則非一人公司可競爭。

---

## 已知事實

### A. 五個子領域定義（矩陣橫軸）

| # | 子領域 | 定義 | 代表玩家 |
|---|--------|------|----------|
| 1 | 人形機器人 (Humanoid) | 雙足/類人形態的通用機器人本體 | Tesla Optimus、Figure、Unitree、1X |
| 2 | 自駕 (Autonomous Driving) | L4 robotaxi 與自駕載客/載物 | Waymo、Tesla、Baidu Apollo Go |
| 3 | 工業協作機器人 (Cobot/工業) | 與人協作的工業機械臂與自動化 | Universal Robots、FANUC、ABB、Techman |
| 4 | 具身基礎模型 (Embodied FM / VLA) | 視覺-語言-動作模型，機器人的「大腦」 | Physical Intelligence、NVIDIA、Google DeepMind |
| 5 | 世界模型 (World Models) | 可生成/模擬物理世界、產合成訓練資料 | NVIDIA Cosmos、DeepMind Genie、World Labs |

### B. 時間軸 × 子領域矩陣（核心交付物）

| 時間 \ 子領域 | 人形機器人 | 自駕 | 工業協作機器人 | 具身基礎模型 (VLA) | 世界模型 |
|---|---|---|---|---|---|
| **2023** | 🔍 Optimus Gen1、Figure 起步（原型階段） | 🔍 Waymo/Cruise 舊金山有限商轉；Cruise 事故後收縮 | ✅ 成熟產業，傳統視覺/示教編程 | 🔍 Google RT-2 開啟 VLA 概念 | ❌ 多為學術概念，無產品 |
| **2024** | 🔍 Figure 01→02、Optimus Gen2 展示；新創大額融資 | 🔍 Waymo 擴 LA/Phoenix（~5萬次/週起步）；Apollo Go 中國擴張 | ✅ 市場穩定成長，VLA 試水 | 🔍 Physical Intelligence 成立、π0 發表；OpenVLA 開源 | 🔍 影片生成（Sora 級）激發世界模型想像 |
| **2025** | 🔍 Unitree 出貨 5,500+ 台；GR00T N1 開源；各廠進入試產 | ✅ Waymo 達 50萬次/週、10 城；Apollo Go 25萬單/週全無人；Tesla Austin robotaxi 啟動 | 🔍 VLA 開始改變機器人編程（具身 AI 進工業） | ✅ **具身基礎模型元年**：π0/π0.5、GR00T N1、Gemini Robotics | ✅ **World Model Inflection**：NVIDIA Cosmos 系列、DeepMind Genie 3（24fps 即時互動數分鐘） |
| **2026** | 🔍→🟡 **Optimus Gen3 宣布量產（1/21），目標 10–30萬台、$20–30K**；Figure 03 工廠部署；外售 late 2026 [部分待驗證] | ✅ Waymo 目標 100萬次/週、擴 20+ 城（含東京/倫敦）；Tesla 擴 Dallas/Houston | 🔍 VLA 賦能的次世代 cobot；具身 AI 重寫編程範式 | 🔍 規模化 + 明確「規劃層」（goal token/空間錨點） | ✅（推）合成資料 pipeline 成熟，餵養人形/自駕訓練 |
| **2027–2028** | 🔍（推）商業量產爬坡，工廠/物流先行；成本下降 | ✅（推）L4 robotaxi 多城常態化、加速國際擴張 | 🔍（推）通用化 cobot 滲透中小製造 | 🔍（推）跨形態泛化驗證中 | ✅（推）成為 Physical AI 訓練核心基礎設施 |
| **2029–2030** | 🔍（推）成本/可靠度若突破→規模商用，否則仍限工業場景 [高風險假設] | 🔍（推）L4 在主要市場普及，L5 仍遠 | 🔍（推）人形與 cobot 界線漸模糊 | 🔍（推）邁向「機器人的 GPT 時刻」？[高風險假設] | 🔍（推）通用世界模擬器 |

### C. 各子領域全球層級事實（每領域 ≥3 量化/時序主張）

**1. 人形機器人**
- Tesla 於 **2026-01-21 宣布在 Fremont 量產 Optimus Gen 3**，2026 目標 **10–30 萬台**、單價 **$20,000–30,000**；外售預計 2026 末/2027 初，先供製造與物流客戶。[來源：多為產業部落格，待一手確認]
- Musk 時程歷史性高估：2025 年初宣稱「2025 數千台、年中月產 1 萬」，實際僅數百台，**落差 >90%**。
- **Unitree 2025 出貨 5,500+ 台**，2026 目標 1–2 萬台，為當前出貨量最大玩家之一。
- Figure 03 展示連續無監督運作與全身自主，已於 **BMW Spartanburg 試點**，2026 路線圖含工廠部署。

**2. 自駕（robotaxi）**
- **Waymo 每週 50 萬次付費載客、橫跨 10 個美國城市**（較 2024-05 的 5 萬次/週成長 10 倍），2026 目標 **100 萬次/週**，並規劃擴張 20+ 城（含東京、倫敦）。
- **Baidu Apollo Go 每週 >25 萬單、22 城、自 2025-02 起 100% 全無人**，擴張至香港、杜拜、阿布達比、瑞士；與 Lyft 合作 2026 進軍德國/英國。
- **Tesla robotaxi 2026-01 於 Austin 商轉**，後擴 Dallas/Houston；Austin+灣區累計近 70 萬次付費載客（至 2025 Q4），但尚缺加州許可。

**3. 工業協作機器人（cobot）**
- 成熟產業，全球工業機器人「四大家」FANUC、ABB、KUKA、Yaskawa + cobot 龍頭 Universal Robots（Teradyne）。[產業常識]
- 2025 起 VLA 模型開始改變機器人編程方式（從逐點示教轉向自然語言/示範學習）。[來源：產業分析]
- 全球協作機器人市場估以雙位數 CAGR 成長、中國機器人密度快速攀升（IFR）。[待驗證：2025–2026 具體市場規模與成長率，本次第 5 次 web search 觸 rate limit 未取得]

**4. 具身基礎模型（VLA）**
- **Physical Intelligence π0（3B 參數）** 採 flow-matching 動作頭，產生平滑軌跡、能處理摺衣/多步組裝；π0.5 採不同架構。
- **NVIDIA GR00T N1（2B 參數）** 於 **GTC 2025** 發表並**公開權重**，以 Omniverse + Cosmos 合成資料 + 真實人形遙操作資料訓練，為首批可外部微調的人形基礎模型。
- **Google DeepMind Gemini Robotics** 已對信任測試者開放，並釋出較小的 on-device VLA；強調以前沿基礎模型適配新機器人本體、所需額外資料少。
- 共同趨勢：從「像素直接到扭矩」轉向**顯式規劃層**（中層 goal token、空間錨點、軌跡提示）。

**5. 世界模型**
- **NVIDIA Cosmos**：世界基礎模型平台。Cosmos-Predict2.5 以 flow-based 架構統一 Text2World/Image2World/Video2World，訓練於 **2 億條影片片段**；**Cosmos Reason（7B 推理 VLM）** 讓機器人以物理常識推理；新增 **Cosmos Policy** 生成機器人動作。CES 2025 launch、2025-08 重大更新。
- **DeepMind Genie 3**：可由提示生成世界並**即時 24fps 導覽、720p 維持數分鐘一致性**，把「可互動」從數秒推進到數分鐘。
- 2025 被稱為「World Model Inflection」，產業分為兩陣營：通用可提示世界模擬器（創意/遊戲）vs 動作條件化模型（機器人/控制）。

---

## 合理推論

- **依賴鏈成形**：世界模型（產合成資料）→ 具身基礎模型（學會泛化策略）→ 人形/cobot（取得通用大腦）。NVIDIA 同時握有 Cosmos（世界模型）+ GR00T（具身模型）+ GPU（算力），是這條鏈上結構性最有利的玩家（依據：上述三者皆出自 NVIDIA 生態）。
- **瓶頸轉移**：模型側 2025 已突破，2026→2028 的關鍵變數轉為**硬體量產、成本、電池/驅動器可靠度**——這對台灣製造供應鏈是機會（依據：Optimus 量產目標與 Musk 時程落差並存）。
- **自駕是先行指標**：robotaxi 是唯一以「每週數十萬次付費」驗證 Physical AI 商業模式的子領域；其法規與安全節奏會被其他子領域借鑑（依據：Waymo/Apollo Go 規模化數據）。
- **台灣定位**：算力地基（半導體）確定性最高且已壟斷；機器人本體零組件是「可爭取但非壟斷」的次級機會（依據：T03 半導體事實 + 機器人 BOM 結構）。

---

## 待驗證

- Tesla Optimus 2026 **實際**量產與出貨數字（Musk 時程一向樂觀，2025 已 miss >90%；量產宣布多源自產業部落格，需一手財報/法說確認）。
- 人形機器人**真實商業訂單** vs 展示影片的比例（Figure/1X/Unitree 的付費部署規模）。
- 台灣機器人供應鏈具體數字：Hiwin（上銀）諧波/應變波減速機市占與營收、Techman（達明）cobot 全球排名、Delta（台達電）伺服在人形 BOM 的份額——**本次第 5 次 web search 因 session rate limit 未取得，留待補搜**。
- 全球協作機器人 2025–2026 市場規模與成長率（IFR/各市調機構最新數據）。
- 具身基礎模型**跨形態泛化**的真實程度（論文展示 vs 產線可靠度）。
- 世界模型合成資料的 **sim-to-real 遷移效率**（能否實質降低真機資料需求）。

---

## 高風險假設（敏感性分析）

| # | 核心假設 | 若假設失效，進度表如何位移 |
|---|----------|---------------------------|
| H1 | 人形機器人量產時程如宣稱推進（成本/電池/驅動器/可靠度達標） | 若 Musk 式樂觀再度 miss → 人形子領域 2027–2030 預測整體**右移 2–3 年**，資本可能轉冷；台灣減速機/伺服機會延後 |
| H2 | 具身基礎模型可跨形態泛化（一個大腦適配多種本體） | 若不成立 → 每款機器人仍需大量專屬資料，**規模化經濟性崩解**，VLA 退回「每形態一模型」，整體進度放緩 |
| H3 | 地緣與供應鏈穩定（先進製程、出口管制、台海） | 若惡化 → **Physical AI 算力地基動搖**；台灣機會與全球進度**同時**受衝擊，這是唯一會橫掃五子領域的系統性風險 |
| H4 | 自駕 L4 法規維持當前開放節奏 | 若重大事故觸發監理收緊 → robotaxi 擴張放緩，先行指標效應反轉，拖累整體投資情緒 |
| H5 | 世界模型 sim-to-real 落差可被工程克服 | 若合成資料無法有效遷移真實 → 訓練成本/時程惡化，依賴鏈上游失靈，人形/cobot 訓練紅利縮水 |

---

## 台灣切入點（全球矩陣之下的在地對照）

> 全球進度由上方矩陣界定；以下是台灣三條可操作的切入軸，含機會與卡點。半導體/AI 伺服器事實基礎引用 outputs/drafts/20260502-T03（2026-05 已查證）。

### 1. 半導體（AI 晶片 / 先進封裝）——確定性最高
- **機會**：Physical AI 的「大腦」（GR00T、Cosmos、自駕模型）全跑在 NVIDIA GPU 上，而 TSMC 先進製程（<7nm）全球份額 ~92%、CoWoS 先進封裝 2026–2027 過半被 Nvidia 鎖死。**台灣是全球 Physical AI 的算力地基**，需求隨人形/自駕擴張水漲船高。
- **卡點**：產能被超大買家鎖死、議價空間有限；地緣政治（H3）；對一人顧問而言，晶片業屬高門檻、非可切入層。

### 2. 機器人供應鏈（減速機 / 伺服 / 感測）——次級可爭取機會
- **機會**：人形機器人 BOM 中**精密減速機、伺服馬達、力/扭矩感測器**是高價值零組件。台灣有 **Hiwin（上銀，諧波減速機 + 線性傳動）**、**Delta（台達電，伺服驅動/自動化）**、**Techman（達明，廣達子公司，協作機器人）** 等切入點；Foxconn 亦投入人形機器人（供自家工廠）。[多為訓練知識/產業常識，具體市占與營收待驗證]
- **卡點**：精密諧波減速機長期由日本 Harmonic Drive Systems 主導、中國低價競爭；良率與精度門檻高；台灣強在「量產與成本」、弱在「最高精度核心件」。

### 3. 製造業（協作機器人 / 邊緣 AI 導入）——顧問最可落地
- **機會**：台灣製造業（電子、金屬、機械）是 cobot 與邊緣 AI 的天然試驗場；研華（Advantech）為全球 IPC 龍頭，ODM（鴻海/廣達/緯創）建置 AI 工廠。VLA 讓「自然語言教機器人」成為可能，**降低中小製造導入門檻**——這是管理顧問「AI 落地陪跑」的直接戰場。
- **卡點**：本地軟體層薄弱、整合人才稀缺；中小企業 capex 保守、需求教育成本高（呼應 T03 觀察）。

---

## 來源

> 子領域 1、2、4、5（人形/自駕/具身模型/世界模型）為本次 web search 取得；子領域 3（工業 cobot）與台灣機器人供應鏈具體數字因第 5 次 search 觸 rate limit，部分以訓練知識陳述並標 [待驗證]。

**人形機器人**
- [Tesla Unveils Ambitious Optimus Humanoid Roadmap (Humanoid Robotics Technology)](https://humanoidroboticstechnology.com/industry-news/tesla-unveils-ambitious-optimus-humanoid-roadmap/)
- [Tesla Optimus Production Timeline 2026 (optimusk.blog)](https://optimusk.blog/blog/tesla-optimus-production-timeline/)
- [Humanoid Robots News (humanoid.press)](https://humanoid.press/)

**自駕**
- [Waymo's skyrocketing ridership in one chart (TechCrunch, 2026-03-27)](https://techcrunch.com/2026/03/27/waymo-skyrocketing-ridership-in-one-chart/)
- [Waymo 2025 Year in Review (Waymo blog)](https://waymo.com/blog/2025/12/2025-year-in-review/)
- [China Baidu robotaxis hit 250,000 weekly — same as Waymo this spring (CNBC, 2025-11-03)](https://www.cnbc.com/2025/11/03/china-baidu-robotaxis-alphabet-waymo-.html)
- [Apollo Go completes 2.2M driverless rides in Q2 2025, up 148% YoY (Gasgoo)](https://autonews.gasgoo.com/icv/70038700.html)
- [Tesla expands unsupervised Robotaxi area in Austin (Electrek, 2026-03-31)](https://electrek.co/2026/03/31/tesla-expands-unsupervised-robotaxi-service-area-still-only-handful-vehicles/)

**具身基礎模型（VLA）**
- [Vision-Language-Action Models and the Search for a Generalist Robot Policy (it can think, substack)](https://itcanthink.substack.com/p/vision-language-action-models-and)
- [Embodied AI: breakthroughs shaping the next 12 months (Air Street Press)](https://press.airstreet.com/p/embodied-ai-breakthroughs-2025)
- [awesome-physical-ai (GitHub, keon)](https://github.com/keon/awesome-physical-ai)
- [Embodied AI in Industrial Robotics: How VLA Models Are Changing Robot Programming (EVS)](https://www.evsint.com/embodied-ai-industrial-robotics-vla-models/)

**世界模型**
- [NVIDIA Cosmos: World Foundation Models Powering Physical AI (NVIDIA)](https://www.nvidia.com/en-us/ai/cosmos/)
- [Nvidia unveils new Cosmos world models for robotics and physical uses (TechCrunch, 2025-08-11)](https://techcrunch.com/2025/08/11/nvidia-unveils-new-cosmos-world-models-other-infra-for-physical-applications-of-ai/)
- [NVIDIA Releases New Physical AI Models as Global Partners Unveil Next-Gen Robots (NVIDIA Newsroom)](https://nvidianews.nvidia.com/news/nvidia-releases-new-physical-ai-models-as-global-partners-unveil-next-generation-robots)
- [The World Model Inflection: 2025 Made It Real (Medium)](https://medium.com/@graison/the-world-model-inflection-2025-made-it-real-f5a9c31475d4)

**台灣切入點（半導體/AI 伺服器/IPC 事實基礎）**
- 內部來源：`outputs/drafts/20260502-T03_taiwan-ai-industry-deep-dive.md`（2026-05-02，含 TSMC/CoWoS、鴻海/廣達/緯創 AI 伺服器、研華 IPC 之查證來源）
- 台灣機器人零組件（Hiwin/Delta/Techman/Foxconn 人形）：訓練知識/產業常識，**具體市占與營收 [待驗證]**

---

## 執行紀錄（壓測相關）

- web_search：5 次（人形 / 具身模型 / 世界模型 / 自駕 成功；第 5 次「台灣機器人供應鏈」觸 session rate limit，resets 1:40am UTC）
- rate-limit 處置：1 次失敗 < 3 次門檻 → 依 `logs/errors/2026-04-04` 前例不硬停，改用 T03 + 訓練知識並標 [待驗證]（SEC-03 降級路徑）
- 工具呼叫（執行期）：web_search ×5、write_drafts ×1、file_read（context 載入）數次、git checkpoint ×3
- 預算狀態：web_searches 5/5（達上限）、tool_calls 約 10/12
- 四態分離：已知事實 / 合理推論 / 待驗證 / 高風險假設 已明確分節
- cost-quality 觀察：留待 RUN log 與下次 retro

---

**End of 20260531-001**

---

> 📌 已晉升為 `outputs/reports/physical-ai-rollout-roadmap-v1.md`（晉升任務 Task Card 20260531-002，2026-05-31，人工核准）。本草稿保留作歷史備援。
