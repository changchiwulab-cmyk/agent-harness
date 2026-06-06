# Evolution Loop — 自我進化迴圈（提案制 / 人工把關）

把 `RETRO_FLOW` 的「事後手動回顧」升級成**可重複執行的閉環引擎**：系統持續觀測自己，
自動產出進化提案，但**永遠停在人工閘門**——任何 `system/`/`skills/`/`memory/` 變更都需人工核可。

## 為什麼是提案制（不是自動改自己）

CLAUDE.md 硬規則與「可控 > 能力」要求：不自動改規則、不自動寫長期記憶。
從 AGI 監督角度，**會自我修改的迴圈正是 reward-hacking / scheming 最危險的地方**，
因此本迴圈：(1) 唯讀觀測、只把提案寫到 `outputs/drafts/`；(2) 餵給它的是**獨立驗證器**
（`verify_completion` / `verify_audit_integrity`）而非執行者自報；(3) 套用一律經人工。

## 迴圈五步

```
1. 觀測 observe   ── scripts/evolution_loop.py 唯讀讀取：
                     logs/runs(成本+gate)、logs/errors、verify_completion、
                     verify_audit_integrity、NATIVE_OVERLAP、check_decision_revisit
2. 分析 analyze   ── 對四面向套閾值，偵測進化觸發
3. 提案 propose   ── 產出 outputs/drafts/evolution-<date>.md（🔴action/🟡warn/🟢info）
   ── ── ── ── ──  ▼  人 工 閘 門（迴圈到此停）  ▼  ── ── ── ── ──
4. 套用 apply     ── 人工勾選 → 改對應 system/skills（ask 級）→ 記一筆 decision log
                     （動到 memory/ 後跑 verify_audit_integrity.py --update）
5. 再觀測 re-obs  ── 下週期重跑 evolution_loop，確認問題收斂
```

## 觀測四面向與觸發閾值

| 面向 | 來源 | 觸發 | 提案目標 |
|------|------|------|------|
| 成本 | logs/runs `token_estimate` | 校準係數（實測均/初估）≥ 1.5 且樣本 ≥ 2 | `COST_POLICY.md` 預算/係數 |
| 失敗 | logs/errors + verify_completion + audit | 同 error_type ≥ 2；任一 verify_completion FAIL；稽核 WARN | `FAILURE_TAXONOMY` / `GLOBAL_RULES` / AUDIT 遷移 |
| Gate | logs/runs `gate_results` | 單層 fail 率 ≥ 34% | `GATE_POLICY` 該層 / `TASK_CARD_TEMPLATE` DoD |
| 決策 | NATIVE_OVERLAP + check_decision_revisit | revisit_trigger 達成；overlap ≥ 40%(warn)/50%(v3) | decision 回看 / v3 評估 |

閾值集中在 `scripts/evolution_loop.py` 頂部常數，對齊 `COST_POLICY` 與 `NATIVE_OVERLAP`。

## 怎麼跑（每週期）

```bash
python3 scripts/evolution_loop.py            # 產出 outputs/drafts/evolution-<date>.md
python3 scripts/evolution_loop.py --check     # 乾跑（不寫檔），CI 用，永遠 exit 0（advisory）
python3 scripts/evolution_loop.py --json       # 提案 JSON
```

- 觸發節奏：沿用 `RETRO_FLOW` 觸發（累積 5 筆任務 / 同類錯誤 2 次 / 手動）；
  亦可用 `loop` skill 或 cron 週期驅動 `evolution_loop.py`。
- CI 只跑 `--check`（乾跑、不寫檔、advisory），確保引擎不退化，不擋 build。

## 與既有機制的關係

- 是 `RETRO_FLOW` 的自動化前端：RETRO 的「資料收集 + 分析維度」由本引擎機器化，
  人工專注在「決定採納哪些」。
- 復用 R4 `check_decision_revisit`、R7 `governance_metrics`、AGI-1/3 驗證器作為觀測來源。
- 套用後的紀錄仍走 `memory/.../decisions/`（人工確認）＋ `logs/AUDIT_LOG.md`。
