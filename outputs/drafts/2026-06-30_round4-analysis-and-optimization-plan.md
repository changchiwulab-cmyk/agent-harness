# Agent Harness v2 — 第四輪分析與研究優化計畫表

> **草稿（draft）** ｜ 日期：2026-06-30 ｜ Task Card：`20260630-001` ｜ skill：research
> 交付範圍：**只分析 + 規劃，不修改 `system/`／`skills/`**。H1–H7、S1–S3 為後續各自獨立 Task Card 的提案。
> 研究方法：3 個 Explore agent（架構地圖／三輪補強史／缺口盤點）＋ 親自校讀 `harness-self-assessment-v1.md`、`COST_POLICY.md`、`NATIVE_OVERLAP.yaml`、`GATE_POLICY.yaml`、`EXECUTION_LOG_SCHEMA.yaml`、`validate_task_card.py`、`check_spec_consistency.rb`、`.claude/settings.json`、`logs/`。
> 審閱通過後可依 `RETRO_FLOW` §5 晉升至 `outputs/reports/`。

---

## 結論

三輪架構補強後，本專案**架構與治理設計已罕見地完備（綜合 ≈7/10、成熟度等級 3「生產前」）**，但卡在同一句話：**「規格寫好了，執行層還沒把它逼出來；設計畫好了，關鍵路徑只實證過一次」**。

第三輪的 R1–R10 路線圖，**多數已以 checkpoint 形式「半落地」**——schema、script、runbook 這些**靜態產物（artifact）都生出來了**，但背後的**動態保證（enforcement）與經驗樣本（empirical base）仍稀薄**：四道 gate 只有 schema gate 有可執行碼、deny-list runtime guard 只覆蓋 Bash、故障路徑只跑過一次受控演練、analysis 成本校準仍 0 筆、R9/R10 戰略未動。

因此**第四輪的天花板不是再加功能，而是把既有設計「落成可執行的 enforcement ＋ 累出經驗樣本 ＋ 收尾 v3 戰略決策」**。據此提出雙軌計畫表：**硬化軌 H1–H7（短中期，主攻成熟度 3→4）＋ 戰略軌 S1–S3（長期 v3）**，建議第一步＝ **H1（gate 可執行化）＋ H2（hook 覆蓋面）**，因為 spec-execution gap 是三輪後最嚴重的存活缺口。

---

## 已知事實

### 一、三輪架構補強回顧（時間軸）

| 輪次 | 期間 | 主題 | 代表產物（證據路徑） |
|------|------|------|------|
| **第一輪** | 2026-04-03 ~ 04-09 | **架構與哲學奠定** | 三平面/11 模組、馬鞍工程六原則、`GATE_POLICY.yaml` 四層、`APPROVAL_POLICY.yaml`、`FAILURE_TAXONOMY.yaml`（14 類）、`EXECUTION_LOG_SCHEMA.yaml`（v1→v1.5→v2.0） |
| **第二輪** | 2026-04-11 ~ 05-03 | **實地驗證與成本定量** | `analysis` skill、`INTAKE_FLOW`/`RETRO_FLOW`、Ruby `check_spec_consistency.rb` CI、成本校準係數（research 1.43／writing 2.00／ops 1.56／review 1.25）、前端看板、**Phase A 執行層 hook**（`permissions_guard.py` + `.claude/settings.json` PreToolUse 註冊）、E2E smoke |
| **第三輪** | 2026-05-09 ~ 05-29 | **系統診斷 + R1–R10 路線圖 + v3 規劃** | `harness-self-assessment-v1.md`（雙軸 ≈7/10、成熟度 3）、R1–R10 roadmap、N-series v3 抽取規劃、`agent-governance-bootstrap/` plugin 骨架（草稿）、`RECOVERY_RUNBOOK.md`、`governance_metrics.py`、`check_decision_revisit.rb` |

> 最新一筆是 `8dd9f42`（2026-06-27）research skill web-search 策略修補，屬第三輪後的零星 follow-up。

