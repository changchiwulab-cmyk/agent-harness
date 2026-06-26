# 架構落差盤點與補齊 — Agent Harness v2 → v2.1

> **草稿（draft）** ｜ 日期：2026-06-26 ｜ Task Card：`20260626-001` ｜ skill：review
> 交付範圍：完整檢視專案 + 對照 2026 公開前沿盤點缺口 + 補齊（實作見 002/003/004）。
> 審閱通過後可依 `RETRO_FLOW` §5 晉升至 `outputs/reports/`。

---

## 摘要

| 項目 | 結論 |
|------|------|
| 專案定位 | 一人公司單代理治理框架，原則「可控 > 能力」；治理面已是成熟招牌（self-assessment 7/10、成熟度 3） |
| 最大結構性盲點 | **威脅模型只防「LLM 自己失控」，缺「輸入是對抗性的」一軸**；`SECURITY.md` 為空白模板 |
| 第二缺口 | `eval_examples.md` 有 golden set 但**無 runner/regression**，「可量化」對輸出品質失守 |
| 本次補齊（Tier 1） | 信任邊界/安全架構 + 評測 harness（皆不可替代、不與原生重疊的厚治理層） |
| 本次補齊（Tier 2） | 上下文工程政策 + 模型路由政策（收斂散落規則 / 補完自家 roadmap） |
| 刻意不補 | 多代理 swarm、複雜 MCP 鏈、自動外發、自建 model router runtime（維持 README 不做清單 + v3 減重方向） |

**方法**：3 個 Explore agent（深度盤點 system/、skills/tasks/logs、git 走向）＋ 親讀關鍵檔（README、GLOBAL_RULES、AGENT_CONTEXT、SECURITY、self-assessment、v3 抽出規劃）＋ 3 次 web search 對照 2026 前沿。

---

## 一、對照 2026 公開前沿的八維盤點

維度取自業界「agent harness engineering」常見清單（tools / patterns / evals / memory / MCP / permissions / observability / orchestration）＋ Anthropic context engineering ＋ lethal-trifecta 安全研究。

| 維度 | 現況 | 落差 | 本次處置 |
|------|------|------|---------|
| Permissions | ✓✓ deny-by-default + `permissions_guard.py` runtime hook + 四級風險 | 無（招牌） | 保留 |
| Patterns（gate/routing/intake） | ✓✓ 四層 Gate + 路由 + fast-path intake | 無 | 保留 |
| Recovery / Durability | ✓ RECOVERY_RUNBOOK + R8 已實測 checkpoint 還原 | 無 | 保留 |
| Observability | ✓ AUDIT/runs/approvals/errors + governance_metrics + frontend | 輕微（trace 模型可日後再議） | 暫不動 |
| **Security / 信任邊界** | ✗ 威脅模型缺對抗性輸入軸；`SECURITY.md` 空模板 | **最大缺口** | **Tier 1A 補** |
| **Evals** | ⚠️ golden set 有、runner 無 | 「可量化」對品質失守 | **Tier 1B 補** |
| Context / Memory | ⚠️ 規則散落、native-memory 卡 draft | 無單一政策 | **Tier 2 補** |
| Model routing | ⚠️ `COST_POLICY` 標 v2 未實作 | 自家 roadmap 未竟 | **Tier 2 補** |
| Orchestration / 複雜 MCP | 刻意單代理、不串複雜 MCP | 不在範圍（v3/v4 再議） | 不補（明示） |

---

## 二、為什麼安全是最大缺口（第一性原理）

`GLOBAL_RULES.md` 開宗明義：「LLM 原生缺四件——穩定目標、上下文邊界、權限意識、自我驗證」。
整套 v2（gate、taxonomy、permissions、approval）都在補這四個洞，**把 agent 自己當不可信方**。

但 2026 前沿的主戰場已轉移：**輸入本身是對抗性的**。
- lethal trifecta = 私有資料 + 不可信內容 + 對外傳出管道；三者齊備時，一份惡意網頁/檔案即可誘導外洩。
- 業界觀察：被評估的生產級 agent 約 98% 同時具備這三腿；防禦必須是**架構性**的，不能只靠模型自律。

本框架的處境：
- 私有資料腿：**present**（可讀專案檔）。
- 不可信內容腿：**present**（web_search / 外部檔為入口）——**但 v2 完全沒有處理規則**。
- 對外傳出腿：**已 blocked**（PERMISSIONS deny 所有對外發送、對外只產 draft）——**這是被低估的強項**。

> 結論：本框架其實**已經斷了 trifecta 的第三腿**，只是從未明說；缺的是第二腿（不可信內容）的處理規則。補齊後三腿同時受控。

---

## 三、本次補齊（與既有資產的關係）

