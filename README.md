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

## 最新模型流程（建議預設）

在既有三平面結構上，執行順序建議固定為：

1. Observe/觀察（O：讀 Task Card 與限制）
2. Plan/規劃（P：先拆解再動作）
3. Act/執行（A：最小必要工具呼叫）
4. Verify/驗證（V：schema → 規則 → 完成 → 風險）
5. Reflect/修正（R：只修缺口，不整段重做）
6. Checkpoint/檢查點（C：關鍵節點 commit）

這個流程可降低迴圈重試、控制 token 成本，並讓審核點更穩定。

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
填入 `goal`、`definition_of_done`、`skill_type`。參考 `tasks/examples/` 下的範例。

### 2. 執行
在 Claude Code CLI 中 `cd ~/Projects/agent-harness`，Claude 會自動讀取 CLAUDE.md。
告訴 Claude：「執行 tasks/2026-04-03_你的任務.yaml」。

### 3. 追蹤
- 執行紀錄：`logs/AUDIT_LOG.md`
- 進度快照：`git log --oneline`
- 草稿輸出：`outputs/drafts/`

## 導入計畫

### 第 1 週：跑通骨架
- 用 `research_skill` 和 `review_skill` 跑 1 條完整任務流
- 確認 Task Card → 執行 → Checkpoint → 驗證 → 輸出 的流程順暢

### 第 2 週：補執行閉環
- 啟用 `writing_skill` 和 `ops_skill`
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
