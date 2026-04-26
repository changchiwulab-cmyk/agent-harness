# Outputs Templates

對外客戶交付的可重用樣板。

## 目錄

| 檔案 | 用途 | 何時使用 |
|------|------|---------|
| `client_cover_letter.md` | 客戶交付件的封面信 | 任何 reports/ 等級的對外產出 |
| `version_record.md` | 版本紀錄表 | 多輪交付的同一份產出 |
| `risk_disclosure.md` | 風險聲明 | 含建議 / 預測 / 分析判斷的產出 |

## 用法

1. 啟動對外交付任務時，於 Task Card `input_data` 列入需要的樣板路徑
2. 複製到 `outputs/drafts/<task_id>/` 子目錄填寫（不要直接編輯本目錄）
3. 與主產出一同經人工審閱後，整批晉升至 `outputs/reports/<task_id>/`

## 與 drafts / reports 銜接

- `drafts/` 階段：樣板可有 [待填] / [待客戶確認] 等佔位符
- `reports/` 階段：樣板必須全部填妥，並通過 `system/GATE_POLICY.yaml` 第四層 risk_check
- 對應 `outputs/LIFECYCLE.md` 的晉升條件第 1 條（被活性文件引用）

## 敏感資料原則

- 樣板本身不含真實客戶資訊；佔位符使用 `<CLIENT_NAME>`、`<PROJECT_CODE>` 等明顯標記
- 填寫時，敏感欄位（價格、合約期、聯絡人）須與一般欄位分開段落，便於審閱前 redact
- 所有對外發送動作受 `system/PERMISSIONS.yaml` 的 `send_email` / `publish_content` deny 規則約束
