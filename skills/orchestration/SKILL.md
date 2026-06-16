# Orchestration Skill（有界編排）

## 用途
把需要**多步驟依賴或可並行**的需求，拆成多張子任務 Task Card，宣告 DAG，排程執行，最後 fan-in 彙整。
這是**控制型 meta-skill**：本身不產內容，而是協調其他 skill（research/analysis/writing/ops/review）的子任務。

與單純線性接力的差異：線性接力用 output 檔依序接（見 ROUTING_RULES）；orchestration 用於有依賴或可並行的情境。

放行依據：決策 D009（局部 carve-out D003）。設計：`outputs/reports/bounded-orchestration-design-v1.md`。

## 執行流程
1. 確認整體 goal 與 definition_of_done（父卡）
2. 拆子任務：**一張子卡一個 skill**，各自有獨立 Task Card
3. 畫 DAG：父卡 `subtasks` 宣告每個 `{id, card, depends_on}`
4. 排程：`depends_on` 為空者經原生 Agent tool **並行 fan-out**；有依賴者依拓樸序，上游 output 作下游 input
5. 每個子任務**各自走 schema/rule/completion/risk 四層 gate 與 checkpoint**
6. fan-in：全部完成後彙整到 `fan_in.into`，做交叉檢查
7. 父卡層級再走一次四層 gate

## 輸出格式（fan-in 彙整報告）
```markdown
# [編排目標]

## 結論
[一段：整體結論]

## 子任務結果
- s1（research）：[摘要 + output 路徑]
- s2（writing）：[摘要 + output 路徑]

## 彙整與交叉檢查
[子任務結果之間是否一致／互補／衝突]

## 待驗證
- [項目]：驗證方式

## 來源對應
- 各結論對應到哪個子任務的哪段 output
```

## 品質標準
- 每個子任務都有獨立 Task Card 與 gate，編排層**不繞過**任何治理
- DAG 無環；`depends_on` 只指向存在的子任務 id
- 失敗的子任務分支不污染其他已完成分支（已 checkpoint 保留）
- 彙整結論可追溯到各子任務 output

## 常見失敗模式
- 把編排當成開放式 agent-to-agent 自由對話 → 必須是 Task Card 治理下的有界編排
- 子任務沒有獨立卡 → 每個子任務都要能單獨驗證
- DAG 有環或依賴懸空 → schema 驗證（validate_task_card.py）會擋
- 父卡 max_tool_calls 未涵蓋子任務加總 → 設為各子卡上限的護欄
