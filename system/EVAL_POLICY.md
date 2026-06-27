# Eval Policy — 評估架構（M1）

> 把「可量化」從靜態範例升級為**可執行評分**。
> 對齊 2026 業界 eval harness（LLM-as-judge + 離線 regression），但嚴守 harness 哲學：
> **確定性檢查入 CI，語意判斷走人工/LLM-as-judge，晉升仍走人工 gate。**

## 為什麼

`skills/*/eval_examples.md` 提供了好/壞範例與「判斷標準」表，但**沒有執行器**——
無法回答「這份新產出有沒有退化？」。本架構補上 runner + rubric + regression set。

## 三個元件

| 元件 | 路徑 | 角色 |
|------|------|------|
| Rubric | `evals/rubrics/<skill>.yaml` | 每個 skill 一份；`auto_checks`（確定性結構）+ `judge_checks`（語意判斷） |
| Regression set | `evals/regression/manifest.yaml` | 以既有優良產出為 golden，防結構性退化 |
| Runner | `scripts/run_evals.py` (+ `test_run_evals.py`) | 跑 auto_checks、輸出 scorecard 到 `logs/evals/` |

## auto vs judge（誠實切分，對齊「區分事實/推論」）

- **auto_checks（確定性）**：結構性、可機器驗證——conclusion-first、四區塊/來源結構、計畫先行、DoD 逐條存在等。由 `run_evals.py` 評分，**入 CI gate**（`check_spec_consistency.rb` 驗 rubric/manifest schema）。
- **judge_checks（語意）**：來源真實性、量化是否到位、誠實度、翻譯腔——**需 LLM-as-judge 或人工**。runner 只把它們列為 `judge_pending`，**不自動評分**（成本與 draft-first 哲學）。

## 何時跑

1. **任務完成**：GATE_POLICY 第三層 `completion_check` 後，若產出對應某 skill，跑 `run_evals.py` 的 auto_checks。
2. **定期 regression**：改動 skill / 產出格式後，跑全 regression set，確認 golden 仍通過。
3. **晉升前**：產出由 `drafts/` → `reports/` 前，judge_checks 由人工確認（`RETRO_FLOW`）。

## 用法

```bash
python scripts/run_evals.py            # 跑 regression，印摘要 + 寫 logs/evals/scorecard-latest.yaml
python scripts/run_evals.py --no-write  # 只看摘要
python scripts/test_run_evals.py        # 單元測試
```

退出碼：`0` 全通過 / `1` 有 case 退化 / `2` 設定錯誤（缺 rubric、manifest 壞）。
scorecard 為**確定性輸出**（無 wall-clock timestamp、key 排序），可安全 commit 為證據。

## enforcement 點（符合 J5）

- `check_spec_consistency.rb` §7–9：rubric schema、五 skill 覆蓋、regression manifest（含 output_path 存在性）。
- CI 既有 workflow 會跑上述檢查 + `test_run_evals.py`。

## 後續（另開卡）

- M1-b：`judge_checks` 半自動 LLM-as-judge 腳本（含成本上限 + 結果寫 `logs/evals/`）。
