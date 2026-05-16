# 前端 / 後端執行測試計畫 — 20260515-001

| 欄位 | 值 |
|------|----|
| task_id | 20260515-001 |
| date | 2026-05-15 |
| skill_type | ops |
| risk_level | low |
| 測試執行者 | Sonnet 4.6 子代理（Agent `model=sonnet`） |
| 計畫/驗證者 | 主代理（Opus） |
| 狀態 | 執行中 → 結果見文末「執行結果」 |

---

## 1. 測試範圍

| 元件 | 定義 | 入口 |
|------|------|------|
| **前端** | `frontend/{index.html, app.js, styles.css, data.json}` 靜態看板，讀 `./data.json` 渲染 summary / timeline / log 三個 panel | `scripts/run_frontend.sh`（`python3 -m http.server`） |
| **後端** | `scripts/generate_frontend_manifest.py`：解析 `tasks/`、`logs/runs/`、`memory/active_projects/*/decisions/` 並序列化為 `frontend/data.json`；支援 `--check`（drift 偵測） | `python3 scripts/generate_frontend_manifest.py` |

「順利運行」定義：後端能無錯誤產生合法且與來源一致的 `data.json`；前端伺服器能啟動並以 HTTP 200 提供 `index.html` 與 `data.json`，且 `data.json` 為合法 JSON。

## 2. 環境前提

- Python 3.11（已確認 3.11.15）、PyYAML（已確認可 import）
- `pytest` **未安裝** → 測試一律以 `python3 -m unittest` 執行
- 所有指令自 repo 根目錄執行

## 3. 限制（PERMISSIONS deny）

- `spawn_background_process` 為 deny：前端伺服器測試必須以 `timeout` 包覆，探測後 `kill` 並確認**無殘留背景程序**；單次伺服器生命週期 < ~8s
- 不刪除任何檔案、不執行任何對外動作

## 4. 測試項目

### 後端（B）

| ID | 項目 | 指令 | 預期 / 通過標準 |
|----|------|------|----------------|
| B1 | 後端單元測試 | `python3 -m unittest scripts.test_generate_frontend_manifest -v`（或對檔案路徑） | 全部 case 通過（`TestGenerator` 3 + `TestDriftCheck` 1），exit 0 |
| B2 | 產生器可運行且輸出合法 JSON | `python3 scripts/generate_frontend_manifest.py` 後 `python3 -c "import json;json.load(open('frontend/data.json'))"` | 產生器 exit 0；`data.json` 可被 `json.load` 解析，含 `tasks`/`logs`/`decisions` 三鍵 |
| B3 | Drift 檢查 | `python3 scripts/generate_frontend_manifest.py --check` | exit 0（`data.json` 與來源一致，無漂移） |
| B4 | 冪等性 | 連續執行產生器兩次後 `git diff --exit-code frontend/data.json` | 無 diff（兩次輸出位元相同） |

### 前端（F）

| ID | 項目 | 指令 | 預期 / 通過標準 |
|----|------|------|----------------|
| F1 | run_frontend.sh CLI 介面 | `scripts/run_frontend.sh --version`、`scripts/run_frontend.sh --help` | 兩者 exit 0；`--version` 印出版本與日期；`--help` 印出 Usage |
| F2 | 靜態伺服器提供 index.html | `timeout` 包覆啟動 `http.server` → `curl -fsS -o /dev/null -w '%{http_code}' http://localhost:<port>/frontend/index.html` | HTTP 200 |
| F3 | 靜態伺服器提供 data.json | 同上伺服器 → `curl -fsS http://localhost:<port>/frontend/data.json` 後 `json.load` | HTTP 200 且為合法 JSON |
| F4 | 伺服器確實關閉 | 探測後 `kill` PID，`pgrep -f "http.server"`（限本測試 port） | 無殘留程序（`timeout` 亦保證上限） |

### 整合（I）

| ID | 項目 | 指令 | 預期 / 通過標準 |
|----|------|------|----------------|
| I1 | 前端與後端輸出對接 | grep `frontend/app.js` 的 `data.json` fetch；比對 `data.json` 鍵 | app.js 確實 fetch `./data.json`；`data.json` 提供 app.js 渲染所需鍵 |

## 5. 執行方式

測試執行委派給 **Sonnet 4.6 子代理**（Agent 工具，`model=sonnet`，`subagent_type=general-purpose`），逐項執行 B1–B4、F1–F4、I1 並回傳結構化結果。主代理（Opus）負責計畫、抽查驗證關鍵指令、四層 gate 與紀錄。

