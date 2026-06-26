# 深度測試研究 T3 — 可觀測性／紀錄防漂移（＋成本/context 橫切）

> **草稿（draft）** ｜ 日期：2026-06-26 ｜ Task Card：`20260626-003` ｜ skill：research
> 方法：唯讀實跑全套觀測/防漂移腳本（`--check`／報告模式）+ 端到端可追溯性稽核。未修改任何受測檔。
> 對應自我評估短板：可觀測性 6。使用者多選的「成本/context」面向於本研究併入橫切視角。

---

## 結論

harness 的**靜態防漂移（工具層可觀測性）已達生產級**：5 個唯讀腳本全綠（drift / spec-consistency / context-budget / decision-revisit / governance-metrics 皆 exit 0），CI 用 ~13 道關卡守住規格。但**動態可觀測性（工作流層 + 業務層）受限於樣本稀疏與狀態未閉環**：(1) `logs/runs/` **只有 2 筆** run log，使工作流層 gate 統計建立在 n=2 之上；(2) **48 張 Task Card 中 19 張（40%）卡在 `review` 狀態**未轉終態，是顯著的生命週期未閉環信號；(3) **全系統零 dashboard 實測 token**，成本可觀測性完全是估算值。context 預算非常健康（~1197/3000，60% 餘裕），不是瓶頸。

一句話：**「規格不漂移」已被 CI 坐實，但「執行過程可量化」仍卡在樣本太少 + 狀態生命週期沒收尾，這正是可觀測 6 分的根因。**

---

## 已知事實（唯讀腳本實跑 + 可追溯性稽核）

### 1. 全套唯讀腳本健康度（皆 exit 0）

| 腳本 | 結果 |
|---|---|
| `generate_frontend_manifest.py --check` | OK：`frontend/data.json` 無漂移 |
| `check_spec_consistency.rb` | OK：spec 一致性通過 |
| `check_context_budget.rb` | OK：CLAUDE.md ~606 + GLOBAL_RULES ~591 = **~1197 / 3000 token** |
| `check_decision_revisit.rb` | OK：D006 OK（runs 2/10 門檻）；D004/D005/D007 為 MANUAL（非量化觸發）|
| `governance_metrics.py` | OK：M1–M4 全 ok（見下） |

### 2. 工作流層可觀測性（governance_metrics，**n=2 run log**）

- status 分佈：`{completed: 1, failed: 1}`
- 平均 checkpoints/run：2.0
- 四層 gate 統計：`schema_check {pass:1, fail:1}`、`rule_check {pass:1, not_run:1}`、`completion {pass:1, not_run:1}`、`risk {pass:1, not_run:1}`

→ 指標引擎（R7）**存在且可跑**，但分母只有 2，無法回答「哪層 gate 最常失敗」這類需要分佈的問題。`not_run:1` 全來自 R5（schema 失敗即停，後續 gate 未跑），與設計一致。

### 3. 業務層可觀測性（governance_metrics，來源 AUDIT_LOG）

| skill | 任務數 | 平均 token | 平均工具呼叫 |
|---|:--:|:--:|:--:|
| analysis | 3 | 16000 | 8.7 |
| ops | 23 | 15272 | 11.5 |
| research | 5 | 23600 | 4.8 |
| review | 5 | 34800 | 9.2 |
| writing | 4 | 16500 | 5.8 |

→ 業務層**已有每 skill 趨勢**（自評時尚缺，R7 已補上）。但所有 token 皆**規則估算值**，非實測（見 §5）。

### 4. 端到端可追溯性稽核（Task Card ↔ AUDIT_LOG ↔ logs/runs）

| 維度 | 數量 | 觀察 |
|---|:--:|---|
| Task Card 總數 | 48 | done 22 / **review 19** / in_progress 5 / pending 2 |
| AUDIT_LOG 任務筆數 | 41 | 與業務層 40 筆大致對齊 |
| `logs/runs/` run log | **2** | completed 1（system-validation）+ failed 1（R5） |
| `logs/errors/` 真實 error log | 2 | tool_failure 1 + schema_failure 1 |
| outputs drafts:reports | 26 : 3 | 草稿為主，晉升率低（符合 drafts-first 設計） |

