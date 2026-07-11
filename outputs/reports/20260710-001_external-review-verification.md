# 外部第一性原理報告對比驗證分析（20260710-001）

> Task Card：`tasks/2026-07-10_external-review-verification.yaml`
> 驗證對象：使用者提供之外部分析報告（綜合評分 7.2/10，Level 3/5）
> 驗證方法：三路 codebase 探索，逐條指控對照程式碼證據（檔案:行號）
> 升格紀錄：2026-07-10 經人工核准由 outputs/drafts/ 升格（升格卡 20260710-004，PR #130 合併後收尾）

## 結論與建議

外部報告的六大類指控**幾乎全數屬實**，核心診斷「文件宣稱的控制力高於 runtime 實際能保證的控制力」成立；但報告有三處低估或措辭不精確，需修正後採用。P0 建議中：(a) active task 綁定與 (b) 精確路徑授權**全盤接受**；(c) fail-closed **修改後接受**（選擇性翻轉，不做全面翻轉）；(d) sandbox **降級接受**（只做邊界聲明與低誤判補強，不在 repo 內自造隔離）。建議以三張 Task Card（20260710-001/002/003）落地，P1（跨模型 core、eval 擴充、LLM judge）本輪明確不做。

---

## 一、指控逐條驗證

### 1. Hooks 強制力（報告缺點一）

**指控**：permissions_guard 是 regex deny-list 而非 sandbox；未命中預設放行；壞 stdin fail-open；只攔 Bash。

**證據**：
- deny-list 樣式：`scripts/permissions_guard.py:51-163`（`DENY_RULES` 全為 `re.compile`）；檔內自承「this guard is a *deny-list*, not a sandbox」（:20-22）
- 未命中放行：`evaluate()` 全數不中即 `return "allow", None`（:203-206）
- 壞 stdin fail-open：空輸入 → allow（:210-215）；`JSONDecodeError` → allow + warning（:217-221）
- 只攔 Bash：非 Bash 工具直接 allow（:229-233）

**判定**：**屬實**。但需補一處報告低估：`PERMISSIONS.yaml` 讀取失敗時 `load_deny_list()` 回 `None`，`active_rules(None)` 會**保留全部規則**（:186-193）— policy 檔壞掉不會關掉 guard，這一段已是 fail-safe，且有測試鎖定（`test_permissions_guard.py` 的 failsafe 測試）。

### 2. Task Card 授權（報告缺點二、三）

**指控**：「沒有 Task Card 不執行」只在新建 `outputs/reports/` 檔時強制；授權以檔名匹配任一張卡，不綁 task_id/status/session/完整路徑，形成 stale authorization。

**證據**：
- 範圍：`scripts/task_card_guard.py:68-93` — 非 reports 路徑 allow（:78-81）、既有檔 allow（:83-84），只有「reports 下的新檔」進比對
- basename 匹配：`if target.name in report_output_filenames(root)`（:86）；`report_output_filenames()`（:39-65）掃全部 `tasks/**/*.yaml`，不看 `status`
- stale authorization：`system/validate_task_card.py:26` 有 done/failed 狀態，但授權函式完全不過濾 — 已結案的卡永久授權同名檔

**判定**：**屬實**。報告的精確化描述正確：這條硬規則目前是「沒有 Task Card 不得建立新的正式報告」，不是「不執行任何任務」。

### 3. Failure counter（報告三條硬規則之三）

**指控**：連續失敗 3 次會停，依賴模型自律。

**證據**：`scripts/failure_counter.py` — 門檻 3（:37）；觸發後 `--hook` 模式 exit 2 硬擋 Bash/Write/Edit（:98-127），這段是 fail-closed；但計數靠 agent 主動 `--record`（:10-14 自承 prompt-driven best-effort），不記錄就永不觸發。

**判定**：**部分屬實，措辭需修正**——弱點不是「不會停」，而是「觸發與否依賴自律」。觸發後的攔阻是確定性的。

### 4. Gate fail-open（報告缺點四）

**指控**：缺 run log 時 rule_check 回 skipped，skipped 不會讓整體 verdict 失敗；最需要稽核的資料缺失本身不導致治理失敗。

**證據**：
- `scripts/gate_check.py:120-126`：`if not run_log: return {"status": SKIPPED, ...}`；docstring :21 明示「skipped never fails」；`failed` property 只看 FAIL（:70-72）
- 同一 fail-open 也在 `scripts/verification_loop.py:112-143` 的 `check_rule()`（:122 註解「無 run-log 不誤判」）
- 加重事實：`gate_check.py` **並未掛在任何 runtime hook 上**（`.claude/settings.json:17-80` 無其身影），它是 CLI/CI 事後驗證器

**判定**：**屬實**，且比報告所述更弱一層（連事後驗證都要手動/CI 觸發）。

### 5. Eval 深度與成本樣本（報告缺點五、七）

