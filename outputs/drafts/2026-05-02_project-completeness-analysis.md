# Agent Harness 專案完整度分析 — 第一性原理檢驗

- 日期：2026-05-02
- 作者：Claude (Opus 4.7) / 對話分析
- 範圍：對 v2 現有結構（CLAUDE.md / system/ / tasks/ / skills/ / logs/ / outputs/ / frontend/）進行第一性原理拆解
- 狀態：草稿（待人工確認後決定是否晉升 reports/）

---

## 1. 第一性原理：本系統存在的本質目的

從最根本拆解，這個 harness 存在是為了補三個洞：

1. **LLM 不穩定** — 缺穩定目標、邊界、權限意識、自我驗證
2. **錯誤成本應該便宜** — 可恢復、可審核 是「敢把任務交給 agent」的前提
3. **人能信任地把事丟給 agent** — 信任 = 可預測 × 可恢復 × 可審核

要滿足以上三點，最少需要的元件：

| 元件 | 對應檔案 | 本質目的 |
|------|---------|---------|
| 任務定義 | `tasks/*.yaml` + `TASK_CARD_TEMPLATE.yaml` | 否則 agent 不知道做什麼 |
| 邊界 | `system/PERMISSIONS.yaml` | 否則 agent 不知道能不能做 |
| 驗證 | `system/GATE_POLICY.yaml` | 否則 agent 不知道做完了沒 |
| 紀錄 | `logs/AUDIT_LOG.md` + `logs/runs/` | 否則人類無法事後檢視 |
| 恢復 | `git checkpoint` + `outputs/drafts/` | 否則錯了無法回頭 |

**結論：五件元件檔案上都齊全，但多數只停在「文字宣告」這一層，沒有 enforcement、沒有自動量測、沒有實證樣本支撐。**

---

## 2. 缺點清單（依嚴重性排序）

### ① 規格 ≠ 執行（Spec-Execution Gap）— 最嚴重

- `PERMISSIONS.yaml`、`GATE_POLICY.yaml`、`APPROVAL_POLICY.yaml` 全是「LLM 自我約束」的自然語言指令
- 只有 `validate_task_card.py` + `check_spec_consistency.rb` + `check_context_budget.rb` 是真正的硬檢查
- **沒有 runtime hook**：deny 清單裡的「shell_delete / send_email」如果 LLM 自己選擇違反，沒有 pre-flight 攔截
- 第一性原理：**規則不靠執行者自律生效**，否則只是榮譽制

### ② 實證樣本貧乏（Empirical Vacuum）

- `logs/errors/` 僅 1 筆（rate limit，2026-04-04）
- `logs/runs/` 僅 1 筆（D006 收斂窄範圍後幾乎不會新增）
- COST_POLICY 校準係數樣本數：research(2)、writing(1)、ops(2)、review(2)、analysis(0)
- `FAILURE_TAXONOMY.yaml` 14 種模式是引用文獻分類，不是專案實證
- 第一性原理：**整套治理建在 ~15 筆任務上**。樣本不足以校準，但已凍結為規範

### ③ 觀測性不對稱（Observability Asymmetry）

- `AUDIT_LOG.md` 是 agent 手寫的 — agent 對自己評分
- 沒有自動 metric 抽取（耗時、token、retry、approval 次數）
- 前端 `data.json` 只是把 YAML 重新序列化，不是運算後的指標
- 第一性原理：**無法測量就無法改善**。手寫紀錄偏向 agent 自我認知，非客觀執行真相

### ④ 學習迴路是開環的

- Retro 流程存在，但觸發靠人記得（5 任務或每週）
- 校準係數算出來了，但 Task Card 創建時不會自動套用，得人類手動查表
- 失敗分類沒有 frequency counter
- 第一性原理：學習系統 = measure → diagnose → adjust → measure。目前缺自動 adjust 環節

### ⑤ 單代理架構的天花板

- 所有 context 塞給同一個 LLM
- `skills/` 只是 prompt 區隔，不是執行隔離
- 3K + 1.5K context 硬限制是症狀補丁，不是解法
- README 已寫 v3 升級條件「context 經常超限 / 規則衝突頻繁」，但**沒有量測這兩件事**，永遠不會自動觸發
- 第一性原理：不同性質工作需要不同 context 邊界，混在一個 agent 必然衝突

### ⑥ HITL 成為瓶頸

- 修改 skills/、system/、memory/、寫 reports 全要 ask
- 批准無 timeout（永遠等待）
- 沒有批次審查、沒有信任分級
- 第一性原理：**人成為吞吐瓶頸**，且沒有機制隨歷史紀錄逐步降低批准粒度（你已把 create_task_card 從 ask 升 allow 是好例子，但這是手動做的）

### ⑦ 前端只是裝飾

- `frontend/` 唯讀展示，無控制能力
- 不能在前端建 Task Card、批准草稿、看到「現在 agent 卡在哪」
- 第一性原理：dashboard 應是 control surface，不只是 view

### ⑧ 沒有 e2e 流程驗證

