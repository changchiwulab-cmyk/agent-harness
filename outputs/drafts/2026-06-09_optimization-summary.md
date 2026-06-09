# Agent Harness — 2026-06-09 優化總結

> Task Card：`20260609-001` ｜ skill：ops ｜ 草稿（依硬規則 2，產出先進 drafts/）

## 檢視結論

專案**遠比表面成熟**：45 張 Task Card、完整 CI（13 道檢查）、`governance_metrics.py` 指標引擎、
e2e failure-drill、前端看板，R1–R8 強化系列已落地。完整度問題不在「缺檔案」，而在三件事：
狀態漂移、三條硬規則仍 prompt-only（plan §3.1）、GATE 四層僅 schema 自動化（§3.6）。

## 本輪交付（三條工作線）

### WS1 — 校正狀態漂移
- `memory/.../context.md`：2026-04-15（6 audit、16 模組）→ 2026-06-09 現況（45 卡、R1–R8、Route 2+3、metrics/frontend/CI）
- `README.md`：補列 R1–R8 後新增 system 檔；過時的 Week 1-3 上手 → 目前運行節奏；版本表更新（v2.x 現在、v3 改為治理層抽出）
- `harness-self-assessment-v1.md`：加 2026-06-09 addendum（不改寫歷史）；強制力表回寫

### WS2 — 硬化三條硬規則（deterministic）
| 規則 | 之前 | 之後 |
|------|------|------|
| 無卡不執行 | 0% | `task_card_guard.py` 擋無卡片的 reports/ 新正式產出 |
| 對外只草稿 | 30%（Bash） | + reports/ 守門，正式產出走 draft→promote |
| 失敗 3 次停 | 0%（無計數器） | `failure_counter.py` 計數 + halt hook + --reset |

兩支 guard 註冊進 `.claude/settings.json`（Bash + Write|Edit）；PERMISSIONS / GATE_POLICY 補述強制點。

### WS3 — 自動化 GATE 剩餘三層
- `gate_check.py`：四層 post-execution validator（L1 重用 validate_task_card；L2 run-log tools 子集；L3 產物存在；L4 drafts 收斂）

## 驗證
- 三支新元件各有單元測試（共 32 測試）並納入 CI
- 手動驗收：無卡寫 reports/ → block；連續 3 失敗 → 後續工具 block；gate_check 對真實卡片輸出四層結果
- 全部既有 CI 對等檢查（spec consistency / YAML parse / frontend --check / 既有測試）通過

## 誠實標註的殘餘
drafts 階段的 Task Card 約束、ask 等級人工確認、失敗的「判定與記錄」仍依賴 Claude 遵循 CLAUDE.md ——
「用 LLM 約束 LLM」的結構性天花板，本輪只能抬高 deterministic 覆蓋率，無法消除。

## 不在範圍
v3 治理插件（`agent-governance`）抽出 —— 已 staged 於 `outputs/drafts/agent-governance-bootstrap/`，
建 repo 延至專屬 session（D007）。
