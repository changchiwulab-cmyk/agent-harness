# Harness v3 遷移就緒度評估（Readiness Assessment）

- Task: `20260620-006`（R10）
- Date: 2026-06-20
- Skill: analysis
- Status: draft（risk_level=low；只評估、不遷移，待人工依 RETRO_FLOW 晉升）

> 定位：本文件不是「怎麼遷移」（那是 `outputs/drafts/2026-05-09_v3_extraction_plan.md`／A01 的工作），而是「**現在準備好遷移了嗎**」。對每個 v2 模組給出 **保留 / 下放原生 / 並存** 的去向 + **就緒度判定**（ready / partial / blocked），盤點不可替代資產，最後對 D003（v2 hold）給出維持或解除的建議。
>
> 與既有決策對齊：D003（維持 v2，下次 retro 再評估）、D007（治理 plugin bootstrap：Apache-2.0 / private / 獨立 repo `agent-governance`）。本評估即 D003 `revisit_trigger` 所要求的「重新檢視」動作。

---

## 0. TL;DR（結論先行）

- **技術就緒度：明顯提升**。R11–R14 把四層 Gate（`gate_runner.py`）、失敗計數（`failure_tracker.py`）、ask 級寫入（`write_guard.py`）抬到 runtime，直接消解 A01 §1.3 症狀 #1「強制力結構嚴重頭重腳輕」——這是 v3 抽出治理層 plugin 時最關鍵的可攜資產。
- **需求就緒度：未達標**。D003 的 v3 觸發條件（context 經常超限、任務類型規則衝突頻繁）目前**皆未滿足**：context budget 1402/3000、無紀錄的規則衝突、近期任務零 failed/partial。
- **建議：Conditional Hold（維持 D003，但升級理由）**。不是「還沒準備好」，而是「準備度提高、但沒有實際需求觸發」。一人公司原則：不做沒有需求的架構升級。把就緒度存著，待任一觸發條件持續 2 週再啟動 v2.5 過渡。

---

## 1. 就緒度三軸評分

| 軸 | 定義 | 2026-05-09（A01 當時）| 2026-06-20（本評估）| 說明 |
|----|------|:---:|:---:|------|
| 技術就緒（強制力）| 治理規則是否可機械驗證、可搬進 plugin hook | 低 | **中-高** | 新增 gate_runner / failure_tracker / write_guard；強制點從 1 hook+3 CI → 3 hook+多測試 |
| 抽出就緒（解耦度）| 治理三件 + 失敗分類學能否獨立於 harness 發布 | 中 | 中 | schema 已穩定；plugin skeleton（N4）已備；尚未 dogfood |
| 需求就緒（觸發）| 是否真的需要拆分 bounded specialists | 低 | **低** | context 未超限、無規則衝突——升級無實際拉力 |

> 健康訊號：技術軸與抽出軸都在前進，需求軸刻意按兵不動。這正是「可控 > 能力」。

---

## 2. 模組逐項就緒度（保留 / 下放原生 / 並存）

> 去向沿用 A01 §4.2 裁決（砍除＝下放原生；抽出＝進治理層 plugin；重構＝介面靠近原生），本表加「**就緒度**」與「**blocker**」兩欄。重疊度數據源 `system/NATIVE_OVERLAP.yaml`。

| # | 模組 | 去向 | 就緒度 | Blocker（達 ready 還缺什麼）|
|---|------|------|:---:|------|
| 1 | Interface | 下放原生（runtime）| ✅ ready | 無；README 改述即可 |
| 2 | Task Card（薄）| 並存（抽治理層 + 留 harness ref）| 🟡 partial | 必填欄位收斂的 v2/v3 雙 schema validator 尚未寫 |
| 3 | Planner/Router | 下放原生 Skills 路由 | 🟡 partial | H1 未驗：原生自動路由能否全取代 ROUTING_RULES |
| 4 | Decision Log | 抽治理層 plugin | ✅ ready | schema 穩定、D001–D008 為樣本；plugin command 待實作 |
| 5 | Context Manager | 並存（CLAUDE.md 留硬上限 + CI）| ✅ ready | 20 輪壓縮為原生；token 上限 CI 已存在 |
| 6 | Skill Executor | 下放原生 Skills | 🟡 partial | N3 PoC 通過；5 個 SKILL.md 尚未全部加 frontmatter |
| 7 | Tool Executor | 並存（allowed_tools 作 hook 輸入）| ✅ ready | permissions_guard + write_guard 已落地 |
| 8 | Gate Verifier | 抽治理層 plugin | ✅ **ready（本批升級）** | **gate_runner.py 已把四層 Gate 變可執行**；plugin 只需包裝為 command/hook |
| 9 | Checkpoint | 下放（git 慣例）| ✅ ready | 無 |
| 10 | Agent Context | 下放（併回 CLAUDE.md）| ✅ ready | 留 stub + 重定向 |
| 11 | Permission | 並存（settings.json 為事實源 + risk_level metadata）| 🟡 partial | H2 未驗：allow/ask/deny 與 risk_level 正交組合 |
| 12 | Approval Policy | 下放（併入 workflow）| 🟡 partial | 邏輯併入 plugin command 尚未實作 |
| 13 | Cost Policy | 並存（校準表保留為 report）| ✅ ready | 校準資料已是 artifact |
| 14 | Failure Taxonomy | 抽治理層 plugin | ✅ ready | 14 類靜態 YAML；failure_tracker 已引用 SEC-03/SPEC-02 |
| 15 | Execution Log（窄）| 抽治理層 plugin | ✅ ready | D006 已收斂觸發範圍；gate_runner 已讀其欄位 |
| 16 | Audit Log | 抽治理層 plugin | ✅ ready | 格式已被 CI lint；generator 已存在 |