**指控**：eval 只有 2 case、只量格式不量品質、LLM judge 未接入；成本樣本 1–2 筆、analysis 0 筆。

**證據**：
- 2 case：`evals/research/taiwan_sme.yaml`、`evals/analysis/notion_ai.yaml`，writing/ops/review 無 eval
- 格式檢查：`scripts/run_evals.py:110-116` 僅 5 種 rubric（section_first/section_nonempty/all_headings/contains_any/regex）
- LLM judge：`run_evals.py:187-189` — `--judge llm` 強制 fallback 到 rule
- 成本：`system/COST_POLICY.md:66-91` — research/ops/review 各 2 筆、writing 1 筆、analysis 0 筆
- 需補：gold/bad calibration 機制**存在且已入 CI**（`run_evals.py:156-176`），報告未給予肯定

**判定**：**屬實**。

### 6. 規格漂移與授權缺失（報告缺點六、待驗證項）

**指控**：重複 Stop key、merge conflict markers 等漂移已發生；根目錄無開源授權。

**證據**：
- 重複 Stop key：git 歷史可還原 — 06-20 加入第二個 `Stop` 鍵，JSON 靜默丟棄 `sync_derived.sh`，直到 07-09 commit c250f0f 才合併；merge conflict markers 亦在 PR #129 處理中被 `sync_derived.sh` 加上檢查（`check_conflict_markers`）
- LICENSE：根目錄僅 README.md / CLAUDE.md / SECURITY.md，全 repo 無授權檔

**判定**：**屬實**。

### 報告需修正的三處

1. **CI 描述**：12 項檢查全部存在，但是**單一 workflow（`.github/workflows/spec-consistency.yml`）單一 job 的 steps**，非多個獨立 job。涵蓋面正確，粒度描述不精確。
2. **permissions_guard 的 policy fail-safe**：報告籠統歸為 fail-open；實際上 policy 檔讀取失敗會保留全部規則，此點已達 P0(c) 要求，無需再修。
3. **failure_counter**：報告「連續失敗 3 次就停」歸類為依賴自律 — 正確的拆分是「計數自律（弱）、觸發後攔阻確定（強）」。修正弱點的槓桿在自動化 `--record`（PostToolUse），不在攔阻端。

---

## 二、P0 建議採納決策（選項比較）

決策問題：對報告 P0 四項，本輪各採取什麼立場？

### 選項 A：全盤照做（含全面 fail-closed、全域 mutating tool 綁卡）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高 — 直接消除「文件強於 runtime」落差 | 報告 P0 定義 |
| 成本 | 高 — 全域綁卡需改 4 個 hook + 82 張存量卡回填風險 | tasks/ 現況 82 張卡 |
| 風險 | **高 — 與專案哲學正面衝突** | `permissions_guard.py:48-50`「false positives 比漏抓更糟」；全面 fail-closed 於壞 stdin 可能 brick 正常 session |
| 可行性 | 低 — 56 張 done 歷史卡在「缺 run log 一律 FAIL」下全數打紅 | gate_check 現行語意 |
| 執行難度 | 高 — 單輪不可完成 | — |
| 預期回報 | 邊際遞減 — drafts/logs 上鎖對安全貢獻小、摩擦大 | 99% 低風險路徑原則 |
| 一人公司適配度 | 低 — 流程負擔立刻放大 | — |

### 選項 B：選擇性翻轉（本輪採用）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 高 — 封掉 stale authorization、crash-open、高風險缺帳三個實質破口 | 指控 2、4 驗證結果 |
| 成本 | 中 — 約 8 個 checkpoint、3 張卡、新增 1 個 CLI + 1 個 state 檔 | 實作計畫 |
| 風險 | 低-中 — 誤傷面被 matcher 天然限制在 Write/Edit 類工具；cutoff（2026-07-10）保證歷史卡零影響 | `.claude/settings.json:32-44`；`APPROVAL_COVERAGE_CUTOFF` 先例 |
| 可行性 | 高 — 全部在既有 chokepoint 與測試框架上疊加 | task_card_guard/gate_check 均有 test_*.py |
| 執行難度 | 中 — 主要工作是 guard 改寫與測試語意翻轉 | — |
| 預期回報 | 高 — 硬規則 1 從「檔名巧合授權」升級為「active task 精確授權」 | — |
| 一人公司適配度 | 高 — 日常 drafts/logs/code 零新增摩擦，只有正式報告要先 `--set` | — |

### 選項 C：只出報告不動 runtime（「不做」選項）

| 維度 | 評估 | 依據 |
|------|------|------|
| 價值 | 低 — 已有多份自評指出同樣問題（self-assessment §3.1、triage 報告），再寫一份不增量 | `outputs/reports/harness-self-assessment-v1.md` |
| 成本 | 低 — 僅文件工時 | — |
| 風險 | 中 — stale authorization 與 crash-open 持續存在；外部報告結論「宣稱強於實際」繼續成立 | 指控 2、4 |
| 可行性 | 高 | — |
| 執行難度 | 低 | — |
| 預期回報 | 低 — 評分停在 7.2，P0 缺口原封不動 | — |
| 一人公司適配度 | 中 — 短期省事，技術債累積 | — |

