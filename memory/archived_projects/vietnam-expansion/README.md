# Vietnam Expansion — 已歸檔

## 狀態

- **歸檔日期**：2026-04-17
- **歸檔依據**：Task Card `20260417-O02`（tasks/2026-04-17_retro-graduation-and-archive.yaml）
- **歸檔原因**：目前無活躍任務，暫無新決策 / 參考資料累積。保留 context 與目錄結構供未來重啟。
- **完整背景**：見 [`context.md`](./context.md)

## 目錄狀態

| 路徑 | 狀態 | 說明 |
|------|------|------|
| `context.md` | 保留 | 專案目標、範圍、限制（archive 時凍結） |
| `decisions/` | 空殼（.gitkeep） | 歸檔時無任何決策紀錄 |
| `references/` | 空殼（.gitkeep） | 歸檔時無外部參考資料 |

## 重啟條件

當下列任一條件成立時，將整個目錄 `git mv` 回 `memory/active_projects/vietnam-expansion/`：

1. 重新啟動越南市場 AI 工具研究任務
2. 一人公司業務開始考慮越南市場切入
3. 取得新的市場資料（公開報告、訪談紀錄）值得納入長期記憶

## 重啟操作（範例）

```bash
git mv memory/archived_projects/vietnam-expansion memory/active_projects/vietnam-expansion
git commit -m "feat: revive vietnam-expansion project"
```

重啟後請建立第一張 Task Card 並更新 `context.md` 的狀態欄位（`status: archived` → `status: active`）。

## 不要做

- **不要刪除** 此目錄（即使長期不用）。歸檔的價值在於「暫停但可追溯」。
- **不要在歸檔狀態下修改** `context.md`。需要修改 = 已重啟，請先 git mv。

---

*建立日期：2026-04-27*
*來源：Task Card 20260427-A01*
*補完原因：原 archive 動作未留 README，新使用者不知歸檔原因與重啟方式*
