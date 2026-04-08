# Agent Harness v1 — 一人公司可控版 Agent 作業系統

## 這是什麼

一人公司用的 Agent 執行框架，跑在 Claude Code CLI 上。
核心目標：**可恢復、可審核、可量化**。

不是多代理平台，不是 AI 自動化全套。
是一個讓 Claude 穩定幫你做事、不失控的結構。

## 架構：三平面、十一模組

```
控制平面（Control）
├── 1. Interface         Claude Code CLI
├── 2. Task Card         tasks/*.yaml — 任務定義
└── 3. Planner/Router    system/ROUTING_RULES.md — skill 路由

執行平面（Execution）
├── 4. Context Manager   CLAUDE.md context 規則 — 上下文組裝
├── 5. Skill Executor    skills/[type]/SKILL.md — 技能執行
├── 6. Tool Executor     allowed_tools 白名單 — 工具執行
├── 7. Verifier          四層驗證（schema→規則→完成→風險）
└── 8. Checkpoint        git commit — 進度保存

治理平面（Governance）
├── 9.  Permission       system/PERMISSIONS.yaml — 權限策略
├── 10. Cost Policy      system/COST_POLICY.md — 成本控制
└── 11. Audit Log        logs/AUDIT_LOG.md — 稽核紀錄
```

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
│   └── ROUTING_RULES.md       ← Skill 路由規則
├── tasks/
│   ├── TASK_CARD_TEMPLATE.yaml
│   └── examples/              ← 填好的範例
├── skills/
│   ├── research/SKILL.md      ← 研究分析
│   ├── writing/SKILL.md       ← 撰寫產出
│   ├── ops/SKILL.md           ← 營運操作
│   └── review/SKILL.md        ← 品質審查
├── memory/
│   ├── README.md              ← 記憶使用規則
│   ├── user_prefs.md          ← 使用者偏好
│   └── active_projects/       ← 進行中專案 context
├── logs/
│   ├── AUDIT_LOG.md           ← 稽核紀錄
│   ├── runs/                  ← 執行紀錄
│   ├── approvals/             ← 核准紀錄
│   └── errors/                ← 錯誤紀錄
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

### 快速一致性檢查（建議）
```bash
python - <<'PY'
import re
from pathlib import Path

allowed = {"research", "writing", "ops", "review"}
for p in [Path("tasks/TASK_CARD_TEMPLATE.yaml"), Path("tasks/examples/2026-04-03_market-research-example.yaml")]:
    text = p.read_text()
    m = re.search(r"^skill_type:.*$", text, flags=re.MULTILINE)
    if not m:
        raise SystemExit(f"{p} 缺少 skill_type 欄位")
    raw = m.group(0).split(":", 1)[1]
    raw = raw.split("#", 1)[0].strip()
    skill_type = raw.strip('"').strip("'")
    if skill_type and skill_type not in allowed:
        raise SystemExit(f"{p} skill_type 不在允許清單: {skill_type}")
print("task card skill_type check passed")
PY
```

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
| **v1（現在）** | 單核心代理 + Task Card + Checkpoint + Verifier + Audit | — |
| **v2** | 拆分 bounded specialists（research/sales/content） | 單一代理的 context 經常超限；任務類型間的規則衝突頻繁 |
| **v3** | Graph orchestration + 進階 checkpoint persistence | 任務間依賴複雜度超過線性拆分能處理的範圍 |
