# 路由規則 ROUTING_RULES

> **路由由原生負責，本檔只寫原生不做的事。**
> 6 個 skill 皆有 frontmatter 並在 `.claude/skills/` 註冊，Claude Code 依 description 自動載入
> （對應的成本路由子代理見 `.claude/agents/`）。原本的「關鍵字 → skill」對照表與各 skill 的
> description 逐字重複，已於 20260831-F01 刪除——兩份會漂移的真相來源不如一份。

## 權威 skill 清單

`research` / `analysis` / `writing` / `ops` / `review` / `retro`

這份清單是 Task Card `skill_type` 欄位的合法值，由 `system/validate_task_card.py` 的
`VALID_SKILLS` 與 `scripts/check_spec_consistency.rb` 的 `ALLOWED_SKILL` 強制，
並由 `test_allowed_skill_matches_skills_directory` 對照 `skills/` 實際目錄鎖定。
**要知道每個 skill 做什麼，讀 `skills/<name>/SKILL.md` 的 description，不要在這裡再抄一份。**

## 原生不處理的部分

1. **一張 Task Card 只對應一個 skill**。跨兩個 skill 的需求要拆卡，
   例如「研究後撰寫報告」→ research 卡產出 `outputs/drafts/research_note.md`，
   writing 卡讀它再產出報告。以 output 檔案作為接力點，不做 agent-to-agent 對話路由。
2. **無法判斷 skill 類型時詢問使用者，不要猜**（`system/INTAKE_FLOW.md`）。
3. **路由判斷本身不該消耗大量 token**——不需要 LLM 做複雜推理才能決定用哪個 skill；
   需要推理才選得出來，通常代表這張卡的範圍沒切乾淨，該回頭拆卡。
