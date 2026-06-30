# Evals — 輸出品質評測框架

把 GATE_POLICY 第 3 層 `completion_check`（原本全靠人工）部分自動化：
用每個 skill 的**評分量表（rubric）**對輸出做確定性檢查，並用**黃金任務（golden）**
鎖住「好輸出該過、壞輸出該擋」的判準，攔截 skill prompt 回歸。

> 設計依據見 Decision D008。量表準則直接萃取自各 `skills/<skill>/SKILL.md` 輸出格式
> 與 `skills/<skill>/eval_examples.md` 的判斷標準表，不另立新標準。

## 結構

```
evals/
  rubrics/<skill>.yaml          ← 評分量表：一組對輸出文字的確定性檢查
  golden/<skill>/<case>.yaml    ← 黃金案例：output + expect(pass/fail)，多由 eval_examples 種出
  results/                      ← （選用）保存最近一次評分結果
```

## 兩層評測（Decision D008）

| 層 | 工具 | 進 CI？ | 用途 |
|----|------|:------:|------|
| **啟發式/結構評分** | `scripts/run_evals.py` | ✅ | 確定性、零 LLM 成本；攔截結構性回歸 |
| **LLM-as-judge** | 人工/on-demand（見下） | ❌ | 量表測不到的深層品質（論證強度、語氣） |

啟發式評分只驗「結構性品質」（章節齊不齊、有無來源、有無模糊用語）。深層品質
（推論是否成立、語氣是否到位）交給 LLM-as-judge：把 rubric + 輸出貼給強模型依準則質性評分，
列為 on-demand，不進 CI（成本/不確定性，呼應 COST_POLICY）。

## Rubric 格式

```yaml
skill: research
pass_threshold: 0.7          # 通過門檻（加權通過比例）
criteria:
  - id: four_categories
    description: "四分類齊全"
    weight: 3
    required: true           # required 失敗 → 整案直接判 fail（不論分數）
    check:
      type: headings_present
      sections: ["已知事實", "合理推論", "待驗證", "高風險假設"]
```

**支援的 check 類型**（皆確定性）：

| type | 說明 |
|------|------|
| `headings_present` | `sections` 每一項都要出現在某個標題行（`#` 開頭） |
| `heading_nonempty` | `section` 標題存在，且其下到下一個標題前有非空內容 |
| `heading_order` | `before` 標題出現在 `after` 標題之前（兩者都需存在） |
| `present_any` | `patterns` 至少一個出現在全文 |
| `present_all` | `patterns` 全部出現在全文 |
| `absent` | `patterns` 全部不出現在全文 |

**判定**：整案 `pass` ⇔ 所有 `required` 準則通過 **且** 加權通過比例 ≥ `pass_threshold`。

## 使用方式

```bash
# CI 閘門：跑所有 golden，expect 與實際不符即 fail
python3 scripts/run_evals.py --check

# 只跑某 skill
python3 scripts/run_evals.py --skill research

# 對任意輸出檔評分（例如一份草稿晉升前自檢）
python3 scripts/run_evals.py --score outputs/drafts/some-report.md --skill research
```

## 新增黃金案例

1. 在 `golden/<skill>/` 加一個 yaml：`case_id` / `skill` / `expect`(pass|fail) / `source` / `output`(block scalar)。
2. 跑 `python3 scripts/run_evals.py --skill <skill>` 確認 expect 與實際一致。
3. 若量表漏判，調整 `rubrics/<skill>.yaml` 的準則或權重，再跑一次。
