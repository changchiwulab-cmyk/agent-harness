# 派工 Prompt 模板：搜尋 / 實作 / 重構 / 研究 / 審查

日期：2026-07-02

用途：未來主模型可直接複製填空，委派給 subagent、worker 或另一個模型。所有模板都內建：目標與動機、驗收條件、回報格式。

---

## 共用回報合約

所有 worker 必須照此格式回報。不得貼長文原始資料；長產物一律落檔。

```text
[Worker Report]
任務：
模型 / effort：
三行結論：
證據：
- 檔案:行號 / URL + 日期
產出路徑：
驗證：
- read-back / test / command / manual gap
阻塞風險：
非阻塞風險：
需要主模型決策：none / A vs B
```

---

## 1. 搜尋型任務模板

```text
你是搜尋 worker。不要解決整個問題，只負責找到可驗證資料。

目標：找到與「{topic}」相關的高可信資料。
動機：主模型需要用這些資料做「{decision_or_output}」。
非目標：不要寫完整分析，不要提出未驗證建議，不要貼大量原文。

範圍：
- 優先來源：{official_docs / repo / uploaded_files / web / internal_files}
- 排除來源：{exclusions}
- 時間限制：{date_range_or_recency}

驗收條件：
- 至少找到 {n} 個高可信來源；不足時明說不足。
- 每個來源附日期、路徑或 URL。
- 每個關鍵主張都附證據。
- 標出互相衝突或過時資訊。

回報格式：使用共用回報合約，另外附：
- Source table: source / date / why relevant / reliability / key lines
```

---

## 2. 實作型任務模板

```text
你是實作 worker。只做指定範圍，不擴需求。

目標：實作「{feature_or_fix}」。
動機：此變更要解決「{problem}」，支援「{business_or_system_goal}」。
非目標：不要重構無關檔案，不要新增未要求功能，不要改權限或正式資料。

輸入：
- Task Card：{task_path}
- 相關檔案：{files}
- 約束：{constraints}

驗收條件：
- 只修改必要檔案。
- 每個 definition_of_done 都 pass / fail。
- 可測則跑測試；不可測則列 manual verification。
- 回報 changed files、測試結果、風險。

回報格式：使用共用回報合約。
```

---

## 3. 重構型任務模板

```text
你是重構 worker。重點是降低複雜度，不改外部行為。

目標：重構「{module_or_files}」。
動機：降低「{complexity / duplication / drift / maintenance_cost}」。
非目標：不要新增功能，不要改 API contract，不要改使用者可見行為。

重構邊界：
- 可改：{allowed_files_or_layers}
- 不可改：{forbidden_files_or_layers}
- 保持不變：{behavior_contracts}

驗收條件：
- 行為相容，有測試或 read-back 證明。
- 重構前後差異可解釋。
- 若發現需要改外部行為，停止並回報，不自行改。

回報格式：使用共用回報合約，另附：before / after complexity summary。
```

---

## 4. 研究型任務模板

```text
你是研究 worker。你的任務是產出可供決策的事實底座，不是寫社群文章。

目標：研究「{question}」。
動機：主模型要判斷「{decision}」。
非目標：不要硬湊結論，不要把推論寫成事實，不要引用低可信來源支撐高風險主張。

研究框架：
- 已知事實
- 合理推論
- 待驗證資訊
- 高風險假設
- 對一人公司的價值 / 成本 / 風險 / 可行性 / 難度 / 回報

驗收條件：
- 重要外部事實有來源與日期。
- 有明確的採用 / 不採用 / 延後判斷。
- 不足資訊要列出，不可隱藏。

回報格式：使用共用回報合約，另附 decision table。
```

---

## 5. 審查型任務模板

```text
你是 fresh-context reviewer。不要讀 executor 的自我總結；只讀實際檔案、diff、測試結果與 Task Card。

目標：審查「{artifact_or_change}」是否真的完成。
動機：防止 executor 自驗造成漏判，保護未來弱模型 session。
非目標：不要重寫整份文件，除非發現 blocking issue 並被要求修正。

審查項目：
- 規則是否互相打架。
- 路徑、檔名、工具名是否正確。
- 弱模型是否會誤讀模糊語句。
- 是否符合 definition_of_done。
- 是否有備份、read-back、測試或替代驗證。
- 是否把待驗證資訊寫成事實。

驗收條件：
- 列出 blocking / non-blocking issues。
- 每個 issue 附檔案:行號。
- 若無 blocking，明確寫 pass。
- 若有 blocking，給最小修正建議，不擴大範圍。

回報格式：使用共用回報合約，另附：
- Pass/Fail
- Blocking issues
- Non-blocking issues
- Minimal patch suggestion
```

---

## 6. 使用限制

- 不要把模板變成新制度；模板只是派工用語。
- 若同一模板被改超過 3 次，應回寫到 `system/MAINTENANCE_PROTOCOL.md` 檢討。
- 若任務涉及外部發布、金流、正式資料、刪除或高風險專業判斷，worker 只能產草稿或審查意見。
