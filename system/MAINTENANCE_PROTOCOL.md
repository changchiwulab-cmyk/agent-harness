# MAINTENANCE_PROTOCOL — 制度檔維護協議

> 讀者：未來要修改 system/、skills/、CLAUDE.md、.claude/ 的任何 session。
> 原則：制度檔是這個 harness 的長期資產，改壞的代價由之後每個 session 承擔。
> 寧可慢，不可漂。

---

## §1 修改權限分級

### 可自行改（不用問，但必走 §2 程序）

| 對象 | 條件 |
|------|------|
| `memory/lessons.md` 新增條目 | 只能**新增**且 `status: proposed`；轉正見 §3 |
| `system/MODEL_ROSTER.md` 型號表 | 必附官方文件查證來源（照該檔「更新程序」）|
| 斷鏈修復 | 檔案引用的路徑/檔名已失效，修成正確值（不改語意）|
| 錯字、格式修正 | 不改語意的前提下 |

### 先問使用者（列 diff＋理由，等明確同意；對應 PERMISSIONS `ask`）

- `system/` 下任何**規則語意**的變更（DISPATCH_POLICY、JUDGMENT_RUBRICS、GATE_POLICY、
  APPROVAL_POLICY、COST_POLICY、ROUTING_RULES、INTAKE_FLOW…）
- `CLAUDE.md`（任何改動，含路由表加減行）
- `skills/` 下任何檔案；`.claude/agents/`、`.claude/settings.json`
- 新增或廢止一個制度檔
- `memory/` 下 lessons 以外的長期記憶寫入（GLOBAL_RULES 既有規則）

### 不可動（只有使用者親手改）

- CLAUDE.md 的**三條硬規則**
- `PERMISSIONS.yaml` 的 **deny 清單**與 `scripts/permissions_guard.py` 的攔截規則
- 本檔 §1 的分級本身（防止「先改權限、再改規則」的自我放權）

## §2 修改程序（六步，一步不省）

1. **備份**：`mkdir -p archive/$(date +%F)-變更主題/ && cp 原檔 archive/.../`
   （沿用 archive/pre-fable5/ 的先例；git 歷史是第二保險，不是替代）
2. **改**：一次一個主題，不順手改別的
3. **檢查**：`ruby scripts/check_context_budget.rb`＋`ruby scripts/check_spec_consistency.rb`；
   動過 tasks/logs/decisions 的 YAML → `python3 scripts/generate_frontend_manifest.py`；
   動過 scripts/ → 跑對應 `test_*`
4. **交叉引用**：grep 舊檔名/舊術語，確認沒有別的檔還指著舊內容
5. **commit**：訊息含「改了什麼＋為什麼」，屬任務的用 checkpoint 格式
6. **記錄**：`ask` 級變更寫入 `logs/AUDIT_LOG.md`；重大方向變更另開
   Decision Log（`tasks/DECISION_LOG_TEMPLATE.yaml` 格式）

## §3 教訓回寫（踩坑之後）

**什麼算教訓**：讓你損失超過 30 分鐘、或差點違反硬規則、或發現制度檔與現實不符的事。

**寫到哪**：`memory/lessons.md`，**只增不改**（append-only），格式見該檔頭。
新條目一律 `status: proposed`——這與 GLOBAL_RULES「長期記憶需人工確認」不衝突：
proposed = 待確認的提案，使用者在 retro 時批量裁決 → `confirmed` 或 `rejected`。

**教訓的品質判準**：下一個 session 讀了能**改變行為**才算教訓。
「要更小心」不合格；「背景 agent 的結果要在收到當下就寫入檔案，因為 session
可能隨時重啟且 task 引用會失效」合格。

## §4 壓縮觸發（防止 lessons 變垃圾場）

任一條件命中 → 開一張 retro Task Card 做蒸餾：

- `memory/lessons.md` 的 active 區超過 **20 筆**
- 該檔估算超過 **2,000 tokens**（`ruby -e` 用 check_context_budget.rb 的算法，或字元數粗估）

**蒸餾動作**：把重複出現的教訓歸戶到對應規則檔（這是規則變更 → 走 §1「先問」）；
歸戶完成的條目標 `status: distilled` 並剪貼到檔尾「已蒸餾歸檔」區。
lessons 是**緩衝區**，規則檔才是長期居所。

## §5 防漂移例行檢查（每季 retro 順做）

- CLAUDE.md 路由表指到的每個檔案都存在（grep 路徑逐一 `ls`）
- MODEL_ROSTER「最後查證」日期 < 4 個月，逾期照該檔程序重查
- `archive/` 只進不出；超過一年的備份可提議使用者歸檔壓縮（不可自行刪除——deny）
- NATIVE_OVERLAP.yaml 的季度 revisit（既有規則，順手一起）
