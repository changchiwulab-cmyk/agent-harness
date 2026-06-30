# 記憶層策略 MEMORY_POLICY

> 本檔定義 agent-harness 的分層記憶架構與權限分界。
> 操作型規則（active/archived、邊界、禁止事項）見 `memory/README.md`，兩者互補不重複。

## 為什麼需要分層記憶

LLM 原生只有「當前 session」這一層 working memory，session 結束即遺忘。
2026 的 agent 架構把記憶當成獨立元件：除了 context window，還要能**跨 run 累積**、
**按需檢索**，讓系統從執行結果學習，而不是永遠用相同設定重來。

本框架在「不自動寫記憶、可稽核、零外部依賴」的前提下補這個洞——
用結構化檔案 + 關鍵字/標籤索引，而非向量資料庫（見 Decision D008）。

## 四層記憶映射

| 層 | 位置 | 內容 | 寫入 | 讀取 |
|----|------|------|------|------|
| **working**（工作） | 當前 session context | 對話、近期工具輸出、當前目標 | 自動（原生） | 自動 |
| **episodic**（情節） | `memory/episodes/` | 跨 run 的單次執行摘要：做了什麼、成功/失敗、學到什麼 | **ask**（人工確認） | **allow**（檢索） |
| **procedural**（程序） | `memory/playbook/` | 可重用的啟發、SOP、踩過的坑（每 skill 一檔） | **ask**（人工確認） | **allow**（檢索） |
| **semantic/decision**（語意/決策） | `memory/active_projects/*/decisions/` | 結構化決策紀錄（既有，D-log） | **ask**（人工確認） | **allow** |

> working 由 Claude Code 原生管理（NATIVE_OVERLAP：context 自動壓縮），本框架不重造。
> 其餘三層是本框架的差異化資產：原生不提供「跨 session 可累積、可檢索」的記憶。

## 權限分界（關鍵）

- **檢索/讀取 = allow**：`read_memory`（既有）+ `read_memory_index`（新增，PERMISSIONS.yaml）。
  進場時依 skill_type/關鍵字檢索相關 episodes/playbook 注入 context，屬純讀取，免確認。
- **寫入 = ask**：寫 episode、playbook、decision 一律 `write_long_term_memory`，需人工確認。
- **自動寫入 = deny**：`auto_write_memory` 維持禁止。不把對話內容自動沉澱成長期記憶。

## 進場檢索（INTAKE 階段）

建立 Task Card 時，依 `skill_type` + goal 關鍵字呼叫 `scripts/memory_retrieve.py`，
撈出相關 episodes（過去類似任務怎麼做、踩過什麼坑）與 playbook（該 skill 的可重用啟發），
摘要注入 context。對應 2026「context playbook」自我改進迴圈（見 INTAKE_FLOW.md）。

## 寫入流程與門檻（RETRO 階段）

學習迴圈由 RETRO 閉合（見 RETRO_FLOW.md）：

1. **episode 寫入門檻**（呼應 D006「不對小任務加負擔」）：僅在任務
   `status=failed/partial`、`risk_level≥high`、或「有可複用的教訓」時寫 episode。
   happy-path 小任務不寫，避免噪音。
2. **playbook 寫入**：當 RETRO 發現「跨任務反覆出現的有效做法或踩坑」時，
   萃取成一條 playbook 條目寫入對應 `memory/playbook/<skill>.md`。
3. 兩者皆**先提議、等人工確認**後才寫入，然後跑 `scripts/build_memory_index.py` 更新索引。

## 索引機制

- `scripts/build_memory_index.py`：從 episode/playbook 檔重建
  `memory/episodes/INDEX.yaml` 與 `memory/playbook/INDEX.yaml`（確定性、可 diff、CI `--check` 防漂移）。
- `scripts/memory_retrieve.py`：讀索引，依 skill_type + 關鍵字/標籤比對回傳相關條目。
- 不用向量庫：保持可稽核、零外部依賴。召回率不足時，先補標籤；
  條目 > 30 筆仍不足再評估語意檢索（D008 revisit_trigger）。

## 禁止事項（延續 memory/README.md）

- 不自動把每次對話寫入 episode/playbook。
- 不在記憶中存敏感個資（密碼、金鑰、身分證號）——晉升前由 `scripts/output_scan.py` 把關。
- 不存大量原始資料，用路徑引用。
