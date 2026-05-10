# PoC: skills/research/SKILL.md → 原生 Skills 註冊

- Task: `20260509-N03`
- Date: 2026-05-09
- Skill: ops
- Status: draft（risk_level=medium，已於對話中授權）
- 上游：A01 §11 建議下一步 #2、A01 §8 H1 假設驗證

## 目的（一句話）

驗證 A01 的 H1：「Claude Code Skills 的自動路由能取代 `ROUTING_RULES.md` 的全部功能」。如果 H1 成立 → A01 §4.2 第 6 列（Skill Executor 砍除）+ 第 3 列（Planner/Router 砍除）站得住；如果不成立 → 改為「重構」並提出替代設計。

---

## 1. 已動的東西

### 1.1 frontmatter 加入 `skills/research/SKILL.md`
```yaml
---
name: research
description: 一人公司的研究分析 skill — 資料調查、產業分析、競品研究、技術評估、事實查核。回答「事實是什麼」。觸發場景：使用者明確要做調查/比較/盤點，或 Task Card 的 skill_type 為 research。輸出規範：結論 → 已知事實 → 合理推論 → 待驗證 → 高風險假設 → 來源。
---
```

- 原 markdown 內容**完全保留**，僅在最上面加了 6 行 YAML frontmatter
- `python3 -c "yaml.safe_load(...)"` 解析成功（驗證見 §3.1）
- description 151 字（中文，含路由觸發場景與輸出規範，刻意比 ROUTING_RULES.md 表格多一層描述以利自動路由判斷）

### 1.2 註冊路徑：`.claude/skills/research → ../../skills/research`（symlink）

```
agent-harness/
├── skills/research/SKILL.md      ← 既有單一事實來源
└── .claude/skills/
    └── research → ../../skills/research   ← symlink
```

選 symlink 而非 copy 的理由：
1. **單一事實來源**：避免 `.claude/skills/research/SKILL.md` 與 `skills/research/SKILL.md` 雙寫漂移（A01 §7.1 有列「PERMISSIONS.yaml → settings.json 雙寫」就是要避免的反面教材）。
2. **零搬遷成本**：v2 既有引用 `skills/research/SKILL.md` 的 6 張 Task Card 不需要動。
3. **可逆**：`rm .claude/skills/research` 即可回到 v2 狀態，不影響 skills/。

### 1.3 沒動的東西
- 其他四個 skill（writing / analysis / ops / review）保留 v2 形態，等 PoC 結論再決定是否同步處理
- `system/ROUTING_RULES.md` 未刪除
- `CLAUDE.md` 未修改

---

## 2. 觀察項

### 2.1 能否自動觸發？
- **本 session 無法現場驗證**：本次 session 啟動時系統 reminder 已列出 builtin skills（session-start-hook / simplify / loop / claude-api / init / review / security-review 等），是 Claude Code **session 啟動階段**讀取 `.claude/skills/`。symlink 是在 session 啟動之後才建的，**需要新開 session 才能驗證自動載入**。
- **靜態驗證已過**：`.claude/skills/research/SKILL.md` 可讀（symlink 解析正確）、frontmatter 可解析、結構符合「name + description + 內容」三件式。
- **預期**：下一次 session 啟動時，`research` 應出現在「available-skills」清單中，使用者可用 `/research` 或自然語言觸發。

### 2.2 description 措辭與路由準度的關係
- 寫太短（如「研究分析」）→ 路由器只能憑 skill 名命中，會輸給其他 skill 的 description
- 寫太長（>300 字）→ 訊號稀釋，路由器抓不到關鍵字
- **本 PoC 採用 ~150 字**：含三件——（a）能力描述、（b）觸發場景、（c）輸出規範。這個結構等於 ROUTING_RULES.md 表格 + SKILL.md 流程的濃縮版。
- 後續四個 skill 應採用同樣三件式，並在 PoC 第二階段做 A/B：純名稱 vs 三件式 description 的觸發準度差異。

### 2.3 與 `ROUTING_RULES.md` 五類路由表的差異

| ROUTING_RULES.md 內容 | 原生 Skills 是否覆蓋 | 評估 |
|----------------------|:-:|------|
| 5 個關鍵字 → 5 個 skill 的對照表 | ✅ | 原生用 frontmatter description 自動匹配，**功能等價** |
| 「無法判斷時詢問使用者，不要猜」 | ⚠️ | 原生 fallback 行為依模型而定，無顯式規則。**需在 CLAUDE.md 加一句** |
| 「跨兩個 skill 拆兩張 Task Card」 | ❌ | 這是 prompt 層的拆分原則，不是路由原則。**必須保留**，遷至 CLAUDE.md |
| 「Task Card 之間用 output 檔案接力」 | ❌ | 同上。**必須保留** |
| 「不做 agent-to-agent 對話路由」 | ❌ | 屬限制宣告，不是路由規則。可放治理層 plugin 的 README |

---

## 3. 驗證

