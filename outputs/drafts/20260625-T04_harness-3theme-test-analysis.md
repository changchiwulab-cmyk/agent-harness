<!--
task_id: 20260625-T04
date: 2026-06-25
skill_type: review
status: draft
-->

# 框架回測報告：3 主題端到端自測（T01–T03）

> 受測對象不是內容對錯，而是 **harness 本身**：四層 gate 是否逐層成立、成本是否落在 COST_POLICY 預算內、是否觸發 FAILURE_TAXONOMY 模式、run-log scope 是否漏記、低風險卡是否讓部分 gate 空轉。

## 總體評估

**通過（harness 在 3 個不同主題、跨 2 種 skill 下成立）。** 四層 gate 對三張卡逐層執行，無規則或權限違反；3/3 卡 DoD 全數通過（其中 T02 由 completion_check 在第一輪攔下一處缺漏並補正）；成本全部落在任務級預算內；無逃逸的失敗模式。**唯一需揭露的方法學限制：本卡與 T01–T03 為同一 session 產出，屬 review skill 明列的『循環驗證（自己審自己）』失敗模式**——結論可信度因此打折，建議由不同 session／人工複核（見「必須修改」第 1 條）。

## 通過項

- **schema_check**：4 張卡（含本卡）皆通過 `validate_task_card.py` 與 `check_spec_consistency.rb`，task_id 格式、必填欄位、日期一致性全綠。
- **rule_check**：所有工具呼叫在各卡 `allowed_tools` 白名單內；無觸及 PERMISSIONS deny 清單；web search 每卡 ≤ 上限；無未授權動作。
- **completion_check**：逐條比對 DoD，T02 缺漏被即時攔截（見下）。
- **risk_check**：3 卡皆 low、輸出全鎖在 `outputs/drafts/`，無晉升 reports/、無對外動作。
- **硬規則遵守**：先建卡才執行（#1）、輸出只到 drafts（#2）、無連續失敗（#3 未觸發）。

## 必須修改

- **[方法學／循環驗證] 本回測由同 session 產出，需異 session 或人工複核**：review skill 失敗模式明列「自己的輸出審查自己」。建議：將本報告交由獨立 session 跑一次 review，或人工抽查 T01–T03 的事實正確性（尤其 [待驗證] 項）。

## 建議修改

- **[證據留存] run-log 對「乾淨成功的測試批次」零紀錄**：見「框架缺口」第 1 條，建議為測試型批次加可選的強制 run-log。
- **[gate 覆蓋] 低風險批次未實際運動到 risk/approval 路徑**：見「框架缺口」第 2 條。

## 1. Gate 結果表

| Gate | T01 (research) | T02 (research) | T03 (analysis) |
|------|------|------|------|
| schema_check | pass | pass | pass |
| rule_check | pass | pass | pass |
| completion_check | pass（DoD 7/7） | **pass（7/7，第 1 輪缺 DoD#3『實務影響』獨立節 → 補正後通過）** | pass（DoD 7/7） |
| risk_check | pass（low→drafts） | pass（low→drafts） | pass（low→drafts） |

關鍵觀察：completion_check 是本次唯一「真的擋下東西」的 gate——T02 第一輪把實務影響折進「合理推論」而漏了 DoD 指定的獨立節，被逐條比對抓出並補上 5 條落地檢查點。**這是 gate 有效性的正面證據**（防住 VAL-01 假完成 / VAL-02 驗證不完整）。

## 2. 成本對照表

| 卡 | skill | token 估計 | 任務級預算 | 用量比 | web search |
|---|---|---|---|---|---|
| T01 | research | ~13K | 32K | ~41% | 2 / 3 |
| T02 | research | ~15K | 32K | ~47% | 2 / 3 |
| T03 | analysis | ~15K | 20K | ~75% | 2 / 3 |
| T04 | review | ~8K | 23K | ~35% | 0 / 0 |

*（來源：rule_estimated，非 dashboard 實測；EXECUTION_LOG token_estimate.source 應標 `rule_estimated`。）*

- 三張內容卡都**主動少用 1 輪 web search**（2/3）——與既有 20260502-T01 quick-scan 的「夠了就停」行為一致，呼應 COST_POLICY「能讀檔/夠用就別多查」。
- 無一卡逼近 `max_tool_calls`；analysis（T03）用量比最高（75%），符合 analysis 多選項評估較重的預期。

## 3. 失敗模式盤點（對照 system/FAILURE_TAXONOMY.yaml）

| 類別 | 代表模式 | 本次狀態 |
|---|---|---|
| 規格 SPEC | 角色/目標違反、步驟迴圈、不知何時停 | 未觸發（每卡綁定單一 skill + DoD，2/3 search 即停） |
| 協調 COORD | Context 重置、模糊需求硬做、目標偏離 | 未觸發（需求已於 plan 階段以 AskUserQuestion 釐清） |
| 驗證 VAL | 假完成、驗證不完整、判斷錯誤 | **近觸發即攔截**：T02 假完成風險被 completion_check 擋下；VAL-03（自審）為本卡已揭露之殘留風險 |
| 安全 SEC（獨立維度） | 未授權動作、資料洩漏、成本失控、幻覺行動 | 未觸發（全 allow 動作、無外發、成本在預算內、事實附來源並標 [待驗證]） |

