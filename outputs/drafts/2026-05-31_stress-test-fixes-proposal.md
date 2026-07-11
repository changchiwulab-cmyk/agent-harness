# 深度測試壓測發現修改提案（F1 / F2 / F4）

- 來源任務：Task Card `20260531-003`（analysis）
- 依據：`outputs/reports/harness-stress-test-20260531-v1.md`（F1–F4）
- 狀態：草稿提案。**本提案不直接修改任何 `system/` 或 `skills/` 檔**；套用屬 ask 級，需人工核准後另立 Task Card 執行。

## 結論與建議

三項都是低風險、小幅、彼此獨立的治理微調，建議**全部採納**並一次性套用：F1 補一條 allow 權限（最有價值，解掉「執行任務無法修復自身 CI 紅燈」），F2 釐清 `max_tool_calls` 計數範圍，F4 把研究類 DoD 從字數導向改為覆蓋度導向。三項可獨立 approve/reject。套用會動到 `system/PERMISSIONS.yaml`、`system/COST_POLICY.md`、`skills/research/SKILL.md`，皆 ask 級。

---

## 提案 F1 — 衍生檔重生的權限地位明文化（P1）

- **問題**：新增 `tasks/` 或 `logs/runs/` 必然使 `frontend/data.json` 漂移、CI `validate-spec` 變紅；但重生它的權限不在 allow/ask/deny 任一清單，造成「研究任務無權讓自己的 PR 轉綠」，每次都要 ask 級人工介入。
- **目標檔案**：`system/PERMISSIONS.yaml`，`permissions.allow` 區塊（行 6–15）。
- **精確 before→after**（在 allow 清單末端、`create_task_card` 之後新增一行）：

  before：
  ```yaml
      - create_task_card         # 建立新的 Task Card（已驗證：8 筆歷史任務全部立即 approve → 升為 allow）
  ```
  after：
  ```yaml
      - create_task_card         # 建立新的 Task Card（已驗證：8 筆歷史任務全部立即 approve → 升為 allow）
      - regenerate_derived_artifacts  # 重生由 tasks/logs/memory 確定性衍生的檔（限 scripts/ 產生器，如 frontend/data.json）；不含 system/skills/reports
  ```
- **理由**：此動作是「從已提交來源確定性重生、可復原」的衍生檔操作，風險等同 `write_logs` / `create_output_files`。明文列為 allow（且嚴格限縮：只限 `scripts/` 產生器、只限衍生檔、絕不含 `system/skills/reports`）即可讓「新增 task/run 的任務」自行保持 manifest 一致，消除 F1 紅燈陷阱。
- **風險**：低。限縮條件已排除越權。**套用為 ask 級**（改 system/）。
- **替代方案**（不建議）：維持 ask，僅在 GATE_POLICY 加註「manifest 重生為核准後步驟」——治標不治本，每次仍卡人工。

---

## 提案 F2 — `max_tool_calls` 計數範圍釐清（P2）

- **問題**：`actual_tool_calls` 把 context 載入的 `file_read` 與 harness 自身驗證器都算進去，易誤報超支。活證據：`RUN-20260531-001` 計 16 > `max_tool_calls=12`，但真正「推進任務的工具」（web_search 5 + write 2 + checkpoint 3）約 10，在預算內；超出全來自參考檔載入與驗證器。
- **目標檔案**：`system/COST_POLICY.md`，「### 工具呼叫限制」段（行 20–23）。
- **精確 before→after**（在該段末新增一段註解）：

  before：
  ```markdown
  ### 工具呼叫限制
  - 單一任務最多 5 次外部工具呼叫後需 checkpoint
  - 單一任務最多 3 輪 web search
  - 連續失敗重試上限 3 次
  ```
  after：
  ```markdown
  ### 工具呼叫限制
  - 單一任務最多 5 次外部工具呼叫後需 checkpoint
  - 單一任務最多 3 輪 web search
  - 連續失敗重試上限 3 次

  > **計數範圍（2026-05-31 retro 釐清）**：`max_tool_calls` 只計「任務工具」（推進任務本身的 web_search / write / 主要 file_read）。下列 overhead **不計入**：context 載入用的 file_read（讀 SKILL / schema / 既有 outputs 等參考檔）、harness 自身的 gate 驗證（validate_task_card / check_spec_consistency / e2e / manifest --check）、git_commit_checkpoint。理由：避免「讀越多參考、驗越嚴謹」反被誤判超支（見 RUN-20260531-001：計 16 vs 任務工具約 10）。
  ```