### 二、R1–R10 落地核對表（本次核對重點）

圖例：✅ 已落地（artifact + enforcement/實證皆在）｜🟡 半落地（artifact 在、但 enforcement 或經驗樣本未到位）｜⏳ 未動

| ID | 項目 | 狀態 | 證據 / 缺口 |
|----|------|:---:|------|
| **R1** | 批准紀錄 schema 化＋首筆回填 | 🟡 | `APPROVAL_LOG_TEMPLATE.yaml` 在、CI 驗 approval schema（`check_spec_consistency.rb:181-209`）；但 `logs/approvals/` **只有 1 筆真實紀錄（2026-04-09）**，單一資料源尚未坐實，且**沒有「approval_needed:true 必有紀錄」的強制** |
| **R2** | CI 擴充 logs schema lint | ✅ | `check_spec_consistency.rb` §4–6 已驗 `logs/runs`、`logs/approvals`、`logs/errors` 必填欄位與枚舉；CI workflow 有跑 |
| **R3** | analysis 成本校準補樣本 | 🟡 | `COST_POLICY.md:61,81` analysis 列仍標 **「尚無實測／0 筆／待累積」**；校準觸發條件「至少 1 筆 analysis 實測」未滿足 |
| **R4** | 決策 revisit 追蹤 | 🟡 | `check_decision_revisit.rb` + 單元測試在、CI 有跑；但屬**手動/CI 掃描**，**無「retro 時自動提醒回看」的機制**，且未連回 NATIVE_OVERLAP |
| **R5** | 故障演練：實測失敗/partial 紀錄路徑 | 🟡 | 已跑**一次**受控演練（`logs/runs/RUN-20260529-003.yaml` + `logs/errors/2026-05-29_20260529-003_error.md`）；但僅此一次、單一情境，未成可重複的經驗基礎 |
| **R6** | EXECUTION_LOG token 量測坐實 | 🟡 | `EXECUTION_LOG_SCHEMA.yaml` 已加 `token_estimate.source` 欄；但 `logs/runs/` **只有 2 筆**，唯一 completed 樣本 token 仍非實測，非零實測 token 尚未坐實 |
| **R7** | 觀測工作流層/業務層補強 | 🟡 | `governance_metrics.py`（M1–M4）+ 前端治理面板已在；但指標**建在 ~30 筆任務**上，工作流層（gate pass 率）與業務層（每 skill 成本/品質趨勢）**資料稀薄**，FAILURE_TAXONOMY 仍無 `observed_count` |
| **R8** | 災難恢復 runbook＋checkpoint 還原實測 | 🟡 | `RECOVERY_RUNBOOK.md` 在、場景 A（單檔還原）已實測（~5ms、byte-identical）；**場景 C（context 重置接續）仍未實測**，與 GATE rollback 的交叉引用未閉環 |
| **R9** | NATIVE_OVERLAP 季度 revisit 自動化 | ⏳ | `NATIVE_OVERLAP.yaml` aggregate 維持 30%；**無季度自動回看、無 >40%/>50% 預警觸發** |
| **R10** | v3 遷移就緒度評估 | ⏳ | `agent-governance-bootstrap/` 骨架為**草稿未上線**；**`v3-readiness-assessment.md` 尚未產出**，逐模組保留/下放裁決未定 |

> 一句話總結：**R2 是唯一完整落地的；R1/R3/R4/R5/R6/R7/R8 都是「artifact 已生、enforcement/樣本未到」的半落地；R9/R10 未動。**

### 三、執行層強制力現況（spec vs enforcement）

