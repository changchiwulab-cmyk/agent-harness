# Knowledge Base 主工具選型 — Notion vs Obsidian vs Logseq

**Task ID**: 20260426-A01
**Date**: 2026-04-26
**Skill**: analysis（首次實戰，校準首筆）
**Decision Owner**: 一人公司管理顧問

---

## 結論與建議

**建議：Obsidian + Sync（$5/月）為主工具**，Notion 作為對外分享專用副工具，Logseq 暫不採用。

**核心理由**：
1. agent-harness 已採 YAML/MD 為持久層（D001），Obsidian 的 markdown-native 與既有檔案結構零摩擦
2. 客戶機密資料的敏感性 → local-first 是硬要求；Notion 的 cloud lock-in 與此不符
3. Obsidian 成熟度與 plugin 生態最佳，Logseq Beta 同步在客戶資料情境下風險過高
4. 對外分享需求（提案、報告）量小但偶發，用 Notion 免費版分享單頁即可，無需付費 plan

---

## 選項比較

### 選項 A：Notion

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中 | 一站式工作區（筆記+資料庫+專案）；分享連結最便利 |
| 成本 | 高 | $10/月 起；長期 $120/年；不含 AI 仍受限 |
| 風險 | 高 | 雲端鎖定，客戶機密上傳第三方雲；資料可攜性差（block 結構非標準 markdown） |
| 可行性 | 高 | 學習曲線低；模板生態成熟 |
| 執行難度 | 低 | 開箱即用 |
| 預期回報 | 中 | 對外協作與分享有明顯價值；個人 KB 用途過重 |
| 一人公司適配度 | 低 | 客戶機密 + cloud lock-in 互斥；月費對單人偏貴 |

### 選項 B：Obsidian + Sync（建議）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高 | Markdown-native；本地檔案；圖譜視圖；plugin 生態 1500+ |
| 成本 | 低 | App 本體免費；Sync $5/月（$60/年）；自架 git/iCloud 可省這筆 |
| 風險 | 低 | 本地優先；資料隨時可帶走；同步衝突在偶發場景下可接受 |
| 可行性 | 高 | 與 agent-harness 既有 markdown 結構零摩擦；可直接掛載 outputs/ |
| 執行難度 | 中 | 初次設定 plugin 與 vault 結構約 1-2 小時 |
| 預期回報 | 高 | 既有檔案立即可用；長期累積知識資產 |
| 一人公司適配度 | 高 | 客戶機密保留本地；成本可控；可選擇是否付費 sync |

### 選項 C：Logseq

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中 | 免費開源；outliner + journals 對日記型輸入友好；block-level reference |
| 成本 | 最低 | 完全免費；Sync $5/月（Beta） |
| 風險 | 中 | Sync 仍 Beta，客戶資料情境下風險偏高；行動端體驗較弱 |
| 可行性 | 中 | 學習曲線需適應 outliner 思維；既有 markdown 檔案需轉換才能完整支援 |
| 執行難度 | 中 | vault 結構與 Obsidian 不同；plugin 生態較小 |
| 預期回報 | 中 | 開源 + 免費的長期保險，但目前成熟度不足以作為主工具 |
| 一人公司適配度 | 中 | 哲學最契合（free + local + open source），但 Beta 同步不可靠 |

### 選項 D：不做（維持現狀，靠 agent-harness outputs/ + memory/ + git）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 低 | 結構化檢索能力不足；筆記無法快速跳轉 |
| 成本 | 0 | 無新增 |
| 風險 | 中 | 知識資產累積後檢索效率低，長期阻礙決策速度 |
| 可行性 | 高 | 已在用 |
| 執行難度 | 0 | 不變 |
| 預期回報 | 低 | 短期可行，長期是技術債 |
| 一人公司適配度 | 中 | 規模小時可，> 6 個月後檢索成本顯現 |

---

## 三個關鍵取捨情境

### 情境 1：跨裝置同步（筆電 + 手機）
- **Notion**：天然支援，無額外成本
- **Obsidian**：需 $5/月 Sync 或自架（git / iCloud / Syncthing 皆可）
- **Logseq**：Sync Beta，穩定性風險

> **取捨**：偶爾在手機看筆記、不在手機編輯 → Obsidian + iCloud 已足。重度跨裝置編輯 → Obsidian Sync 或 Notion。

### 情境 2：客戶資料敏感性 / 本地優先
- **Notion**：所有資料上傳第三方雲，與客戶 NDA 條款可能衝突
- **Obsidian**：本地優先，Sync 為選配（即使用也是 end-to-end 加密）
- **Logseq**：本地優先，Sync 為選配

> **取捨**：客戶資料敏感是一人公司顧問的硬約束 → 強烈傾向 Obsidian / Logseq。
> 若有極敏感資料（金融、醫療客戶），即使 Obsidian Sync 也建議停用。