## 6. 通過判定

- **全綠**：B1–B4、F1–F4、I1 全部 pass → status `done`
- **部分**：任一 fail → status `partial`，列缺漏，輸出留在 `outputs/drafts/`
- **失敗**：核心項（B1/B2/F2/F3）fail → status `failed`，依 schema 寫 `logs/runs/` 與 `logs/errors/`

---

## 7. 執行結果

執行者：Sonnet 4.6 子代理（`model=sonnet`, general-purpose）。主代理（Opus）已獨立抽查 B1 / B3 / F4 與 drift 規模。

### 初次執行（8/9）

| ID | 結果 | 證據 |
|----|------|------|
| B1 | ✅ PASS | exit 0；4 tests OK（TestGenerator×3 + TestDriftCheck×1）。主代理重跑覆核：`Ran 4 tests ... OK` |
| B3 | ❌ FAIL | exit 1；`DRIFT: frontend/data.json is out of date` |
| B2 | ✅ PASS | 產生器 exit 0；`data.json` 可 `json.load`；keys = `['decisions','logs','tasks']` |
| B4 | ✅ PASS | 連續兩次 sha256 相同：`f4687a4eeada…3de85`（冪等） |
| F1 | ✅ PASS | `--version` exit 0（`version 1.4.0 ... 2026-04-27`）；`--help` exit 0（印 Usage） |
| F2 | ✅ PASS | `INDEX_CODE=200` |
| F3 | ✅ PASS | `curl` exit 0；`DATA_JSON_VALID=yes` |
| F4 | ✅ PASS | 探測後 `kill`；`ps aux` 覆核殘留 = 0（`timeout 8` 另保證上限） |
| I1 | ✅ PASS | `app.js:25` → `const res = await fetch('./data.json');` |

### B3 失敗根因與處置（已解決）

- **根因**：版本控制中的 `frontend/data.json` 落後來源。`git diff --stat` 顯示 **僅 10 insertions、0 deletions**，與「本任務新增的 Task Card `20260515-001` 尚未反映到 `data.json`」完全一致 → drift 為**本次任務自身造成**，非產生器缺陷。
- **驗證**：主代理重跑產生器後 `python3 scripts/generate_frontend_manifest.py --check` → `OK: frontend/data.json is up to date.`，**exit 0**。後端產生器健康。
- **處置**：重新產生並提交 `frontend/data.json`（符合 repo 既有 CI 契約 `.github/workflows/spec-consistency.yml` 的 drift 檢查；不提交將使 CI 失敗）。
- **修復後狀態**：B3 PASS（exit 0）→ **9/9 全綠**。

### 結論

- **前端順利運行 ✅**：`run_frontend.sh` CLI 正常；`http.server` 啟動後以 HTTP 200 提供 `index.html` 與 `data.json`，`data.json` 為合法 JSON；伺服器確實關閉、無殘留背景程序。
- **後端順利運行 ✅**：產生器單元測試 4/4 通過、可產出合法 JSON、冪等、修復後 drift 檢查 exit 0。
- 唯一 fail（B3）為本任務新增 Task Card 自身造成的可預期 drift，已重生並提交 `data.json` 解決。

## 8. 四層 Gate 驗證

| Gate | 結果 | 說明 |
|------|------|------|
| schema_check | ✅ pass | `validate_task_card.py` exit 0 |
| rule_check | ✅ pass | 使用工具皆在白名單；無 deny 動作（未刪檔、未對外、伺服器 timeout 包覆+kill+覆核無殘留）；web search 0 ≤ 3；>5 工具呼叫前後皆有 checkpoint |
| completion_check | ✅ pass | DoD 8 條逐條對應（DoD#4 初次為自身 drift，重生 `data.json` 後 `--check` exit 0） |
| risk_check | ✅ pass | 實際動作為唯讀 + 跑既有測試 + 短暫本地伺服器 + 重生既有生成物 + 草稿輸出，與 risk_level=low 一致；無對外動作 |

**最終狀態：done**（初次 8/9；解決自身 drift 後 9/9）。checkpoints = 2（< 3）、status = done、risk = low → 依 EXECUTION_LOG_SCHEMA 免寫 `logs/runs/`，記入 `logs/AUDIT_LOG.md`。
