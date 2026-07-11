# 深度測試研究 — 三面向綜合（T1/T2/T3）

> **草稿（draft）** ｜ 日期：2026-06-26 ｜ 來源：使用者 `/goal`「做 3 個不同面向的深度測試研究」
> Task Cards：`20260626-001`（T1 可靠性）／`-002`（T2 安全）／`-003`（T3 可觀測性）
> 方法共通：**實證探測**——唯讀執行 harness 自帶 validator/guard/CI 腳本取得真實 pass/fail，再寫成研究草稿。全程 `allow` 權限，**未修改任何 `system/`／`skills/`／`CLAUDE.md`**。

---

## 一句話總結

對 harness 三個關鍵面向做了**真槍實彈的探測**（共 ~95 個探針案例），結論一致指向自我評估那句話的精確化：**harness 的「靜態/結構」維度已生產級，但「動態/真實故障下」維度仍是設計完備而未坐實**——而且這次我們把「未坐實」從口號**量化**成了具體的缺口清單。

## 三面向結論對照

| 面向 | 自評分 | 探針結果 | 一句話 |
|---|:--:|---|---|
| **T1 可靠性/故障恢復** | 可靠 7 / 耐久 6 | schema gate 8/9 多模式攔截 + R5 真實閉環；**rule/completion/risk 仍是 in-process 模擬**；恢復資料源（22 checkpoints）實跑可用 | schema 層生產級，其餘 3 層 gate 真實故障未坐實 |
| **T2 安全/權限邊界** | 安全 9 | 43 例對抗：**0 FP、11 FN**；canonical 全攔、規避有缺口；guard 自承「deny-list 非 sandbox」 | 招牌成立於**架構縱深**，非單一正則；4 個低成本收緊點 |
| **T3 可觀測/防漂移** | 可觀測 6 | 5 腳本全綠（靜態）；**run log 僅 2 筆、19/48 卡卡在 review、零實測 token**；context 餘裕 60% | 規格不漂移已坐實，執行可量化卡在樣本+狀態收尾 |

## 貫穿三份研究的單一主題

> **harness 用「腳本可強制」的地方都很硬（schema 驗證、deny hook、CI 防漂移），用「LLM 自律」的地方都未坐實（rule/completion/risk gate、3-連續-停、狀態收尾）。**

成熟度 3→4 的真正門檻不是再加治理檔，而是**把靠 LLM 自律的關鍵路徑，要嘛真實演練坐實、要嘛加外部可觀測強制**。

## 跨面向最高槓桿動作（建議優先序）

1. **R-T1a — rule/completion/risk gate 真實演練**（仿 R5）。一動三得：坐實 3/4 gate（T1）、餵回工作流層 run log 樣本（T3）、補上「LLM 自律路徑」的實證（主題核心）。**單一最高槓桿。**
2. **R-T3a — Task Card 狀態生命週期收尾**：消除 19/48（40%）卡在 review 的可追溯黑洞。唯讀掃描，成本極低。
3. **R-T2a — 補 4 個低成本 deny pattern**（`/bin/rm` 絕對路徑、`git clean`/`truncate`/`dd`、`+refspec` 強推）+ regression 測試。
4. **R-T1b / R-T2c — 把「LLM 自律」可觀測化/文件化**：3-連續-停加外部計數紀錄；guard 標註「非 sandbox，真實保證來自縱深」。

## 自我合規記錄（一邊測規則、一邊守規則）

本研究本身即 harness 流程的一次正面實例：
- **硬規則 1**：先建 3 張 Task Card（`20260626-001/002/003`）並通過 `validate_task_card.py` 才執行。
- **硬規則 2**：所有產出落 `outputs/drafts/`，未晉升 reports（晉升走 `ask`/RETRO_FLOW）。
- **COORD-02（模糊需求不硬做）**：以 `AskUserQuestion` 澄清「測試對象/三面向/深度」3 項決策後才動工。
- **權限**：全程唯讀執行 + 寫草稿/紀錄（`allow`）；發現的所有缺口**只提案、不就地修** `system/`/`scripts/`（那些走 `ask`）。

## 後續

- 本三份草稿經人工審閱後，可依 `RETRO_FLOW` 晉升至 `outputs/reports/`，並把 R-T1a 等建議各自開 Task Card 落地。
- 使用者於面向題多選的「成本/context」面向，已作為 **T3 的橫切視角**併入（context 餘裕、token 實測缺口）。若要獨立成第 4 份研究，告知即可加開 Task Card。

## 子報告

- `outputs/drafts/2026-06-26_depth-test-t1-reliability.md`
- `outputs/drafts/2026-06-26_depth-test-t2-security.md`
- `outputs/drafts/2026-06-26_depth-test-t3-observability.md`
