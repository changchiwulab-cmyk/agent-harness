# 全域規則 GLOBAL_RULES

## 核心原則

本系統的設計原則不是讓 agent 更強，而是讓 agent 不失控。
LLM 原生缺乏四件事：穩定目標、穩定上下文邊界、穩定權限意識、穩定自我驗證能力。
所有規則都是在補這四個洞。

## 任務規則

- 所有任務必須有 Task Card，無例外
- Task Card 必須包含 definition_of_done，否則不進入執行
- 單一任務最多 3 輪外部查詢，超過需 checkpoint 後再繼續
- 任務中途變更目標時，更新 Task Card 再繼續，不要在空中轉彎

## 輸出規則

- 所有正式輸出存入 outputs/（drafts/ 或 reports/）
- 不確定的資訊標記 [待驗證]
- 不把推論當事實
- 區分：已知事實 / 合理推論 / 待驗證 / 高風險假設

## 記憶規則

- 短期記憶：當前 session，自動管理
- 長期記憶：只有經人工確認的內容才寫入 memory/
- 不自動把對話內容當長期知識儲存
- memory/active_projects/ 下每個專案一個資料夾，存該專案的持久 context
- 重要決策用 tasks/DECISION_LOG_TEMPLATE.yaml 格式記錄到 memory/active_projects/[project]/decisions/
- Decision Log 寫入同樣需人工確認

## 工具使用規則

- 每次任務只使用 Task Card 白名單內的工具
- 工具呼叫前確認輸入格式正確
- 工具返回錯誤時記錄，不要靜默忽略
- 單一任務累計超過 5 次工具呼叫 → 先 checkpoint

## 成本意識

- 能用檔案讀取解決的，不要用 web search
- 能用一次查詢解決的，不要拆成多次
- 長文件用摘要引用，不要全文貼入 context
- 意識到每次 LLM 呼叫都有成本，避免不必要的重試循環

## 失敗分類學

14 種常見失敗模式（規格 42% / 協調 37% / 驗證 21% / 安全獨立維度）。
→ 詳見 `system/FAILURE_TAXONOMY.yaml`，含每種失敗的 ID、描述、緩解措施。