- CI 只跑靜態檢查（YAML schema、目錄存在、context budget）
- 沒有「跑一條 dummy Task Card 走完所有 gate」的 smoke test
- 第一性原理：規格存在 ≠ 規格被遵守

### ⑨ 成本控制是建議值不是硬上限

- `max_tool_calls` / `max_retries` / token 上限都是 self-policed
- 沒有 budget kill switch（達到上限自動終止）
- 第一性原理：**失控成本需要外部 enforcement**，不能靠 agent 自我節制

### ⑩ 跨 session handoff 仰賴 git log

- 沒有「上次停在哪、下一步是什麼」的結構化 resume point
- 對長任務不友善
- 第一性原理：分散式系統（含跨 session）需要可靠 checkpoint，目前只有人工 + commit log

---

## 3. 改善計畫（三階段，依槓桿率排序）

### Phase A — 補硬 enforcement 與觀測（1–2 週，槓桿最高）

| # | 動作 | 解決缺點 | 風險 |
|---|------|---------|------|
| A1 | 加 Claude Code `PreToolUse` hook：在 Bash/Edit/Write 前比對 `PERMISSIONS.yaml` deny 清單 | ① | low |
| A2 | `AUDIT_LOG.md` 改由 script 從 Task Card + git log 推導生成（人寫降為人補 notes） | ③ | low |
| A3 | 加 e2e smoke test：CI 跑一條 dummy Task Card，斷言 4 個 gate 都被觸發、輸出落到 drafts/ | ⑧ | low |
| A4 | `max_tool_calls` 由 SessionStart hook 注入硬計數器，達上限觸發 Stop 並寫 error_log | ⑨ | medium |

### Phase B — 閉合學習迴路（3–4 週）

| # | 動作 | 解決缺點 | 風險 |
|---|------|---------|------|
| B1 | 從 audit log 自動算 metric → 寫 `frontend/data.json`：平均 token、retry 率、approval 等待時間 | ③④ | low |
| B2 | Task Card 創建時自動套用 calibration_factor（讀 COST_POLICY 表，調整 max_*） | ④ | low |
| B3 | 累積 5 筆任務由 Stop hook 自動印出 retro 提醒 | ④ | low |
| B4 | `FAILURE_TAXONOMY.yaml` 加 `observed_count`，每筆 error_log 引用一個 ID 自動 +1；半年清掉 count=0 的條目 | ② | medium |
| B5 | v3 升級條件量化：自動偵測「context 壓縮次數」「single-skill 任務跨 skill 工具呼叫」並計次 | ⑤ | medium |

### Phase C — 架構演進（5–8 週，視 B5 數據再決定）

| # | 動作 | 解決缺點 | 風險 |
|---|------|---------|------|
| C1 | 前端加最小 control surface：建立 Task Card 表單、批准草稿按鈕、中止 button（local server） | ⑦ | medium |
| C2 | HITL 信任分級：approval 連續 N 次同類 approve → 自動降級為 inline_confirm；再 N 次 → 提名為 allow（仍需人類點頭升級） | ⑥ | high |
| C3 | 跨 session resume：每次 session 結束寫 `state/last_checkpoint.yaml`（next_action / open_questions / partial_outputs） | ⑩ | medium |
| C4 | 視 B5 數據判斷是否分拆 sub-agent（Agent SDK 的 Task tool）— 如數據顯示沒衝突就不要做 | ⑤ | high |

---

## 4. 建議優先順序

從第一性原理看，**A1 + A2 + B1 + B4 是最高槓桿**：

- **A1** 把規則從「自律」變「外部 enforce」 — 解決最根本的信任問題
- **A2 + B1** 讓系統能客觀衡量自己 — 沒有這個，後面所有改進都是猜
- **B4** 把治理建在實證上而非文獻上 — 解決「規則建在 15 筆任務上」的脆弱性

C 階段（特別是 C4 多代理）**先別碰**。README 上 v3 升級條件寫得很對：「等量到的數據叫你升級再升」。目前數據量根本不到觸發點，提早拆只會增加維運面積。

---

## 5. 反向質疑（self-critique）

為避免分析本身落入「規則更多就更好」的陷阱，列出反向觀點：

- **不是所有缺點都該補。** 例如缺點⑩（跨 session handoff）若你實際上每個任務都在單一 session 完成，補了沒意義
- **enforcement 過頭會反噬。** A1 PreToolUse hook 若誤判太多，會打斷正常流程；需要 dry-run 階段
- **量測本身有成本。** B1 metric 自動化若每筆任務多花 30 秒分析，得不償失
- **校準係數 n=1~2 拿來決策本來就脆弱。** 不要過度相信 `calibration_factor` 的精度

---

## 6. 下一步

如人工確認此分析方向：

1. 拆 3 張 Task Card：`phase-a-enforcement-hooks` / `phase-b-metric-loop` / `phase-c-trust-gradient`
2. 先執行 Phase A，跑 2 週後檢驗 metric，再決定 B、C 是否啟動
3. 若 Phase A 數據顯示「enforcement 攔截事件 = 0」，代表 LLM 自律已足夠，可考慮拔掉 hook 簡化系統

---

**End of draft**
