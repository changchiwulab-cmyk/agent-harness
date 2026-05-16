# 20260516-002 — 最壞情境（failure injection）測試套件：執行摘要

## 結論

DoD 6/6 通過。新增 `tests/e2e/test_failure_injection.py`,對 `FAILURE_TAXONOMY.yaml` 每個失敗模式注入壞輸入並斷言對應 guardrail 觸發,含防漂移守衛,並掛進 CI。全 CI 套件本機綠。

## 故障注入矩陣（15 模式全覆蓋）

| 失敗模式 | 注入 | 斷言 guardrail |
|---|---|---|
| SPEC-01/03/04, COORD-03, VAL-01 | 產物缺失/不對 DoD | completion gate 逐條 fail,非靜默通過 |
| SPEC-02 / SEC-03 | 連續 3 次相同動作 | `should_stop(3)` 觸發、`should_stop(2)` 不觸發 + CLAUDE.md 硬規則 3 |
| SPEC-03 | — | CLAUDE.md 宣告 checkpoint + 20 輪摘要 |
| COORD-01 | context 重置 | `rule_check.rollback` 含 git checkout |
| COORD-02 | 模糊需求(空 goal) | schema gate 拒絕,不執行 |
| COORD-04 | — | taxonomy 載明 confirm-before-continue 緩解 |
| VAL-02 | 部分 DoD(2/3) | 精確列出缺漏該條 |
| VAL-03 | schema 有效但內容空 | schema pass 但 completion fail(格式≠內容分離) |
| SEC-01 | allowed_tools 含 deny 項 | rule gate fail |
| SEC-02 | — | PERMISSIONS deny 含 send_email/外發/publish |
| SEC-04 | 幻覺驅動高風險產物 | risk gate 強制鎖回 drafts/ |

防漂移：`test_handler_registry_matches_taxonomy_no_drift` 動態比對 taxonomy id 與 handler 集合,新增/刪除模式而無對應 case 即 fail。CI 新增 `E2E failure-injection suite` step。

## 重要發現（待人工決策,未自行修改）

`system/FAILURE_TAXONOMY.yaml` 檔頭與多處文件寫「14 種失敗模式」,但實際有 **15** 種(SPEC×4 + COORD×4 + VAL×3 + SEC×4)。SEC-04 是依 Task Card 20260409-001 後補,但 header、`README`、`tasks/2026-04-09_system-validation.yaml` DoD#3 仍寫 14,未同步。

- 測試已改為 count-agnostic(`>= 14` + 結構健全 + drift guard),不依賴錯誤常數。
- 修正 `system/` 文件屬 `ask` 權限,超出本 Task Card 範圍。**建議另開一張低風險卡同步「14 → 15」文件**(FAILURE_TAXONOMY 檔頭、README、system-validation 卡 DoD#3)。

## Gate 驗證

schema/rule/completion/risk 四層皆 pass;low risk,無對外動作。

## 驗證指令

```bash
python3 tests/e2e/test_failure_injection.py   # 3 tests OK（15 模式 subTests 全綠）
```
