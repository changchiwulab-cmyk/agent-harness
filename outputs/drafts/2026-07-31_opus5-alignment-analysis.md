# Opus 5 能力對齊分析 — Agent Harness v2

**Task Card**：20260731-A01 ｜ **skill**：analysis ｜ **日期**：2026-07-31
**接力點**：本報告為 20260731-O01（實作）的輸入

---

## 結論與建議

**建議選「選項 C：文件與措辭層對齊，保留三層 alias 路由」。**

理由是這個 harness 的落差不在治理骨架（那層是強項：4 個 PreToolUse guard、兩套 gate 驅動器、278 個單元測試都已佈線），而在**模型層的三個過期前提**：成本模型是一維的（沒有 effort）、prompt 措辭是照 Opus 4.8 的行為特性寫的（Opus 5 有四項反向位移）、文件記載的實測值已漂移到 4 倍。這三項都能靠文件與措辭修正解決，不需要動任何確定性程式碼，因此風險低、可逆、且能立即讓下一批任務的成本量測有意義。

選項 D（全面改 Opus 5 + effort 分層、廢除模型分流）在能力上更誘人——Opus 5 的 `low`/`medium` 常已勝過前代高 effort——但它會讓 COST_POLICY 累積四個月的校準係數表（research 1.43 / writing 2.00 / ops 1.56 / review 1.25）**整張作廢**，而本專案近兩週零提交、review 佇列又堆回 4 張，沒有重新累積樣本的產能。這是能力與產能的錯配，不是能力不夠。

---

## 選項比較

### 選項 A：不做（維持現狀）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 零 | 三個過期前提繼續累積誤差 |
| 成本 | 0 人時 | — |
| 風險 | 中高 | 成本量測持續失真：新任務的 token 數會混入未標註的 effort 變因，校準係數表越量越沒有解讀價值；`ai-bubbly-mountain.md` §5.2 標的最大風險「harness 從『看起來工程化』變成『看起來繁瑣』」正是靠這種漂移累積 |
| 可行性 | 100% | — |
| 執行難度 | 無 | — |
| 預期回報 | 負 | 漂移只會擴大 |
| 一人公司適配度 | 低 | 一人公司最禁不起的就是「量了但數字沒意義」 |

### 選項 B：只修版本引用

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 低 | 只修 `COST_POLICY.md:48-52` 路由表與 `EXECUTION_LOG_SCHEMA.yaml:58` 的 `claude-opus-4-x` |
| 成本 | ~0.5 小時 | 純文字替換 |
| 風險 | 低 | 無行為變更 |
| 可行性 | 100% | — |
| 執行難度 | 極低 | — |
| 預期回報 | 低 | 修掉「看起來過時」，但 effort 缺口與行為位移都沒碰，成本量測仍失真 |
| 一人公司適配度 | 中 | 便宜但沒解決真問題 |

### 選項 C：文件與措辭層對齊，保留三層 alias 路由（建議）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高 | 成本模型從一維升二維（tier × effort）→ 未來每筆樣本可分層解讀；四項行為位移各有對策；實測值漂移修正後 CI 的 context 預算檢查才有基準意義 |
| 成本 | ~3–4 小時 | 7 個檔案（COST_POLICY、EXECUTION_LOG_SCHEMA、CLAUDE.md、GLOBAL_RULES、agents ×5、writing SKILL） |
| 風險 | 低—中 | 全部是文件／措辭，無程式邏輯變更；唯一硬性風險是 CLAUDE.md 改動後可能撞破 3000 token 上限（目前 ~861，餘裕充足）。四個檔案屬 ask 權限，需逐一核准 |
| 可行性 | 100% | 不依賴任何外部資源或帶外動作（對比 N06 plugin 線卡死在建外部 repo 已 3 個月） |
| 執行難度 | 低 | 措辭收斂需要判斷力（哪些「驗證」該砍見下節），但無技術風險 |
| 預期回報 | 中—高 | 立即回報：量測有意義。延遲回報：下次 retro 有分層資料可校準 |
| 一人公司適配度 | 高 | 可在一個 session 內完成、可逆、不引入新維護面 |