| 規則來源 | 宣告 | 實際 enforcement | 缺口 |
|------|------|------|------|
| Gate 1 schema_check | `GATE_POLICY.yaml` | ✅ `validate_task_card.py` + CI | 無 |
| Gate 2–4 rule/completion/risk_check | `GATE_POLICY.yaml`（散文） | 🟡 **無可執行碼**；僅 `tests/e2e/` 模擬 + LLM 自律 | **`scripts/run_gates.py` 不存在** |
| 權限 deny-list | `PERMISSIONS.yaml` | 🟡 `permissions_guard.py` 經 `.claude/settings.json` **PreToolUse 註冊（僅 Bash matcher）** | 非 Bash 外發路徑未覆蓋；PostTask gate-check hook（`post_task_use.py`）仍是 `outputs/drafts/` 內的 **stub** |
| 批准 | `APPROVAL_POLICY.yaml` | 🟡 schema + CI 驗格式 | 無「該批未批」的偵測 |
| retry / max_tool_calls / 成本上限 | `CLAUDE.md` + Task Card | ❌ **self-policed**（無計數、無 kill switch、無自動 checkpoint） | 全靠 LLM 自律 |

---

## 合理推論

1. **三輪的進步模式是「先把規格與骨架補滿，再逐步坐實」**——這是健康的順序（先有 schema 才能 enforce），但目前正卡在「坐實」這一步：**artifact 產出速度遠快於 enforcement/經驗累積速度**。第四輪若繼續加 artifact 只會擴大此落差。

2. **五大存活缺口可收斂如下**（依嚴重度）：
   - **① spec-execution gap（最嚴重）**：Gate 2–4 無可執行碼、deny-guard 僅覆蓋 Bash、retry/成本全 self-policed。規則寫得很好但執行層不保證會逼出來——這是成熟度卡在 3 的**主因**。
   - **② 可觀測不對稱**：happy-path 任務依 D006 收斂跳過 run log，導致成功任務無法事後回溯走過四 gate；觀測只到工具層，工作流/業務層資料稀薄。
   - **③ 批准 trail 不一致**：schema 有了，但「approval_needed:true 的 done 任務必須有對應紀錄」無人強制，無法證明該批的都批了。
   - **④ v3 戰略未動**：R9/R10 是季度級戰略決策，plugin 骨架草擬完成卻未做就緒度評估與上線裁決，懸而未決會讓部分抽象持續與原生重疊（Skill 85%／Tool 80%）。
   - **⑤ 經驗稀薄（橫切）**：整套治理建在 ~15–30 筆任務、2 筆 run log、1 次故障演練、0 筆 analysis 成本樣本上；FAILURE_TAXONOMY 14 類無任何真實命中計數。統計上不足以宣稱「生產級」。

3. **最高槓桿不是補最多項，而是補「能一次解開多個缺口」的項**：H1（gate 可執行化）同時推進 ①②⑤——一旦 gate 結果被結構化記錄，工作流層觀測（②）與失敗樣本（⑤）會自然產生。

---

## 四、第四輪研究優化計畫表

**落地通則**（每項都遵守三條硬規則）：每個項目**先開一張 Task Card**（硬規則 1）→ 產出**先進 `outputs/drafts/`**（硬規則 2）→ 改 `system/`／`skills/` 走 `ask`（列 diff 後人工確認）→ 寫 `logs/` 屬 `allow`。`I/E/R` = impact / effort / risk。

### 硬化軌（短→中期，主攻成熟度 3→4）

