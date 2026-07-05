# Lessons — 踩坑教訓帳本

> 規則：**只增不改**（append-only）。新條目一律 `status: proposed`，使用者 retro 時
> 裁決轉 `confirmed` / `rejected`；蒸餾進規則檔後轉 `distilled` 並移到檔尾歸檔區。
> 什麼算教訓、何時壓縮：見 `system/MAINTENANCE_PROTOCOL.md` §3–§4。
> 品質判準：下一個 session 讀了能**改變行為**才算教訓，「要更小心」不算。

## 格式（複製這塊）

```markdown
### L-YYYYMMDD-NN ｜ 一句話標題
- date: YYYY-MM-DD
- task: Task Card ID 或 session 描述
- status: proposed
- 症狀: 發生了什麼（可觀察的事實）
- 根因: 為什麼會發生（不是「不小心」，是機制）
- 教訓: 下次遇到 X 就做 Y（可執行的行為改變）
- 建議寫回: 哪個規則檔的哪一節（蒸餾時用；沒有就寫「暫留」）
```

---

## Active

### L-20260705-01 ｜ 背景 agent 的結果要在收到當下落檔
- date: 2026-07-05
- task: 20260704-F01
- status: proposed
- 症狀: session 中途重啟，兩個背景 subagent 的 task 引用全部失效（`No task found`），
  其中一個的研究結果差點遺失，靠事後從 transcript 檔案搶救回來。
- 根因: 雲端 session 可能隨時重啟；task 引用存在記憶體，重啟即斷；只有寫進
  repo 檔案（且 commit）的內容保證存活。
- 教訓: 背景 agent 回報一到手，先把結論寫入 `outputs/drafts/` 或計畫檔再繼續；
  長任務每完成一個交付立即 commit（checkpoint），把「已落檔」當成唯一的進度定義。
- 建議寫回: `system/RECOVERY_RUNBOOK.md` 場景 C（已部分覆蓋）；DISPATCH_POLICY §4 已含
  「長產物寫入檔案」。暫留觀察是否重複發生。

## 已蒸餾歸檔

（尚無）
