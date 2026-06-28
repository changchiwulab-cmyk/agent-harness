# Agent Harness v2.0 — 一人公司 Decision Control Plane

## 這是什麼

一人公司用的 Agent 執行框架，跑在 Claude Code CLI 上。
核心目標：**可恢復、可審核、可量化**。

不是多代理平台，不是 AI 自動化全套。
是一個讓 Claude 穩定幫你做事、不失控的結構。

## 架構：四平面、二十一模組

```
控制平面（Control）
├── 1. Interface         Claude Code CLI
├── 2. Task Card         tasks/*.yaml — 任務定義
├── 3. Planner/Router    system/ROUTING_RULES.md — skill 路由
└── 4. Decision Log      tasks/DECISION_LOG_TEMPLATE.yaml — 決策紀錄

執行平面（Execution）
├── 5. Context Manager   CLAUDE.md context 規則 — 上下文組裝
├── 6. Skill Executor    skills/[type]/SKILL.md + eval_examples.md — 技能執行
├── 7. Tool Executor     allowed_tools 白名單 — 工具執行
├── 8. Gate Verifier     system/GATE_POLICY.yaml — 五層驗證 checklist
└── 9. Checkpoint        git commit — 進度保存

治理平面（Governance）
├── 10. Agent Context      system/AGENT_CONTEXT.yaml — 系統自我認知
├── 11. Permission         system/PERMISSIONS.yaml — 權限策略
├── 12. Approval Policy    system/APPROVAL_POLICY.yaml — 批准流程（v2 新增）
├── 13. Cost Policy        system/COST_POLICY.md — 成本控制（量化「成本」）
├── 14. Failure Taxonomy   system/FAILURE_TAXONOMY.yaml — 失敗分類學（v2 新增）
├── 15. Execution Log      system/EXECUTION_LOG_SCHEMA.yaml — 執行紀錄 schema（v2 新增）
└── 16. Audit Log          logs/AUDIT_LOG.md — 稽核紀錄

評估平面（Evaluation，v2.1 新增 — 量化「品質」，補可量化最後一軸）
├── 17. Eval Policy        system/EVAL_POLICY.yaml — 評分尺度/verdict/judge 協定/記錄 schema
├── 18. Rubrics            evals/rubrics/*.yaml — 5 skill 可機讀 rubric（由 eval_examples 轉寫）
├── 19. Golden Set         evals/golden/cases.yaml — 真實案例回歸錨點
├── 20. Eval Records       evals/results/*.yaml — 結構化評分記錄
└── 21. Eval Runner        scripts/run_evals.py — scaffold / schema 守護 / golden 回歸
```

> **評估平面緣由**：v2 量化了「成本」（COST_POLICY 校準係數）卻未量化「品質」——
> `eval_examples.md` 只是死文件，從不被執行/評分/追蹤。v2.1 把它升級成可運行的品質迴路
> （rubric 自評＋schema 守護，對齊 2026 eval-driven development：rubric + golden set + 回歸閘門），
> 補上「可量化」最後一軸，並閉合自我評估指出的「業務層品質趨勢缺、學習迴路開環」。
> LLM-as-judge 為 v2 保留介面，待校準到與人工 85–90% 一致再啟用。

## 資料夾結構