| ID | 項目 | 解決缺口 | 動作（檔層級） | I/E/R |
|----|------|:---:|------|:---:|
| **H1** | **Gate 2–4 可執行化** | ① ② ⑤ | 新增 `scripts/run_gates.py`：把 rule_check（deny-list/工具白名單）、completion_check（逐條 DoD pass/fail）、risk_check（risk_level↔實際動作）由散文落成可執行碼；輸出結構化 `gate_results`；固化 `tests/e2e/test_dummy_task_smoke.py` 既有雛形為回歸 | 高/中/中 |
| **H2** | **hook 覆蓋面補齊** | ① | 把 `outputs/drafts/agent-governance-bootstrap/hooks/post_task_use.py`（現為 v0.1.0 stub）落成真正的 PostTask gate-check 並經 `.claude/settings.json` 註冊；評估 deny-guard 是否需涵蓋非 Bash 外發路徑 | 高/中/中 |
| **H3** | **成本/呼叫 enforcement** | ① ⑤ | `max_tool_calls`/`max_retries` 由 self-policed 改為**有計數 + 達閾值自動 checkpoint/停**（hook 或 wrapper）；與 EXECUTION_LOG token 串接 | 中/中/低 |
| **H4** | **批准紀錄一致性 enforcement** | ③ | 擴 `check_spec_consistency.rb`：凡 `approval_needed:true` 且 `status:done` 的 Task Card，必須有對應 `logs/approvals/` 紀錄，否則 CI fail；坐實單一資料源 | 高/低/低 |
| **H5** | **三層可觀測補實** | ② ⑤ | 擴 `governance_metrics.py`：四層 gate pass 率、每 skill 成本/品質趨勢；`FAILURE_TAXONOMY.yaml` 加 `observed_count` 並由 error log 自動回填；接前端面板 | 高/中/低 |
| **H6** | **happy-path 可回溯** | ② | 重審 D006：對成功任務留**輕量 run log**（或由 audit log + H1 的 `gate_results` 反推四 gate 軌跡），消除觀測不對稱 | 中/中/低 |
| **H7** | **失敗/恢復閉環再實證** | ① ⑤ | 補 `RECOVERY_RUNBOOK.md` **場景 C（context 重置接續）實測**，固化成 `tests/e2e/`；與 GATE rollback 交叉引用閉環；累出第 2、3 筆 run log 樣本 | 高/高/中 |

### 戰略軌（長期，季度級 v3）

| ID | 項目 | 解決缺口 | 動作 | I/E/R |
|----|------|:---:|------|:---:|
| **S1** | **NATIVE_OVERLAP 季度回看自動化**（R9 接續） | ④ | `governance_metrics.py` 讀 `aggregate_estimate_pct`：>40% 預警、>50% 觸發 v3 評估建議；併入季度 RETRO；與 H5/R4 合流 | 中/中/中 |
| **S2** | **v3 抽出就緒度評估**（R10 接續） | ④ | 產 `outputs/drafts/v3-readiness-assessment.md`：逐模組標「保留／下放原生／並存」，明確不可替代資產（校準表、FAILURE_TAXONOMY、Decision/Audit 紀錄）；對齊既有 `2026-05-09_v3_extraction_plan.md`，更新 D003/D007。**只評估不遷移** | 中/高/高 |
| **S3** | **governance-bootstrap plugin 上線決策** | ④ | 評估 `outputs/drafts/agent-governance-bootstrap/` 推上 GitHub 的就緒度與風險（依賴 H1/H2 把 hook/gate 坐實後再決） | 中/高/高 |

### 相依性與排程

```
週1（quick wins）：H4（獨立，CI 立即收斂③）
週2-4（核心主幹）：H1 ┬→ H3（gate/計數串接）
                     ├→ H5（需 gate_results 資料）
                     ├→ H6（需 H1 的 gate 軌跡）
                     └→ H2（PostTask 掛 H1 的 gate）
                  H1 + H2 → H7（失敗/恢復實證，餵 run log 樣本）
季度（戰略）：H5 + R4 → S1 → S2 → S3（plugin 上線需 H1/H2 先坐實）
關鍵路徑：H1 → H2 → H7  ＝ 把成熟度從 3 推到 4 的主幹
建議第一步：H1 + H2（spec-execution gap 是三輪後最嚴重存活缺口）；H4 可並行先收一個 quick win
```

### 成熟度 3 → 4 缺口對照

