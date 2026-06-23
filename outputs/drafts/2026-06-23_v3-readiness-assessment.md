# v3 遷移就緒度評估（v3-readiness-assessment）

> **草稿（draft）** ｜ 日期：2026-06-23 ｜ Task Card：`20260623-002` ｜ skill：analysis
> 交付範圍：**只評估、不遷移**。未改任何 `system/` 或 `skills/`。
> 對齊既有 `outputs/drafts/2026-05-09_v3_extraction_plan.md`（A01）；本文加「就緒度」視角，不重做 A01 的去留裁決。
> roadmap R10（自我評估 `outputs/reports/harness-self-assessment-v1.md` §五）。R1–R9 已完成。

---

## 結論（先講）

| 項目 | 判定 |
|------|------|
| **是否該現在遷移 v3？** | **否。維持 v2（D003 hold 不變）。** 兩條 v3 觸發皆未達標。 |
| **若觸發，執行就緒度？** | **高。** A01 已完成 16 模組裁決與遷移路徑；D007 bootstrap 檔案樹已備齊；缺的只是「按下去」。 |
| **一句話** | **「藍圖畫好、觸發未到」**——v3 是一個**待命方案**，不是待辦事項。就緒度的天花板已達，剩下由觸發條件決定何時啟動。 |
| **本次唯一新增的活件** | R9 已把 NATIVE_OVERLAP 過季/破閾值**自動化偵測**（M4），所以「觸發到了沒」從此不靠人記得去看。 |

> 設計原則回扣（一人公司）：**不做沒有實際需求的架構升級**（D003 reasoning）。R10 的價值不是催遷移，而是把「何時該遷、遷的時候帶什麼走、哪些不可丟」一次定清楚，並交給 R9 的自動偵測去盯觸發。

---

## 一、v3 觸發現況（兩條觸發要分清楚）

v2→v3 有**兩條彼此獨立**的觸發，過去常被混為一談：

| # | 觸發 | 來源 | 閾值 | 現況（2026-06-23） | 達標？ |
|---|------|------|------|---------------------|:---:|
| T-A | **規模/多代理觸發**（bounded specialists 拆分） | D003 | context 經常超限／規則衝突頻繁／成本持續超標／錯誤率上升，任一持續 2 週 | context 未超限、無規則衝突、token 未超 dashboard 上限、錯誤率低 | ❌ 未達標 |
| T-B | **原生重疊觸發**（治理層抽出為獨立 plugin） | NATIVE_OVERLAP.yaml | aggregate > 50% → 重構；≥40% → 預警 | aggregate **30%**（reviewed 2026-05-09） | ❌ 未達標 |

**關鍵釐清**：A01（治理層抽出 / plugin 化）對應的是 **T-B**，不是 D003 的 T-A。D003 講的是「要不要拆成多代理」，與「要不要把治理三件抽成獨立 plugin」是兩件事。本評估把兩者並列，避免再被混淆。

**R9 的貢獻**：T-B 現在由 `governance_metrics.py` M4 自動盯——
- aggregate `>50%` → 報告自動建議「產出本評估的後續：實際遷移評估」；
- `reviewed_on` 逾 `revisit_interval_days`（90 天）→ 自動 warn「季度 revisit 到期」。
- 下次到期日：約 **2026-08-07**（reviewed 2026-05-09 + 90 天）。現距 45 天，未到期。

T-A 目前**無自動偵測**（四項條件分散在 context/audit/cost）——這是本評估識別出的下一個可自動化缺口（見 §七）。

---

## 二、逐模組就緒度（保留 / 下放原生 / 並存）

把 A01 §4.2 的去留裁決翻譯成「v3 三去向 + 離 v3 形態的距離」：

- **下放原生**＝A01 的「砍除」（交給 Claude Code 原生）
- **並存**＝A01 的「抽出」（獨立治理 plugin 元件）或「重構」（介面重做、靠近原生但仍存在）
- **保留原樣**＝0（A01 已證實 v2 無任何模組「不重疊且不需動」）

> 計數校正：依 A01 §4.2 **逐項表**重新點算為 **砍除 5 / 抽出 5 / 重構 6**（#1,3,6,9,10 砍；#4,8,14,15,16 抽；#2,5,7,11,12,13 重構）。A01 §4.2 **摘要列**寫「砍5/抽6/重構5」與逐項表有 1 項出入，**以逐項表為準**。對 v3 三去向的結論不受影響（下放 5 / 並存 11 / 保留 0）。

