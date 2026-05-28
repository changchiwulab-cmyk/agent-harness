# Agent Harness v2 — 第一性原理自評（Opus 4.8）

- **狀態**：草稿（draft-first，未經人工確認，不得晉升 outputs/reports/）
- **日期**：2026-05-28
- **產出者**：Claude Code（claude-opus-4-8）
- **性質**：對本專案自身的評估（meta self-assessment），非對外交付物
- **交叉佐證來源**：`system/NATIVE_OVERLAP.yaml`、`system/COST_POLICY.md`、`logs/AUDIT_LOG.md`、`system/GLOBAL_RULES.md`、`README.md`

---

## 結論與建議

綜合評分 **約 6.5 / 10 ——「值得續做，但必須轉向」**。

這是一個工程紮實、設計哲學少見地清醒的「個人治理框架」。**當下實用性高**；但它的**長期必要性與 AGI 貢獻被「苦澀的教訓（The Bitter Lesson）」封頂**——平台（Claude Code 原生功能）正在吸收它 70–85% 的機制。最強的正向訊號是：專案**自己已經量化承認這件事**（`NATIVE_OVERLAP.yaml`）並規劃轉向（v3）。

一句話：**別再跟平台拼機制，去拼平台拿不走的東西——你的紀律、你的數據、和獨立的驗證。**

---

## 一、已知事實（探勘所得，可由 repo 檔案佐證）

- **本質**：跑在 Claude Code CLI 上、給「一人公司」用的單一代理治理框架。自述核心目標「可恢復、可審核、可量化」，設計哲學「可控 > 能力」（`README.md`、`system/AGENT_CONTEXT.yaml`）。
- **不是空殼**：約 1,500 LOC 真實 Python 護欄——`scripts/permissions_guard.py`（PreToolUse hook，依 deny list 攔截 Bash）、`system/validate_task_card.py`、`scripts/governance_metrics.py`、`scripts/generate_frontend_manifest.py`、`scripts/generate_audit_log.py`；含 e2e/plugin 測試、CI 漂移檢查（`scripts/check_spec_consistency.rb` + manifest `--check`）、靜態前端看板。
- **三平面十六模組**：控制（Task Card/路由/決策紀錄）、執行（Context/Skill/Tool/Gate/Checkpoint）、治理（Permission/Approval/Cost/Failure Taxonomy/Execution Log/Audit）（`README.md`）。
- **真實營運數據**：約 6 週、`logs/AUDIT_LOG.md` 40+ 筆稽核紀錄、25+ 草稿產出、依 8 筆 audit log **實測校準**的 token 預算表（`system/COST_POLICY.md`）、ask→allow 的權限畢業機制（`system/PERMISSIONS.yaml`）。
- **自省檔**：`system/NATIVE_OVERLAP.yaml` 自評與原生重疊 **30%（總體）**——Skill Executor 85%、Tool Executor 80%、Permission 75%、Router 70%、Agent Context 60%、Context Manager 50%。
- **第一性原理框定**（`system/GLOBAL_RULES.md`）：「LLM 原生缺乏四件事：穩定目標、穩定上下文邊界、穩定權限意識、穩定自我驗證能力。所有規則都是在補這四個洞。」

---

## 二、第一性原理拆解（合理推論）

**公理 1｜LLM 是無狀態的隨機函數。** 無持久目標、無權限意識、無可靠自我驗證。本專案正確命名這四個洞並逐條補償（compensating controls）。→ 哲學紮實。

**公理 2｜The Bitter Lesson。** 靠算力的通用方法會吃掉手工 scaffolding。證據就在專案自己的 `NATIVE_OVERLAP.yaml`：70–85% 核心「機制」正被平台原生功能商品化。這是「未來必要性」的最大威脅，且這道牆在縮水。

**公理 3｜不被商品化的東西只有三樣。**
1. 操作者專屬數據：你自己的成本校準、失敗案例庫、決策史、偏好。
2. 治理紀律本身：強制 `definition_of_done`、對外動作 draft-first、稽核軌跡、3 次停損。
3. 對照真值的「獨立驗證 / grounding」與人類監督介面。
這 ≈ 重疊率剩下的那 15–30%，才是真正的護城河。

**公理 4｜AGI = 可規模化監督（Scalable Oversight）問題。** 模型越強越自主，瓶頸從「會不會做」轉成「能不能信任、驗證、設界、稽核」。本專案「可控 > 能力」與 AI control / 防禦縱深 / 最小權限 / tripwire 的研究議程**方向一致**——這是它最強的 AGI 相關性。
**致命短板**：gate 結果、DoD pass/fail、audit 多由**同一個模型自評**產生——而「自我驗證」正是它自己命名的四大缺口之一。它只用人審 + review skill 緩解，沒真正關閉。能力趨近 AGI 時，自評式監督**越來越不可信**。這封頂了 AGI 貢獻分。

