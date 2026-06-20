# Lessons — 程序性記憶（跨 skill 通則）

把「重複發生的失敗 / 校準偏差」精煉成**一行可執行指引**，在下次任務載入，
讓系統不必每次重踩同一個洞。對應 2026 研究的 failure-driven guideline 路線（Reflexion / ACON）。

## 用法

- **載入**：每次任務在組裝 context 時，載入本檔 + `memory/lessons/[skill_type].md`（若存在）。
- **寫入**：屬長期記憶（`write_long_term_memory`，ask 權限）。**只在 RETRO 經人工確認後晉升**，
  不自動寫入。收錄門檻：同類失敗重複 ≥ 2 次，或有明確校準數據佐證。
- **退役**：指引過時 → 把 `status` 改為 `superseded`，保留歷史不刪除。

## 條目格式

```
## LSN-YYYYMMDD-NN ｜ <短描述>
- trigger: <對應 FAILURE_TAXONOMY id 或失敗樣式>
- guideline: <一行可執行指引>
- source: <retro / error / run / draft 來源路徑或 ref>
- date: YYYY-MM-DD
- status: active | superseded
```

---

## LSN-20260620-01 ｜ 多代理/超長原文審查會數倍燒 token
- trigger: SEC-03 成本失控 ／ 校準偏差
- guideline: 建立涉及多代理或超長原文的 review/research Task Card 時，預期 token 為常態的數倍，先上調 `max_tool_calls` 一檔；RETRO 校準該 skill 平均時用中位數或排除離群值。
- source: outputs/drafts/2026-05-29_observability-metrics.md（review 平均被單筆 ~120K 任務拉高）
- date: 2026-06-20
- status: active

## LSN-20260620-02 ｜ 高決策價值的 research 值得放寬查詢深度
- trigger: research 深度不足、硬湊結論
- guideline: 顧問決策型 research，於 Task Card 顯式把 `max_web_searches` 放寬至 5，並在 DoD 要求「政策時序 + 敏感性表」；實測比 3 輪多產出最高 ROI 的決策輸入。
- source: tasks/2026-05-02_taiwan-ai-industry-deep-dive.yaml（result_summary：5 search 比 3 search 多三項高 ROI 產出）
- date: 2026-06-20
- status: active