| 缺口 | 生產級要求 | 三輪後現況 | 第四輪補齊項 |
|------|----------|------|------|
| 規則可強制 | gate/權限/成本由碼強制 | gate 2–4 無碼、guard 僅 Bash、成本 self-policed | **H1、H2、H3** |
| 全程可觀測 | 工具+工作流+業務三層 | 僅工具層紮實 | **H5、H6** |
| 批准可審計 | 該批必有紀錄、單一源 | schema 有、無強制 | **H4** |
| 失敗/恢復實證 | 多情境演練 + post-mortem | 1 次演練、場景 C 未測 | **H7（+H1）** |
| 經驗樣本充足 | 統計上足夠 | run log 2 筆、analysis 0 筆 | **H3、H5、H7（+R3）** |
| 與原生長期共存 | 定期回看 + v3 裁決 | 觸發欄位有、無機制 | **S1、S2、S3** |

> 簡言之：成熟度 4 的門檻不是再加功能，而是把既有設計**「落成 enforcement ＋ 累出樣本 ＋ 收尾戰略」**。短期 H4 收批准審計；中期 H1/H2/H3/H5/H6/H7 把強制力與可觀測坐實（成熟度 3→4 主幹）；長期 S1/S2/S3 處理與原生平台的共存與 v3 上線。

---

## 待驗證

- **R3/R6 的部分落地證據**：本次以 `COST_POLICY.md` 與 `logs/runs/` 現況推斷 analysis 樣本 0、token 非實測；若第三輪另有未進 `logs/runs/` 的草稿樣本，狀態可上修。
- **H7 場景 C 可行性**：context 重置接續是否能在單一 session 內可控模擬，需在真實多階段任務中途驗證。
- **S3 plugin 上線就緒度**：`agent-governance-bootstrap/` 與 Claude Code plugin 規格的實際相容性未端到端測過。
- **effort 估計**：I/E/R 為相對量級判斷，非工時量測；實際工時待各項開 Task Card 時細估。

## 高風險假設

- **經驗稀薄是橫切風險**：整套治理結論建在 ~15–30 筆任務、2 筆 run log、1 次故障演練上。若把當前 7/10 評等當「已驗證的生產前」而非「設計完備但樣本不足」，會高估系統可靠性——**H5/H7 的價值正是把這個假設轉成數據**。
- **「半落地」可能被誤讀為「已完成」**：R1–R8 的 checkpoint 都存在，易讓人以為 R 系列已收工；本核對表的核心訊息是**artifact ≠ enforcement**，第四輪務必聚焦後者。
- **v3 過早遷移風險**：NATIVE_OVERLAP 30% 未達 50% 觸發閾值，S2/S3 維持「只評估不遷移」，避免在強制力尚未坐實前就把治理層抽離。

## 來源

- 本專案內部檔（一手）：`outputs/reports/harness-self-assessment-v1.md`（R1–R10 原始 roadmap，本表接續不重造）、`CLAUDE.md`、`README.md`、`system/GATE_POLICY.yaml`、`system/PERMISSIONS.yaml`、`system/APPROVAL_POLICY.yaml`、`system/COST_POLICY.md`、`system/NATIVE_OVERLAP.yaml`、`system/EXECUTION_LOG_SCHEMA.yaml`、`system/RECOVERY_RUNBOOK.md`、`system/FAILURE_TAXONOMY.yaml`
- 強制力證據：`.claude/settings.json`（PreToolUse 僅 Bash matcher）、`scripts/check_spec_consistency.rb`、`scripts/permissions_guard.py`、`scripts/governance_metrics.py`、`scripts/check_decision_revisit.rb`、`outputs/drafts/agent-governance-bootstrap/hooks/post_task_use.py`（stub）
- 樣本現況：`logs/runs/`（2 筆）、`logs/approvals/`（1 筆 + template）、`logs/errors/`（2 筆 + template）、`logs/AUDIT_LOG.md`
- git 歷史：commit `5a9ddd1`（v1 init）→ `f99223f`（v2）→ Phase A `a75e826` → 第三輪 N/R-series `8031b9e`…`0c56e72` → `8dd9f42`（2026-06-27 最新）