### 選項 D：改 Opus 5 + effort 分層，廢除模型分流

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高（理論） | 全部走 opus alias，用 effort 區分（ops=low、research/writing/review=medium、analysis=xhigh），品質上限最高 |
| 成本 | ~3–4 小時實作 **＋ 至少 10 筆新任務的重新校準期** | `COST_POLICY.md:85-91` 的四個係數全部作廢；該表自述「累積 10 筆以上同類任務後，用實測平均 × 1.5 作為建議上限」 |
| 風險 | 高 | 成本模型從「有 4 個係數、2 個標 pending stabilization」倒退回「零樣本」。本專案 2026-06 只開 1 張卡（M1 指標已 warn）、最後提交停在 2026-07-17，沒有產能在合理時間內重建樣本 |
| 可行性 | 60% | 技術可行，但 `.claude/agents/*.md` 是否支援 effort frontmatter 鍵**未經驗證**；`check_spec_consistency.rb:392` 的 `allowed_agent_model` lint 會擋未知鍵 |
| 執行難度 | 中 | 需先驗證 frontmatter 支援度，不支援則整個方案只剩政策層記載＝退化成選項 C |
| 預期回報 | 不確定 | 高上限但無法量化，因為量測基準同時被打掉 |
| 一人公司適配度 | 低 | 「同時改變數與量尺」是量測大忌 |

**排序：C > B > D > A。** D 不是錯的方向，是**時機**不對——它應該等 C 累積出帶 effort 標註的樣本後，用資料驅動地做，而不是現在憑直覺切換。

---

## 落差詳表

### A. effort 維度缺口（最大單項）

全 repo 對 `effort` 的引用只有一處，且是無關的用法：`tasks/2026-05-29_harness-self-assessment.yaml:29` 的「每項含 impact/effort/risk」——那是工作量估計，不是模型參數。**成本控制體系完全沒有 effort 概念。**

Opus 5 的相關事實：

| 事實 | 對本專案的意義 |
|---|---|
| 支援完整 `low`/`medium`/`high`/`xhigh`/`max`，預設 `high` | 現行所有子代理都跑在未宣告的預設值上 |
| `low`/`medium` 表現常已勝過前代的高 effort | 動搖 `COST_POLICY.md:46-52`「便宜任務用便宜模型」的分流前提 |
| effort **不是**縮短可見輸出的手段——降 effort 會改變思考量，不會可靠縮短輸出 | 這是反直覺點，必須寫進文件，否則未來會被誤用來壓 token |
| 建議做法是「設起點後往下掃到品質開始掉」，不是沿用前代預設 | 需要一個成文的掃描方法，否則不會有人做 |

**衍生問題**：`COST_POLICY.md:85-91` 的校準係數表（research 1.43 / writing 2.00 / ops 1.56 / review 1.25，樣本數 2/1/2/2）是在無 effort 概念下量的。這些樣本**無法分層解讀**——不知道當時跑在什麼 effort，也就不能拿來跟未來標註了 effort 的樣本混算。表本身仍有價值（記錄了「原預估普遍低估 25%–100%」這個事實），但必須加上時代標記。

### B. 四項行為位移對照

| 位移 | 本專案的接觸面（含行號） | 方向 |
|---|---|---|
| **被指示驗證→過度驗證**（刪掉指示不降能力） | `skills/writing/SKILL.md:16`「5. 自我檢查：邏輯、用詞、格式、完整度」；`.claude/agents/*.md` ×5 的「完成後回報：…逐條對照 definition_of_done」 | 需**收斂**，但要分類——見下節 |
| **範圍擴張**（會加使用者沒要的步驟） | Task Card 的 `definition_of_done` 已是範圍契約（結構上是強項），但 `GLOBAL_RULES.md` 無範圍紀律段落 | 需**新增**紀律 |
| **交付物變長**（寫到磁碟的檔案更長） | `outputs/drafts/` 已有約 100 份；`GLOBAL_RULES.md:18-21` 輸出規則無長度約束；`skills/writing/SKILL.md` 有「嚴守 expected_output 篇幅」但其他 skill 無 | 需**新增**長度紀律 |
| **更愛派子代理**（相對 4.8 是**方向反轉**） | 5 個子代理已就緒（`.claude/agents/`）、`ROUTING_RULES.md` 鼓勵路由；`README.md:181` 的「現階段不做清單」有「多 agent swarm」但那是架構聲明，非執行期節流 | 需**新增**委派上限 |

第四項值得特別註記：Opus 4.8 是**低**估委派、需要被鼓勵去派；Opus 5 反過來。任何為 4.8 寫的「多用子代理」指引現在是反效果。本專案沒有這類指引（`README` 反而是抑制的），所以只需補上限，不需刪東西。

### C. 驗證分類表（本次最關鍵的判斷）

Opus 5 遷移指引說「刪掉你的驗證 scaffolding」。**這句話不能整段套用到本專案**，必須分四類處理：