- **理由**：把預算對準「真正花錢推進任務」的工具，讓 `max_tool_calls` 成為有意義的護欄而非雜訊。
- **風險**：低（釐清既有規則，不改數值）。**套用為 ask 級**（改 system/）。

---

## 提案 F4 — 研究類 DoD 改以覆蓋度為主（P3）

- **問題**：DoD 寫「~3500-5000 字（含表格）」與品質脫鉤；本次純 CJK prose 2975、含表格非空白 8961，判定模糊（completion_check 只能給軟 pass）。
- **目標檔案**：`skills/research/SKILL.md`，「## 品質標準」段（行 54–58）。（附帶可在 `TASK_CARD_TEMPLATE.yaml` 的 `definition_of_done` 註解呼應，非必要。）
- **精確 before→after**（品質標準末新增一條）：

  before：
  ```markdown
  ## 品質標準
  - 每個事實主張都要有來源
  - 推論要標明推論依據
  - 不確定的資訊標記 [待驗證]
  - 不把搜尋結果直接複製貼上，要消化重組
  ```
  after：
  ```markdown
  ## 品質標準
  - 每個事實主張都要有來源
  - 推論要標明推論依據
  - 不確定的資訊標記 [待驗證]
  - 不把搜尋結果直接複製貼上，要消化重組
  - 完成度以「章節 / 主張覆蓋度」為主要判準，字數僅作軟性參考（避免量化字數與品質脫鉤）
  ```
- **理由**：研究品質取決於覆蓋的切片、量化主張數、四態分離是否到位，而非字數。改後 completion_check 可給明確 pass/fail。
- **風險**：低。新增一行後 research SKILL.md 仍遠低於 1.5K token 硬限制。**套用為 ask 級**（改 skills/）。

---

## 高風險假設

- **F1 限縮條件足夠**：假設「限 scripts/ 產生器 + 衍生檔」能涵蓋未來所有衍生檔情境。若日後出現非 scripts/ 產生的衍生檔，需再擴充定義；目前僅 `frontend/data.json` 一個衍生檔，假設成立。
- **權限守門人能辨識**：`scripts/permissions_guard.py` 目前以動作名稱比對清單。新增 `regenerate_derived_artifacts` 若要被執行期 hook 強制，需同步在 guard 與其測試補對應規則（見「建議下一步」）。

## 待驗證

- `regenerate_derived_artifacts` 是否需在 `scripts/permissions_guard.py` 與 `test_permissions_guard.py` 補對應條目（取決於 guard 是否對 allow 清單做 enforcement，待讀該腳本確認）。
- F2 註解是否需同步反映到 `scripts/`（目前無腳本自動計 `max_tool_calls`，純人工/紀錄層，推測無需改碼，[待驗證]）。

## 建議下一步

1. 你逐項 approve/reject F1 / F2 / F4。
2. 核准者另立一張 ask 級 Task Card（skill_type: ops，risk: medium，allowed_tools 含 modify_system_rules / modify_skills），套用核准項到 `system/` 與 `skills/`。
3. 若 F1 採納，於同卡補 `permissions_guard.py` 規則 + 測試，並重生 manifest。
4. 套用後跑全 CI 套件（13 步）確認綠燈；寫 audit + 批准日誌。
