# 自我進化提案 — 2026-06-06

> **草稿（draft）** ｜ 由 `scripts/evolution_loop.py` 自動觀測+分析產出。
> **提案制（人工把關）**：本檔只是提案。任何 `system/`/`skills/` 變更**須人工核可後**才套用；
> 本迴圈不自行修改任何規則/政策/記憶（CLAUDE.md 硬規則、可控 > 能力）。

觀測四面向：成本 / 失敗 / Gate / 決策。共 3 條提案（🔴 1 action、🟡 1 warn、🟢 1 info）。

| | 面向 | 發現 | 建議變更（待人工核可） |
|:--:|------|------|------|
| 🔴 | gate | schema_check 失敗率 1/2（≥34%）—— 該層最常卡。 | system/GATE_POLICY.yaml（schema_check）/ tasks/TASK_CARD_TEMPLATE.yaml：檢視該 gate 條件或 DoD 顆粒度。 |
| 🟡 | failure | verify_audit_integrity 報 2 筆稽核 WARN（覆蓋缺口/生成漂移）。 | logs/AUDIT_LOG.md：考慮開「遷移到生成格式」任務，之後把 generate_audit_log --check 升為硬 gate。 |
| 🟢 | cost | 只有 0 筆 dashboard_measured token 樣本（需 ≥2 才能可信回測）。 | logs/runs/*.yaml：未來 run 的 token_estimate.source 填 dashboard_measured；暫不調 COST_POLICY 數字。 |

## 閉環下一步（人工）
1. 審閱上表，勾選要採納的提案。
2. 採納者：人工修改對應 `system/`/`skills/`（ask 級），並依 RETRO_FLOW 記一筆 decision log。
3. 若動到 memory/，套用後跑 `verify_audit_integrity.py --update` 重建完整性 manifest。
4. 下個週期再跑 `evolution_loop.py` 重新觀測，確認問題收斂。

_來源工具：verify_completion / verify_audit_integrity / logs(runs,errors) / check_decision_revisit / NATIVE_OVERLAP / COST_POLICY。_
