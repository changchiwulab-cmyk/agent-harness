# Evals — 可執行的產出品質評估（G-B）

把 `skills/*/eval_examples.md` 的「好/壞範例」散文，變成**可執行的回歸 eval**，
補上專案「可量化」支柱中缺的最後一塊：量**產出品質**（不是操作次數）。

## 與其他驗證層的分工（不重疊）

| 層 | 量什麼 | 何時跑 | 檔案 |
|----|--------|--------|------|
| `system/GATE_POLICY.yaml` | 任務當下是否合規（schema/規則/完成/風險） | 每次任務收尾，人工 | 規範 |
| `scripts/governance_metrics.py` | **操作型**指標（Task Card 數、draft:report 比、audit 覆蓋、原生重疊） | 每月，人工 | 月報 |
| **`scripts/run_evals.py`（本層）** | **產出品質**：輸出是否符合該 skill 的 DoD rubric | 任意/CI，可重現 | `evals/` |

## 結構

```
evals/
├── README.md
├── research/taiwan_sme.yaml      # case：input + DoD + rubric + gold/bad 校準對
└── analysis/notion_ai.yaml
```

每個 case：`case_id` / `skill` / `prompt` / `definition_of_done` / `rubric`
（可機檢規則）/ `gold_example`（應 PASS）/ `bad_example`（應 FAIL）。
rubric 直接對應 `skills/<skill>/eval_examples.md` 的「判斷標準」表。

## 評分器（judge）

- **rule（預設）**：deterministic 結構檢查（heading 位置、區塊齊全、來源非空、量化 regex…）。
  無網路、CI 可重現。rubric `kind`：`section_first` / `section_nonempty` / `all_headings` /
  `contains_any` / `regex`。
- **llm（`--judge llm`）**：LLM-as-judge 擴充點。目前未接 provider → 自動 fallback 到 rule，
  確保 CI 不依賴 live model。未來接上時，用每個 case 既有的 gold/bad 對校準（對齊業界
  「calibrate judge against a gold set」做法）。

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
