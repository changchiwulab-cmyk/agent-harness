# 審查報告：system/GLOBAL_RULES.md

## 總體評估

**有條件通過**

GLOBAL_RULES.md 結構清晰，核心原則正確，覆蓋了主要執行場景。但存在 2 項必須修改的缺漏，以及 4 項建議強化的細節。整體架構健全，修改後可升為「通過」。

---

## 通過項

- **核心原則區塊**：清楚說明設計哲學，四個待補洞（穩定目標/上下文邊界/權限意識/自我驗證）的框架完整
- **任務規則**：Task Card 強制要求、definition_of_done 必填、查詢限制均明確
- **輸出規則**：事實/推論/待驗證三層分類規則一致，與各 skill/SKILL.md 格式相符
- **記憶規則**：短期/長期記憶邊界清晰，禁止自動儲存的規則正確
- **工具使用規則**：白名單概念正確，與 PERMISSIONS.yaml allow 清單吻合
- **成本意識**：優先順序正確（本機 > web），避免重複查詢的原則合理
- **失敗分類學引用**：以路徑引用取代全文複製，符合 Context 硬限制設計

---

## 必須修改

**M1：輸出路徑未區分 drafts/ vs reports/**

- **位置**：`## 輸出規則` → 第一條「所有正式輸出存入 outputs/（drafts/ 或 reports/）」
- **問題**：僅列出括號說明，未說明兩個路徑的觸發條件差異。PERMISSIONS.yaml 明確指出 `write_reports`（寫入 outputs/reports/）需要人工確認，但 GLOBAL_RULES 中無此說明。新使用者會不清楚何時用 drafts/、何時才能用 reports/。
- **建議**：補充一行：「草稿輸出進 drafts/（可自動執行）；reports/ 需人工確認（ask 權限）」

**M2：Checkpoint 格式未定義**

- **位置**：`## 工具使用規則` → 第四條「累計超過 5 次工具呼叫 → 先 checkpoint」
- **問題**：GLOBAL_RULES 提到 checkpoint 概念，但 checkpoint 的 git commit 格式定義在 CLAUDE.md（`checkpoint: [task_id] [階段描述]`）而非 GLOBAL_RULES，造成規則分散。若 CLAUDE.md 更新但 GLOBAL_RULES 未同步，可能造成格式不一致。
- **建議**：在工具使用規則中加入一行格式引用：「格式見 CLAUDE.md #Checkpoint 區塊」

---

## 建議修改

**S1：任務規則缺少 Skill 路由說明**

- **位置**：`## 任務規則`
- **問題**：任務規則提到 Task Card 但未提到 skill_type 路由邏輯（research/writing/analysis/ops/review）。新使用者不知道 Task Card 中的 skill_type 欄位連結到哪裡。
- **建議**：加一行「任務 skill_type 決定執行流程，詳見 system/ROUTING_RULES.md」

**S2：記憶規則引用路徑不完整**

- **位置**：`## 記憶規則` → 第四條「memory/active_projects/ 下每個專案一個資料夾」
- **問題**：路徑格式提到了但未說明 decisions/ 子資料夾的存在，DECISION_LOG_TEMPLATE.yaml 的存在在 GLOBAL_RULES 中完全沒有提及。
- **建議**：補充「decisions/ 子資料夾儲存 DECISION_LOG_TEMPLATE.yaml 格式的決策紀錄」

**S3：輸出規則未定義「高風險假設」標記**

- **位置**：`## 輸出規則`
- **問題**：規則提到「已知事實 / 合理推論 / 待驗證 / 高風險假設」四分類，但僅前三項在說明中有對應的輸出格式，「高風險假設」只在分析類 skill 使用。若其他 skill 也需要標記高風險假設，缺乏指導。
- **建議**：明確說明「高風險假設」適用於 analysis 類輸出，其他 skill 以「待驗證」處理即可

**S4：成本意識缺少與 COST_POLICY.md 的連結**

- **位置**：`## 成本意識`
- **問題**：成本意識章節是概念性原則，具體的 token 預算、任務類型上限等定義在 system/COST_POLICY.md，但 GLOBAL_RULES 沒有引用。
- **建議**：加一行「具體 token 預算與工具呼叫上限見 system/COST_POLICY.md」

---

## Definition of Done 逐條確認

- [x] 逐節確認 GLOBAL_RULES.md 的所有規則區塊（7 個區塊全部完成）：**通過**
- [x] 列出缺漏項目（M1 輸出路徑區分、M2 Checkpoint 格式）：**通過**
- [x] 列出與其他系統文件的潛在矛盾或不一致（M1 與 PERMISSIONS.yaml 不一致、M2 與 CLAUDE.md 格式分散）：**通過**
- [x] 每個問題項目有具體修改建議：**通過**
- [x] 最終給出總體評估（有條件通過）：**通過**
