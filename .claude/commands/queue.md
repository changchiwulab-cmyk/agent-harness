---
description: 未結卡片盤點與治理指標，輸出 keep/merge/kill 分流建議（不改任何卡片狀態）
argument-hint: [可選：只看某個狀態，如 review]
allowed-tools: Bash(python3 scripts/governance_metrics.py:*), Bash(grep:*), Bash(ls:*), Bash(python3 scripts/check_native_overlap_freshness.py:*), Read, Glob, Grep
---

# 未結卡片盤點

篩選條件：$ARGUMENTS（留空則看全部 status ∉ {done, failed} 的卡）

## 為什麼有這支指令

本專案的瓶頸是**人工審核**，不是 agent 能力（20260711-A01 已驗證結論）。
未結卡片佇列無上限成長時，加再多治理機制都只會讓瓶頸更緊。
這支指令的用途是讓佇列**定期見底**，不是再產出一份待辦。

## 步驟

1. **治理指標**：`python3 scripts/governance_metrics.py`
   （M1 建卡數／M2 drafts:reports 比／M3 audit 覆蓋率／M4 原生重疊度）。
   任何 alert → 開 retro task；warn → 下次 retro 帶討論。

2. **盤點未結卡**：列出 `tasks/20*.yaml` 中 status ∉ {done, failed} 的卡，
   附 `task_id`、status、`risk_level`、建立日期、**停留天數**（WIP aging）。

3. **逐張分流**，每張標一個並附一句理由：

   | 判定 | 準則 |
   |---|---|
   | **keep** | 真正降低人工成本，或修補已驗證存在的缺陷 |
   | **merge** | 與其他卡或已完成工作重疊，應併入而非獨立推進 |
   | **kill** | 加的是「再一道 gate」但瓶頸在人工審核 → 淨負貢獻；或前提已不成立 |

4. **輸出建議，不改狀態**。實際改 status 需使用者點頭
   （先例：`tasks/2026-07-12_clear-review-queue.yaml`，該卡把 17 張 review 收斂到 0）。

## 完成後

回報：未結總數、各狀態分佈、最久停留天數、keep/merge/kill 各幾張、建議先動哪 1–2 張。
