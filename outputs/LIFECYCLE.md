# Outputs 生命週期 SOP

`outputs/` 下三個子目錄各代表不同成熟度，本檔定義晉升 / 棄用 / 歸檔的條件。

## 三態定義

| 目錄 | 性質 | 變更權限 |
|------|------|---------|
| `outputs/drafts/` | 任務產出的草稿，可能含 [待驗證] 標記、未經人工確認 | `write_drafts`（allow） |
| `outputs/reports/` | 經人工確認、可被其他治理 artifact 引用的正式產出 | `write_reports`（ask） |
| `outputs/archived/` | 已被取代、棄用或失去引用價值的舊版產出，僅供考古 | `write_drafts`（allow），但不可刪除 |

## 晉升條件：drafts/ → reports/

任一成立即可由人工確認後晉升：

1. 被 `system/` 或 `README.md` 等活性文件引用為 source of truth
2. 累積 ≥ 5 筆相關 audit log 後仍持續被引用
3. retro 或人工審閱後標記為「需正式化」

晉升步驟（見 `tasks/2026-04-17_retro-graduation-and-archive.yaml` 為範例）：

1. 在 `outputs/reports/` 建立新檔，檔頭加「晉升標記」段（原 draft 路徑、晉升日期、晉升任務、審閱者）
2. 原 `outputs/drafts/` 檔尾補一行回指 `outputs/reports/...`
3. 將活性引用全部改指新路徑
4. 人工確認 → 寫入 audit log

## 棄用條件：reports/ 或 drafts/ → archived/

任一成立即可棄用：

1. 被新版本取代（v1 → v2，且 v1 不再被引用）
2. 對應任務或專案已封存（如 `memory/archived_projects/` 內專案的產出）
3. 內容過時且無人接手更新（建議在最後一次更新 ≥ 90 天後重新評估）

棄用步驟：

1. `git mv` 至 `outputs/archived/`，保留原檔名（必要時加日期後綴避免衝突）
2. 在原檔的歷史引用處註記「已歸檔至 outputs/archived/...」
3. 寫入 audit log；不刪除（`shell_delete` 在 PERMISSIONS deny 清單）

## 現有 drafts/ 狀態（2026-04-26 盤點）

| 檔名 | 狀態 | 備註 |
|------|:----:|------|
| `20260424-O01_cleanup-summary.md` | 終態（任務摘要） | ops 任務 summary，永遠保留在 drafts/ |
| `20260424-O02_restructure-summary.md` | 終態（任務摘要） | 同上 |
| `20260424-O03_guardrails-summary.md` | 終態（任務摘要） | 同上 |
| `analysis-create-task-card-permission.md` | 已被引用 | 支撐 `memory/.../decisions/20260415-D004`，暫留 |
| `retro-2026-04-15.md` | 已晉升 | → `outputs/reports/retro-2026-Q2-01.md`（2026-04-17） |
| `token-calibration-table-v1.md` | 已晉升 | → `outputs/reports/token-calibration-v1.md`（2026-04-24） |

> 任務摘要類（`*-summary.md`）視為終態：產生時即為任務完成註記，不再演進，也不晉升。
> 已晉升的兩份草稿在 90 天評估期後（≥ 2026-07-15）若無人引用 drafts/ 版本，可考慮棄用。

## 與其他治理檔的關聯

- `system/PERMISSIONS.yaml`：`write_drafts` allow / `write_reports` ask
- `system/GATE_POLICY.yaml`：第四層 risk_check 失敗時，產出鎖定在 drafts/
- `tasks/TASK_CARD_TEMPLATE.yaml`：`expected_output.location` 預設為 `outputs/drafts/`
