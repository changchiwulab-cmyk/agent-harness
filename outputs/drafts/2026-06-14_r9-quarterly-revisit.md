# R9 — NATIVE_OVERLAP 季度 revisit 自動化（交付草稿）

> **草稿（draft）**｜日期：2026-06-14｜Task Card：`20260614-R09`｜skill：ops
> 範圍：擴充 `scripts/governance_metrics.py`（M4 季度逾期偵測 + R4 合流）、補測試並掛進 CI、`system/RETRO_FLOW.md` 加季度重評維度。
> roadmap 來源：`outputs/reports/harness-self-assessment-v1.md` §五 R9（季度級，相依已完成的 R4+R7）。

---

## 結論

R9 落地：原本 roadmap 規劃的「季度 revisit 自動化」中，**數值閾值（>50% alert / 40–50% warn）在 R7 前就已存在於 M4**，
真正缺的三塊已補齊——**(1) 季度逾期偵測**、**(2) 與 R4 決策回看合流的單一視圖**、**(3) >50% 或逾期時明確觸發 R10 v3 評估**。
附帶修掉一個治理漏洞：`test_governance_metrics.py` 過去**未被任何 CI 步驟執行**，現已掛入 `spec-consistency` workflow。

跑一次 `python3 scripts/governance_metrics.py` 即得單一季度治理視圖。今日（2026-06-14）實況：

```
## 季度治理重評（R9：原生重疊 + 決策回看）
- 原生重疊：30%（reviewed 2026-05-09；36 天前重評） → ✅ ok
- 決策回看（R4 check_decision_revisit）：DUE=0 OK=2 MANUAL=5
  - 無 DUE 決策
```

→ 重疊 30% 未破門檻、距上次重評 36 天未逾季、無 DUE 決策 → **本季無需開 R10**。

---

## 變更明細

| 檔案 | 變更 | 權限 |
|------|------|------|
| `scripts/governance_metrics.py` | `metric_m4` 加 `today` 參數：解析 `reviewed_on`、計 `days_since_review`、`QUARTER_DAYS=90`；逾期升級 status；`details` 增 `days_since_review / revisit_overdue / recommended_action`。新增 `collect_decision_revisit()`（subprocess 跑 R4 tracker，best-effort）＋ `render_quarterly_revisit_markdown()`。 | allow（code） |
| `scripts/test_governance_metrics.py` | 既有 4 個 M4 測試改傳 `today`；新增逾期/接近到期/建議/不可解析 + R4 合流（解析、ruby 缺失、非零、壞 JSON、渲染）共 13 個案例。 | allow（code） |
| `.github/workflows/spec-consistency.yml` | 新增 `Governance metrics tests` 步驟，把孤兒測試掛進 CI。 | allow（code） |
| `system/RETRO_FLOW.md` | §1 資料蒐集加跑 governance_metrics；§2 分析維度加「原生重疊季度重評」列。 | **ask**（經計畫核准） |

---

## 判定邏輯（M4 雙軸取較嚴重者）

- **數值軸**：`pct > 50 → alert`；`40 ≤ pct ≤ 50 → warn`；否則 ok（既有，不變）。
- **新鮮度軸（R9 新增）**：`days_since_review > 90 → alert`（逾一季的 30% 不可信，視同需重評）；`75 < days ≤ 90 → warn`（接近到期）；否則 ok。
- `pct > 50` **或** 逾期 → `recommended_action` 指向 `outputs/drafts/v3-readiness-assessment.md`（R10）。
- `reviewed_on` 無法解析 → `days_since_review=None`，不觸發新鮮度升級（由數值軸決定），避免誤報。

> 設計取捨：R4 合流以 subprocess 呼叫既有 `check_decision_revisit.rb --json`，**不在 Python 重寫**，維持單一事實來源；任何失敗（無 ruby／非零／壞 JSON）降級為 `available=False`，不影響 `governance_metrics` 的 exit code，`--json` 仍只輸出 M1–M4（回歸守門測試保留）。

---

## 驗證

| 檢查 | 結果 |
|------|------|
| `python3 scripts/test_governance_metrics.py` | 37 tests OK（含 R9 新案例；現已在 CI） |
| `python3 scripts/governance_metrics.py --today 2026-06-14` | 含「季度治理重評」節，exit 0 |
| `python3 scripts/governance_metrics.py --json` | 仍只 M1–M4（無回歸） |
| `ruby scripts/check_decision_revisit.rb` | exit 0（R4 未受影響） |
| `ruby scripts/check_spec_consistency.rb` | OK（含新 Task Card schema） |
| `python3 scripts/generate_frontend_manifest.py --check` | up to date（已重生 data.json） |
| `ruby scripts/check_context_budget.rb` | within limit |

---

## 下一張卡（不在本次範圍）

**R10 — v3 遷移就緒度評估**：本季 M4 顯示 30% / 未逾期 → **暫不觸發**。待 M4 報 alert（重疊破 50% 或季度逾期）時，
依 `recommended_action` 開新 Task Card，產 `outputs/drafts/v3-readiness-assessment.md`（逐模組保留/下放原生/並存、
盤點不可替代資產、對齊 `2026-05-09_v3_extraction_plan.md`、提 D003/D007 status 更新；只評估不遷移）。