**統計**：ready 10 / partial 6 / blocked 0。較 A01 當時，#8 Gate Verifier 因本批 gate_runner 由「待抽出」升為「ready」。

---

## 3. 不可替代資產清單（v3 必須帶走，不可砍）

A01 §4.1 已列治理三件 + 失敗分類學。本評估新增**第五類：runtime 強制層**——這是 2026-05-09 之後才存在的資產：

1. **治理三件**：Decision Log（D001–D008）、Audit Log、DoD 契約。
2. **Failure Taxonomy**（14 類，`failure_tracker` 已實際引用）。
3. **Execution Log Schema**（窄範圍 post-mortem，`gate_runner` 已讀）。
4. **Token 校準資料表**（唯一的成本實證資產）。
5. **🆕 Runtime 強制層**：
   - `gate_runner.py`（四層 Gate 可執行驗證器，schema 重用 `validate_task_card.py`）
   - `failure_tracker.py`（連續失敗 circuit breaker + 自動 error log）
   - `write_guard.py` / `permissions_guard.py`（PreToolUse 路徑與指令守衛）
   - → v3 應直接落為治理 plugin 的 `hooks/`（A01 §5.2 的 `pre_tool_use.py` / `post_task_use.py` 即此），**而非重寫**。這把 A01「強制力頭重腳輕」的最大風險點預先解掉。

> 反例（**可**替代、不帶走）：ROUTING_RULES.md、AGENT_CONTEXT.yaml、Approval Policy 文件、16 模組編號制度。

---

## 4. 與 D003 / D007 的對齊與建議

### 4.1 D003（維持 v2，下次 retro 再評估）
- `revisit_trigger`：任一 v3 觸發條件持續 2 週以上；或單 session context 超限頻率 > 30%。
- **現況檢核**：
  - context 超限？否（1402/3000 ≈ 47%，無單 session 超限紀錄）。
  - 任務類型規則衝突頻繁？否（無紀錄）。
  - 錯誤率阻斷性？否（近期零 failed/partial）。
- **建議**：**維持 hold，但更新理由**——從「能力不足」改為「準備度已提升、需求未觸發」。建議在 D003 補一條 note 指向本評估，並把 `revisit_trigger` 細化為可量測門檻（例：context 超限頻率 > 30% 連續 2 週、或單月 ≥ 2 筆規則衝突 error log）。

### 4.2 D007（治理 plugin bootstrap 決策）
- D007 已定 repo 名 / License / visibility / bootstrap 走法（帶外手動執行）。**本評估不改 D007**，僅補：plugin 的 `hooks/` 應移植本批 runtime 強制層（資產 #5），作為 v3.0 的 dogfood 起點。

---

## 5. Go / No-Go 建議

| 動作 | 建議 | 條件 |
|------|------|------|
| 立即啟動 v3 全面遷移 | **No-Go** | 需求觸發條件未達標（D003）|
| 啟動 v2.5 過渡（雙寫 settings.json、skills frontmatter、AGENT_CONTEXT 併入）| **Conditional-Go** | 任一 D003 觸發條件持續 2 週，或 partial 模組的 blocker（H1/H2、雙 schema validator）被清掉 |
| 把 runtime 強制層整理為治理 plugin `hooks/` 雛形 | **Go（低風險、高槓桿）** | 可在 hold 期間先做，作為 D007 plugin 的 dogfood 種子 |
| 清 partial blocker（H1 路由 PoC、H2 權限正交、v2/v3 雙 schema validator）| **Go（可並行）** | 不破壞 v2；逐項把 partial 升 ready |

---

## 6. 待驗證 / 高風險假設（沿用 A01，更新狀態）

| 項目 | 狀態 |
|------|------|
| H1：原生 Skills 自動路由能取代 ROUTING_RULES | 待驗（影響 #3 就緒度）|
| H2：settings.json allow/ask/deny 與 risk_level 正交 | 待驗（影響 #11 就緒度）|
| H3：plugin 能同時掛 hooks+skills+commands | 待 plugin repo 實作驗證（D007）|
| 🆕 H4：本批 runtime 強制層可原樣移植為 plugin hooks | 待 dogfood——若原生 plugin hook 介面與獨立 script 簽章不同，需加 `adapters/` 薄層 |

---

## 7. 建議下一步（hold 期間可做、不觸發遷移）

1. 在 D003 補 note 指向本評估，細化 `revisit_trigger` 為可量測門檻。
2. 低風險高槓桿：把 `gate_runner` / `failure_tracker` / `write_guard` 整理成治理 plugin `hooks/` 雛形（dogfood 本 repo）。
3. 並行清 partial blocker：H1 路由 PoC、H2 權限正交實測、v2/v3 雙 schema validator。
4. 下次 RETRO 把本評估的三軸就緒度納入儀表，作為 D003 是否解除的依據。