| 模組 | A01 裁決 | v3 去向 | 就緒度 | 離 v3 距離 / 阻塞點 |
|------|---------|---------|:------:|------|
| Interface | 砍除 | 下放原生 | ✅ ready | 本就是 runtime，README 改一段即可 |
| Planner/Router | 砍除 | 下放原生 | 🟡 partial | 依賴 H1（原生 Skill 自動路由能否全覆蓋手動路由）`[待驗證]` |
| Skill Executor (skills/) | 砍除 | 下放原生 | ✅ ready | N3 PoC 已驗 frontmatter + symlink 註冊可行 |
| Checkpoint (git) | 砍除 | 下放原生 | ✅ ready | git 慣例，CLAUDE.md 一行帶過 |
| Agent Context | 砍除 | 下放原生 | ✅ ready | 內容併回 CLAUDE.md「邊界」段 |
| Decision Log | 抽出 | **並存（治理資產）** | ✅ ready | schema 已存在；plugin `/decision` 介面已在 bootstrap skeleton |
| Gate Verifier (GATE_POLICY) | 抽出 | **並存（治理資產）** | ✅ ready | 四層 + rollback 已成熟；plugin `/gate-check` 已在 skeleton |
| Failure Taxonomy | 抽出 | **並存（治理資產）** | ✅ ready | 14 類靜態 YAML，可直接搬 |
| Execution Log Schema | 抽出 | **並存（治理資產）** | ✅ ready | 窄範圍觸發（D006）；R6 已加 token source 欄 |
| Audit Log | 抽出 | **並存（治理資產）** | ✅ ready | append-only + CI 格式檢查已具 |
| Task Card | 重構 | 並存（瘦身） | ✅ ready | 必填欄位收斂方案已定（A01 #2） |
| Context Manager (CLAUDE.md 規則段) | 重構 | 並存（瘦身） | ✅ ready | 只留 token 硬上限 + 三硬規則 |
| Tool Executor (allowed_tools) | 重構 | 並存（hook 輸入） | ✅ ready | enforcement 已在 `permissions_guard.py` |
| Permission (PERMISSIONS.yaml) | 重構 | 並存（搬 settings.json） | 🟡 partial | 依賴 H2（allow/ask/deny × risk_level 可否正交）`[待驗證]` |
| Approval Policy | 重構 | 並存（併入 workflow） | ✅ ready | 邏輯併入 Decision Log + Task Card |
| Cost Policy | 重構 | 並存（資料留、規則瘦） | ✅ ready | 校準表保留為 report；行為段收進 CLAUDE.md |

**就緒度小結**：16 模組中 **14 ready / 2 partial（Planner/Router、Permission，皆卡在 A01 的 H1/H2 假設）**。沒有任何 blocked。

---

## 三、不可替代資產（v3 必須帶走，不可丟）

這些是 Claude Code 原生**不做**、且是本 harness 真正價值所在。遷移時無論形態怎麼變，這四類必須完整保留：

| 資產 | 為何不可替代 | v3 安置 | 現況保護 |
|------|------------|---------|---------|
| **Token 校準表** | 實測係數（research 1.43／writing 2.00／ops 1.56／review 1.25），非猜測；多數框架沒有 | `outputs/reports/token-calibration-v*.md`（治理資產，非 policy） | ✅ 已晉升 report；analysis 仍 0 樣本（R3 待補） |
| **Failure Taxonomy（14 類）** | 獨立可引用的失敗知識庫 | 治理 plugin 靜態 YAML | ✅ R5 故障演練已產生首筆真實 error log 連結 |
| **Decision Log（D001–D007）** | 結構化決策追溯 + revisit_trigger | 治理 plugin `/decision` | ✅ R4 已加 revisit 追蹤器 |
| **Audit Log** | 任務後事實紀錄（事實導向、抗自評偏差） | 治理 plugin `/audit` append-only | ✅ 已有 CI 格式守護 + 產生器 |

> 加碼觀察：R7 的可觀測性引擎（gate pass 率、每 skill 趨勢、失敗分佈）也應列為「帶走」清單——它把上述靜態資產變成**可量化趨勢**，是 v2 後期才長出來的資產，A01（5/9 撰寫）尚未涵蓋。建議併入 D007 後續或治理 plugin 的 `governance_metrics` 元件。

---

## 四、就緒度評分

| 維度 | 分數 | 依據 |
|------|:---:|------|
| 模組裁決完備度 | 9/10 | A01 已逐項裁決 16 模組，僅 2 項 partial（H1/H2 待驗） |
| 不可替代資產保護 | 8/10 | 四類資產皆有 v3 安置與現況保護；analysis 校準仍空（R3） |
| Bootstrap 執行就緒 | 8/10 | D007 檔案樹（plugin.json + 5 commands + 4 schemas + 2 hooks + 2 validators）已備；缺實際建 repo（跨 session） |
| 觸發偵測自動化 | 6/10 | T-B 已自動化（R9 M4）；**T-A 仍無自動偵測**（缺口） |
| 遷移風險緩解 | 7/10 | A01 §8 已列 R1–R4 風險 + 緩解；v2.5 雙寫過渡策略明確 |
| **綜合就緒度** | **≈ 7.6/10** | **「執行藍圖就緒、觸發未到、偵測半自動」** |

