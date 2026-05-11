# Plan — 20260511-F02 錯誤儀表板（Phase 1 視覺化）

> **Status**: 規劃草稿，待人工審核通過後由 Sonnet 4.6 sub-agent 執行實作。
> **Owner**: 規劃 Opus 4.7 / 實作 Sonnet 4.6 high。
> **Task Card**: `tasks/2026-05-11_error-dashboard-html.yaml`（schema 驗證 ✅ pass）。
> **依據**: 20260427-F01 Phase 0 baseline；本卡承接其留下的 Phase 1。

---

## 1. 為什麼要做（與 CLAUDE.md 對齊）

CLAUDE.md 三條硬規則中有兩條跟「錯誤可見性」直接相關：
- **連續失敗 3 次就停下來** → 需要一眼看到失敗事件。
- **每階段 git checkpoint + 4 層 gate 驗證** → 需要一眼看到 gate 哪一層 fail。

目前 frontend/ 看板把 task / decision / log 並排呈現，但**沒有把「錯誤」當主角**：
- `logs/errors/*.md` 完全沒被 generator 收進 `data.json`。
- `logs/runs/*.yaml` 雖有收 `gate_results`，但前端僅顯示 `status` 與時間，沒有把 4 層 gate fail 突顯。
- Task Card schema 缺漏（缺 DoD、缺 risk_level）目前只有 `validate_task_card.py` 在 CLI 提示，沒有看板可看。

本卡把這三類失敗訊號統合到同一頁面，並加上 Chart.js 的時間軸/分類圖，讓檢視動作一次完成。

---

## 2. Out-of-scope（避免任務膨脹）

- ❌ 不引入前端 framework（React / Vue），維持 vanilla JS + ESM。
- ❌ 不做 push / live reload；資料來自 build-time 的 `data.json`。
- ❌ 不改 `system/` 下任何規則檔（FAILURE_TAXONOMY 不擴充類別）。
- ❌ 不改 `validate_task_card.py`（schema 缺漏判斷在 generator 內獨立函式做，不耦合 validator）。
- ❌ Phase 2（Context Budget 儀表板）、Phase 3（Decision Graph）依舊是後續任務。
- ❌ 不引入 npm / package.json（Chart.js 走 CDN ESM）。

---

## 3. 資料來源 → payload schema 對照

### 3.1 Errors（**新增**）

來源：`logs/errors/*.md`（排除 `ERROR_LOG_TEMPLATE.md` 與 `.gitkeep`）。
每個 markdown 內含**一個** ` ```yaml … ``` ` fenced block。解析該 block 為 dict 後萃取：

| payload 欄位 | 來源 YAML key | 備註 |
|---|---|---|
| `path` | （檔案路徑，相對 root） | drill-down 用 |
| `error_id` | `error_id` | e.g. `ERR-20260404-001` |
| `task_id` | `task_id` | 與 tasks/runs join |
| `date` | `date` | 排序、時間軸用 |
| `error_type` | `error_type` | 5 種：tool_failure / rule_violation / schema_failure / timeout / unknown |
| `error_summary` | `error_summary` | 列表主標 |
| `failure_count` | `failure_count` | KPI 加總用 |
| `related_rule` | `related_rule` | 對 FAILURE_TAXONOMY 分類；可能是字串描述（如「SEC-03」「COORD-02」），用 regex 抽 ID |
| `resolution` | `resolution` | stopped / escalated / retried_success |
| `skill_type` | `skill_type` | 篩選用 |
| `taxonomy_codes` | （衍生） | 從 `related_rule` 用 `r"\b(SPEC|COORD|VAL|SEC)-\d{2}\b"` 抽出，去重後排序 |

**邊界處理**：
- 沒 fenced block → skip 並 print warning（不算失敗）。
- YAML parse error → skip 並 print warning（同上）。
- 缺欄位 → 對應 payload 值為 None / `[]`。

### 3.2 Logs（**擴充**）

