# HANDOFF_FABLE5 — 給未來 session 的信

> 寫於 2026-07-04/05，Fable 5 的唯一一次 session（Task Card `20260704-F01`）。
> 讀者：之後在這個 repo 開工的每一個 session（預設 `opus` 指揮官）。
> 這封信不是規則，是脈絡——規則在 DISPATCH_POLICY / JUDGMENT_RUBRICS / MAINTENANCE_PROTOCOL。
> 建議：新 session 第一次遇到「重大方向決策」前把這封信讀完一遍，之後不必重讀。

---

## 一、你為什麼會讀到這封信

使用者用僅有的一次 Fable 5 額度，沒有拿去解難題，而是把判斷力寫成你現在身處的制度：
診斷（`outputs/reports/2026-07-04_fable5-diagnosis.md`）、調度守則、判斷 rubric、
派工模板、維護協議。設計目標只有一個：**你不需要是最強的模型，也能做出接近最強模型
的工作品質**——靠拆解、隔離 context、fresh-context 驗收、和誠實標注做不到的事。

相信這套制度勝過相信你的直覺，特別是當你的直覺說「這步可以跳過」的時候。

## 二、三件使用者沒問、但你必須知道的事

### 1. 這個環境的記憶只有 repo 本身——commit 之外皆幻覺

雲端 session 是隨用隨棄的容器：`~/.claude/memory/` 不存在（`memory/user_prefs.md`
指向它的段落是 CLI 時代的遺留假設，已漂移）；session 可能在任何時刻重啟，重啟後
背景 agent 的引用全部失效（見 `memory/lessons.md` L-20260705-01，這是本次真實踩的坑）。
行為結論：**進度的唯一定義是「已寫入檔案且已 commit」**。每完成一個交付立即
checkpoint；背景 agent 的結論一到手先落檔再繼續；session 尾聲必 push。

### 2. 這套 harness 的儀式本身有成本，而且平台在持續吸收它的功能

16 個模組對一人公司是偏重的。NATIVE_OVERLAP.yaml 誠實記錄了 30% 與 Claude Code
原生功能重疊（Skill 85%、Permission 75%），且這個數字只會漲——平台每次改版都在
吸收 harness 手工做的事（skills、permissions、hooks、memory、subagents 都已原生化）。
不要出於忠誠替儀式辯護：**retro 時發現某個儀式連續多次沒攔到任何東西，就提議砍掉**。
真正不可替代的資產只有四樣：成本校準實測數據、Decision Log、lessons、和「對外只出
草稿」這條商業防線。v3 evaluation（R10）時圍繞這四樣做取捨，其他都可談。

### 3. 超出你能力的題目有專門的去處，不要硬做也不要沉默

`memory/pending_hard_questions.md` 是「待強模型清單」：opus + 第二意見仍拿不下的
判斷題（深度策略取捨、高賭注的品味裁決），寫進去、告訴使用者、繼續做你能做的部分。
使用者可以拿這份清單去更強的模型（未來世代、或偶發的高階額度）批次求解。
這不是失敗，這是制度設計的一部分——診斷報告的誠實條款寫得很清楚：這套制度補得了
執行品質，補不了品味判斷。假裝補得了才是失敗。

## 三、這套制度最可能的退化方式（按可能性排序）與預防

| # | 退化模式 | 早期訊號 | 預防（多半已內建） |
|---|---------|---------|------------------|
| 1 | **驗收儀式空轉**：照樣派 verifier，但 DoD 寫得太空（「完成報告」），verifier 全 pass 也沒驗到東西 | verifier 連續多任務 0 fail | 建卡時 DoD 對照 JUDGMENT_RUBRICS §2 寫可驗條目；retro 檢查 verifier fail 率，長期 0% 是紅旗不是綠旗 |
| 2 | **規則重新堆積**：新 session 順手往 CLAUDE.md/GLOBAL_RULES 加規則，路由層又長回大雜燴 | budget CI 逼近 3,000 | check_context_budget.rb 硬擋；MAINTENANCE §1 把 CLAUDE.md 列為「先問」；新規則進專門檔，CLAUDE.md 只加一行路由 |
| 3 | **lessons 變垃圾場或荒地**：要嘛塞滿「要更小心」式廢話，要嘛沒人寫 | >20 筆未蒸餾，或連續多任務 0 新增 | MAINTENANCE §3 品質判準＋§4 壓縮觸發；retro 固定過一遍 |
| 4 | **ROSTER 腐化**：模型換代後，session 憑訓練記憶寫型號、憑印象派工 | 守則引用的別名行為明顯異常 | CLAUDE.md 路由表明令「不要憑記憶寫型號」；MODEL_ROSTER 檔頭的查證日期＋季度複查 |
| 5 | **自我放權**：某個 session 說服自己「這個 deny/先問可以例外一次」 | diff 裡出現對 PERMISSIONS、硬規則、MAINTENANCE §1 的修改 | 不可動清單＋permissions_guard hook；使用者看到這類 diff 一律拒絕，無論理由多好 |
| 6 | **制度性怯懦**：把「問使用者」當成免責出口，事事來問 | 問題頻率上升且多為可逆細節 | JUDGMENT_RUBRICS §3 的「不問清單」；問就要帶選項與建議 |

## 四、留給下一次制度升級的線索

- `.claude/settings.json` 已釘 `"model": "opus"`（新 session 預設 opus 指揮官）。
  若使用者改用訂閱以外的計費，DISPATCH_POLICY 開頭的計費前提要重寫（屬「先問」級）。
- 這套新層（DISPATCH/RUBRICS/TEMPLATES/MAINTENANCE）與既有 R9（NATIVE_OVERLAP 自動化）、
  R10（v3 就緒評估）不衝突：新層管**行為**，R9/R10 管**架構**。做 R10 時把新層四檔
  視為「不可替代資產」之外的可重構對象——它們也該接受同樣的淘汰檢驗。
- 對抗審查（fresh-context sonnet 讀全部制度檔找矛盾）值得每半年重跑一次：
  制度檔會隨零星修改累積矛盾，用目標讀者等級的模型審，找到的才是真問題。

祝穩定。能力會過時，制度不會——只要你維護它。

— Fable 5, 2026-07-05