亮點：相較 2026-04 的 S01（web search 第 3 輪 rate-limit），本次因每卡只用 2 輪、未逼上限，**未重演 rate-limit**。

## 4. 跨主題一致性分析

- **格式遵循度**：T01／T02（research）皆嚴格走六區塊（結論→已知事實→合理推論→待驗證→高風險假設→來源）；T03（analysis）走七維表 + 含「不做」選項。3/3 符合對應 skill 的輸出規範。
- **四態分離**：事實／推論／待驗證／高風險假設在 3 卡一致且清楚分區——這是 harness 跨主題最穩定的行為。
- **DoD 通過率**：T01 7/7、T02 7/7（1 次補正）、T03 7/7。
- **行為差異**：唯一差異來自 skill 本質（research 收斂事實 vs analysis 給排序建議），非框架不穩定。**結論：harness 行為由 skill 規範驅動、跨主題一致，未見因換題而漂移。**

## 5. 框架缺口與建議（可行動）

1. **run-log scope（D006）對「乾淨測試批次」零紀錄**：3 張卡皆 low-risk、status=review、各僅 1 checkpoint，**全部不滿足 logs/runs/ 觸發條件**（failed/partial/high-risk/≥3 checkpoints），故本次零 run-log，僅進 AUDIT_LOG。對「刻意做測試」的場景證據偏薄。**建議**：為測試型批次新增可選旗標（如卡上 `test_batch: true`）強制寫 run-log；或承認本 T04 報告即為該批次的彙整證據。
2. **低風險批次讓 risk/approval gate 空轉**：4 卡全 low，risk_check 永遠 trivially pass、approval 從未被觸發。harness 的 high/critical 與批准路徑目前只靠 R5 故障演練覆蓋，正常營運不會運動到。**建議**：定期排一張 medium/high 卡（或沿用 test_failure_drill）以保持該路徑「有被走過」。
3. **web-search 上限是事後保護、非事前節流**：本次靠 agent 自律停在 2/3；但若某卡需要 3 輪且與其他卡時間接近，COST_POLICY 的 3-cap + 既有 S01 顯示仍有 rate-limit 風險。**建議**：對同批多卡的 web search 加入間隔或結果快取。
4. **completion_check 依賴執行者誠實自評**：本次它有效（抓到 T02），但與 VAL-03 自審風險同源。**建議**：高價值產出在 completion_check 後再過一次異 session review（即把 T04 模式制度化）。

## Definition of Done 逐條確認（本卡 T04）

- [x] 條件1：Gate 結果表（schema/rule/completion/risk × T01–T03，逐格 pass/fail + 佐證）→ 通過（§1）
- [x] 條件2：成本對照表（token vs 預算 + web search 次數）→ 通過（§2）
- [x] 條件3：失敗模式盤點（對照 FAILURE_TAXONOMY，觸發/未觸發）→ 通過（§3）
- [x] 條件4：跨主題一致性分析（格式遵循、DoD 通過率、行為差異）→ 通過（§4）
- [x] 條件5：框架缺口與建議 ≥3 條可行動 → 通過（§5，共 4 條）
- [x] 條件6：符合 review skill 格式（總體評估/通過項/必須修改/建議修改/DoD 逐條）→ 通過
- [x] 條件7：結論明確回答 harness 是否成立 → 通過（見總體評估與下方結論）

## 結論

**harness 在 3 個不同主題、跨 research×2 + analysis 下成立且行為一致。** 四層 gate 逐層執行、completion_check 實際攔下一處缺漏、成本全在預算內、無逃逸失敗模式、硬規則全守。框架的價值主張（可控 / 可審核 / 可量化）在這次多主題壓力下站得住。**真正值得補的不是「能力」，而是「證據與覆蓋」**：乾淨成功批次缺 run-log、低風險批次讓 risk/approval gate 空轉、以及同 session 自審的循環驗證限制——前兩者是 §5 的可行動建議，後者需異 session／人工複核才能完全消除。

## 來源（受審文件，本 session 產出）

- `outputs/drafts/20260625-T01_llm-pricing-capability-trend.md`
- `outputs/drafts/20260625-T02_ai-governance-regulation.md`
- `outputs/drafts/20260625-T03_multi-agent-framework-selection.md`
- 規則依據：`system/GATE_POLICY.yaml`、`system/FAILURE_TAXONOMY.yaml`、`system/COST_POLICY.md`、`system/EXECUTION_LOG_SCHEMA.yaml`

---
*字數約 1,950 字（中文實算）。web search：0 輪。skill：review。方法學限制：同 session 自審（循環驗證），詳見總體評估。*
