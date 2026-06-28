# 評估平面（Evaluation Plane）v1 — 架構設計

> **草稿（draft）**｜日期：2026-06-28｜Task Card：`20260628-001`｜skill：ops
> 交付：補齊專案缺的架構——把「可量化」從只有成本，補上品質軸。經人工確認後可依 RETRO_FLOW 晉升 reports/。

---

## 一、為什麼（缺口）

對照 2026 公開 AI harness 元件分類（evals / memory / MCP / permissions / observability / orchestration），
本專案在 **權限 / HITL / 稽核 / 成本 / 恢復** 上已強，但「**可量化**」只做了一半：

| 軸 | 既有 | 缺口 |
|----|------|------|
| 成本 | `COST_POLICY` 實測校準係數（research 1.43 / writing 2.00 / ops 1.56 / review 1.25）| — |
| **品質** | `skills/*/eval_examples.md` 有現成 rubric（判斷標準表）| **死文件**：從不被執行、評分、追蹤 |

`GATE_POLICY` 四層只驗「對不對／安不安全」（schema→rule→completion→risk），不評「好不好」。
自我評估（`2026-05-29_harness-self-assessment.md`）已自承：「可觀測性只到工具層、業務層品質趨勢缺、學習迴路開環」。
2026 業界共識（eval-driven development：rubric + golden set〔取自真實案例〕+ 回歸閘門 + LLM-as-judge）正是這條缺的閉環。

## 二、做什麼（第四平面）

新增 **評估平面**，與 Control / Execution / Governance 並列，5 個模組（第 17–21）：

| # | 模組 | 檔案 |
|---|------|------|
| 17 | Eval Policy | `system/EVAL_POLICY.yaml`：評分尺度(0/1/2)、verdict 推導、judge 協定、eval_record schema、golden 回歸規則 |
| 18 | Rubrics | `evals/rubrics/{research,analysis,writing,ops,review}.yaml`：由各 `eval_examples.md` 判斷標準表轉寫 |
| 19 | Golden Set | `evals/golden/cases.yaml`：真實既有產出 + 期望 verdict（回歸錨點） |
| 20 | Eval Records | `evals/results/*.yaml`：結構化評分記錄（鏡像 EXECUTION_LOG_SCHEMA 風格） |
| 21 | Eval Runner | `scripts/run_evals.py`：`--scaffold` / `--check`（schema＋verdict 重算＋golden 回歸）/ `--judge`(v2 stub) |

### 機制：rubric 自評＋schema 守護（與 GATE 同哲學）
- **評分由 Claude 執行**（如 GATE 的 completion_check），依 rubric 維度填 `evals/results/*.yaml`。
- **deterministic 守門由 script + CI 負責**：`run_evals.py --check` 重算 `score_pct`/`verdict`、比對 golden 回歸。
- 評分尺度：每維度 2=通過 / 1=部分 / 0=不通過；`score_pct = 100*Σ/(2n)`；blocker 維度得 0 直接 fail；
  pass 門檻預設 80。verdict ∈ {pass, partial, fail}。
- **LLM-as-judge**：v2 保留介面，待校準到與人工 85–90% 一致再啟用（見 EVAL_POLICY judges）。

## 三、四平面圖

```
Control ── Execution ── Governance ── Evaluation（新）
任務定義     技能/驗證/     權限/批准/      Eval Policy
路由/決策    checkpoint    成本/失敗/稽核   Rubrics / Golden
                          （量化成本）     Records / Runner（量化品質）
```

## 四、接線（與既有系統整合，非新模組）

1. **GATE_POLICY** 第五層 `quality_check`（核心四層之後）：對交付產出評分，verdict==fail → 鎖 drafts/、不得晉升 reports/。
2. **CI**：`check_spec_consistency.rb` 加 `evals/` schema lint；workflow 加 `run_evals.py --check` 與 `test_run_evals.py`。
3. **觀測**：`governance_metrics.py` 新增品質層（每 skill 評分數/平均分/pass 率/verdict 分佈）——閉合 R7 業務層品質缺口。
4. **前端**：`generate_frontend_manifest.py` 序列化 `evals/` → `data.json`；`frontend/` 新增「品質評估（Quality / Eval）」面板。
5. **文件**：README（四平面）、CLAUDE.md 執行流程、context.md、AGENT_CONTEXT.yaml、NATIVE_OVERLAP.yaml、COST_POLICY.md 交叉引用。

## 五、重用點（避免造輪子）

- Rubric ← `skills/*/eval_examples.md` 既有判斷標準表（5 skill 全有）
- Record 結構 ← `system/EXECUTION_LOG_SCHEMA.yaml`
- Policy 風格 ← `GATE_POLICY.yaml` / `APPROVAL_POLICY.yaml`
- Schema lint ← `check_spec_consistency.rb`（與 logs lint 同途徑）
- 指標/序列化 ← `governance_metrics.py` / `generate_frontend_manifest.py`
- 首筆 golden/result ← 既有真實產出 `outputs/drafts/20260502-T01_*.md`（避免空目錄/合成資料）

## 六、驗證（端到端，皆綠）

```bash
python system/validate_task_card.py tasks/2026-06-28_evaluation-plane-v1.yaml
ruby scripts/check_spec_consistency.rb              # 含 evals/ lint
python3 scripts/run_evals.py --check                # schema＋verdict 重算＋golden 回歸（CI 同指令）
python3 scripts/run_evals.py --scaffold outputs/drafts/<draft>.md research   # 產空白評分卡
python3 scripts/governance_metrics.py --observability  # 出現品質層
python3 scripts/generate_frontend_manifest.py --check  # data.json 不漂移
python3 scripts/test_run_evals.py                   # 19 tests
```

首筆 `evals/results/EVAL-20260628-001` 為真實樣本（評 T01 research，verdict=pass、score_pct=100），
非空目錄、非合成資料。

## 七、不做（守紀律）

- 不做 LLM-as-judge 實作（只留介面，v2 校準後啟用）。
- 不做多 agent / orchestration / MCP / 沙箱（仍在 v3–v4 與不做清單）。
- 不自動寫長期記憶；eval 記錄屬 `evals/`（執行紀錄類），決策日誌仍走 ask。
- 不破 Context 硬限制（CLAUDE.md + GLOBAL_RULES 現 ~1.2K / 3K）。

## 八、後續（建議）

- 累積評分時補一筆 **partial/fail** 樣本，讓品質分佈不只有 pass（首筆刻意誠實標記為強樣本）。
- 正式報告晉升 reports/ 前固定跑一次 eval，把 verdict 寫進 RETRO。
- rubric_self 累積 ≥ 15 筆 + 1 筆失敗演練 → 評估啟用 LLM-as-judge（見 D008 revisit_trigger）。

---

> 決策紀錄：`memory/active_projects/agent-harness/decisions/20260628-D008_evaluation-plane.yaml`