---

## 三、1–10 分類評分

| # | 維度 | 分數 | 理由（一句話） |
|---|------|:---:|------|
| 1 | 實用性（一人公司當下） | **8** | 真能把無序的 LLM 助手變成有紀律、可稽核、有成本上限的流程；但範圍窄（單人、手動觸發、絕對槓桿有限）。 |
| 2 | 工程成熟度 / 執行品質 | **8** | 1500 LOC 有效護欄 + CI 漂移檢查 + 測試 + 實測校準；務實不形式主義。封頂因「硬」強制僅限 Bash hook，其餘靠 LLM 詮釋 md/yaml。 |
| 3 | 設計哲學第一性原理深度 | **9** | 明確命名四大缺口並逐條補償，反 cargo-cult（fast-path、選擇性記錄、權限畢業）。未完全解自評信任問題故非 10。 |
| 4 | 與 AGI 發展配合性 | **5** | 哲學方向正確，但停在流程紀律層、依賴同模型自評 + 人審、缺對抗式/獨立驗證深度。 |
| 5 | 抗淘汰性 / 護城河（Bitter Lesson） | **4** | 自評 70–85% 機制與原生重疊且上升，護城河薄且縮水；真正耐用的只有操作者專屬數據那一小塊。 |
| 6 | 創新性 / 獨特貢獻 | **5** | 整合極用心，但個別原語（權限/稽核/eval examples/plan-execute）已漸成標配，屬「優秀的應用整合」非「新機制」。 |
| 7 | 未來發展必要性 | **7** | 有必要——但前提是轉向；若原封不動維護 16 模組則僅 4。 |

**綜合：約 6.5 / 10。**

---

## 四、判斷：有沒有必要繼續發展？

**有，但要轉向。** 方向（給 AI agent 的治理/控制紀律）耐用且越來越重要 → 必要。現形式（手工 16 模組、重複造原生輪子）正在過時 → 專案自己已承認（`NATIVE_OVERLAP.yaml` + v3 計畫）。

轉向四步（從「做框架 breadth」→「治理深度 + 可攜性 depth + portability」）：
1. **蒸餾**不被商品化的核心（Task Card 紀律、DoD/audit/decision schema、failure taxonomy、cost calibration、draft-first gate）成**薄、模型無關、可攜的 plugin**（`outputs/drafts/agent-governance-bootstrap/` 就是對的直覺，應加速）。
2. **加碼護城河**：操作者專屬學習迴路（retro 校準、失敗案例庫、決策記憶）。
3. **補 AGI 短板**：引入**獨立於執行模型**的驗證（不同模型 / 規則式 / 對照真值 grounding），破解「自評式監督」信任問題。
4. **砍掉 / 委派**那 70–85% 原生已覆蓋的部分（skill 路由、權限、context 壓縮 → `/skill`、`settings.json`、PreToolUse、native compaction）。

→ 已開立 Task Card：`tasks/2026-05-28_v3-governance-distillation-poc.yaml`（status: pending，待人工確認後執行）。

---

## 五、高風險假設

- **「平台會持續吸收機制」是趨勢外推**：若 Anthropic 改變方向、放慢原生治理功能，護城河評分（4）會偏低。
- **NATIVE_OVERLAP 的重疊百分比是專案自評**，非獨立量測；可能高估或低估。
- **AGI 配合性評分**建立在「自評式監督隨能力上升而失效」的假設上；此為主流 AI safety 觀點但未經本專案實證。

## 六、待驗證

- v3 plugin 蒸餾後，實際維護成本是否真的下降（需 retro 數據佐證）。
- 「獨立驗證」PoC 是否能在不顯著增加成本下，量測到自評以外的錯誤捕捉率提升。
- 16 模組中，哪些一旦交給原生會導致功能/可審核性退化（需逐模組實測，非僅看重疊率）。

## 七、來源

- `README.md`、`CLAUDE.md`、`system/GLOBAL_RULES.md`、`system/NATIVE_OVERLAP.yaml`、`system/COST_POLICY.md`、`system/PERMISSIONS.yaml`、`system/AGENT_CONTEXT.yaml`、`logs/AUDIT_LOG.md`
- 外部觀念：The Bitter Lesson（Sutton）、Scalable Oversight / AI Control（AI safety 文獻）— 屬通識引用，未逐篇查證。
