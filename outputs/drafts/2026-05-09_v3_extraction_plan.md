# Harness v3 治理層抽出規劃

- Task: `20260509-A01`
- Date: 2026-05-09
- Skill: analysis
- Status: draft（risk_level=medium，需人工確認）

> 範圍說明：本文件僅做「規劃」，不動既有代碼或結構。目的是把 v2 的 16 模組逐項裁決，把與 Claude Code 原生重疊的部分砍除，把「治理三件 + 失敗分類學」抽成獨立可發布的治理層。
>
> Plan 對齊（2026-05-09 N1 補）：上游 plan 已歸檔至 `memory/active_projects/agent-harness/plans/ai-bubbly-mountain.md`，本卡與 plan §8.1 Task A 的對齊報告見 `outputs/drafts/2026-05-09_n01_plan-alignment.md`。原本的 `[待驗證 — 取決於 plan]` 多項已解，僅保留與外部規範相關者（Claude Code 原生 spec、Skills frontmatter 規範）。

---

## 1. 現況

### 1.1 規模快照
- v2 已運行約 2 個月（首筆 audit 2026-04-04，最後 2026-05-02）。
- Audit Log 本 PR 推送前共 **18 筆**任務（grep `^- task_id:` 扣除 1 筆格式範例）；本 PR 加 A01/W01/N3/N4/N1 共 5 筆 → **23 筆**。Plan §Context 與本卡 task card context 欄位的「30+」是 plan 撰寫時的概數，不準（plan 為歷史 snapshot 不更新；事實計數見此處）。
- `outputs/drafts/` 累積 12+ 草稿；`outputs/reports/` 已晉升 2 份（retro、token-calibration）。
- Decision Log 累積 6 筆（D001–D006）。
- 16 模組分布：control 4、execution 5、governance 7。

### 1.2 已落地的「強制力」清單
- `PreToolUse` hook（`scripts/permissions_guard.py`，Phase A）— 唯一 runtime 攔截。
- `spec-consistency` CI（schema、路徑、`completion_time`、frontend manifest 漂移）。
- `check_context_budget.rb` CI（CLAUDE.md+GLOBAL_RULES ≤3K token）。
- 其餘 16 模組皆為 prompt 約束 + 文件規範，無強制檢查。

