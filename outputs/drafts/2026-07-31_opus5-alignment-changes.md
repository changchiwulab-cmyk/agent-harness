# Opus 5 對齊變更摘要 — 20260731-O01

- **卡片**：`tasks/2026-07-31_opus5-alignment-uplift.yaml`（risk medium，approval_needed）
- **依據**：`outputs/drafts/2026-07-31_opus5-alignment-analysis.md`（20260731-A01，選項 C）
- **範圍**：文件與設定層。治理骨架、閘門腳本、CI 一行未動。
- **checkpoint**：`d343dd7`（C1）

## 變更清單（10 個檔案：4 份 policy/schema/規則 + 5 支 agent + 1 支 skill）

| # | 檔案 | 變更 |
|---|---|---|
| 1 | `system/COST_POLICY.md` | 路由表改為「alias → 當代對映」並刪去寫死的版本號（4.5/4.6/4.8 已全數過期，把過期本身寫成表下註記當教訓）；實際模型以 `request_model` 為準 |
| 2 | `system/COST_POLICY.md` | 新增「effort 維度」小節：成本模型由一維（tier）升為二維（tier × effort），各 skill_type 建議起始值（ops `low`／research·writing·review `medium`／analysis `high`），方法為「設起點後往下掃到品質開始掉」 |
| 3 | `system/COST_POLICY.md` | 兩個反直覺註記：effort 不是縮短輸出的手段；低 effort 已可能勝過前代高 effort（後者動搖三層分流前提，本次決議先不動、記為觀察點，累積 ≥3 筆帶 effort 樣本後於 retro 重評） |
| 4 | `system/COST_POLICY.md` | 校準係數表加時代標記：既有 4 筆樣本標為 pre-Opus-5、effort 未標註、不可與新樣本混算；新增 effort 欄 |
| 5 | `system/COST_POLICY.md` | context 基準表修正實測值（~400 → ~2,340；skill 200-600 → 521-985），新增「最小可快取前綴」列（Opus 5：512／前代 1,024），並標注量測方式與回填時機 |
| 6 | `system/EXECUTION_LOG_SCHEMA.yaml` | `request_model` 註解世代中性化＋值格式規範（`<family>-<tier>-<generation>`）；新增 optional `effort` 欄（`low`…`max`／`not_recorded`），讓校準係數可按 effort 分層 |
| 7 | `CLAUDE.md` | 修正 baseline 實測值、補 prompt cache 門檻說明、新增「產出紀律」三條（範圍／長度／委派）；段落標題由「軟性護欄」改為「CI 硬閘」以符實情 |
| 8 | `system/GLOBAL_RULES.md` | 新增「產出紀律」三段：範圍紀律（含**不自行縮小範圍**、全做完才回報完成）、長度紀律、委派紀律（含驗證與收尾留主線） |
| 9 | `.claude/agents/*.md` ×5 | 收尾措辭由「完成後回報」改為「交一份對照表 + 這是稽核產物、不為填表再跑一輪自我驗證」；保留逐條對照 DoD；analysis-specialist 的 `opus` 改述為 alias → 當代最強層。**`model` frontmatter 未動** |
| 10 | `skills/writing/SKILL.md` | 執行流程第 5 步由開放式「自我檢查：邏輯、用詞、格式、完整度」改為**有界**收尾：契約面對照 Task Card（`expected_output` ＋ DoD 篇幅約束），內容面保留三項自動閘測不到的檢查（自相矛盾／專有名詞不一致／數據無來源）；新增「篇幅紀律」小節 |

## 驗證結果（全綠）

| 項目 | 結果 |
|---|---|
| `check_context_budget.rb` | OK，1,106 + 1,234 = **2,340 / 3,000**；6 支 SKILL.md 全數 ≤ 1,500 |
| `check_spec_consistency.rb` | OK |
| Python 單元測試 ×13 | 全 OK |
| Ruby 單元測試 ×4 | 76 runs / 199 assertions / 0 failures |
| e2e ×4 | 全 OK |
| `run_evals.py`（rule judge） | 2 cases 皆能區辨 gold/bad |
| 確定性閘門零變更 | `git diff --name-only` 未命中 `gate_check.py`／`verification_loop.py`／`GATE_POLICY.yaml`／`.github/workflows/` |

context budget 是本次唯一有硬性失敗模式的一項：改動前 1,620，改動後 2,340，仍有 660 tokens 餘裕。

## 兩項須知

1. **`scripts/check_context_budget.rb:6` 的註解仍指向舊段落名「Context 硬限制」**（CLAUDE.md 現為「Context 上限」）。修這行需要 `file_write`，不在本卡 `allowed_tools` 內，`allowed_tools_guard.py` 當下攔下——依範圍紀律不擴卡，留作後續一行修正。這也是白名單機制實際生效的一次紀錄。
2. **effort 二維模型目前是零樣本**。新增的 `effort` 欄要有人真的填，校準係數表才重建得起來；舊 4 筆已明文標為不可混算，等於刻意讓成本模型退回「粗估可用、分層待建」的狀態。

## Review 回應（PR #141，Codex 4 則，全數採納）

| 意見 | 判定 | 處置 |
|---|---|---|
| CLAUDE.md 的 baseline 仍是改動前的 1,620 | **成立**——填了自己改動前的數 | 兩處回填 2,340（1,106 + 1,234）；COST_POLICY 同步，並在量測方式註記補上「包含同一次改動自己造成的增量」 |
| writing skill 移除了唯一的內容檢查，`gate_check.py` 只驗產出存在 | **成立**——原措辭「其餘交給四層閘」高估了自動閘的覆蓋範圍 | 第 5 步改為有界兩面：契約面對照 Task Card，內容面保留自相矛盾／專有名詞／數據來源三項，並註明理由是自動閘測不到 |
| 篇幅紀律指向 `expected_output`，但模板只有 format/location/filename | **成立**——現行卡片的篇幅約束寫在 DoD | 規則改為「先看 DoD 再看 expected_output，兩處都沒寫才算未指定」；CLAUDE.md 與 GLOBAL_RULES 同步。**未**新增 schema length 欄——那是模板＋驗證器變更，超出本卡範圍，列入建議下一步 |
| result_summary 記 `DoD 9/9`、`8 檔`，實為 10 項、10 檔 | **成立**——計數錯誤，且會被複製進 AUDIT_LOG | 更正為 10/10 與「10 個檔案（4+5+1）」的明確拆解 |

四則都是事實層面的錯誤或過度宣稱，無一需要架構討論，故直接修正未另行詢問。

## 建議下一步

- 下一張卡執行時在 run log 填 `effort`，開始累積新樣本。
- 累積 ≥3 筆後於 retro 重評「三層模型分流 vs 單一模型 + effort 分層」。
- 順手修掉上述註解漂移（一行，任何有 `file_write` 的卡都可帶）。
- 評估在 Task Card schema 的 `expected_output` 新增 `length` 欄並納入驗證（Codex 第 3 則的另一個選項）——需同步改模板、`check_spec_consistency.rb` 與既有卡片，應獨立開卡。
