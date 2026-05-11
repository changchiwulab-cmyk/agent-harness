# N7：評估啟用 Claude Code 原生 Memory

- Task: `20260509-N07`
- Date: 2026-05-09
- Skill: analysis
- Status: draft（risk_level=low）
- 上游：A01（已被使用者接受）；N3 PoC（Skills 原生路由經驗）；plan §3.5 / §4.1 趨勢 B

> 本卡只做評估，不啟用、不改 PERMISSIONS.yaml、不刪 memory/。

---

## 0. 結論一句話

> **Conditional-Go**：可啟用，但須在 4 條前置條件全部滿足後才動。最自然的路徑是比照 N3 Skills PoC 的 symlink 模式，把 `.claude/memory/agent-harness` 指向 `memory/active_projects/agent-harness/`，**不接管既有結構**。在條件滿足前，先產出 1 張 PoC 卡（PoC `M1`）做最小驗證即可。

---

## 1. 原生 Memory 機制摘要（事實）

| # | 項目 | 既知事實 | 來源 |
|---|------|---------|------|
| 1 | 觸發 | Claude Code session 啟動讀取 user-level（`~/.claude/`）+ project-level（`.claude/`）路徑下的 memory 內容；不需明確指令 | N3 PoC §2.1：「Skills 是 session 啟動階段讀取 `.claude/skills/`」，Memory 機制屬同一層 hook |
| 2 | 寫入 | Claude Code 提示寫入時須使用者明確確認（非自動寫入）；本框架對話中已多次出現「是否要將 X 寫入記憶？」的提問 | 本 session：使用者觀察行為；對應 `PERMISSIONS.yaml` 中 `write_long_term_memory` 走 ask 級的設計初衷 |
| 3 | Scope | user-level 跨專案、project-level 限該 repo；可同時並存 | Plan §3.5 引用「Anthropic、OpenAI 都在內建 long-term memory」 |
| 4 | 可控性 | 寫入路徑、檔名、scope 皆透明（純檔案）；可直接 git diff、可 rm 撤回 | 與 N3 PoC §1.2 symlink 設計同質：純檔案 = 可審計 |

> 備註：本評估未做工具實測，依據是 N3 PoC 累積的 Claude Code 行為觀察 + plan 引用。Go 後的 PoC 卡須補一次性實測（觸發、寫入提示、撤回）。

---

## 2. 與本框架 4 條硬規則的衝突點逐條檢視

| 硬規則 | 規則內容 | 與原生 Memory 衝突？ | 衝突細節 / 折衷 |
|---|---|:-:|---|
| #1 | 沒有 Task Card 不執行任務 | ✗ | 不衝突。Memory 是讀取側 context，不是「執行任務」。寫入側若要走 Task Card 也可以掛在「定期 retro」卡裡。 |
| #2 | 對外動作只產出草稿 | ✗ | 不衝突。Memory 是內部狀態，不是「對外動作」。但需確認原生 Memory 的儲存路徑是否會被 Claude Code 同步上雲——若是，須降級為 No-Go 或加額外條件。 |
| #3 | 連續失敗 3 次停下 | ✗ | 不衝突。Memory 與失敗計數正交。 |
| #4 | PERMISSIONS：`auto_write_memory` 在 deny | ⚠ **間接衝突** | 原生 Memory 寫入提示需人工確認，**符合 deny 的精神**（不自動）。但 PERMISSIONS.yaml 目前沒有「人工確認後寫入長期記憶」對應的 allow/ask 欄位；現況 `write_long_term_memory` 在 ask（§4.1 條件 3）。 |

→ **唯一需要補的是 PERMISSIONS.yaml 的詞彙**，不是規則衝突。

---

## 3. 三選一建議：**Conditional-Go**

### 3.1 為什麼不是 Go

直接 Go 的代價：
- 兩個 memory 系統並存（`memory/` 與原生 `.claude/memory/`）會同時增長，**雙寫漂移**——A01 §7.1 列為失敗模式 SPEC-04 的反面教材。
- 寫入策略尚未設計：哪些事該入 native、哪些該入 `memory/`？沒答案就動，後悔成本高。

