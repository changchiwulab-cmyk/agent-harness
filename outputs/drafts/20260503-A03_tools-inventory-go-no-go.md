# Tools-Inventory 線 Mini Go/No-Go 決策分析

- Task ID：20260503-A03
- 日期：2026-05-03
- 範圍：20260404-R01（research）/ R02（review）/ O01（fix）三張 status: done 的 Task Card

## TL;DR

**建議：選項 B「archive 三張 + 寫 1-page tools-inventory memo」**，與 A02→W02→O04 平行的 D 路徑。

理由：(1) AI 工具 4 週迭代速度高於策略提案，4 週前的具體工具列表時效風險最大；(2) **結構價值**（7 大類別架構、四態採用狀態框架）與 R02 的審查標準在 audit log 中已固化，memo 即可保留；(3) O01 已證明 rebuild 不依賴 web_search，未來重啟成本可控；(4) 沒有外部對齊壓力（這是內部 reference 文件），park 完全合理。

選項 A（重產 v3 + 升級 reports/）只在「使用者打算把 tools-inventory 變成定期維護的活文件」這個前提下才划算 — 否則重產一份 4 週後又會過時的列表，純粹是成本黑洞。

---

## 結論與建議

排序：**B > A > C > D**。

- **B（archive + memo）**：成本低、固化結構價值、解除 CI 紅燈、未來可重啟。**首選**。
- **A（重產 v3）**：條件性 — 僅當打算定期維護才做。次選。
- **C（archive 不寫 memo）**：丟失 7 類別 / 四態框架的可追溯性，不推薦。
- **D（healthcheck 改 warn）**：剛上線就被閹割，違背 strict 上線的設計意圖；強烈不推薦。

---

## 已知事實 / 推論 / 待驗證

### 已知事實（Task Card + AUDIT_LOG）
- R01 result：6 大工具類別（AI / 專案管理 / 通訊 / 財務行政 / 行銷 / 自動化），共 20+ 工具
- R02 result：5 條 DoD 中 3 通過 / 2 部分通過；2 個必修（知識管理類別缺失、採用狀態不一致）、3 個建議修改
- O01 result：新增「知識管理」類別（Obsidian / Notion / Mem.ai / Readwise Reader / agent-harness memory/ 共 5 工具）；7 大類別採用狀態統一四態格式（✅已用 / ✅推論已用 / 🔍待評估 / ❌不適用）
- O01 audit log 明文：「原 v1 草稿因 .gitignore 未存磁碟，v2 依 Task Card context + audit log + memory/ 重建」— 證明 rebuild path 已被驗證一次
- 三份 draft（`solo-company-tools-inventory.md` / `tools-inventory-review-report.md` / `solo-company-tools-inventory-v2.md`）目前皆不在 working tree 與任一 git ref
- A02 的 S01 卡 input_data 引用了 `solo-company-tools-inventory-v2.md` — 表示此線曾被下游消費（但 S01 自己也已 archived）
- 距產出 28 天

### 合理推論
- **結構層**已固化在 audit log（7 類別名稱、四態框架、知識管理 5 工具清單）— 重啟時這層免重做
- **內容層**（其餘 6 類別共 15+ 工具的具體清單、每工具的月費 / 評估 / 適用性說明）已遺失
- O01 的 v2 是「審查修正後的可用版本」，是這條鏈最有商業價值的一份；但同樣物理遺失
- 4 週前盤點的部分工具可能已：價格變動、功能改版、新競品出現、被併購

### 待驗證
- **使用者是否打算把 tools-inventory 變成定期維護的活文件？**（決定 B vs A 的關鍵分水嶺）
- 過去 4 週內，被盤點的 20+ 工具中有多少實際變動？（決定重產的價值衰減速度）
- A02 已 archive，下游消費者（原本是策略提案線）已不存在，是否還有其他下游？

### 高風險假設
- **「結構層 audit log 摘要足夠」**：若未來重啟需要追溯「為何挑這 5 個知識管理工具而非其他」的理由，audit log 可能不夠
- **「沒有其他下游」**：若使用者其實有用此盤點做日常工具決策（採購、淘汰），archive 會中斷 reference
- **「4 週前的工具列表已過時」**：若被盤點的多為老牌工具（Notion/Obsidian 等），實際過時程度可能比想像低

---

## 選項比較

### 選項 A：重產 v3，升級至 outputs/reports/

| 維度 | 評估 | 依據 |
|---|---|---|
| 價值 | 中–高 | 若會定期維護，重產 v3 是 baseline；否則只是修補 |
| 成本 | 中 | ~10-15K tokens + 1-1.5 hr；O01 證明 rebuild 不需 web_search，但若要更新工具現況則需 web_search 配額 |
| 風險 | 中 | 重產出來不會 bit-for-bit 等於原 v2（細節需重判斷）；4 週後又會過時 |
| 可行性 | 高 | research/ops skill 就位，O01 已驗證 rebuild path |
| 執行難度 | 中 | 需要決定是否更新工具現況（純還原 vs 升版）|
| 預期回報 | **條件性** | **高（會維護）/ 低（一次性練習）** |
| 一人公司適配度 | 中 | 一人維護一份工具盤點負擔不小；除非有具體決策需求 |

### 選項 B：archive 三張 + 寫 1-page tools-inventory memo（**首選**）

| 維度 | 評估 | 依據 |
|---|---|---|
| 價值 | 中 | 固化 7 類別架構 + 四態框架 + 知識管理 5 工具清單；其餘細節留 ⟨遺失⟩ 標記 |
| 成本 | 低 | ~5-8K tokens + 30 min（memo）+ 10 min（archive）|
| 風險 | 低 | 完全可逆；memo 本身是高品質 rebuild input |
| 可行性 | 高 | 模式與 W02 + O04 完全平行 |
| 執行難度 | 低 | 兩張小卡序列依賴 |
| 預期回報 | 高（風險調整後）| 最小投入鎖住結構層 + 解除 CI 紅燈 |
| 一人公司適配度 | 高 | 符合「可控 > 能力」、低維護成本 |