---

## 五、D003 / D007 更新建議（提案；實際套用屬 ask）

> 以下為 **proposed diff**，不在本卡直接套用。改 decision logs 屬記憶/決策變更（ask），需人工確認後另行套用。

### D003（v3-upgrade-hold）— 維持 hold，加註現況與交叉引用

```diff
  decision: "維持 v2，下次 retro（累積 5 筆後）再評估"
+ # 2026-06-23 R10 複查：T-A 四項觸發條件仍全未達標，hold 不變。
+ # 釐清：D003 管的是「規模/多代理」觸發（T-A）；治理層抽出（A01/plugin）由 NATIVE_OVERLAP >50% 觸發（T-B），
+ # 兩條獨立。T-B 現 30%，已由 R9 governance_metrics M4 自動偵測，不再依賴人工記得回看。
  reasoning: >
    ...
  risk: "若業務急速擴張，v2 的單代理架構可能成為瓶頸"
  revisit_trigger: "任一 v3 觸發條件持續 2 週以上；或單 session context 超限頻率 > 30%"
```

### D007（v3-plugin-bootstrap-decisions）— 四項決策不變，加註 bootstrap 仍待命

```diff
  status: "active"
+ # 2026-06-23 R10 複查：四項決策（repo 名 / Apache-2.0 / Private / 獨立 repo）不變；
+ # bootstrap 檔案樹仍完整備於 outputs/drafts/agent-governance-bootstrap/，尚未實際建 repo（仍待下個 session）。
+ # T-B 未觸發，故無急迫性；待 NATIVE_OVERLAP 破 50% 或使用者明示再執行。
```

> 兩者皆**只加註、不改既有決策內容**——符合「決策可追溯」原則（保留原始判斷，疊加複查紀錄）。

---

## 六、高風險假設（沿用並更新 A01 §9）

- **H1**：原生 Skill 自動路由能取代 `ROUTING_RULES.md` 全部功能。`[待驗證]`
  - 影響就緒度：Planner/Router 從「下放原生」降級為「並存」。
- **H2**：`settings.json` 的 allow/ask/deny 與 `risk_level` 可正交組合。`[待驗證]`
  - 影響就緒度：Permission 從「重構搬移」變「抽出自管 risk_level」。
- **H3**：plugin 形態能同時承載 hook + skill + slash command。`[待驗證 — 取決於 Claude Code plugin spec 當下能力]`
  - 影響就緒度：不成立則先做 standalone CLI，plugin 延後（A01 §5.1 已備此退路）。
- **H4（R10 新增）**：T-A 的四項觸發（context/規則/成本/錯誤率）可被一支唯讀腳本量化偵測，如同 R9 對 T-B 所做。`[待驗證]`
  - 不成立則：T-A 維持人工 RETRO 判斷。

---

## 七、待驗證

| 項目 | 驗證方式 | 狀態 |
|------|---------|------|
| H1 原生路由覆蓋率 | 分支上做 1 個 multi-skill 路由 PoC | 待 v3 啟動時 |
| H2 permission × risk_level 正交 | 查 settings.json schema + 試做 | 待 v3 啟動時 |
| H3 plugin 三件並存 | 官方 plugin spec / 最小範例 | 待下個 session 建 repo 時（D007） |
| H4 T-A 可否自動偵測 | 仿 R9 寫唯讀偵測腳本 | **可作為 R11 候選（見下一步）** |
| analysis 校準樣本 | 跑 1–2 張真實 analysis 任務記 token | R3 既有缺口；本卡即 analysis，可作首筆樣本 |

---

## 八、下一步

1. **不啟動遷移**——T-A/T-B 皆未觸發，維持 hold（D003）。
2. 人工確認後套用 §五 的 D003/D007 加註（ask）。
3. （可選 R11 候選）把 **T-A 觸發自動化**：仿 R9 M4，寫唯讀腳本盯 context 超限率／規則衝突／成本／錯誤率，與 R9 的 T-B 偵測合流成單一「v3 觸發儀表板」。這會把「觸發偵測自動化」維度從 6 補到 9，是 v3 就緒度的最後一塊。
4. 本卡作為 analysis skill 的**首筆成本校準樣本**（補 R3 缺口）——完成後把 token 估值記入 `COST_POLICY.md` analysis 列。
5. 本草稿經人工確認後，可依 `RETRO_FLOW` §5 晉升至 `outputs/reports/`。

---

### 來源

- `outputs/drafts/2026-05-09_v3_extraction_plan.md`（A01，16 模組裁決 + 遷移路徑）
- `system/NATIVE_OVERLAP.yaml`（aggregate 30%，T-B 觸發來源；R9 自動偵測）
- `memory/.../decisions/20260415-D003`（T-A hold）、`20260509-D007`（bootstrap 決策）
- `outputs/reports/harness-self-assessment-v1.md`（roadmap R1–R10）