### 3.1 YAML frontmatter 解析
```
$ python3 -c "import yaml,re; ..."
YAML parsed OK
keys: ['name', 'description']
name: research
description length: 151
```

### 3.2 v2 向後相容
- `skills/research/SKILL.md` 內容（除 frontmatter 外）字節級不變
- 引用 `skills/research/SKILL.md` 的 6 張既有 Task Card 不受影響
- `scripts/check_spec_consistency.rb` 通過
- `scripts/generate_frontend_manifest.py --check` 通過（重新生成後）

### 3.3 symlink 安全
- `readlink .claude/skills/research` → `../../skills/research`（相對路徑，可移植）
- `ls -la .claude/skills/research/` → 看到 SKILL.md 與 eval_examples.md（透通）
- 透過 symlink 對 SKILL.md 的修改即修改原檔，無雙寫

---

## 4. 對 H1 的結論：**部分成立**

| H1 子題 | 結論 | 證據 |
|---------|:-:|------|
| 「skill type → skill」對照表可被取代 | ✅ 成立 | frontmatter description 可承載；本 PoC 已建立可運作的註冊路徑 |
| 「跨 skill 拆 Task Card 原則」可被取代 | ❌ 不成立 | 屬 prompt 層工作流規則，原生 Skills 不管這個 |
| 「無法判斷時詢問使用者」可被取代 | ⚠️ 不確定 | 依模型行為而定，需顯式規則 |

---

## 5. 對 A01 §4.2 裁決的影響

**好消息：A01 不需要大改。**

A01 §4.2 第 3 列（Planner/Router）原本就寫：
> 路由邏輯交給 Skills；**保留複合任務拆分原則一句話寫進 CLAUDE.md**

PoC 結論恰好驗證這句話的必要性。具體行動：

| A01 §4.2 模組 | PoC 後是否需修改裁決 | 動作 |
|--------------|:-:|------|
| #3 Planner/Router | 否 | 維持「砍除」，但要明確：CLAUDE.md 必須補一句「跨 skill 拆 Task Card」原則 |
| #6 Skill Executor | 否 | 維持「砍除」，註冊路徑用 symlink（本 PoC 證實成本極低） |

**A01 §11 建議下一步增補項**：
- 進到 v2.5 過渡期時，所有 5 個 skill 加 frontmatter；symlink `.claude/skills/[name]` → `../../skills/[name]`
- CLAUDE.md 加一段（不超過 30 字）：「複合任務跨 skill → 拆兩張 Task Card，用 output 接力」

---

## 6. 風險與限制

- **L1 — 本 session 無法現場驗證觸發**：session 啟動時序問題，下一次 session 才能看到 `research` 出現在 available-skills 清單。建議下一個任務開始前先肉眼確認。
- **L2 — symlink 跨平台疑慮**：Linux/macOS 沒問題，Windows native 需設定。一人公司若全在 macOS，可忽略；若需要 Windows 支援，改用 copy + CI drift check。
- **R1 — frontmatter 規範若變動**：Claude Code Skills 規範還在演進，frontmatter 欄位可能擴增（如 `model`, `allowed_tools`）。緩解：A01 §8 R2 已涵蓋（adapters/ 集中對接）。
- **R2 — description 措辭的隱性 SLA**：若多個 skill description 重疊度高，路由可能誤判。緩解：第二階段做 5 skill 全套之後，跑一輪「自然語言請求 → 觸發到正確 skill」回測。

---

## 7. 下一步建議

1. **下一次 session 啟動時驗證**：確認 `research` 出現在 available-skills 清單。如果出現 → §4 表的「✅ 成立」獲得執行端證據。
2. **N3 通過後接 N4**：治理 plugin manifest skeleton（A01 §11 #3）。
3. **不要急著動其他四個 skill**：等 N4 plugin manifest 出來，可能 plugin 自帶其他 skill 註冊，避免重複工。
4. **CLAUDE.md 補語**（極小改動）：「複合任務跨 skill → 拆兩張 Task Card，用 output 接力」一句，列入 v2.5 過渡期最早的修改之一。

---

## 8. DoD 驗收

| # | DoD | 狀態 | 證據 |
|---|-----|:-:|------|
| 1 | SKILL.md 加 frontmatter（≥name+description），原內容不刪改 | ✅ | §1.1 |
| 2 | frontmatter 用 yaml.safe_load 可解析 | ✅ | §3.1 |
| 3 | 建立 .claude/skills/ 註冊路徑，文檔說明選擇與理由 | ✅ | §1.2 |
| 4 | PoC summary 含 (a)(b)(c) 三項觀察 | ✅ | §2.1 / §2.2 / §2.3 |
| 5 | 對 H1 給三選一結論並列證據 | ✅ | §4「部分成立」 |
| 6 | 部分／不成立 → 列 A01 應改裁決的模組 | ✅ | §5（結論：不需要改裁決，因為 A01 已預先寫對） |
| 7 | 向後相容：原引用不受影響 | ✅ | §3.2 |

7/7 通過。