`collect_logs()` 已存在，目前 `LOG_FIELDS` 已含 `gate_results`。本卡保持 `gate_results` 完整收進，並衍生：
- `has_gate_failure: bool` — 任一 gate 值為 `"fail"`。
- `failed_gates: [str]` — 列出值為 `"fail"` 的 gate 名稱（保持原 4 個固定順序：schema_check, rule_check, completion_check, risk_check）。

加入 `LOG_FIELDS` 的還有 `error_summary`（schema 已有，方便儀表板顯示）。

### 3.3 Tasks（**擴充**）

`collect_tasks()` 已存在，新增衍生欄位 `schema_issues: [str]`，由獨立函式 `detect_task_schema_issues(doc)` 判定。判定規則：
- `goal` 缺、空字串、純空白 → `"missing_goal"`。
- `definition_of_done` 缺、非 list、長度 0、或所有元素都是空字串 → `"missing_dod"`。
- `risk_level` 不在 `{low, medium, high, critical}` → `"invalid_risk_level"`。
- `skill_type` 不在 `{research, writing, ops, review, analysis}` → `"invalid_skill_type"`。
- `status` 在 `{failed, blocked}` → `"task_failed"` / `"task_blocked"`（用同一函式輸出，便於前端統一渲染）。

獨立成函式的好處：可單獨單元測試（DoD #8 case ii）。

### 3.4 最終 `data.json` schema 變化

```jsonc
{
  "tasks":     [{ /* 原欄位 */, "schema_issues": ["missing_dod", ...] }],
  "logs":      [{ /* 原欄位 */, "has_gate_failure": true, "failed_gates": ["completion_check"] }],
  "decisions": [/* 不變 */],
  "errors":    [{ "path": "...", "error_id": "...", ..., "taxonomy_codes": ["SEC-03"] }]   // 新
}
```

排序：`errors` 依 `(date desc, error_id desc)`，與 generator 既有「排序輸出」一致確保 idempotent。

---

## 4. Generator 變更（`scripts/generate_frontend_manifest.py`）

### 4.1 新增模組層常數

```python
ERRORS_GLOB = "logs/errors/*.md"
ERRORS_EXCLUDE = {"ERROR_LOG_TEMPLATE.md"}     # 顯式排除
ERROR_FIELDS = (
    "error_id", "task_id", "date", "skill_type",
    "error_type", "error_summary", "failure_count",
    "related_rule", "resolution",
)
TASK_FIELDS_EXTRA = TASK_FIELDS  # 不動既有，新增 schema_issues 在 collect 時組進去
LOG_FIELDS = LOG_FIELDS + ("error_summary",)   # 加一欄
TAXONOMY_RE = re.compile(r"\b(?:SPEC|COORD|VAL|SEC)-\d{2}\b")
YAML_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)
VALID_RISK = {"low", "medium", "high", "critical"}
VALID_SKILL = {"research", "writing", "ops", "review", "analysis"}
```

### 4.2 新增函式（簽章）