### Tier 1A — Security / 信任邊界（Task `20260626-002`）
- `system/TRUST_BOUNDARY.yaml`：三層信任分級（trusted / semi_trusted / untrusted）+ 核心規則 TB-01~06 + lethal trifecta 對照（明載 exfiltration 腿 = blocked）。
- 改寫 `SECURITY.md` 為雙軸威脅模型真政策（取代 GitHub 空模板）。
- `FAILURE_TAXONOMY.yaml` 新增 SEC-05（間接注入）/ SEC-06（工具污染）/ SEC-07（外洩），14 → 17 類。
- `GLOBAL_RULES.md` 加信任邊界段；`skills/research/SKILL.md` 加不可信內容/provenance 段。
- **Enforcement（守 J5）**：`check_spec_consistency.rb` 驗 schema + SEC-05~07 存在；`tests/e2e/test_trust_boundary.py`；CI 串接。

### Tier 1B — Evaluation harness（Task `20260626-003`）
- `system/EVAL_POLICY.md`：評什麼 / 兩層（deterministic + 可選 LLM-judge）/ rubric schema / 不變式。
- `skills/<5 type>/rubric.yaml`：把既有 `eval_examples.md` 的「判斷標準」表轉成機器可讀規則。
- `scripts/run_evals.py`（+ 單元測試）：對 golden set 跑 regression——**實測 good 滿分、bad 0 分**。
- `RETRO_FLOW.md` 新增 eval 維度；CI 串接 `run_evals` + e2e smoke。

### Tier 2 — Context + Model（Task `20260626-004`）
- `system/CONTEXT_POLICY.md`：context 預算配置 / 壓縮 / JIT 取用 / 子代理隔離 / 記憶架構，收斂散落規則；收斂 native-memory 為「混合」決策（D008）。
- `system/MODEL_POLICY.md`：四層（Haiku 4.5 / Sonnet 4.6 / Opus 4.8 / Fable 5）+ skill_type→預設 tier；`COST_POLICY` 模型路由段標已落地；`TASK_CARD_TEMPLATE` 加可選 `model_tier`（D009）。

---

## 四、刻意不補（維持 anti-bloat 與 v3 方向）

| 不補項 | 理由 |
|--------|------|
| 多代理 swarm | README 不做清單；單代理是刻意定位（v3/v4 才議拆分） |
| 複雜 MCP 鏈 | 同上；本次僅在 TRUST_BOUNDARY 預留「MCP 輸出 = untrusted、採 allowlist」規則 |
| 自動外發 / 自動 shell | 違反硬規則 2 與 deny 清單；正是 trifecta 第三腿，刻意維持 blocked |
| 自建 model router runtime | 與平台模型選擇高度重疊；違背 v3「砍冗餘、不重造原生」（只定治理意圖，不造 runtime） |
| Observability OTel trace 模型 | 現有 logs/metrics/frontend 已覆蓋多數；trace 形式化價值中等，列入日後 |

---

## 五、與 v3 抽出規劃的對齊

`2026-05-09_v3_extraction_plan.md` 的判準：砍與原生重疊者、深化不可替代治理層、每條規則對應一個 enforcement（J5）。

- 本次新增的**安全 / eval / context / model 政策皆屬「不可替代治理層」**（原生不做），與 v3「治理層應更厚、更獨立」方向一致——v3 抽出 plugin 時，這幾件應一併納入治理層，不是被砍對象。
- 每條新規則都接了 CI / e2e / schema 檢查（守 J5），未留「只有文檔、零檢查」的空規則。
- 模組數：治理平面 16 → 18（Tier 1）→ 20（含 Tier 2）。

---

## 六、驗證（本盤點對應的實證）

- `python3 scripts/run_evals.py` → 5 skill regression 全綠（good 通過 / bad 不通過）。
- `python3 scripts/test_run_evals.py` / `tests/e2e/test_eval_smoke.py` / `tests/e2e/test_trust_boundary.py` 全綠。
- `ruby scripts/check_spec_consistency.rb`（含新 TRUST_BOUNDARY + SEC-05~07 + rubric 驗證）綠。
- `ruby scripts/check_context_budget.rb`：CLAUDE.md + GLOBAL_RULES 仍 < 3K。
- `python3 scripts/generate_frontend_manifest.py --check`：data.json 同步。

---

## 七、後續

- 本評估只產草稿，**未自行 merge 任何 system/ 變更**；002/003/004 的 system/ diff 走本 PR review（ask 等級 diff 閘），merge 後回填 `logs/approvals/`。
- 人工確認後，本草稿可依 `RETRO_FLOW` §5 晉升 `outputs/reports/`。
- 建議下一個季度 RETRO 納入新的 eval 維度趨勢，並重評 NATIVE_OVERLAP（安全/eval 屬不可替代，應拉高「治理層不可替代度」估值）。
