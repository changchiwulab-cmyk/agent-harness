# Retro Skill — 評測範例

## 好的輸出範例

> 題目：對最近 6 筆任務做週期 retro

```markdown
# Retro 2026-05-15

## 數據摘要
- 涵蓋期間：2026-04-27 → 2026-05-09（上次 retro 截止點：2026-04-26）
- 任務總數：6 / 完成：5 / 失敗：0 / 部分：1 / 待執行：0
- 錯誤次數：1（SPEC-04 事實引用錯誤，任務 20260509-N02）
- Token 消耗（估計）：F01 18K / T01 9K / T02 24K / T03 42K / A01 28K / N05 14K
  → T03 超出 COST_POLICY deep-dive 建議上限 32K，已在 task card 預告為實驗

## 五維發現

### 成本
- T03 42K 超出 COST_POLICY research deep-dive 建議 32K（依據：20260502-T03 notes）
- 其餘 5 任務均在預算內
- 建議 MED：COST_POLICY 新增「實驗性深度研究」例外欄位，明訂最高 50K + 事後 retro 必填

### 錯誤
- 1 筆 SPEC-04（草稿引用未交叉驗證）：20260509-N02 修正 A01 §1.1 錯誤歸因
- 上次 retro 後同類錯誤首次出現，不達「2 次升級」閾值，觀察即可

### 流程
- N06（plugin bootstrap）因工具範圍限制跨 2 個 session，DoD 留 2 條未完成（依據：20260509-N06 notes）
- 建議 LOW：GATE_POLICY 新增「工具範圍限制」標準備注欄，讓跨 session DoD 可明確標記而非只在 notes 寫

### 權限
- T01/T02/T03 均為 approval_needed: false，全部自動通過，無畢業候選
- N06（risk=high）核准後 PR #69 執行順利，approve 流程運作正常

### 品質
- 積壓在 drafts/ 的晉升候補：
  - outputs/drafts/2026-05-09_methodology_outline.md（W01，done）
  - outputs/drafts/2026-05-09_n08_w01-chapter-one-draft.md（N08，done）
- DoD 品質：T01-T03 成本對照用途明確，DoD 寫得夠具體；N06 DoD 有 9 條但 2 條受工具限制

## 建議修改清單
- [MED] COST_POLICY.md §research 新增「深度實驗」例外欄位（上限 50K + 事後 retro 必填）→ 依據：20260502-T03
- [LOW] GATE_POLICY.yaml 新增 tool_scope_limitation 備注欄 → 依據：20260509-N06

## 待人工確認
- Draft → Report 晉升候補：W01 方法論大綱、N08 第一章草稿（兩份已 done，等使用者確認是否晉升）
- 專案封存候補：無
- 新技能 / 自動化建議：無（governance_metrics.py 月度人工觸發已足夠）
```

**為什麼好**：數據摘要有具體數字；每條發現都附 task_id；建議分 HIGH/MED/LOW；不自動執行修改；待確認清單具體可行動。

---

## 壞的輸出範例

> 同一批任務的錯誤 retro 輸出

```markdown
# Retro 2026-05-15

這批任務整體表現不錯。發現了一個關於 token 使用過多的問題，
應該要改進。另外有些任務審批比較麻煩，可以考慮調整。

建議：
- 控制 token 使用
- 簡化審批
- 改善錯誤處理
```

**哪裡錯**：
- 沒有數據摘要，無法量化
- 每條建議都沒有 task_id 作為證據（「感覺上」）
- 建議模糊（「控制 token」→ 怎麼控制？修改哪個檔案的哪個段落？）
- 沒有 Draft→Report 晉升候補、專案封存候補
- 缺少五維分析框架

---

## 判斷標準

| 項目 | 通過 | 不通過 |
|------|------|--------|
| 數據摘要 | 有具體數字（任務數、錯誤次數、token 估計） | 只有定性描述 |
| 證據引用 | 每條發現附 task_id | 無引用，只說「感覺上」|
| 建議具體性 | 指向檔案名 + 段落 | 只說「應該改進」|
| 不自動執行 | 草稿完成後等待確認 | 草稿中已宣稱「已修改 system/ 檔案」|
| 晉升候補 | 明確列出待晉升的 drafts | 未列或「沒有」但 drafts/ 有積壓 |