**斷點 1（最重要）**：**19/48（40%）Task Card 停在 `review` 狀態**——非終態（done/failed）。可能是「等人工審閱」或「狀態漂移未收尾」；無機制區分，是可追溯性的真實黑洞。
**斷點 2**：41 筆 audit 對 2 筆 run log——但這**多屬 D006 設計**（run log 僅 failed/partial/high-risk/checkpoints≥3 才必填），非缺陷；代價是工作流層樣本天生稀疏。

### 5. 成本／context 橫切視角

- **context 預算非瓶頸**：~1197/3000，餘裕 60%。CLAUDE.md + GLOBAL_RULES 都在硬限制內。
- **零 dashboard 實測 token**：唯一非零的 run log（R5）`token_estimate.source = "rule_estimated"`，completed 那筆 token 為 0。即 R6 加的 `source` 欄位**已就位但從未被 `dashboard_measured` 填過** → 全系統成本數據可信度＝估算級。
- **analysis 成本校準樣本**：業務層顯示 analysis 已有 3 筆 audit（自評時為 0），缺口部分收斂，但仍是最少樣本的 skill。

---

## 合理推論

- 工具層（防漂移/CI）成熟而動態層（執行可量化）滯後，是因為**前者可被腳本靜態強制、後者需累積真實執行樣本**；R5/R7/R8 已把「機制」補齊，現在卡的是「樣本量」與「狀態收尾」而非「缺工具」。
- 19 張 `review` 卡若多為「草稿已產、等晉升 reports」，則與 drafts:reports = 26:3 一致（晉升閘很嚴）；但 `review` 是 Task Card 狀態而非輸出狀態，二者混用會讓「任務是否真的結案」難以一眼判定。
- token 全估算不影響「相對比較」（research/review 偏貴的排序仍有意義），但**絕對成本與預算告警**會失真。

## 待驗證

- 19 張 `review` 卡逐張屬「真的等審閱」還是「狀態忘了更新」？需逐卡核對 result_summary／completion_time。
- governance_metrics 的 M3 audit 覆蓋率「全 ok」是否因門檻寬鬆？需確認門檻定義 vs 41/48 的實際覆蓋。
- `frontend/data.json` 只含 2 logs——前端看板是否反映 run log 稀疏，使用者看板觀感是否誤導「執行很少」？

## 高風險假設

- **「可觀測性已足以支撐生產決策」是過度樂觀**：能回答的多是靜態結構問題；「本月哪類任務成本在漲」「哪層 gate 最常卡」這類需要分佈的問題，在 n=2 run log 與全估算 token 下**無法可靠回答**。
- 假設 `review` 狀態 = 等人工——若其實是漂移，則 40% 的卡其真實狀態未知，可追溯性帳面好看但實質有黑洞。
- 假設 rule_estimated token「夠用」——一旦要做預算告警（COST_POLICY 升級觸發），估算誤差可能讓告警失準。

## 建議（只提案，不就地修；應另開 Task Card 走 ask）

1. **R-T3a（高 C/P）**：Task Card 狀態生命週期收尾——加唯讀腳本掃出停在 `review` 超過 N 天的卡，逼其轉 done/failed 或註明審閱中。直接消除「40% 黑洞」。
2. **R-T3b**：至少回填 1–2 筆 `dashboard_measured` token，讓 R6 的 `source` 欄位有真實樣本，成本可觀測性從估算升一級。
3. **R-T3c**：工作流層樣本——隨 T1 的 rule/completion/risk 真實演練（R-T1a）自然增加 run log，把 gate 統計分母從 2 拉高到可分析。

> 三層可觀測性現況評級：**工具層 8（生產級）／工作流層 5（機制有、樣本薄）／業務層 6（趨勢有、全估算）**。瓶頸是後兩層的「樣本 + 狀態收尾」，非缺工具——印證自評可觀測 6。

---

## 來源

- 唯讀實跑：`scripts/generate_frontend_manifest.py --check`、`check_spec_consistency.rb`、`check_context_budget.rb`、`check_decision_revisit.rb`、`governance_metrics.py`
- 可追溯性：`tasks/20*.yaml`（48 張，status 分佈）、`logs/AUDIT_LOG.md`（41 筆）、`logs/runs/*.yaml`（2 筆）、`logs/errors/`（2 筆）、`outputs/drafts|reports`
- `system/EXECUTION_LOG_SCHEMA.yaml`（D006 run log 使用範圍 + R6 token source 欄）、`system/COST_POLICY.md`
- 交叉引用：T1（gate 真實演練會餵回工作流層樣本）
