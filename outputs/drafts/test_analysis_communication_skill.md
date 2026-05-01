# 決策分析：是否在 agent-harness 新增第 6 個 communication skill

**Task ID**: 20260501-T02
**執行時間**: 2026-05-01
**Skill**: analysis

---

## 結論與建議

**建議選項：維持現狀（不新增），優先強化現有 writing + ops 的邊界定義。**

理由：communication skill 的核心功能（對外訊息起草）已由 writing skill 覆蓋，額外的路由判斷與維護負擔對一人公司而言不划算。現有 PERMISSIONS.yaml 的 deny 清單已明確鎖定「對外發送」，新增 skill 不會改變安全邊界，只會增加系統複雜度。

---

## 選項比較

### 選項 A：維持現狀（不新增 communication skill）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中 | 現有 writing skill 已覆蓋對外訊息起草功能（`skills/writing/SKILL.md`：「對外文案」列入用途）；ops skill 覆蓋流程文件化；對外發送已在 deny 清單內 |
| 成本 | 0 | 無額外開發、維護、文件負擔；無需新增 SKILL.md、eval_examples.md、ROUTING_RULES 更新 |
| 風險 | 低 | 不引入新的路由歧義；不增加 agent 需要判斷的 skill 數量 |
| 可行性 | 高 | 直接可執行，無前置條件 |
| 執行難度 | 極低（0 工作量） | 不做即完成 |
| 預期回報 | 維持現狀 | 短期無明顯收益，但避免了維護成本增加 |
| 一人公司適配度 | 高 | 一人公司的核心原則是減少維護負擔、保持系統可控。新增 skill 需持續維護 eval_examples、ROUTING_RULES、GATE_POLICY 等連帶文件 |

### 選項 B：新增獨立 communication skill（完整實作）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中低 | 主要解決 writing skill 路由歧義（「對外訊息」vs「內部文件」），但歧義問題現在並不嚴重（`system/ROUTING_RULES.md`：路由規則已涵蓋） |
| 成本 | 估計 3-5 小時初始設計 + 每版本 0.5-1 小時維護 | 需新增 `skills/communication/SKILL.md`、`eval_examples.md`、更新 `ROUTING_RULES.md`（新增 communication 欄位）、更新 `GATE_POLICY.yaml`（新增 skill_type 有效值）、更新 `GLOBAL_RULES.md` 與 `README.md` |
| 風險 | 中 | 新 skill 定義不清可能導致與 writing、ops 的路由衝突；一人公司單點維護風險高（若設計者長期缺席，新 skill 可能僵化） |
| 可行性 | 中 | 技術上可行，但需人工審核（modify_skills 為 ask 等級，見 `system/PERMISSIONS.yaml`） |
| 執行難度 | 中（3-5 小時 + 持續維護） | 需協調多個 system 檔案的更新，每次更新需經人工確認 |
| 預期回報 | 低至中 | 若路由歧義確實影響任務品質，則有價值；否則為過度設計 |
| 一人公司適配度 | 低 | 維護 6 個 skill 比 5 個 skill 複雜度高出 20%，但一人公司能分配給 agent 系統維護的時間有限 |

### 選項 C：不新增 skill，但在 writing skill 內加「communication 子模式」

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 中 | 在不增加路由層級的前提下，細化 writing 的輸出類型定義；可解決「對外文案」與「內部報告」的品質標準差異 |
| 成本 | 估計 1-2 小時 | 僅需修改 `skills/writing/SKILL.md`（modify_skills 為 ask 等級，需人工確認）和 `skills/writing/eval_examples.md` |
| 風險 | 低至中 | 若子模式定義太複雜，會讓 SKILL.md 膨脹，違反 context ≤ 1,500 tokens 限制（`CLAUDE.md`：「單一 skill prompt ≤ 1,500 tokens」） |
| 可行性 | 高 | 技術上可行；比選項 B 的協調成本低 |
| 執行難度 | 低（1-2 小時） | 只改一個 skill 檔案 |
| 預期回報 | 中 | 若 writing 任務中「對外」vs「對內」的品質標準確實有差異，此方案可精準對應需求 |
| 一人公司適配度 | 中 | 比選項 B 更輕量，但仍需維護；context token 限制是實際限制條件 |

