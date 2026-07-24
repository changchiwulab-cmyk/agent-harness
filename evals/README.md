# Evals — 可執行的產出品質評估（G-B）

把 `skills/*/eval_examples.md` 的「好/壞範例」散文，變成**可執行的回歸 eval**，
補上專案「可量化」支柱中缺的最後一塊：量**產出品質**（不是操作次數）。

## 與其他驗證層的分工（不重疊）

| 層 | 量什麼 | 何時跑 | 檔案 |
|----|--------|--------|------|
| `system/GATE_POLICY.yaml` | 任務當下是否合規（schema/規則/完成/風險） | 每次任務收尾，人工 | 規範 |
| `scripts/governance_metrics.py` | **操作型**指標（Task Card 數、draft:report 比、audit 覆蓋、原生重疊） | 每月，人工 | 月報 |
| **`scripts/run_evals.py`（本層）** | **產出品質**：輸出是否符合該 skill 的 DoD rubric | 任意/CI，可重現 | `evals/` |

## 覆蓋（6/6 skill）

每個可執行 skill 至少 1 個 case，rubric 對齊該 skill `eval_examples.md` 的「判斷標準」表：

| skill | case | 主要 rubric |
|-------|------|-------------|
| research | `research/taiwan_sme.yaml` | 結論先行 / 四區塊 / 來源 / 待驗證 |
| analysis | `analysis/notion_ai.yaml` | 結論先行 / 含「不做」/ 量化 / 高風險假設 / 下一步 |
| writing | `writing/vietnam_proposal.yaml` | 結論先行 / 比較表 / 風險 / 下一步 |
| ops | `ops/downloads_cleanup.yaml` | 計畫先行 / 盤點 / Dry-run / 排除系統檔 / 等待確認 |
| review | `review/vietnam_report_review.yaml` | 通過項 / 必須修改 / 建議修改 / DoD 逐條比對 |
| retro | `retro/cycle_retro.yaml` | 數據摘要 / task_id 證據 / HIGH-MED-LOW 分級 / 晉升候補 |

> `retro` 不在 `validate_task_card` 的 VALID_SKILLS（不可路由）為已知現況；
> eval 覆蓋與路由解耦——照補 case，不動 VALID_SKILLS。

## 結構

```
evals/
├── README.md
├── research/taiwan_sme.yaml            # case：input + DoD + rubric + gold/bad 校準對
├── analysis/notion_ai.yaml
├── writing/vietnam_proposal.yaml
├── ops/downloads_cleanup.yaml
├── review/vietnam_report_review.yaml
└── retro/cycle_retro.yaml
```

每個 case：`case_id` / `skill` / `prompt` / `definition_of_done` / `rubric`
（可機檢規則）/ `gold_example`（應 PASS）/ `bad_example`（應 FAIL）。
rubric 直接對應 `skills/<skill>/eval_examples.md` 的「判斷標準」表。

## 評分器分層（judge）

| judge | 量什麼 | 何時跑 | 網路 |
|-------|--------|--------|------|
| **rule（預設，CI 基線）** | deterministic 結構檢查（heading 位置、區塊齊全、來源非空、量化 regex…） | 每次 / CI，可重現 | 無 |
| **llm（`--judge llm`，本地語意層）** | 語意層品質：輸出是否『語意上』滿足 rubric，不只結構符合 | 本地／有金鑰環境 | 需 |

- **rule**：rubric `kind`：`section_first` / `section_nonempty` / `all_headings` /
  `contains_any` / `regex`。無外呼、CI-safe，是校準與回歸的基線。
- **llm**：接 Anthropic Messages API（走 stdlib `urllib`，**不新增第三方依賴**）。
  - **金鑰閘**：只在 `ANTHROPIC_API_KEY` 存在時觸網；無金鑰（CI／離線）印 notice 並
    **自動 fallback rule**，CI 與 rule judge 位元級一致、永不觸網。
  - **離線安全**：provider 例外或回傳非 JSON → 該 case 自動 fallback rule 並印 warning。
  - **校準**：用每個 case 既有的 gold/bad 對校準（對齊業界「calibrate judge against a
    gold set」做法）。
  - 模型可由 `EVAL_JUDGE_MODEL` 環境變數指定（預設 `claude-sonnet-5`）。

```bash
# 本地語意層驗證（需金鑰；不入 CI）
ANTHROPIC_API_KEY=sk-... python scripts/run_evals.py --judge llm
```

## 用法

```bash
python scripts/run_evals.py                 # 校準全部 case（gold 應 PASS、bad 應 FAIL）
python scripts/run_evals.py --json
python scripts/run_evals.py --candidate outputs/drafts/x.md --case research-taiwan-sme
python scripts/test_run_evals.py            # 單元測試
```

`run_evals.py`（無參數）為**校準模式**：對每個 case 跑 gold（須過）與 bad（須不過），
證明 rubric 能區辨好壞 — exit 1 表示某 case 失去鑑別力。可納入 CI 作為產出品質回歸關卡。

## 新增 case

1. 在 `evals/<skill>/` 加一個 `*.yaml`，rubric 對齊該 skill 的 `eval_examples.md` 判斷標準。
2. 附 `gold_example` / `bad_example` 校準對。
3. 跑 `python scripts/run_evals.py` 確認新 case `calibration_ok`。
