# 一人公司工具盤點（台灣＋越南雙市場）

**草稿 2026-04-22** · Task Card 20260404-R01 · skill: research

## 結論

一人公司工具組合以「**AI 核心 + 輕量 SaaS 外圍 + 會計委外**」為軸。Claude 生態系（Claude Code / API / Projects）是已確認的核心決策槓桿；外圍工具傾向選「月費 < USD 30 / 無年約 / 有繁中介面」者優先。跨台越運作的特殊需求（雙幣、雙語、雙時區客戶）使得**帳務與通訊類**最可能需要並行兩套工具；其他類別可單套覆蓋。

---

## 已知事實

- 使用者深度整合 Claude 生態系（來源：`memory/active_projects/agent-harness/context.md`）
- 使用者為 20+ 年跨產業管理顧問、台灣＋越南雙市場運作（來源：同上）
- 使用者全域偏好儲存在 `~/.claude/memory/`，本 repo `memory/user_prefs.md` 僅做指引（來源：`memory/user_prefs.md` L3）
- agent-harness v2 以 Claude Code CLI 為 Interface，Task Card 為執行入口（來源：`CLAUDE.md`、`README.md` L13–34）
- 架構禁用項：multi-agent swarm、自動外發、自動 shell 執行（來源：`README.md` L139–151）

## 合理推論

- 使用者已採用 GitHub（由本 repo 為 git + GitHub workflow + MCP github server 推論）
- 使用者會接觸 MCP ecosystem（CLAUDE.md 提到 MCP 串接限制，代表有在觀望）
- 台越雙市場情境下，USD/TWD/VND 三幣記帳與越文發票可能是痛點
- 一人公司規模通常 < 3 位關係人同步，故**不需要**多席次協作平台（Notion 單人足矣）

## 待驗證

- [ ] 使用者是否已採用 Notion / Obsidian 作知識管理？
- [ ] 現有會計系統（台灣 vs 越南兩套？）
- [ ] 客戶溝通主渠道（Email / LINE / Zalo / Google Meet）？
- [ ] 行銷產出目前是否有使用 Canva / Figma？
- [ ] 稅務：越南營業據點或是台灣發票為主？

## 高風險假設

- 假設使用者可接受 SaaS 資料存外部雲端（若有嚴格資料主權要求則需自架）
- 假設雙市場收入以 USD 計費結算（若以當地幣別則匯損/匯兌策略不同）
- 假設越南端無實體辦公室（若有則增 HRM / 考勤工具需求）

---

## 六大類別盤點

採用狀態沿用 `skills/research/SKILL.md` 定義：✅ 已用 / ✅ 推論已用 / 🔍 待評估 / ❌ 不適用

### 1. AI 工具

| 工具 | 主要功能 | 採用狀態 | 月費估算（USD） | 適合一人公司？ |
|------|---------|---------|----------------|----------------|
| Claude Pro / Max | 對話式 AI 主工具 | ✅ 已用 | 20–100 | ✅ 核心必備 |
| Claude Code CLI | Terminal/IDE 程式與任務執行 | ✅ 已用 | 併在 Pro/Max | ✅ 核心必備 |
| Claude API | 自動化流程、Agent Harness 本身 | ✅ 已用 | 依用量 | ✅ 流量小成本可控 |
| Anthropic Projects | 跨對話知識捆包 | ✅ 推論已用 | 併在 Pro/Max | ✅ 輕量知識庫 |
| ChatGPT Plus / Gemini Advanced | 交叉驗證、特定任務備援 | 🔍 待評估 | 20 / 20 | ⚠️ 僅在 Claude 明顯弱項補位 |
| Perplexity Pro | 即時聯網研究 | 🔍 待評估 | 20 | ⚠️ 可被 Claude + web_search 替代 |
| Whisper / ElevenLabs | 語音轉文字／合成 | 🔍 待評估 | 5–30 | 按需用 API 即可，不需訂閱 |

### 2. 專案／任務管理

| 工具 | 主要功能 | 採用狀態 | 月費估算（USD） | 適合一人公司？ |
|------|---------|---------|----------------|----------------|
| agent-harness（本 repo） | Task Card 驅動的執行框架 | ✅ 已用 | 0 | ✅ 核心 |
| GitHub（含 Issues / Projects） | 版控＋任務追蹤 | ✅ 已用 | 0 (free) | ✅ 足夠 |
| Notion | 知識庫＋輕專案 | 🔍 待評估 | 10 | ✅ 適合（取代 Confluence + Trello） |
| Linear | 工程型 ticket | ❌ 不適用 | 8–14 | ❌ 一人公司過度 |
| Trello / Asana | 看板 | ❌ 不適用 | 5–13 | ❌ GitHub Projects 可替代 |

### 3. 通訊／客戶溝通

| 工具 | 主要功能 | 採用狀態 | 月費估算（USD） | 適合一人公司？ |
|------|---------|---------|----------------|----------------|
| Gmail + Google Workspace | Email + 行事曆 + Meet | ✅ 推論已用 | 7–14 | ✅ 業界標配 |
| LINE（台灣） | 本地客戶即時溝通 | ✅ 推論已用 | 0 | ✅ 台灣必備 |
| Zalo（越南） | 越南本地即時溝通 | ✅ 推論已用 | 0 | ✅ 越南必備 |
| Zoom / Google Meet | 視訊會議 | ✅ 推論已用 | 0 / 15 | ✅ Meet 搭配 Workspace 即可 |
| Calendly / Cal.com | 時程預約 | 🔍 待評估 | 0–15 | ✅ 跨時區很實用 |
| WhatsApp Business | 東南亞客戶延伸 | 🔍 待評估 | 0 | 依越南客戶偏好而定 |