```
agent-harness/
├── CLAUDE.md                  ← Claude Code 自動載入的 boot prompt
├── README.md                  ← 本檔案
├── .gitignore
├── system/
│   ├── GLOBAL_RULES.md        ← 全域規則 + 失敗分類學
│   ├── PERMISSIONS.yaml       ← 權限策略（allow/ask/deny + 四級風險）
│   ├── COST_POLICY.md         ← 成本控制 + 升級觸發條件
│   ├── ROUTING_RULES.md       ← Skill 路由規則
│   ├── GATE_POLICY.yaml            ← 四層驗證 checklist + rollback（v1.5+v2）
│   ├── AGENT_CONTEXT.yaml          ← 系統自我認知與邊界（v1.5 新增）
│   ├── APPROVAL_POLICY.yaml        ← 批准流程規則（v2 新增）
│   ├── FAILURE_TAXONOMY.yaml       ← 14 種失敗模式獨立檔（v2 新增）
│   └── EXECUTION_LOG_SCHEMA.yaml   ← 執行紀錄結構定義（v2 新增）
├── tasks/
│   ├── TASK_CARD_TEMPLATE.yaml
│   ├── DECISION_LOG_TEMPLATE.yaml  ← 決策紀錄模板（v1.5 新增）
│   ├── archived/              ← 已 deprecated 模板（如 WEEKLY_REVIEW_TEMPLATE）
│   └── examples/              ← 填好的範例
├── skills/
│   ├── research/
│   │   ├── SKILL.md           ← 研究分析
│   │   └── eval_examples.md   ← 好/壞輸出範例（v1.5 新增）
│   ├── analysis/
│   │   ├── SKILL.md           ← 決策支援與策略分析
│   │   └── eval_examples.md   ← 好/壞輸出範例（v2 新增）
│   ├── writing/
│   │   ├── SKILL.md           ← 撰寫產出
│   │   └── eval_examples.md   ← 好/壞輸出範例（v1.5 新增）
│   ├── ops/
│   │   ├── SKILL.md           ← 營運操作
│   │   └── eval_examples.md   ← 好/壞輸出範例（v2 新增）
│   └── review/
│       ├── SKILL.md           ← 品質審查
│       └── eval_examples.md   ← 好/壞輸出範例（v1.5 新增）
├── memory/
│   ├── README.md              ← 記憶使用規則
│   ├── user_prefs.md          ← 使用者偏好
│   └── active_projects/       ← 進行中專案 context
├── logs/
│   ├── AUDIT_LOG.md           ← 稽核紀錄
│   ├── runs/                  ← 執行紀錄
│   ├── approvals/             ← 核准紀錄
│   └── errors/                ← 錯誤紀錄
├── evals/                     ← 評估平面（v2.1 新增）
│   ├── rubrics/              ← 每 skill 可機讀 rubric
│   ├── golden/cases.yaml     ← 真實案例回歸錨點
│   └── results/              ← 結構化評分記錄
└── outputs/
    ├── drafts/                ← 草稿輸出
    └── reports/               ← 正式報告
```

## 快速上手（3 步驟）

### 1. 建立任務
```bash
cp tasks/TASK_CARD_TEMPLATE.yaml tasks/2026-04-03_你的任務.yaml
```
填入 `goal`、`definition_of_done`、`skill_type`。  
`skill_type` 請使用：`research` / `writing` / `ops` / `review`。參考 `tasks/examples/` 下的範例。

### 2. 執行
在 Claude Code CLI 中 `cd <agent-harness 專案路徑>`，Claude 會自動讀取 CLAUDE.md。
告訴 Claude：「執行 tasks/2026-04-03_你的任務.yaml」。

### 3. 追蹤
- 執行紀錄：`logs/AUDIT_LOG.md`
- 進度快照：`git log --oneline`
- 草稿輸出：`outputs/drafts/`

## 提交前檢查（建議）

為避免範例路徑或資料夾結構漂移，提交前先執行（且 CI 也會自動執行同組檢查）：

```bash
scripts/check_spec_consistency.rb
```

此檢查已包含：目錄存在性、Task Card 必填欄位 schema、`task_id`/`date` 格式與一致性驗證、`completion_time` 日期驗證（且 `status=done/failed` 時必填）、範例 `input_data` / `expected_output.location` 路徑驗證。

若要額外確認 YAML 可被解析，可再執行：

```bash
ruby -e 'require "yaml"; Dir.glob("**/*.yaml").each{|p| YAML.load_file(p)}; puts "ALL_YAML_OK"'
```

若要驗證單張 Task Card：

