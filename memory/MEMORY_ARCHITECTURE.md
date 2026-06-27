# Memory Architecture — 受控記憶架構（M4）

> 解「`memory/` 形同虛設、保守過頭＝能力閹割」（plan §3.5），
> **但不破壞**「不自動寫長期記憶」的 deny 規則。
> 對齊 2026 業界：filesystem-as-memory（Letta benchmark）、learned-patterns 庫（Letta Skill Library）。
> 做法：定義 working memory **可以累積的位置**與**人工晉升 gate**，而非開放自動長期記憶。

## 四層記憶（OS 式分層，靈感自 MemGPT/Letta）

| Tier | 內容 | 位置 | 寫入權限 | 存活範圍 |
|------|------|------|---------|---------|
| **Tier 0** working / session note | 當前任務的暫存狀態、handoff note | `memory/active_projects/<p>/notes/` | **allow**（session 內可自由寫） | 單 session；可被 checkpoint 保存 |
| **Tier 1** project context | 專案持久背景 | `memory/active_projects/<p>/context.md` | **ask**（人工確認） | 跨 session |
| **Tier 2** decisions | 結構化決策日誌 | `memory/active_projects/<p>/decisions/*.yaml` | **ask**（human-confirm，既有） | 永久 |
| **Tier 3** learned patterns / playbook | 反覆有效的可重用樣式 | `memory/playbooks/*.yaml` | **ask**（human-confirm 晉升） | 永久、跨專案 |

> 關鍵：**Tier 0 是新解放的空間**——session 內 working memory 可累積（不再每次從零），
> 但「跨 session 存活」一律需人工晉升（Tier 1–3）。`auto_write_memory` **仍在 deny**：
> 沒有任何路徑會在無人工確認下把對話自動寫成長期記憶。

## Tier 3：learned-patterns / playbook 庫（NEW）

把「學會的有效做法」存成 `.md`/`.yaml`，下次遇到類似問題可主動調用（對齊 Letta Skill Library）。
- 範本：`memory/playbooks/PLAYBOOK_TEMPLATE.yaml`。
- 晉升條件（human-confirm）：同一樣式在 ≥2 個任務被驗證有效，且不與既有 decision 衝突。
- 與 skills/ 的差別：skills/ 是**能力定義**（怎麼做某類任務）；playbook 是**經驗結晶**（這個專案/情境下，這樣做最有效）。

## 與其他模組的關係

- **Context Engineering（M3）**：Tier 0 note = compaction 的 context 外落點（filesystem-as-memory）。
- **Decision Log（既有）**：Tier 2 不變，仍是治理三件之一。
- **PERMISSIONS.yaml**：寫入權限對齊 allow（Tier 0）/ ask（Tier 1–3）/ deny（auto long-term write）。

## enforcement 點（符合 J5）

- 寫入分層對應 `PERMISSIONS.yaml` 的 allow/ask/deny（runtime 由 `permissions_guard.py` 守 deny）。
- Tier 3 playbook 有 schema（`PLAYBOOK_TEMPLATE.yaml`）；晉升自動化檢查另開卡（M4-b）。

## 後續（另開卡，M4-b）

- playbook 晉升自動化：掃 Tier 0 notes → 偵測重複樣式 → 提示人工晉升（讀寫 gate hook）。
- `check_spec_consistency.rb` 加 playbook schema lint。
