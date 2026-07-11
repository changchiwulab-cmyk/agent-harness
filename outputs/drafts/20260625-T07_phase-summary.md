<!--
task_id: 20260625-T07
date: 2026-06-25
skill_type: ops
status: draft
-->

# T07 實作摘要：批次 web-search 節流/快取規則（補 T04 缺口 #3）

## 總結

T04 缺口 #3：web-search 只有「單卡 ≤3 輪」的**事後上限**，同批/同日多卡仍可能撞 rate limit（2026-04 S01 前例）。`web_search` 沒有程式碼 wrapper，因此這是**政策規則**而非程式碼/CI——在 `system/COST_POLICY.md` 加批次層級的事前節流。

## 變更

| 檔案 | 變更 |
|---|---|
| `system/COST_POLICY.md`「工具呼叫限制」 | 新增子節「批次 web-search 節流與快取」 |

規則四點：
1. **快取優先**：外查前先查 project 內部與既有 `outputs/`、`memory/`（延伸既有「能讀檔解決的不做 web search」）。
2. **批次合計上限**：同批 web search 合計建議 ≤ 卡數 × 2 輪。
3. **卡間間隔**：多卡連續執行時 web search 留間隔，降低 rate-limit。
4. **觸發上限**：以既有結果 + 內部資料補足，缺口標 [待驗證]，不硬重試。

## 邊界與驗證

- **未動 `GLOBAL_RULES.md`**：避開 CLAUDE.md + GLOBAL_RULES ≤ 3K 的 context budget；COST_POLICY 不在該 budget 內。`check_context_budget` 仍 OK（~1197 tokens）。
- 純政策文字，無程式碼/CI 變更；`check_spec_consistency.rb` OK、ALL_YAML_OK。
- 本次 3 主題自測（T01–T03）其實已體現此規則精神：每卡只用 2/3 輪、未撞 rate-limit——T07 把這個「夠了就停 + 先查內部」從行為固化為政策。

## 待人工確認

- 修改 `system/COST_POLICY.md` 屬 ask 級，於 PR #109 review 確認。