---

## 建議排序

1. **選項 A（維持現狀）**：優先選擇，理由見結論。
2. **選項 C（writing 內加子模式）**：若日後出現 3 次以上「routing 到 writing 但品質標準不明確」的問題，再考慮。
3. **選項 B（新增獨立 skill）**：僅在以下情境才考慮：（a）communication 任務量超過每週 5 張 Task Card；（b）writing skill 的 context token 已逼近上限。

---

## 高風險假設

- **假設 1**：Writing skill 已足夠處理對外訊息的品質需求。
  - 如果不成立（即 writing skill 在對外訊息上的錯誤率明顯偏高）：應優先考慮選項 C 或 B。
  - 驗證方式：觀察未來 4 週內 writing skill 任務的 review gate 結果。
- **假設 2**：一人公司的 communication 任務量不足以撐起獨立 skill 的維護成本。
  - 如果不成立（即每週 communication 任務超過 5 張）：選項 B 的 ROI 會轉正。
  - 驗證方式：統計 writing skill 任務中「對外訊息類」佔比。

---

## 待驗證

- [待驗證] Writing skill 在過去任務中，對外文案任務的品質是否有系統性問題？需查看 `logs/AUDIT_LOG.md` 與 `logs/runs/` 中 writing 任務的 gate 結果。驗證方式：審閱既有執行紀錄。
- [待驗證] ROUTING_RULES.md 的路由規則是否已足夠區分「communication」與「writing」任務？需確認是否有任務因路由不清而重工。

---

## 建議下一步

1. 維持現狀，在接下來的 4 週觀察 writing skill 任務中「對外訊息類」的品質表現。
2. 若出現 2 次以上因 skill 路由不清導致任務重工，建立一張新的 analysis Task Card 重新評估選項 C。
3. 現階段不需修改任何 system/ 或 skills/ 檔案。

---

## Gate 驗證

### 第一層：Schema 驗證
- task_id：`20260501-T02` ✅（格式 YYYYMMDD-###）
- goal：非空 ✅
- definition_of_done：6 條 ✅
- skill_type：`analysis`（有效值）✅
- risk_level：`low`（有效值）✅
- allowed_tools：`file_read, file_search` ✅
- **結果：PASS**

### 第二層：規則驗證
- 使用工具：`file_read`（讀取 skills/writing/SKILL.md、skills/ops/SKILL.md、system/PERMISSIONS.yaml、system/ROUTING_RULES.md、CLAUDE.md）✅
- 無 web search ✅（max_web_searches: 0 遵守）
- 無 deny 動作 ✅
- 工具呼叫次數：5 次，在 max_tool_calls: 8 範圍內 ✅
- **結果：PASS**

### 第三層：完成驗證（definition_of_done 逐條）
- [x] 至少列出 3 個選項，且必含「維持現狀（不新增）」：**PASS** — 選項 A 即維持現狀，共 3 個選項
- [x] 每個選項都跑完六維評估（價值/成本/風險/可行性/執行難度/回報）+ 一人公司適配度：**PASS** — 7 個維度均涵蓋
- [x] 成本與風險具體化（時間/維護負擔/與既有 writing+ops 的重疊度）：**PASS** — 成本以小時估計、維護負擔量化、重疊度說明
- [x] 明確給出建議排序與理由：**PASS** — 建議排序段落清楚
- [x] 列出高風險假設（如不成立會推翻結論的假設）：**PASS** — 2 個假設含驗證方式
- [x] 輸出符合 analysis skill 的 Markdown 結構：**PASS** — 含結論、選項比較、高風險假設、待驗證、建議下一步
- **結果：PASS**

### 第四層：風險驗證
- risk_level: low，執行動作為純讀取與 drafts 輸出 ✅
- 輸出存放於 `outputs/drafts/` ✅
- 無對外動作 ✅
- **結果：PASS**