| 類別 | 例子 | 處置 | 理由 |
|---|---|---|---|
| 確定性閘門 | `scripts/gate_check.py`(333行)、`scripts/verification_loop.py`(401行)、四層 `GATE_POLICY.yaml`、CI 約 30 steps | **完整保留，一行不動** | 這是稽核證據產生器，產出 run log 帳本與 approval 紀錄。它跟「模型會不會自我驗證」無關——即使模型完全不自檢，這些閘門照樣執行並留下證據 |
| 稽核契約型措辭 | `.claude/agents/*.md` 的「逐條對照 definition_of_done」 | **保留** | 這要求的是**產出一份對照表**（審計產物），不是要求模型多驗一輪。刪掉會失去 DoD 追溯性 |
| 安全／context 衛生自檢 | `INPUT_GUARDRAILS.md:57`、`CONTEXT_ENGINEERING.md:65` 的「自我檢查」清單 | **保留** | 便宜且承重。過度驗證的成本問題出在**產出驗證**，不在安全檢查；砍這裡是拿安全換一點 token |
| 泛用產出自我檢查 | `skills/writing/SKILL.md:16` | **收斂改寫** | 正是會觸發過度驗證的措辭，且其內容（邏輯／用詞／格式／完整度）已被 `expected_output` 契約與四層閘覆蓋——是重複，不是保險 |

**這張表是本報告最重要的產出**：它把一句可能造成誤刪治理骨架的通用建議，翻譯成本專案可安全執行的四類處置。

### D. 實測值漂移（用本 repo 自己的工具佐證）

跑 `ruby scripts/check_context_budget.rb`（估算法：ASCII/4 + 非 ASCII ×1，保守上界）：

| 項目 | 文件記載 | 實測 | 差異 |
|---|---|---|---|
| CLAUDE.md + GLOBAL_RULES | `CLAUDE.md:24`、`COST_POLICY.md:39`「實測 baseline **~400 tokens**」 | **~1620** tokens（861 + 759） | **4.05×** |
| 單一 skill prompt | `COST_POLICY.md:39`「實測 baseline 200-600 tokens」 | **483–985** tokens | 上界 1.64× |
| 單一 skill prompt | `CLAUDE.md:25`「實測 baseline 480-990 tokens」 | 483–985 tokens | ✅ 準確 |

`CLAUDE.md:25` 與 `COST_POLICY.md:39` 對**同一件事**給出不同數字（480-990 vs 200-600），其中 COST_POLICY 那筆是錯的。這是雙寫漂移，正是 `AGENT_CONTEXT.yaml:12-13` 明文要避免的模式（「單一事實來源…避免兩處漂移」）。

**Opus 5 相關的附帶事實**：最小可快取前綴從 Opus 4.8 的 1024 tokens 降到 **512 tokens**。本 repo 穩定前綴實測 ~1620 tokens，兩個世代都在門檻之上——所以 `CLAUDE.md:27`「載入順序對 prompt caching 友善」這個宣稱**成立**，而且 Opus 5 下餘裕更大。值得把數字記進文件，讓宣稱從「未驗證」升級為「有量測支撐」。

---

## 落地位置對照

| # | 變更 | 檔案 | 權限 | 風險 |
|---|---|---|---|---|
| 1 | 模型路由表更新至 Opus 5 世代（alias 機制不動） | `system/COST_POLICY.md` | ask（modify_system_rules） | 低 |
| 2 | 新增 effort 維度小節＋各 skill 建議起始值＋掃描方法 | `system/COST_POLICY.md` | ask | 低 |
| 3 | 兩個反直覺註記（effort 不縮短輸出／低 effort 已勝前代高 effort） | `system/COST_POLICY.md` | ask | 低 |
| 4 | 校準係數表標記 pre-Opus-5、effort 未標註、禁止混算 | `system/COST_POLICY.md` | ask | 低 |
| 5 | context 基準表修正 skill baseline＋新增 cache 最小前綴列 | `system/COST_POLICY.md` | ask | 低 |
| 6 | `request_model` 註解世代中性化＋值格式規範；新增 optional `effort` 欄 | `system/EXECUTION_LOG_SCHEMA.yaml` | ask | 低 |
| 7 | 修正 baseline 實測值、補 cache 門檻、新增產出紀律三條 | `CLAUDE.md` | ask（modify_claude_md） | **中**（3000 token 硬上限） |
| 8 | 範圍／長度／委派三段紀律完整版 | `system/GLOBAL_RULES.md` | ask | 低 |
| 9 | 收斂泛用自我檢查、保留 DoD 對照、analysis-specialist 世代中性化 | `.claude/agents/*.md` ×5 | ask（modify_settings_json） | 低 |
| 10 | 自我檢查步驟收斂為對照 expected_output＋補篇幅紀律 | `skills/writing/SKILL.md` | ask（modify_skills） | 低 |

