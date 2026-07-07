---
name: writing
description: 一人公司的撰寫產出 skill — 提案、報告、文件包裝、內容規劃、SOP、對外文案。觸發場景：使用者要草擬/撰寫/產出文件，或 Task Card 的 skill_type 為 writing。輸出規範：結論先行、段落短密、台灣商業用語、嚴守 expected_output 的格式與篇幅，草稿進 outputs/drafts/。用於 Task Card 執行階段。
---

# Writing Skill

## 用途
提案撰寫、報告產出、文件包裝、內容規劃、SOP 撰寫、對外文案。

## 執行流程
1. 確認寫作目標、讀者、格式、篇幅（從 Task Card 取得）
2. 載入相關 context（project context、參考資料）
3. 先產出大綱，確認結構
4. 逐段撰寫
5. 自我檢查：邏輯、用詞、格式、完整度
6. 輸出草稿到 outputs/drafts/

## 寫作原則
- 結論先行，再展開論述
- 段落短而密，每段一個重點
- 用台灣商業用語，避免翻譯腔
- 區分事實與推論
- 數據要有來源

## 輸出格式
依 Task Card 的 expected_output.format 決定：
- md：Markdown 文件
- html：互動式文件
- yaml：結構化資料

## 品質標準
- 符合指定的篇幅與格式
- 邏輯連貫，無自相矛盾
- 專有名詞一致
- 結論有依據支撐

## 常見失敗模式
- 寫太多（沒控制篇幅）→ 先確認字數/段落限制
- 格式不符需求 → 先確認 expected_output
- 內容空洞（大量修飾語無實質資訊）→ 每段要有具體 insight
- 自動加了沒被要求的章節 → 嚴格遵照大綱