```python
def parse_error_markdown(text: str) -> dict[str, Any] | None:
    """Extract first ```yaml fenced block and parse as dict; return None if absent/invalid."""

def collect_errors(root: Path) -> list[dict[str, Any]]:
    """Walk logs/errors/*.md, exclude template, parse, project to ERROR_FIELDS + taxonomy_codes."""

def detect_task_schema_issues(doc: dict[str, Any]) -> list[str]:
    """Return list of issue codes per §3.3 rules. Pure function for easy testing."""

def derive_gate_failures(gate_results: dict[str, str] | None) -> tuple[bool, list[str]]:
    """Return (has_gate_failure, failed_gates)."""
```

### 4.3 修改既有函式

- `collect_tasks`：在每個 item 後 merge `{"schema_issues": detect_task_schema_issues(doc)}`。
- `collect_logs`：在每個 item 後 merge `derive_gate_failures(item.get("gate_results"))` 結果。
- `build`：在 dict 加 `"errors": collect_errors(root)`。

### 4.4 不變的部分

- `--check` drift 檢測邏輯不動。
- `dump()` 仍用 `sort_keys=True, indent=2, ensure_ascii=False`，新增欄位自動穩定排序。
- 排序原則：`errors` 用 `sorted(items, key=lambda e: (e.get("date") or "", e.get("error_id") or ""))`。

---

## 5. 前端變更

### 5.1 `frontend/index.html` 區塊新增

於既有 `<section class="filters">` 與 `<section class="cards" id="summaryCards">` **之間**插入一個 anchor `<a id="errors">`，並在現有 `<main class="grid">` **之前**插入：

```html
<section class="error-dashboard">
  <h2>錯誤儀表板</h2>
  <div class="error-kpis">
    <article class="card kpi" data-kpi="errors"><div class="label">錯誤事件</div><div class="value">…</div></article>
    <article class="card kpi" data-kpi="gate-fails"><div class="label">Gate 失敗</div><div class="value">…</div></article>
    <article class="card kpi" data-kpi="failed-tasks"><div class="label">失敗/封鎖任務</div><div class="value">…</div></article>
    <article class="card kpi" data-kpi="schema-issues"><div class="label">Schema 缺漏</div><div class="value">…</div></article>
  </div>
  <div class="charts">
    <div class="chart-box"><canvas id="taxonomyChart"></canvas></div>
    <div class="chart-box"><canvas id="timelineChart"></canvas></div>
  </div>
  <div class="error-controls">
    <label>類型 <select id="errorTypeFilter"><option value="">全部</option>…</select></label>
    <label>Gate <select id="gateFilter"><option value="">全部</option>…</select></label>
    <label>排序 <select id="errorSort"><option value="date_desc">日期新→舊</option><option value="date_asc">日期舊→新</option></select></label>
  </div>
  <div id="errorList" class="panel"></div>
</section>
```

### 5.2 `frontend/app.js` 模組責任拆分

新增以下函式（不動既有 render*）：

- `loadChartJs()` — 動態 `import("https://cdn.jsdelivr.net/npm/chart.js@4.4.4/+esm")`，回傳 module 或 null（CDN 失敗）。
- `unifyErrors(payload)` — 把 payload.errors / payload.logs(has_gate_failure) / payload.tasks(schema_issues) 統一成一條 `unifiedIssue` list，每項帶 `kind: 'error'|'gate'|'schema'`、`date`、`title`、`detail`、`source_path`、`taxonomy: [str]`。
- `renderErrorKpis(unified)` — 4 張 KPI 卡。
- `renderTaxonomyChart(Chart, unified)` — 圓餅圖；無 Chart.js 時把 canvas 換成 `<ul>` 文字版。
- `renderTimelineChart(Chart, unified)` — 月份桶柱狀圖；同上 fallback。
- `renderErrorList(unified)` — `<details>` 元素列表，summary 顯示 kind+date+title，展開區塊顯示 `<pre>` raw YAML/Markdown 摘要與「open in editor」連結（用 `vscode://file/<absolute-path>` 視為可選增益，無也無妨）。
- `bindErrorControls(unified)` — 篩選/排序事件。

`init()` 流程修改：
```js
const Chart = await loadChartJs();   // 不阻塞 render
const unified = unifyErrors(payload);
renderErrorKpis(unified);
if (Chart) { renderTaxonomyChart(Chart, unified); renderTimelineChart(Chart, unified); }
else        { renderChartFallback(unified); }
renderErrorList(unified);
bindErrorControls(unified);
// 既有 task/decision/log 路徑不動
```

`escapeHtml` 沿用既有，不可繞過。所有來源字串都必須走它。

### 5.3 `frontend/styles.css` 新增

- `.error-dashboard` 區塊背景 / padding / 邊框沿用 `.panel` 視覺。
- `.error-kpis` grid `repeat(auto-fit, minmax(200px, 1fr))`。
- `.charts` grid `repeat(auto-fit, minmax(320px, 1fr))`，`.chart-box { background: #fff; padding: .8rem; border-radius: .6rem; min-height: 280px; }`。
- KPI 卡若值 > 0 加 `.has-issue` modifier，文字色 `#b91c1c` 提示警示。
- ≤ 900px 時 `.charts` 自動單欄（既有 `.grid` 已有同樣 pattern，照抄）。

### 5.4 Chart.js 離線降級策略

- `loadChartJs` 用 `try { … } catch { return null; }`。
- `null` 時 `renderChartFallback` 把 canvas 容器替換為「`<p class="chart-fallback">未能載入 Chart.js（離線環境）。改顯示文字摘要：</p><ul>…</ul>`」。
- 不阻擋頁面其他功能。

---

## 6. 測試擴充（`scripts/test_generate_frontend_manifest.py`）

新增 `TestErrorCollection` 與 `TestSchemaIssues` 兩個 class，至少 4 個 case：

1. **`test_errors_parse_and_exclude_template`**
   - 在 tmp `logs/errors/` 放：`ERROR_LOG_TEMPLATE.md`（含 yaml block）、`.gitkeep`、`2026-04-04_S01_error.md`（含完整 yaml）。
   - 期望 `payload["errors"]` 長度 = 1，`error_id == "ERR-20260404-001"`，`taxonomy_codes` 含 `"SEC-03"` 與 `"COORD-02"`。

2. **`test_detect_task_schema_issues`**
   - 直接呼叫 `gen.detect_task_schema_issues({"goal": "x", "definition_of_done": []})` → contains `"missing_dod"`。
   - `{"goal": "", "risk_level": "extreme"}` → contains `"missing_goal", "invalid_risk_level"`。
   - `{"status": "failed", "goal": "x", "definition_of_done": ["a"], "risk_level": "low", "skill_type": "ops"}` → `["task_failed"]`。

3. **`test_logs_derive_gate_failures`**
   - 給含 `gate_results: {schema_check: pass, rule_check: fail, completion_check: pass, risk_check: fail}` 的 fixture。
   - 期望 `has_gate_failure == True` 且 `failed_gates == ["rule_check", "risk_check"]`。

4. **`test_idempotent_with_errors`**
   - 含 task + log + decision + error 的 fixture，連續呼叫 `dump(build(root))` 兩次結果 byte-identical。

既有 4 個 test 不動，全綠維持。

---

## 7. CI / 啟動腳本影響

- `.github/workflows/spec-consistency.yml` 已含 `python3 scripts/test_generate_frontend_manifest.py` 與隱式 drift（透過 `git diff --exit-code frontend/data.json` —— 若 F01 沒這行，本卡也**不**新增；只確保 generator 能跑通）。實作後**必須在 push 前**先在本地跑 `python3 scripts/generate_frontend_manifest.py` 一次，避免 PR 上 drift。
- `scripts/run_frontend.sh` 升版至 `1.5.0` 並更新 `LAST_UPDATED="2026-05-11"`；CLI 介面（`--no-generate / --help / --version / 自訂 port`）完全不變。

---

## 8. 風險評估與緩解

| # | 風險 | 等級 | 緩解 |
|---|------|------|------|
| R1 | Chart.js CDN 在受限網路（CI / 離線審閱）載入失敗 | medium | `loadChartJs` try/catch → fallback 文字版；KPI/列表絕不依賴 Chart.js |
| R2 | `logs/errors/` 中的 yaml fenced block 格式不一（縮排、欄位變動） | medium | 用 `re.DOTALL` 抓第一個 fenced block；parse 失敗 skip + warn；不 raise |
| R3 | `data.json` 因新欄位 drift CI fail | low | 規劃裡明確要求實作後本地重產一次；`sort_keys=True` 保證確定性 |
| R4 | `escapeHtml` 漏掉導致 XSS（資料源含未信任字串） | high if missed | 新增的所有 render 都必須走 `escapeHtml`；code review 重點檢查 |
| R5 | sub-agent 越界改 `system/` 或 `validate_task_card.py` | medium | sub-agent prompt 明列**不可動清單**；上層 gate `rule_check` 對白名單再驗 |
| R6 | sub-agent 自作主張引入 npm / package.json | low | sub-agent prompt 明列「不准引入 build tool / 套件管理」 |

`risk_level: medium` + `approval_needed: true` 已對應 APPROVAL_POLICY 的「修改 frontend/scripts/CI 相關檔案」。最終 summary 會落在 `outputs/drafts/` 等人工確認後才能合併。

---

## 9. Sub-agent 委派（Sonnet 4.6 high）

待人工核准本規劃後，由 Opus 用以下方式 spawn：

```
Agent(
  subagent_type="general-purpose",
  model="sonnet",
  description="Implement F02 error dashboard",
  prompt=<見 §9.1>
)
```

### 9.1 Sub-agent prompt 大綱

明確包含：
- 必讀檔案清單（與 input_data 一致 + 本規劃檔）。
- **不可動清單**：`system/`、`skills/`、`memory/`、`validate_task_card.py`、`CLAUDE.md`、CI workflow（除非為了 drift check 微調）。
- **必動清單**：generator / generator test / index.html / app.js / styles.css / run_frontend.sh / README.md / 最終 summary md。
- DoD 13 條，要求逐條 pass。
- 完成後不要 commit；改丟 unified diff 摘要 + 本地測試結果到 stdout，由 Opus 做 4 層 gate 後 commit。
- 失敗 3 次 → stop & 寫 `logs/errors/2026-05-11_F02_error.md`。
- 工具預算：tool_calls ≤ 50（generator 改 + test 跑 + 前端煙測讀檔 + 寫 summary）。

### 9.2 Opus 接手後的驗證流程（Gate 4 層）

| Gate | 動作 |
|------|------|
| schema_check | 重跑 `python3 system/validate_task_card.py tasks/2026-05-11_error-dashboard-html.yaml`；JSON schema 驗 `frontend/data.json`（loadable JSON、`errors` 為 list） |
| rule_check | `git diff` 比對只動 §9.1 必動清單；確認 `escapeHtml` 在所有新 render 都被呼叫；確認沒新增 npm 依賴 |
| completion_check | 13 條 DoD 逐條 pass/fail 表，列 evidence（檔案路徑+行號 / 測試輸出） |
| risk_check | drift `--check` 通過；CI workflow 不變；summary 落在 drafts/ |

### 9.3 Checkpoint 計畫

- C1: Task Card + 規劃接受 →（本卡，本訊息）。
- C2: Sub-agent 完成、Opus 4 層 gate 通過 → `git commit -m "checkpoint: 20260511-F02 implement error dashboard"`。
- C3: 人工審 summary 通過 → 視情況進入 PR 流程（本卡到 C2 即達成 DoD）。

---

## 10. 與 DoD 13 條對照（規劃完整性自檢）

| DoD # | 對應段落 | 是否覆蓋 |
|------:|---------|--------|
| 1 collect_errors | §3.1, §4.1, §4.2 | ✅ |
| 2 has_gate_failure | §3.2, §4.2 | ✅ |
| 3 schema_issues | §3.3, §4.2 | ✅ |
| 4 idempotent + drift | §4.4, §6 case 4, §7 | ✅ |
| 5 HTML 區塊 | §5.1 | ✅ |
| 6 Chart.js + fallback | §5.2, §5.4, §8 R1 | ✅ |
| 7 styles | §5.3 | ✅ |
| 8 tests ×4 | §6 | ✅ |
| 9 run_frontend.sh 1.5.0 | §7 | ✅ |
| 10 README | （sub-agent 必動清單 §9.1） | ✅ |
| 11 validate + tests + 煙測 | §9.2 schema/completion gate | ✅ |
| 12 summary md | §9.2, §9.3 | ✅ |
| 13 AUDIT_LOG / runs/ | §9.3 + D006 narrow scope | ✅ |

13/13 規劃覆蓋。

---

## 11. 待人工確認的單點

請使用者確認以下任一即可：

1. ✅ **同意按本規劃實作** → Opus 立即 spawn Sonnet sub-agent。
2. ✏️ **要修正範圍/DoD/技術選型** → 指出後 Opus 改 Task Card + 本規劃，再走一次。
3. ⏸️ **暫緩** → 任務維持 `status: pending`，Task Card 與本規劃保留。