### 情境 3：對外分享（提案、報告、客戶協作）
- **Notion**：分享連結最便利，免費版即可分享單頁
- **Obsidian**：Publish $10/月 才能對外分享；或 export 為 PDF/HTML
- **Logseq**：對外分享能力最弱

> **取捨**：頻繁對外分享 → Notion 免費版作為「對外」副工具，主 KB 仍 Obsidian。
> 對外分享 < 月 2 次 → 直接 export PDF 即可，免付費。

---

## 高風險假設

- **客戶資料敏感性的真實程度**：本分析假設客戶資料屬「不上第三方雲」級別。若實際多數客戶不在意 → Notion 的雲端便利性權重會上升。
- **Markdown-native 的長期價值**：假設 agent-harness 持續以 YAML/MD 為主。若未來轉向 DB-backed 結構（v3 規劃時可能），Markdown 親和力的價值會下降。
- **手機端使用頻率**：本分析假設手機端僅用於閱讀。若需頻繁手機編輯 → Notion / Logseq 的優先級會微升。

## 待驗證

- **Obsidian 與 Claude Code CLI 的整合摩擦**：本框架的 outputs/ 與 memory/ 目錄能否直接作為 Obsidian vault 而不衝突？建議建一個小型試驗 vault 驗證。
- **Logseq Sync 何時離開 Beta**：若年內離開 Beta，Logseq 的成本優勢會凸顯。

## 已知事實（含來源）

- Obsidian：免費；Sync $5/月；Publish $10/月（[Obsidian Pricing 2026](https://aisotools.com/pricing/obsidian)）
- Logseq：免費開源；Sync $5/月（Beta）（[Logseq Pricing 2026](https://costbench.com/compare/logseq-vs-obsidian/)）
- Notion：個人 Plus 起 $10/月；Business $15/月（[Notion 對比](https://oitia.com/en/article/notion-vs-obsidian-vs-logseq-2026/)）

## 合理推論

- Obsidian Sync 的 e2e 加密在實務上已可滿足多數一人公司客戶的 NDA（Anthropic、多數 SaaS 廠商皆採類似標準）
- Notion 雖有 Enterprise plan 提供更多控制，但月費跳到 $20+，對單人不划算

---

## Reverse 條件（什麼情況下推翻 Obsidian 主用）

| 觸發條件 | 處理 |
|---------|------|
| 多人協作專案 ≥ 1 個月 | 該專案改用 Notion；主 KB 仍 Obsidian |
| 對外分享次數 ≥ 月 5 次 | 評估 Notion 全面遷移或加購 Obsidian Publish |
| Obsidian Sync 連續 2 個月內出現 ≥ 3 次資料衝突 | 改自架 git 同步或考慮 Notion |
| 客戶 NDA 出現「禁止本地檔案儲存」條款 | 該客戶資料改用客戶指定環境，主 KB 不變 |
| Logseq 離開 Beta + 行動端達 Obsidian 水準 | 重新評估，但既有資料遷移成本仍是阻力 |

---

## 建議下一步

1. **2026-04-26 ~ 04-30**：建立 Obsidian vault，掛載 agent-harness 的 outputs/ 與 memory/ 為唯讀目錄，驗證整合摩擦
2. **首月不付費**：先用 iCloud / git 做手動同步，觀察是否真有跨裝置編輯需求
3. **2026-05-31**：累積 1 個月使用後決定是否購買 Sync
4. **2026-Q3 retro**：檢視本決策的 Reverse 條件是否觸發

---

## 校準資料（analysis skill 首筆）

| 項目 | 值 |
|------|---|
| 預估 tokens（事前） | 12K |
| 實測 tokens（事後估） | ~14K |
| Web search 用量 | 1/3（保留 2 輪備用 — 符合新策略） |
| 工具呼叫 | file_read ×2、web_search ×1、file_write ×2、bash ×3 |
| 原始觀測比例 | 14K / 12K = 1.17（**未生效**，依 SOP 第 3 條樣本 < 3 不更新 COST_POLICY 校準係數） |
| 樣本數 | 1（仍 < 3，COST_POLICY 校準係數欄維持「—」狀態） |
| 下一筆 analysis 觸發 | 累積至 ≥ 3 筆後重算（依 COST_POLICY 校準 SOP） |

---

*Sources*:
- [Obsidian Pricing 2026 — AISO Tools](https://aisotools.com/pricing/obsidian)
- [Obsidian vs Logseq Pricing — CostBench](https://costbench.com/compare/logseq-vs-obsidian/)
- [Notion vs Obsidian vs Logseq 2026 — Oitia](https://oitia.com/en/article/notion-vs-obsidian-vs-logseq-2026/)