`#7` 是唯一有硬性失敗模式的一項：`check_context_budget.rb` 是 CI 的 blocking step，改爆就是紅燈。目前 861/3000，餘裕 2139 tokens。

---

## 明確排除項

以下在調查中發現且確認為真，但**與 Opus 5 無關**，各自應獨立開卡——列出來是為了不讓它們搭順風車擴張本次範圍：

| 項目 | 證據 | 建議 |
|---|---|---|
| `skills/retro/` 無法被路由到 | `.claude/skills/` 缺 retro symlink；`system/validate_task_card.py:24` 的 `VALID_SKILLS` 不含 retro，但 `ROUTING_RULES.md:16` 列它為第 6 個路由目標 | 獨立開卡（三處不一致，需決定是補齊還是移除） |
| 重複 task_id | `20260417-O01`、`20260417-O02` 各出現兩次；CI 的 referential integrity lint 未檢查唯一性 | 獨立開卡（含補 lint） |
| `permissions_guard.py` permission_key 錯位 | `git_force_push` 規則掛在 `permission_key="modify_production_data"`，但 `PERMISSIONS.yaml:47` 把後者標為 `model`、前者標為 `runtime` | 獨立開卡（效果正確、語意錯位） |
| `check_native_overlap_freshness.py` 零引用 | 55 行腳本，不在 CI、不在任何 hook、不在 `sync_derived.sh`；自述要接的 periodic reminder 不存在 | 併入 P2-1（有界自主維運迴圈） |
| Opus 5 當 LLM judge | `run_evals.py:182-185` 的 `--judge llm` 未接 provider、自動 fallback 到 rule judge；P1-4（`20260716-P14`）就是這張卡 | **這是 Opus 5 帶來的新機會**，但需 API 憑證且是獨立交付，建議本次結束後接著做 |
| review 佇列 4 張、N06 plugin go/no-go | 07-12 才清到 0，11 天回堆 4 張；N06 線 4 張卡等一個帶外動作已 3 個月 | 治理決策，非本卡範圍 |

---

## 高風險假設

1. **假設 `.claude/agents/*.md` 不支援 effort frontmatter 鍵。**
   若不成立（實際支援），選項 C 可再進一步把 effort 從政策層下放到執行層，效果更好。實作卡已把這條設計成**條件式驗證**：先驗證，支援才寫入並擴充 `check_spec_consistency.rb:392` 的 lint 白名單；不支援就只留政策層記載。無論哪個結果，選項 C 都成立——這條假設不會翻轉結論。

2. **假設模型 alias（`haiku`/`sonnet`/`opus`）確實自動對映到當代最新模型。**
   這是 `COST_POLICY.md:54` 的既有宣稱，本次沿用但**未實測驗證**。若不成立，路由實際跑在舊模型上，整個 Opus 5 對齊只有文件意義。驗證方式見下節。

3. **假設本專案會恢復產能。**
   最後提交 2026-07-17，距今兩週。若持續停擺，本次對齊的延遲回報（分層校準資料）永遠不會兌現，只剩立即回報（文件正確性）。這也是選項 D 被降級的主因。

---

## 待驗證

| 項目 | 驗證方式 |
|---|---|
| agent frontmatter 是否支援 effort/thinking 鍵 | 實作卡執行時查 Claude Code 當前 agent frontmatter 規範；未經證實不寫入（`check_spec_consistency.rb:392` 會擋未知鍵） |
| alias → 實際模型的對映 | 下次任務執行時記錄 `EXECUTION_LOG_SCHEMA` 的 `request_model` 實際值，比對是否為 Opus 5 世代 id |
| effort 建議起始值是否合適 | 各 skill_type 累積 ≥3 筆帶 effort 標註的樣本後，於下次 retro 檢視 |
| 收斂自我檢查措辭後產出品質是否下降 | 對照 `evals/` 的 gold/bad 校準對；目前只有 research/analysis 兩個 case，覆蓋不足（見 P1-4） |

---

## 建議下一步

1. 執行 **20260731-O01**，依「落地位置對照」表逐項套用，每個 ask 級檔案改動前先出 diff 過目。
2. 收尾前跑完整驗證：`check_context_budget.rb`（#7 的硬約束）、`check_spec_consistency.rb`、既有單元測試與 4 支 e2e、`sync_derived.sh --check`。
3. 本次結束後接 **P1-4（20260716-P14）**：用 Opus 5 把 `run_evals.py` 的 LLM judge 接上真 provider——這是待驗證第 4 項的前提，也是把品質保證從結構層升到語意層的唯一路徑。
4. 累積 ≥3 筆帶 effort 標註的樣本後，重新評估選項 D（改 effort 分層、廢除模型分流）——屆時是資料驅動的決策，不是直覺切換。
