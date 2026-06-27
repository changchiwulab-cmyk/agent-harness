# Subagent Policy — 受控子代理（M5）

> 區分兩件被混為一談的事：
> **「情境隔離子代理」（該做、本架構納入）** vs **「多代理 swarm」（仍在不做清單）**。
> 對齊 Claude Agent SDK：subagent = fresh context window 的情境隔離原語，不是自治群。

## 為什麼要「子代理」但不要「swarm」

- **問題**：寬探索（掃很多檔/搜很多來源）會污染母代理 context、撐爆預算。
- **業界解**：派**唯讀子代理** fan-out 探索，各自燒自己的 context，只回傳精煉摘要（母代理只花幾百 token）。
- **這不是 swarm**：沒有對等 agent 互相寫入/行動，只有「母代理指派唯讀研究 → 收摘要」。

## 硬邊界（嚴守「可控 > 能力」）

| 規則 | 內容 |
|------|------|
| **唯讀** | 子代理 `allowed_tools` 僅唯讀（讀檔/搜尋/抓取）；**禁止**寫檔、git、外發、shell 變更 |
| **單一決策者** | 所有決策、所有產出、所有寫入**只由母代理**執行 |
| **全 gate 在母代理** | 子代理結果回來後，母代理照常跑 GATE 四層 + provenance 標記（子代理抓的外部資料一律 `[外部未驗證]`） |
| **結果復驗** | 母代理不得直接採信子代理摘要為事實；關鍵主張需復驗來源 |
| **成本上限** | 子代理 token 數倍增；fan-out 數量受 COST_POLICY 約束，非必要不派 |
| **仍不做 swarm** | 無對等 agent、無 agent 間直接通訊、無自治寫入/行動——維持單核心治理 |

## 與既有模組的關係

- **Context Engineering（M3）**：子代理是 JIT 檢索的 fan-out 手段（情境隔離）。
- **Security（M2）**：子代理擴大「未受信任內容曝露」（trifecta ②），但因唯讀 + 母代理無自動外發（③ 已切斷），不增加外洩風險。
- **COST_POLICY**：fan-out 是成本放大器，列入成本意識。

## enforcement 點（符合 J5）

- 子代理 `allowed_tools` 限唯讀：由 Task Card 白名單 + `permissions_guard.py`（deny 寫入類）守。
- 母代理對子代理結果套 GATE + `[外部未驗證]` provenance（見 SECURITY_ARCHITECTURE.md）。

## 後續（另開卡）

- 子代理唯讀工具集的 settings.json / hook 範本化（確保子代理不可寫）。