### 1.3 結構性症狀
1. 強制力結構不對稱：~156 行 deny hook + 3 條 CI 檢查，對照 16 模組與數千行 system/* 規則 → 嚴重頭重腳輕。
2. 與 Claude Code 原生重疊：Skills、CLAUDE.md 自動載入、PreToolUse、Memory、subagent、SessionStart hook 皆已是 first-class，重疊估 ~30%（見 §4 表 A）。
3. 治理三件（Audit / Decision / DoD 契約）與失敗分類學不依賴「一個 Harness」存在，可獨立發布；目前被綁在框架內無法被別處用。

---

## 2. 診斷（從第一性原理）

| 提問 | v2 答案 | v3 應有答案 |
|------|--------|------------|
| 框架最不可替代的價值是什麼？ | 模組齊全、規則完整 | 治理思維（可恢復／可審計／可量化）+ DoD 契約 + 失敗分類學 |
| 哪些是「Claude Code 還沒做的」才該由我做？ | 沒區分 | 治理層；其餘交給原生 |
| Prompt 規則的有效性如何驗證？ | 幾乎無 | 全部要對應 CI 或 hook，不能只是文檔 |
| 模組越多越穩定嗎？ | 預設是 | 否；模組數與穩定性無正相關，與維護成本正相關 |

第一性原理結論：**砍冗餘 + 深化治理層**。框架自身應更薄、更小、更靠近 Claude Code 原生；治理層應更厚、更獨立、可被別人引用。

---

## 3. 去留判準（明文化）

| 判準 | 規則 |
|------|------|
| J1 | 與 Claude Code 原生功能重疊 ≥70% 且原生已穩定 → 砍 |
| J2 | 文檔長度 ≥100 行但對應 0 個自動化檢查 → 砍或大幅瘦身 |
| J3 | 治理屬性（Audit / Decision / DoD / Failure / Postmortem）且可獨立發布 → 抽出 |
| J4 | v2 留下、未來仍需要、但介面要重做以靠近原生 → 重構 |
| J5 | 留下的每一條規則必須能對應一個 enforcement 點（hook、CI、schema） → 否則砍 |

---

## 4. 模組逐項裁決

### 4.1 重疊度對照（與 Claude Code 原生功能）

> 表 A：依當前公開資料粗估，未做工具實測。

| v2 模組 | 對應原生功能 | 重疊度估計 | 證據 |
|---------|-------------|-----------|------|
| Skill Executor (skills/) | Claude Code Skills（`/skill`、自動載入） | ~85% | 本 session 已展示 `Skill` tool + skills 列表自動列出 |
| Planner/Router (ROUTING_RULES.md) | Skill 自動路由 + 子代理 | ~70% | 原生會根據 skill description 觸發；表格式手動路由屬冗餘 |
| Tool Executor (allowed_tools) | `.claude/settings.json` permissions + PreToolUse | ~80% | Phase A 已有 `permissions_guard.py` 把 deny 抬到 runtime |
| Permission (PERMISSIONS.yaml) | `settings.json`（allow/ask/deny） | ~75% | 兩者語意幾乎 1:1，僅缺風險等級欄位 |
| Agent Context (AGENT_CONTEXT.yaml) | CLAUDE.md / 系統 prompt | ~60% | 內容 ≈ 自我描述段落，與 CLAUDE.md 互相重複 |
| Context Manager（CLAUDE.md 規則段） | CLAUDE.md 自動載入、自動壓縮 | ~50% | 「20 輪壓縮」原生已具；token 上限規則仍需 CI 護欄 |
| Checkpoint (git commit) | 無原生對應 | 0% | 但本來就是 git 慣例，不需要設成「模組」 |
| Cost Policy（行為規則段） | 平台 dashboard + 模型路由 | ~40% | 校準資料表是真資產；其餘段落多為提醒 |
| Interface | Claude Code CLI / web / IDE | 100% | 屬於 runtime，不是我們的模組 |

非重疊（治理屬性，原生不做）：
- Task Card 的 `definition_of_done` 契約模式
- Decision Log（D001–D006 結構化決策追溯）
- Audit Log（任務後事實紀錄）
- Failure Taxonomy（14 類獨立可引用檔）
- Execution Log Schema（窄範圍 post-mortem）
- Gate Policy（四層驗證 + rollback）
- Approval Policy（draft_first / human_confirm 流程）

### 4.2 模組逐項裁決表

| # | 模組 | 裁決 | 理由 | v3 安置 |
|---|------|------|------|---------|
| 1 | Interface | 砍除 | 是 runtime 不是模組（J1） | 留在 README「環境說明」段，不再列為模組 |
| 2 | Task Card | 重構 | 治理思想骨幹；但欄位過多需瘦身 | 抽到治理層 plugin，必填欄位收斂為 `goal / definition_of_done / risk_level / allowed_tools / expected_output` |
| 3 | Planner/Router | 砍除 | 與原生 Skill 自動路由重疊（J1） | 路由邏輯交給 Skills；保留複合任務拆分原則一句話寫進 CLAUDE.md |
| 4 | Decision Log | 抽出 | 治理三件之一，獨立發布價值最高（J3） | 治理層 plugin 主元件 |
| 5 | Context Manager（CLAUDE.md 規則段） | 重構 | 一半已是原生行為（J4） | CLAUDE.md 只留 token 硬上限 + 三條硬規則；CI 護欄不變 |
| 6 | Skill Executor (skills/[type]/) | 砍除 | 與原生 Skills 重疊（J1） | 把 5 個 SKILL.md 改寫為原生 Skills 註冊；eval_examples 移到治理層的 evals/ |
| 7 | Tool Executor (allowed_tools 白名單) | 重構 | enforcement 已在 hook（J4） | Task Card 仍需 `allowed_tools` 欄位作為 hook 輸入；不再單列為「模組」 |
| 8 | Gate Verifier (GATE_POLICY.yaml) | 抽出 | DoD 契約的執行器，治理層核心（J3） | 治理層 plugin：`/gate-check` 指令 + Pre/PostToolUse hook |
| 9 | Checkpoint (git commit) | 砍除 | 是慣例不是模組（J2） | 留在 CLAUDE.md 一行慣例描述 |
| 10 | Agent Context | 砍除 | 與 CLAUDE.md 重複（J1, J2） | 內容併回 CLAUDE.md「邊界」段 |
| 11 | Permission | 重構 | 語意搬到 settings.json（J4） | `settings.json` 為事實來源；保留 `risk_level` 維度作為 plugin metadata |
| 12 | Approval Policy | 重構 | 邏輯併入 Decision Log + Task Card workflow（J4） | 由 plugin 觸發 `draft_first` / `human_confirm`，文件刪除 |
| 13 | Cost Policy | 重構 | 行為段重疊（J1）、校準資料是資產 | 校準資料保留為 `outputs/reports/token-calibration-v*.md`；行為規則收進 CLAUDE.md 三行 |
| 14 | Failure Taxonomy | 抽出 | 獨立可引用知識資產（J3） | 治理層 plugin：靜態 YAML + Decision Log 引用欄位 |
| 15 | Execution Log Schema | 抽出 | post-mortem 唯一紀錄結構（J3） | 治理層 plugin：`/run-log` 指令，僅 fail/partial/high-risk/多 checkpoint 觸發 |
| 16 | Audit Log | 抽出 | 治理三件之一（J3） | 治理層 plugin：`/audit` 指令 append-only，CI 檢查格式 |

統計：保留 0 / 砍除 5 / 抽出 6 / 重構 5。

> 「保留 0」反映一件事：v2 沒有任何模組同時滿足「不重疊 + 不該抽出 + 不需要重構」。這是健康訊號。

---

## 5. 抽出邊界：治理層獨立發布形態

### 5.1 候選形態評估

| 形態 | 優點 | 缺點 | 一人公司適配 |
|------|------|------|-------------|
| Claude Code Plugin | 距離使用情境最近、可掛 hooks/skills/slash | 綁定 Claude Code | 高 — 立即可用 |
| MCP Server | 跨 client（Claude.ai/Code/Desktop） | 需要 server runtime；初次設定門檻高 | 中 — 第二步才做 |
| Standalone CLI | 與 LLM 解耦，最廣泛適用 | 失去 Claude Code 內嵌的 hook 觸發機制 | 中 — 適合方法論發布 |

**建議排序**：Plugin（v3.0）→ Standalone CLI（v3.1，含 schema 與 validator）→ MCP Server（v3.2，視外部需求）。

### 5.2 治理層 plugin 邊界

```
agent-governance/
├── plugin.json                # Claude Code plugin manifest
├── skills/
│   └── governance/SKILL.md    # 引導使用者建立 Task Card / 寫 audit
├── commands/
│   ├── task-card.md           # /task-card 建立卡，含 DoD 強制
│   ├── audit.md               # /audit 寫一筆 audit log
│   ├── decision.md            # /decision 寫一筆 Decision Log
│   ├── run-log.md             # /run-log（窄範圍）
│   └── gate-check.md          # /gate-check 跑四層驗證
├── hooks/
│   ├── pre_tool_use.py        # 從 settings.json + Task Card.allowed_tools 攔截
│   └── post_task_use.py       # 完成後自動跑 gate-check
├── schemas/
│   ├── task_card.schema.yaml
│   ├── decision_log.schema.yaml
│   ├── execution_log.schema.yaml
│   └── failure_taxonomy.yaml  # 14 類靜態資料
├── validators/                # standalone CLI 入口
│   ├── validate_task_card.py
│   └── check_audit_format.py
└── README.md                  # 單頁說明：治理三件 + 失敗分類學
```

### 5.3 相依關係

- 上：Claude Code（plugin runtime）、`git`（checkpoint 慣例）。
- 下：純檔案系統，不依賴 DB/雲服務。
- 與 Harness 主 repo 解耦：plugin 不引用 `agent-harness/` 任何路徑；agent-harness 反過來成為 plugin 的 reference implementation。

---

## 6. v3 架構圖（取代 README 三平面十六模組圖）

```
┌─────────────────────────────────────────────────────────┐
│                  Claude Code (runtime)                  │
│   CLAUDE.md  │  settings.json  │  原生 Skills/Memory     │
└──────────────┬──────────────────────────┬───────────────┘
               │                          │
               ▼                          ▼
   ┌────────────────────┐    ┌──────────────────────────┐
   │  Task Card (薄)     │    │ Governance Plugin (厚)   │
   │  goal / DoD /       │◄──►│  ├── Decision Log        │
   │  risk / tools /     │    │  ├── Audit Log           │
   │  output             │    │  ├── Gate Policy         │
   └────────────────────┘    │  ├── Failure Taxonomy    │
                              │  ├── Execution Log (窄)  │
                              │  └── Pre/Post hooks      │
                              └──────────────────────────┘
                                          │
                                          ▼
                              outputs/drafts/, logs/, memory/
```

兩件事而已：薄 Task Card（契約）+ 厚 Governance Plugin（治理）。其他都靠 Claude Code 原生。

---

## 7. v2 → v3 遷移路徑

### 7.1 相容變更（不破壞既有任務卡）

| 變更 | 動作 | 影響 |
|------|------|------|
| skills/ 內 SKILL.md 改寫為原生 Skills 註冊 | 加 frontmatter，內容不變 | 既有 Task Card 的 `skill_type` 仍可用 |
| PERMISSIONS.yaml → settings.json | 雙寫一段時間，CI 校驗一致 | hook 改讀 settings.json |
| AGENT_CONTEXT.yaml 內容併回 CLAUDE.md | 留 stub 檔案 + 重定向註解 | Task Card 不再引用 |
| ROUTING_RULES.md 收斂為 1 段話寫進 CLAUDE.md | 留歸檔 | 路由由原生 Skills 接管 |

### 7.2 破壞性變更（需要明確版本切換）

| 變更 | 動作 | 緩解 |
|------|------|------|
| Approval Policy 文件刪除 | 邏輯併入 plugin command | 保留歷史版本於 archived/ |
| Task Card 必填欄位收斂 | 舊卡仍能跑（多餘欄位視為 optional），新卡走新 schema | validator 同時支援 v2/v3 schema 6 個月 |
| logs/runs/ 寫入觸發條件改為窄範圍 | 文檔已先收斂（D006），v3 hook 只在符合條件時自動寫 | 保持向後相容 |
| 16 模組編號制度廢除 | README 改寫 | 搜尋舊編號者導向新章節 |

### 7.3 階段性切換策略

| 階段 | 範圍 | 退出條件 |
|------|------|---------|
| v2.5（過渡）| 雙寫 settings.json；skills/ 加 frontmatter；AGENT_CONTEXT 併入 CLAUDE.md | 連續 5 張新 Task Card 在 v2.5 下無摩擦 |
| v3.0（治理層 plugin）| 治理 plugin 公開 release；agent-harness 主 repo 砍除已抽出模組 | plugin 通過 dogfood：本 repo 全用 plugin command 跑 |
| v3.1（CLI）| validators/ 釋出為 standalone | 至少 1 個外部使用者引用 |
| v3.2（MCP）| 視需求 | 出現第二個 client 場景 |

---

## 8. 風險點與緩解

### R1：使用者習慣斷裂
- 描述：26 張 Task Card 都用 v2 結構；CLAUDE.md 文案、README 三平面圖被引用於 retro 與 audit notes。突然切換會讓既有自動化（CI、frontend manifest、generate scripts）連鎖失效。
- 機率：高。
- 緩解：
  1. 強制 v2.5 過渡期，CI 同時校驗兩種 schema。
  2. validator 接受兩種 Task Card 形態 6 個月。
  3. README 保留「三平面十六模組（v2 archive）」連結，避免外部引用 404。

### R2：Claude Code 原生功能再變動
- 描述：Skills、settings.json schema、hook 名稱皆仍在演進；若 v3 過度貼近原生介面，原生變更直接打到我們。
- 機率：中。
- 緩解：
  1. plugin 內所有對原生 API 的呼叫集中到 `adapters/`，外部介面不變。
  2. failure taxonomy / decision log schema 與原生解耦，純 YAML，可被任何 client 讀。
  3. 設置「原生功能對照表」`docs/native-mapping.md`，每季校準。

### R3：治理層開源維護成本
- 描述：抽成 plugin 後若無人維護，會比留在內部還快過時；外部使用者期待文檔、issue 回應、版本相容。
- 機率：中（一人公司資源有限）。
- 緩解：
  1. v3.0 release 採「reference implementation」定位，不承諾 SLA。
  2. 主 repo 自身就是最大用戶（dogfood），保證至少一個活躍使用情境。
  3. 文件以「方法論先行、工具其次」為主軸（對應 W01 產出），降低使用者對工具完整度的依賴。

### R4：方法論／工具脫節（額外識別）
- 描述：W01 在做方法論大綱、A01 在做工具抽出，兩者若獨立演進，工具會比方法論先過時，方法論會比工具先脫離實作。
- 機率：低-中。
- 緩解：每章方法論必須對應一個治理層 plugin command 或 schema，沒有對應就不寫進方法論。

---

## 9. 高風險假設

- H1：Claude Code Skills 的自動路由能取代 ROUTING_RULES.md 的全部功能。`[待驗證]`
  - 不成立則：Planner/Router 改為「重構」而非「砍除」，加入 plugin。
- H2：settings.json 的 allow/ask/deny 與 risk_level 維度可正交組合。`[待驗證]`
  - 不成立則：Permission 改為「抽出」，plugin 自管 risk_level，hook 從 plugin 讀。
- H3：plugin 形態能承載 hook + skill + slash command 三件並存。`[待驗證 — 取決於 Claude Code plugin spec 當下能力]`
  - 不成立則：先做 standalone CLI + 文件，plugin 延後。

---

## 10. 待驗證

| 項目 | 驗證方式 | 狀態 |
|------|---------|------|
| Plan 檔 `ai-bubbly-mountain.md` §8.1 是否與本卡裁決一致 | 取得檔案後逐項 diff | ✅ 已解（N1 對齊報告：13/13 條 DoD 全 pass，A01 額外 over-deliver 2 條）|
| Audit Log 任務數準確值（plan §Context 寫 30+；非 README）| 直接讀檔重新計數 | ✅ 已解（N2：本 PR 前 18 筆，本 PR 後 23 筆）|
| 原生 Skills 的 frontmatter 規範與 SKILL.md 兼容性 | 在分支上做 1 個轉檔示範 | ✅ 已解（N3 PoC：frontmatter 解析通過，symlink 註冊建立）|
| Plugin 能否同時掛 hooks + skills + commands | 查官方 plugin 文件或試做最小範例 | 待 N4 後續真正建 plugin repo 時驗證 |

---

## 11. 建議下一步

1. 把本卡與 plan §8.1 對齊（取得 plan 檔案後 30 分鐘核對）。
2. 在分支上做「skills/research/SKILL.md → 原生 Skills 註冊」一個 PoC（4 小時內）。
3. 起草治理 plugin 的 manifest skeleton（不寫實作，只定 commands 介面）。
4. W01（方法論大綱）依本卡的「保留／抽出」清單寫，確保不把該砍的工程細節包裝成方法論。

---

## 附錄 A：v3 模組清單（最終）

| 編號 | 模組 | 形態 | 來源 |
|------|------|------|------|
| G1 | Task Card（薄）| schema + plugin command | v2 #2 重構 |
| G2 | Decision Log | plugin command + schema | v2 #4 抽出 |
| G3 | Audit Log | plugin command + append-only file | v2 #16 抽出 |
| G4 | Gate Policy | plugin command + Pre/PostToolUse hook | v2 #8 抽出 |
| G5 | Failure Taxonomy | 靜態 YAML + decision log 引用欄位 | v2 #14 抽出 |
| G6 | Execution Log（窄）| plugin command（fail/partial/high-risk/多 checkpoint） | v2 #15 抽出 |
| R1 | CLAUDE.md（瘦身）| 三條硬規則 + 三條 token 上限 + 一段路由 + 一段 checkpoint 慣例 | v2 #5/#9/#10/#3 合併重構 |
| R2 | settings.json | 原生 permissions（取代 PERMISSIONS.yaml） | v2 #11 重構 |
| R3 | scripts/permissions_guard.py | hook，從 settings.json + Task Card.allowed_tools 取規則 | v2 #7 重構 |
| R4 | outputs/reports/token-calibration-v*.md | 仍是治理資產，但不再是「policy」文件 | v2 #13 重構 |

> 7 件（4 個治理 + 3 個重構）取代 v2 的 16 模組。