**採納結論**：選 **B**。逐項立場：

| P0 項 | 立場 | 修改內容 |
|---|---|---|
| (a) mutating tool 綁 active task_id | **修改後接受** | 不做全域綁定（違反低風險哲學）；只綁 `outputs/reports/` chokepoint，真相來源為新檔 `state/active_task.yaml` + `scripts/active_task.py` CLI |
| (b) 精確路徑授權 | **接受** | basename 比對 → normalized 完整路徑 + task_id + status∉{done,failed} 三段綁定；不加 Task Card 新必填欄位（避免 82 卡回填） |
| (c) hook fail-closed | **修改後接受** | 只翻 task_card_guard（壞 stdin/未捕捉例外 → exit 2）與 gate 高風險缺 run log（cutoff 2026-07-10 後 + risk≥high + status∈{done,review,failed} → FAIL）；permissions_guard/failure_counter 維持 fail-open，理由入 SECURITY.md 並以測試鎖定 |
| (d) sandbox | **降級接受** | repo 內不自造 sandbox；SECURITY.md 寫明威脅模型與防護邊界（regex ≠ 隔離、interpreter one-liner 屬已知接受邊界）；defense-in-depth 僅做低誤判項（4 條網路規則 curl → curl|wget） |

與專案哲學的衝突處理：`permissions_guard.py:48-50` 的「false positive 比漏抓更糟」原則**保留**，fail-closed 只施加在「誤傷面可證明有界」的點位 — task_card_guard 的 matcher 只掛 Write/Edit 類工具（`.claude/settings.json:32-44`），壞 stdin block 不影響 Bash 與讀取；gate 的 FAIL 條件以 cutoff 日期排除全部歷史卡。

---

## 三、本輪不做清單（scope 邊界）

1. **LLM judge 接入**（P1）— `run_evals.py:187-189` fallback 維持；gold/bad calibration 已為未來接入備好
2. **Eval 案例擴充 2 → 20×4**（P1）— 框架已在（20260630-G02），擴充是量的問題
3. **跨模型 core / adapters 抽取**（P1）— 已有獨立卡群（N09/N11 plugin 路線）在進行
4. **容器/OS 層 sandbox** — 超出 repo 能力，屬 Claude Code runtime 外的部署決策
5. **failure_counter 自動化（PostToolUse 掛鉤）**（P1）— 本輪維持現狀
6. **全域 mutating tool 綁卡** — 違反 99% 低風險哲學，只綁 reports chokepoint
7. **Task Card 新必填欄位（writable_paths 等）** — 避免 82 張存量卡回填與三處 parity 同步成本
8. **Interpreter one-liner regex 攔截** — false positive 不可控
9. **26 張未結卡 status triage** — guard v2 後 stale 卡已無授權力，失去安全急迫性，另卡處理
10. **Blocking Stop gate** — 先以警告模式觀察誤報率（本輪只做 stderr 警告）

## 四、高風險假設

- **「matcher 限制誤傷面」假設 Claude Code 對 Write/Edit 一定送合法 JSON payload**：若某版本 runtime 對這些工具送空 stdin，fail-closed 會誤擋正常寫入。緩解：block 訊息附明確診斷與 `--set` 指令；若不成立可單點回退 stdin 分支而保留三段綁定。
- **cutoff 模式假設今後高風險卡都誠實填 date**：若新卡回填舊日期可繞過 run log 強制。接受此風險 — 偽造 date 屬主動規避，非本輪防禦對象（deny-list 哲學一致）。
- **active_task.py --set 仍是自律動作**：強制力來自「不 set 寫不了 reports」的結構性誘因；若任務根本不產正式報告，綁定不觸發 — 此為刻意設計（低風險路徑不上鎖），非疏漏。

## 五、待驗證

- guard v2 上線後的實際誤擋率：以 logs/errors/ 中 task_card_guard block 記錄觀察 2 週
- Stop hook gate 警告的誤報率：決定是否升級為 blocking（P1 決策點）
- 升檔本報告至 outputs/reports/ 時，guard v2 應以 20260710-001 的 active 綁定放行 — 這是第一個 dogfood 案例

## 六、建議下一步

1. 人工審核本報告；核准後升 `outputs/reports/`（將成為 guard v2 首個 dogfood）
2. 執行 20260710-002（active task 綁定 + 精確路徑授權）
3. 執行 20260710-003（選擇性 fail-closed + SECURITY.md 邊界聲明）
4. 兩週後回顧誤擋/誤報數據，決定 P1 排程（LLM judge、eval 擴充、failure_counter 自動化）