### 3.2 為什麼不是 No-Go

純拒絕的代價：
- Plan §3.5 痛點實在：「每 session 從零開始」對效率有真實傷害。
- 趨勢 B（plan §4.1）已說：原生 Memory 將取代自定義 Memory。**長期不啟用 = 持續維護一個會被取代的東西**。
- 本 session 自己就遇過「上次 plan 不可讀 → A01 多次標 [待驗證]」（N1 對齊報告 §1）——這正是 Memory 該解的問題。

### 3.3 為什麼是 Conditional-Go（決策依據 ≥3）

1. **N3 已給出範式**：Skills 透過 `.claude/skills/research → ../../skills/research` symlink，避免雙寫、零搬遷、可逆。Memory 可比照這個模式（§4.2）。
2. **PERMISSIONS 補一個欄位即可**：`write_native_memory_with_confirm`（ask 級），不動 deny 的 `auto_write_memory`。語意清楚、改動小。
3. **可先以 1 張 PoC 卡做最小驗證**：類似 N3 是「先動一個 skill」，Memory 可以「先綁一個 namespace」（如 `agent-harness` 專案）。風險可控。
4. **Audit / Decision Log 結構不會被吃掉**：governance 三件位於 `memory/active_projects/agent-harness/decisions/`，是 YAML 結構化檔。原生 Memory 主要承載偏好與長文 context，不會接管這些檔。

---

## 4. 啟用條件清單（≥3 條）

> 任一條未滿足即降級為 No-Go 或停在 PoC。

| # | 條件 | 驗收方式 |
|---|------|---------|
| C1 | 寫入仍須人工確認 | PERMISSIONS.yaml 新增 `write_native_memory_with_confirm`（ask 級）；deny 中 `auto_write_memory` 不動 |
| C2 | 限定 namespace：原生 Memory 僅作 user-level 偏好 + 該 project 的 cross-session context；不接管 `memory/active_projects/agent-harness/decisions/` 與 `memory/active_projects/agent-harness/plans/` 的結構化 YAML | 用 symlink 方式：`.claude/memory/agent-harness → memory/active_projects/agent-harness/`（單一事實來源）；或限定原生只讀不寫該路徑 |
| C3 | 寫入路徑不出本機（非雲端同步） | PoC 階段驗證 Claude Code 實際儲存位置，若預設走雲端則需關閉同步或不啟用 |
| C4 | 與 governance plugin（N6）相容 | plugin v0.1.0 不應接管原生 Memory；N6 §1.2 已寫「不替代原生 Memory」可保留此條，無需新增約束 |

---

## 5. 與 N3 Skills PoC 的對位分析

### 5.1 比照表

| 維度 | N3（Skills） | M1 候補（Memory） |
|------|------------|------------------|
| 衝突風險 | 低（描述路由，無寫入） | 中（涉及寫入） |
| 設計手段 | symlink `.claude/skills/research → ../../skills/research` | symlink `.claude/memory/agent-harness → ../../memory/active_projects/agent-harness/` |
| 雙寫風險 | 0（symlink） | 0（symlink）— 前提是原生支援指向自訂路徑 |
| 可逆 | `rm .claude/skills/research` | `rm .claude/memory/agent-harness` |
| 對 v2 既有引用 | 不破壞（路徑不變） | 不破壞（`memory/` 仍為單一事實來源） |
| 風險殘留 | description 寫法影響路由準度（軟） | 寫入觸發頻率、儲存路徑（雲/本機）尚未實測 |

### 5.2 結論

**Memory 可比照 Skills 的 symlink 模式**，前提是 Claude Code 支援把 `.claude/memory/` 指向 repo 內路徑。如果原生 Memory 強制走 `~/.claude/memory/` 不能 symlink → 降級為「只用 user-level」+ 不接管 `memory/`。

---

## 6. 對 12+ drafts / 18+ audit 工作流的預期影響