### 4. 財務／行政

| 工具 | 主要功能 | 採用狀態 | 月費估算（USD） | 適合一人公司？ |
|------|---------|---------|----------------|----------------|
| 台灣記帳士／會計師 | 台灣報稅與發票 | ✅ 推論已用 | 委外月費 USD 100–300 | ✅ 強烈建議委外 |
| 越南當地會計事務所 | 越南報稅與發票 | 🔍 待驗證是否有實體 | 委外月費 USD 150–400 | ✅ 若有當地營收則必備 |
| Wise（前 TransferWise） | 多幣別收款 / 匯款 | 🔍 待評估 | 0 + 匯差 | ✅ USD/TWD/VND 效率佳 |
| Stripe / Paddle | 客戶信用卡收款 | 🔍 待評估 | 2.9% + USD 0.30 | ✅ 顧問費自動扣款用 |
| QuickBooks / Xero | 自動記帳 | 🔍 待評估 | 15–40 | ⚠️ 若委外會計可省 |
| Google Sheets + 模板 | 輕量記帳 | ✅ 推論已用 | 0 | ✅ 對一人公司足夠 |

### 5. 行銷／內容產出

| 工具 | 主要功能 | 採用狀態 | 月費估算（USD） | 適合一人公司？ |
|------|---------|---------|----------------|----------------|
| Canva Pro | 簡報／社群視覺 | 🔍 待評估 | 13 | ✅ 非設計師的最快解 |
| Figma（Starter） | UI 設計或進階視覺 | 🔍 待評估 | 0–15 | ⚠️ 若不做產品 UI 可省 |
| Buffer / Hootsuite | 社群排程 | ❌ 不適用 | 6–15 | ❌ 顧問業務社群需求低 |
| LinkedIn Premium | 顧問業開發管道 | 🔍 待評估 | 30 | ✅ 高 ROI（跨台越 B2B） |
| Substack / Beehiiv | 電子報 | 🔍 待評估 | 0 (免費開始) | ✅ 顧問知識變現管道 |
| Medium / 個人 blog | 內容佈局 | 🔍 待評估 | 5 (Medium) | ⚠️ 擇一即可 |

### 6. 知識管理／第二腦

| 工具 | 主要功能 | 採用狀態 | 月費估算（USD） | 適合一人公司？ |
|------|---------|---------|----------------|----------------|
| Obsidian | Markdown 本地筆記 | 🔍 待評估 | 0 (Sync 10) | ✅ 深度使用者首選 |
| Notion | 結構化筆記＋輕 DB | 🔍 待評估 | 10 | ✅ 與第 2 類合併算 |
| Google Drive | 檔案存儲 | ✅ 推論已用 | 併 Workspace | ✅ 不可少 |
| iCloud / Dropbox | 裝置同步備援 | 🔍 待評估 | 3–10 | ⚠️ 二擇一 |
| Readwise | 閱讀筆記彙整 | 🔍 待評估 | 8 | ✅ 顧問業知識輸入必備 |
| agent-harness `memory/` | 專案 context 固化 | ✅ 已用 | 0 | ✅ 核心 |

---

## 建議配置（一人公司 × 台越雙市場，初期預算 < USD 150/月）

| 角色 | 建議工具 | 月費（USD） |
|------|---------|-------------|
| AI 核心 | Claude Pro/Max + Claude Code + API | 20–100 |
| 任務執行 | agent-harness + GitHub | 0 |
| 知識庫 | Notion or Obsidian（擇一） | 0–10 |
| 通訊 | Gmail + LINE + Zalo + Google Meet | 7–14 |
| 預約 | Cal.com（免費版） | 0 |
| 收款 | Wise + Stripe | 依用量 |
| 會計 | 台越各一家委外會計 | 250–700 |
| 行銷 | LinkedIn Premium + Substack | 30 |
| **合計（不含會計）** | | **USD 57–154 / 月** |

## 需要使用者確認的決策點

1. Notion vs Obsidian：是否已固定偏好？
2. 是否已採用 Wise？若否，可優先評估（跨幣別 ROI 最高）
3. 會計：台越是否已雙軌委外？
4. LinkedIn Premium 是否已訂？顧問業此投資 ROI 通常 > 3x

---

## 來源

- `memory/active_projects/agent-harness/context.md`（使用者背景與 AI 生態採用）
- `memory/user_prefs.md`（記憶架構）
- `CLAUDE.md`、`README.md`（agent-harness 架構與限制）
- `skills/research/SKILL.md`（採用狀態定義與輸出格式）
- 月費範圍為 2026 Q1 常見公開定價之個人觀察，實際以官方為準（標記為合理推論）

## DoD 自查

- [x] 六類別齊全：AI / 專案管理 / 通訊 / 財務 / 行銷 / 知識管理
- [x] 每工具：名稱＋功能＋採用狀態＋月費估算
- [x] 「適合一人公司？」欄位齊全
- [x] 事實／推論／待驗證／高風險假設分開標記
- [x] 符合 research skill 輸出結構
