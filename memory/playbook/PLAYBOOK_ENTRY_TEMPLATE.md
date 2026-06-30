# Playbook 條目格式（程序記憶）

程序記憶 = 可重用的啟發、SOP、踩過的坑。每個 skill 一個檔（`<skill>.md`）。
由 RETRO 萃取、經人工確認後寫入（ask）。寫完跑 `scripts/build_memory_index.py` 更新索引。

## 條目格式

每條 playbook 以一行 HTML 註解標記開頭，供 `build_memory_index.py` 解析：

```
<!-- ENTRY id=PB-<skill>-### skill=<skill> tags=tag1,tag2 -->
## 條目標題（一句話可執行的啟發）
條目內容：說明這個做法、為什麼有效、適用情境。
來源：<episode / retro / error log 路徑>
```

規則：
- `id` 全域唯一，格式 `PB-<skill>-###`（如 `PB-research-001`）。
- `skill` 必填，須為 research / analysis / writing / ops / review 之一。
- `tags` 逗號分隔、無空白，供關鍵字檢索。
- 標題用 `## `，是檢索結果顯示的主文。
- 一條只講一件事；跨任務反覆出現才值得收錄。