```bash
python system/validate_task_card.py tasks/your-task.yaml
```

## 安全政策

安全議題回報流程見 [SECURITY.md](SECURITY.md)。

## 導入計畫

### 第 1 週：跑通骨架
- 用 `research` 和 `review` 跑 1 條完整任務流
- 確認 Task Card → 執行 → Checkpoint → 驗證 → 輸出 的流程順暢

### 第 2 週：補執行閉環
- 啟用 `writing` 和 `ops`
- 開始累積 audit log 數據
- 補充 working memory

### 第 3 週：補治理
- 根據前兩週數據調整 COST_POLICY 的任務級預算
- 完善 approval policy
- 建立 failure taxonomy 的實際案例

## 現階段不做清單

以下事項先不做，避免過早拉高維護成本與風險暴露：

- 多 agent swarm
- 自動長期記憶擴寫
- 太多工具串接
- 自動寫入正式資料庫
- 自動外發信件/貼文/發布
- 把所有規則塞進單一超長 system prompt
- 複雜 MCP 串接
- 自動 shell 執行

## 版本規劃

| 版本 | 內容 | 升級觸發條件 |
|------|------|-------------|
| **v1** | 單核心代理 + Task Card + Checkpoint + Verifier + Audit | — |
| **v1.5** | + Gate Policy + Operating Context + Decision Log + Eval Examples + Weekly Review | 馬鞍工程原則導入：驗證集中化、系統自知、決策可追溯 |
| **v2** | + Approval Policy + Failure Taxonomy + Execution Log Schema + Rollback Path + Ops Eval | 馬鞍工程落地：批准流程獨立化、失敗模式可引用、執行紀錄結構化 |
| **v2.1（現在）** | + Evaluation Plane（Eval Policy + Rubrics + Golden Set + Eval Records + Eval Runner） | 對齊 2026 eval-driven development：把品質從「死文件」變成可量化、可追蹤、可防漂移的迴路；補可量化最後一軸 |
| **v3** | 拆分 bounded specialists（research/sales/content） | 單一代理的 context 經常超限；任務類型間的規則衝突頻繁 |
| **v4** | Graph orchestration + 進階 checkpoint persistence | 任務間依賴複雜度超過線性拔分能處理的範圍 |

## 前端動態介面（本地觀看）

已提供最小版前端看板於 `frontend/`，包含：
- Task 清單瀏覽
- Logs 儀表板
- Decision Timeline（可點擊展開）

資料來源唯一化於 `frontend/data.json`，由 `scripts/generate_frontend_manifest.py` 在產生階段以 PyYAML 解析下列來源後序列化：
- `tasks/20*.yaml`
- `logs/runs/*.yaml`
- `memory/active_projects/*/decisions/*.yaml`（多 project）

CI 會跑 `python3 scripts/generate_frontend_manifest.py --check`，若 `frontend/data.json` 與檔案系統實況有漂移即失敗。

### 啟動方式

在 repo 根目錄執行（一鍵啟動，含自動重新產生 `data.json`）：

```bash
scripts/run_frontend.sh
```

如需自訂 port：

```bash
scripts/run_frontend.sh 9000
```

如需跳過 `data.json` 重新產生（加速本地反覆測試）：

```bash
scripts/run_frontend.sh --no-generate
```

也可同時指定 port：

```bash
scripts/run_frontend.sh --no-generate 9000
```

查看完整參數說明：

```bash
scripts/run_frontend.sh --help
```

查看腳本版本與最後更新日期：

```bash
scripts/run_frontend.sh --version
```

開啟：`http://localhost:8000/frontend/index.html`（或對應自訂 port）

### 漂移檢查

新增、刪除或重新命名 `tasks/`、`logs/runs/`、`memory/active_projects/*/decisions/` 下的 YAML 後，請重新執行：

```bash
python3 scripts/generate_frontend_manifest.py
```

並把更新後的 `frontend/data.json` 一起 commit。CI 會驗證二者一致。