### 6.1 正面（≥1）
- **Session-0 痛點修復**：使用者開新 session 不需重貼 plan / 不需重述「3 條硬規則」/ 不需重指 active_projects。對 18+ audit 的歷史脈絡 baseline 可達秒級熱啟動。
- **N1 類型對齊任務減少**：A01/W01 因 plan 不可讀而需要 N1 補對齊的情況，預期降至 0。

### 6.2 負面（≥1）
- **Context window 污染風險**：原生 Memory 預設可能載入過多 cross-session 內容，撞 CLAUDE.md+GLOBAL_RULES ≤3K token 預算。需要在 PoC 卡中加 token 量測 step。
- **雙系統認知負擔**：若 PoC 階段 namespace 沒切乾淨，使用者要記「這件事該寫 `memory/` 還是 native」。M1 卡 DoD 必須包含一條「寫入決策樹」單頁文件。

---

## 7. 後續候補 Task Card 草案

> 若使用者接受 Conditional-Go，可直接建立。

### 7.1 M1（建議優先）— Memory PoC：symlink + namespace 試點
- **goal**：在 `agent-harness` namespace 試點原生 Memory（symlink 模式），實測觸發 / 寫入提示 / 撤回 / token 影響
- **DoD（草案）**：
  1. `.claude/memory/agent-harness` symlink 建立並可讀（或證明不能 symlink → 改 fallback）
  2. 一次寫入提示實測紀錄（觸發句、確認流程、結果）
  3. context budget 影響量測：CLAUDE.md+GLOBAL_RULES+memory ≤ 3K
  4. 雙系統決策樹單頁：哪些事入 native / 哪些入 `memory/`
  5. PERMISSIONS.yaml 草案 patch（新增 `write_native_memory_with_confirm`）
- **risk**：medium（涉及 PoC 寫入，但 namespace 受限）
- **預估 max_tool_calls**：8

### 7.2 M2（M1 通過後）— PERMISSIONS.yaml + plan §3.5 收斂
- **goal**：把 M1 結論寫入 PERMISSIONS.yaml + 更新 plan §3.5 為已落地
- **DoD（草案）**：
  1. PERMISSIONS.yaml 新欄位
  2. plan §3.5 註記「2026-05-XX M1 PoC 驗證後啟用」
  3. README / `memory/README.md` 更新 native 與 `memory/` 邊界說明
- **risk**：medium（modify_system_rules）
- **預估 max_tool_calls**：6

---

## 8. 待驗證

- 原生 Memory 是否支援 symlink 至 repo 內路徑（決定 M1 §7.1 條件 1 的可行性）
- 原生 Memory 預設儲存位置是否走雲同步（C3 驗證）
- 觸發頻率：是 session-start 一次載入，還是動態 retrieve（影響 token 預算規畫）

> 三項皆於 M1 PoC 內實測後解。本卡不做工具實測。

---

## 9. DoD 自評（7 條）

| # | 條件 | 對應段 | 結果 |
|---|------|--------|:----:|
| 1 | 原生 Memory 機制摘要 ≥3 條經驗事實或來源引用 | §1 表 4 列 + 來源 | ✅ |
| 2 | 與本框架 4 條硬規則的衝突點逐條檢視 | §2 4 列 | ✅ |
| 3 | 三選一明確建議（Go / No-Go / Conditional-Go），且依據 ≥3 條 | §3.3（4 條依據） | ✅ |
| 4 | 若 Conditional-Go：≥3 條啟用條件 | §4 表（C1-C4，4 條） | ✅ |
| 5 | 與 N3 Skills PoC 的對位分析 | §5 比照表 + 結論 | ✅ |
| 6 | 對 12+ drafts / 18+ audit 工作流的影響（正/負面各 ≥1） | §6.1 / §6.2 | ✅ |
| 7 | 後續候補 task：1-2 張 Task Card 草案標題 | §7.1 M1 + §7.2 M2 | ✅ |

→ 7/7 通過。risk_level=low → 草稿留在 `outputs/drafts/`。
