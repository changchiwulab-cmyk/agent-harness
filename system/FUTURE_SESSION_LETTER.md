# 給未來 session 的信

日期：2026-07-02

## 結論

你接手的是一套一人公司 harness，不是企業級 agent 平台。你的任務是讓下一個 session 少犯錯，不是展示你能新增多少規則。

## 三件最重要的事

### 1. 不要再把系統變重

這個 repo 已有 Task Card、Gate、Permissions、Cost Policy、Audit Log、Failure Taxonomy 的方向。優先擴展既有 `research / analysis / writing / ops / review`，不要急著新增 parallel skill 或 subagent。

### 2. 讓弱模型變強的不是更多口號，而是可驗證格式

請優先補：好壞範例、DoD、read-back、測試、錯誤寫回。不要寫「保持高品質」這種不能驗收的規則。

### 3. 一人公司最怕制度變成第二份工作

每個新增檔案、規則、workflow 都要問：是否低維護、可回復、可手動接管、能節省 Johnny 未來注意力？不能通過就不要新增。

## 最可能退化的方式

1. `CLAUDE.md` 變成百科全書。預防：只放硬規則與路由，超過 100 行就精簡。
2. subagent swarm theater。預防：沒有目標、驗收、回報格式，就不派工。
3. 驗證變成儀式。預防：文件 read-back；程式碼實跑或測試；高風險判斷加第二意見。
4. Memory 變成垃圾桶。預防：未驗證推論不得寫入長期記憶。
5. 模型升級變成逃避。預防：升級時帶原目標、已試方案、錯誤證據、剩餘不確定性。

## 待驗證交接

- 本 session 無法直接讀取使用者本機 `~/.claude/`、`/model`、`/effort`、MCP 與實際 subagent 狀態。
- 下一個 Claude Code session 必須先做本機 discovery，再套用模型調度守則。
- 本分支完成後，先 read-back 與跑 repo 既有一致性檢查，再決定是否合併到 main。

## 最後提醒

制度只收三種東西：會重複發生的錯誤、會節省未來 token 的路由、會降低風險的硬限制。其他內容放草稿，不要污染 boot context。