### 選項 C：archive 三張，不寫 memo

| 維度 | 評估 | 依據 |
|---|---|---|
| 價值 | 低 | 結構層完全埋進 audit log，重啟成本變高 |
| 成本 | 極低 | ~3K tokens + 15 min（純 archive）|
| 風險 | 中 | 「7 類別 / 四態框架」是 R01-R02-O01 三輪迭代成果，遺失可惜 |
| 可行性 | 高 | 純檔案搬動 |
| 執行難度 | 低 | — |
| 預期回報 | 負 | 比 B 省的 5K tokens 換來結構層遺失，划不來 |
| 一人公司適配度 | 低 | 違反「保留可追溯性」 |

### 選項 D：把 healthcheck 改為 warn 模式（exit 0 + 列印）

| 維度 | 評估 | 依據 |
|---|---|---|
| 價值 | 負 | O05 strict 上線才剛 24 小時就被閹割，設計意圖被破壞 |
| 成本 | 低 | 改 1 行 + 改 1 個 CI step；~3K tokens |
| 風險 | 高 | 未來真的有 drift（誤刪 draft、gitignore 誤設）將不會被攔下 |
| 可行性 | 高 | 技術上極簡 |
| 執行難度 | 低 | — |
| 預期回報 | 負 | 用一次性的 CI 紅燈換永久的健檢能力下降 |
| 一人公司適配度 | 低 | 違背「可控 > 能力」 — 健檢就是控制機制 |

---

## 三張卡的 status 收斂建議

| Task Card | 目前 | 建議新 status | 處置 | 理由 |
|---|---|---|---|---|
| 20260404-R01 (research) | done | **保留 done** | 移到 tasks/archived/ | 「曾經完成」事實成立；歸檔表達「已 park」 |
| 20260404-R02 (review)   | done | **保留 done** | 移到 tasks/archived/ | 同上；R02 必修項已被 O01 處理，紀錄完整 |
| 20260404-O01 (ops/fix)  | done | **保留 done** | 移到 tasks/archived/ | 同上；audit log 完整保留修改項清單 |

**重要設計選擇**：與 A02→O04 模式一致，**不改 status 欄位**（VALID_STATUS 沒有 archived），歸檔意義由所在目錄表達。

---

## 排序後下一步行動清單

優先級從高到低，每項標註「是否需要新 Task Card / 預估成本 / 是否需要人工輸入 / 是否解除 CI 紅燈」。

1. **【需人工輸入】確認是否會定期維護 tools-inventory**（決定 B vs A 的關鍵）
   - 若會 → 跳 #2A；若不會（或不確定）→ 跳 #2B
   - 預估成本：對話即可
   - 解除 CI 紅燈：否

2A. **【若 #1 = 會維護】開新 research/ops 卡：重產 v3 + 升級 reports/**
   - 卡名草案：`20260503_tools-inventory-v3-rebuild.yaml`
   - 範圍：rebuild + 更新工具現況（會用 web_search 配額）
   - 預估：~15K tokens、1.5 hr；risk_level: low、approval_needed: true
   - 解除 CI 紅燈：✅（輸出存在後 healthcheck 通過）

2B. **【若 #1 = 不會 / 不確定】開新 writing 卡：寫 1-page memo（B 路徑步驟 1）**
   - 卡名草案：`20260503_tools-inventory-memo.yaml`（task_id: `20260503-W03`）
   - 來源：R01/R02/O01 的 result_summary + Task Card context
   - 輸出：`outputs/drafts/20260503-W03_tools-inventory-memo.md`
   - 預估：~5K tokens、30 min；risk_level: medium、approval_needed: true
   - 內容：7 類別名稱 + 四態框架 + 知識管理 5 工具 + ⟨遺失⟩標記其他細節 + 重啟條件
   - 解除 CI 紅燈：否（memo 本身不在三張卡的 expected_output）

3. **【若走 B 路徑】開新 ops 卡：archive 三張卡（B 路徑步驟 2）**
   - 卡名草案：`20260503_archive-tools-inventory-cards.yaml`（task_id: `20260503-O06`）
   - 動作：git mv 三張到 tasks/archived/、regen frontend manifest
   - 前置：W03 memo 已落地
   - 預估：~3K tokens、15 min；risk_level: low、approval_needed: true
   - 解除 CI 紅燈：✅（archived 卡會被 healthcheck 跳過）

4. **【可選，後續】Decision Log 紀錄本次選擇**
   - 在 `memory/active_projects/agent-harness/decisions/` 開 `20260503-D007_tools-inventory-go-no-go.yaml`
   - 把 A02 的 D007 號讓給本決策（A02 並未真正落地 D007；或避開取 D008）
   - 預估：~3K tokens、10 min

---

## 元層觀察

- 連續 7 張卡（4 AI-proposal + 3 tools-inventory）都是 pre-2026-04-11 gitignore 受害者。O05 健檢的價值已經在第一次上線就證明了 — 但也提醒：**重要 fix（如 commit f32ba4a 那次 gitignore 修正）應該主動回頭巡一次當時受影響的歷史輸出**，而不是等下游檢查。可考慮加入 RETRO 的標準巡檢項。
- A02→W02→O04 + A03→W03→O06 是同一套 pattern。如果未來再遇到第三、第四條同類型遺失線，可以考慮把這個 pattern（analysis-card → memo-card → archive-card）做成一個 ops 子流程模板放在 `tasks/examples/`。
