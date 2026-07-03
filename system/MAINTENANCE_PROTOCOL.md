# 制度維護協議 MAINTENANCE_PROTOCOL

> 讀者：未來每一個要動 CLAUDE.md、system/、skills/ 檔案的 session。
> 目的：讓弱模型能安全地更新制度，而不是讓制度在好意的修補中慢慢爛掉。
> 原則：**制度檔的預設狀態是「不動」**。每一條新規則都是所有未來 session 的固定成本。

## 1. 修改分級

### 1a. 可自行改（不需問使用者，但要 git commit 留痕）

- `logs/` 與 `outputs/drafts/` 下的紀錄與產出（allow）。注意：寫 `outputs/reports/` 屬 ask（PERMISSIONS.yaml），已晉升的 reports 見 1c。
- 各制度檔尾「**教訓紀錄（append-only）**」段：只能**追加**，不能改寫或刪除既有條目。
- `system/COST_POLICY.md` 校準表的**數字**（實測值、樣本數）——但係數樣本 < 5 筆前，表格必須保留「參考值，不得作為調參依據」的標註。
- 修正客觀錯誤：失效的檔案路徑、錯字、已改名的工具名。修正時 commit message 要寫明「修正失效引用：舊 → 新」。

### 1b. 先問使用者（列出 diff，取得同意才改）

- CLAUDE.md 任何改動（它進每個 session 的 context，影響最大）。
- 三條硬規則、`system/PERMISSIONS.yaml`、`system/APPROVAL_POLICY.yaml`。
- `system/DELEGATION_PLAYBOOK.md` 的升降級路徑與量化門檻、`system/JUDGMENT_RUBRICS.md` 的判準本身、`system/DELEGATION_TEMPLATES.md` 的模板結構（驗收條件/回報格式兩塊）。
- 新增任何制度檔、或把規則從一個檔搬到另一個檔。
- skills/ 下的 SKILL.md（既有 ask 權限）。

### 1c. 絕不自改

- `system/_archive/` 下的備份（歷史就是歷史）。
- 已晉升的 `outputs/reports/`（要改就出新版本，不覆蓋）。
- 教訓紀錄的既有條目（append-only 的意義）。

### 改前備份

動 1b 類檔案前：複製原檔到 `system/_archive/YYYY-MM-DD_[簡述]/`，再改。1a 類靠 git 歷史即可，不用複製。

## 2. 教訓格式

踩坑之後，教訓寫回**離使用現場最近的檔案**的「教訓紀錄」段：調度踩坑 → DELEGATION_PLAYBOOK；判斷失誤 → JUDGMENT_RUBRICS；skill 執行問題 → 對應 SKILL.md 的「常見失敗模式」；其他 → `logs/errors/`。

格式（一條 3–4 行，超過就是在寫報告不是寫教訓）：

```
- [YYYY-MM-DD] 情境：一句話。
  教訓：下次改怎麼做，一句話，可執行。
  證據：logs/errors/ 或 run log 路徑。
```

**教訓 ≠ 新規則。** 教訓是紀錄；要把教訓升級成正文規則（改判準、改門檻），走 1b 問使用者。這是防止規則膨脹的主閥門。

## 3. 精簡觸發

任一條成立就開一張精簡 Task Card（review 類，改動走 1b）：

- 單一檔案的教訓紀錄 ≥ 10 條。
- CLAUDE.md + GLOBAL_RULES 估算超過 2,500 tokens（CI 上限 3,000 前的預警線，跑 `ruby scripts/check_context_budget.rb` 看）。
- 單一制度檔超過 250 行。
- 同一條規則出現在兩個以上檔案的正文（副本會漂移——見診斷報告第 1 名問題）。

精簡的方向：合併同類教訓為一條規則提案、刪除從未被引用的段落、把細節下放到 load-on-demand 的檔案。**精簡是刪東西，不是重新組織**——重新組織常常越理越肥。

## 4. 衝突處理

發現兩份檔案的規則互相打架時：

1. 當下：採**限制較嚴**的那條執行（CLAUDE.md §規則衝突時）。
2. 事後：在對話裡向使用者回報衝突的兩條原文（檔案:行號）+ 你建議保留哪條、理由一句話。
3. 使用者裁決後，勝出的留在權威檔案，敗方檔案改成一行指標指向權威出處（不留副本）。
4. 各領域的權威出處：權限 → PERMISSIONS.yaml；調度 → DELEGATION_PLAYBOOK.md；驗收關卡 → GATE_POLICY.yaml；判斷 → JUDGMENT_RUBRICS.md；成本 → COST_POLICY.md。

## 5. 與 RETRO_FLOW 的銜接

`system/RETRO_FLOW.md` 管**執行資料**的回顧（成本、錯誤率、權限畢業）；本檔管**制度文本**的維護。銜接點：

- Retro 的「流程」維度發現制度檔問題 → 建議寫進 retro 報告，落實走本檔 1b。
- Retro 觸發時順帶檢查 §3 精簡觸發是否成立。
- 教訓紀錄是 retro 的資料源之一（與 logs/errors/ 並列）。

## 6. 收斂 backlog（2026-07-03 診斷遺留，逐次任務順手收，不專案化）

依 `outputs/reports/2026-07-03_harness-diagnosis.md`，以下副本待收斂（每次收斂走 1b）：

- [ ] `system/AGENT_CONTEXT.yaml` 的 boundaries 段 vs PERMISSIONS.yaml（權限副本）
- [ ] `system/GLOBAL_RULES.md` 成本意識段 vs COST_POLICY.md（成本副本）
- [ ] `system/GLOBAL_RULES.md` 記憶規則段 vs memory/README.md
- [ ] `system/ROUTING_RULES.md` 表格 vs skills 各檔的 description（原生 skill 路由已可承擔，NATIVE_OVERLAP 評 70%）
- [x] COST_POLICY「模型路由規則（v2 準備）」段——已被 DELEGATION_PLAYBOOK 取代（✓ 2026-07-03 已改為指標）
- [ ] `logs/AUDIT_LOG.md` 手寫機制 vs `scripts/generate_audit_log.py` 推導機制並存且已 drift（`--check` fail、檔內無 MANUAL_NOTES 標記）→ 請使用者裁決哪個是權威，另一個改為指標；裁決前照 AUDIT_LOG.md 檔頭手動附加

## 教訓紀錄（append-only）

（尚無紀錄）
