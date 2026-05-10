# Governance Metrics — 2026-05

- 採集時間：2026-05-09
- 來源：plan §5.3
- 警訊處理：alert → 開 retro task；warn → 下次 retro 帶討論

## 摘要
- 整體狀態：**✅ OK**（ok=4 / warn=0 / alert=0）

## 指標明細

| ID | 名稱 | current | threshold | status |
|----|------|---------|-----------|:------:|
| M1 | 月 Task Card 建立數 | 2026-04=16, 2026-05=11 | 連續 2 個月 < 3 張 → alert；單月 < 3 張 → warn | ✅ ok |
| M2 | outputs/drafts:reports 比例 | 19/2 = 9.50 | < 1:1 → alert（草稿流程被繞過） | ✅ ok |
| M3 | audit log 覆蓋率（status ∈ {review, done, failed, partial}） | 24/26 = 92.3% | < 80% → alert；< 90% → warn | ✅ ok |
| M4 | Claude Code 原生功能重疊度（人工評估） | 30% (reviewed 2026-05-09) | > 50% → alert；40-50% → warn | ✅ ok |

## 詳細資料（debug）
```json
[
  {
    "id": "M1",
    "name": "月 Task Card 建立數",
    "current": "2026-04=16, 2026-05=11",
    "threshold": "連續 2 個月 < 3 張 → alert；單月 < 3 張 → warn",
    "status": "ok",
    "details": {
      "counts_by_month": {
        "2026-04": 16,
        "2026-05": 11
      },
      "recent": [
        [
          "2026-04",
          16
        ],
        [
          "2026-05",
          11
        ]
      ],
      "below_threshold_months": []
    }
  },
  {
    "id": "M2",
    "name": "outputs/drafts:reports 比例",
    "current": "19/2 = 9.50",
    "threshold": "< 1:1 → alert（草稿流程被繞過）",
    "status": "ok",
    "details": {
      "drafts": 19,
      "reports": 2,
      "ratio": 9.5
    }
  },
  {
    "id": "M3",
    "name": "audit log 覆蓋率（status ∈ {review, done, failed, partial}）",
    "current": "24/26 = 92.3%",
    "threshold": "< 80% → alert；< 90% → warn",
    "status": "ok",
    "details": {
      "completed_total": 26,
      "with_audit": 24,
      "missing_task_ids": [
        "20260409-001",
        "20260415-A01"
      ],
      "coverage_pct": 92.3
    }
  },
  {
    "id": "M4",
    "name": "Claude Code 原生功能重疊度（人工評估）",
    "current": "30% (reviewed 2026-05-09)",
    "threshold": "> 50% → alert；40-50% → warn",
    "status": "ok",
    "details": {
      "aggregate_pct": 30,
      "reviewed_on": "2026-05-09",
      "modules": [
        {
          "name": "Skill Executor (skills/)",
          "overlap_pct": 85,
          "native": "Claude Code Skills（/skill、自動載入）",
          "evidence": "本 session Skill tool + skills 列表自動列出；N3 PoC 已建立 .claude/skills/research symlink"
        },
        {
          "name": "Planner/Router (ROUTING_RULES.md)",
          "overlap_pct": 70,
          "native": "Skill 自動路由 + 子代理",
          "evidence": "原生會根據 skill description 觸發；表格式手動路由屬冗餘"
        },
        {
          "name": "Tool Executor (allowed_tools)",
          "overlap_pct": 80,
          "native": ".claude/settings.json permissions + PreToolUse",
          "evidence": "Phase A 已有 permissions_guard.py 把 deny 抬到 runtime"
        },
        {
          "name": "Permission (PERMISSIONS.yaml)",
          "overlap_pct": 75,
          "native": "settings.json（allow/ask/deny）",
          "evidence": "兩者語意幾乎 1:1，僅缺風險等級欄位"
        },
        {
          "name": "Agent Context (AGENT_CONTEXT.yaml)",
          "overlap_pct": 60,
          "native": "CLAUDE.md / 系統 prompt",
          "evidence": "內容 ≈ 自我描述段落，與 CLAUDE.md 互相重複"
        },
        {
          "name": "Context Manager (CLAUDE.md 規則段)",
          "overlap_pct": 50,
          "native": "CLAUDE.md 自動載入、自動壓縮",
          "evidence": "「20 輪壓縮」原生已具；token 上限規則仍需 CI 護欄"
        },
        {
          "name": "Checkpoint (git commit)",
          "overlap_pct": 0,
          "native": "—",
          "evidence": "本來就是 git 慣例"
        },
        {
          "name": "Cost Policy (行為規則段)",
          "overlap_pct": 40,
          "native": "平台 dashboard + 模型路由",
          "evidence": "校準資料表是真資產；其餘段落多為提醒"
        },
        {
          "name": "Interface",
          "overlap_pct": 100,
          "native": "Claude Code CLI / web / IDE",
          "evidence": "屬於 runtime，不是模組"
        }
      ]
    }
  }
]
```

## 建議動作
- 全部 ok：保持現狀，下個月再採集

