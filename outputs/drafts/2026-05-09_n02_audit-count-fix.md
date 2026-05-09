# N2 — Audit 計數錯誤歸因修正

- Task: `20260509-N02`
- Date: 2026-05-09
- Skill: review
- Status: draft（risk_level=low）

## 0. TL;DR

A01 §1.1 與 W01 §9 都把「30+」歸因 README，但 grep 顯示 **README 從無「30+」字樣**。
真正出處是 plan §Context 與 A01/W01 task card 的 context 欄位（引自 plan）。
順帶修正計數：本 PR 推送前實 18 筆（不是 17），本 PR 後 23 筆。

---

## 1. 事實核對

### 1.1 README.md 是否有「30+ audit」字樣？
```
$ grep -in "30+\|30+ audit\|30 筆\|26 張" README.md
（無輸出）
```
**結論：沒有。** README 只在 v1/v1.5/v2/v3/v4 版本表中提到 audit 為功能名，未給數字。

### 1.2 「30+」真正出處
```
$ grep -rn "30+" .
memory/active_projects/agent-harness/plans/ai-bubbly-mountain.md (§Context 與 §2.3、§4.1、§7)
tasks/2026-05-09_harness-v3-governance-extraction.yaml (context 欄位，引自 plan)
tasks/2026-05-09_harness-methodology-outline.yaml (context 欄位，引自 plan)
outputs/drafts/2026-05-09_v3_extraction_plan.md (修正前的 §1.1 與 §10，誤歸因 README)
outputs/drafts/2026-05-09_methodology_outline.md (修正前的 §9，誤歸因 README)
```

### 1.3 實際計數
```
$ grep -c '^- task_id:' logs/AUDIT_LOG.md
24
```
扣除頭部「## 紀錄格式」段落內的 1 筆空 `task_id: ""` 範例 → **23 筆**真實 audit。

| 計數 | 本 PR 推送前 | 本 PR 後 |
|------|:-:|:-:|
| audit entries | 18 | 23（+A01/W01/N3/N4/N1）|
| outputs/drafts/ files | 12 | 17（同上 5 份草稿）|
| outputs/reports/ files | 2 | 2 |
| Decision Log entries | 6 | 6 |

> A01 §1.1 原文「Audit Log 共 17 筆任務」也偏少 1 筆 — 漏算了某筆，已隨修正一併校正為「本 PR 前 18 筆」。

---

## 2. 修正清單

| 檔案 | 段落 | 動作 |
|------|------|------|
| `outputs/drafts/2026-05-09_v3_extraction_plan.md` | §1.1 | 移除「README 文案稱『30+』」誤歸因，改為「plan §Context 與 task card context 欄位的『30+』是 plan snapshot」+ 列出本 PR 前後實計 |
| `outputs/drafts/2026-05-09_v3_extraction_plan.md` | §10 待驗證表 | 「README 寫 30+，實 17」→「plan §Context 寫 30+；非 README」+ 標 ✅ 已解 |
| `outputs/drafts/2026-05-09_methodology_outline.md` | §1.4 推薦理由 | 「17 筆 audit」→「18+ 筆 audit」 |
| `outputs/drafts/2026-05-09_methodology_outline.md` | 第 11 章標題 | 「從 17 筆」→「從 20+ 筆」 |
| `outputs/drafts/2026-05-09_methodology_outline.md` | §9 待驗證表 | 同 §10，註記為已解 + 點明 README 並無此字 |
| `outputs/drafts/2026-05-09_n01_plan-alignment.md` | §7.2 #2 | 改寫整段：N2 不是修 README，是修 A01/W01/N1 的錯誤歸因 |

**不修**（視為歷史 snapshot）：
- `memory/active_projects/agent-harness/plans/ai-bubbly-mountain.md`（plan 是固定時點的研判報告）
- `tasks/2026-05-09_harness-v3-governance-extraction.yaml` 的 context 欄位（卡片建立時的引用）
- `tasks/2026-05-09_harness-methodology-outline.yaml` 的 context 欄位 + DoD 中「30+ audit log」（DoD 條件，已歸檔）

---

## 3. 計數規則（建立日後標準）

| 文件類別 | 計數性質 | 是否隨時間更新 |
|---------|---------|:-:|
| Plan / 研判報告（`memory/.../plans/`、`outputs/reports/`）| 撰寫時點 snapshot | ❌ 不更新 |
| Task Card 的 `context` 欄位 | 建立時點 snapshot | ❌ 不更新 |
| Task Card 的 `definition_of_done` | 條件聲明 | ❌ 不更新（DoD 一旦定，就不改）|
| Draft / 對齊報告（含本卡）| 當下事實 | ✅ 更新；引用 audit 計數時要標日期或 PR# |
| README / CLAUDE.md / system/* | 規範文件 | ✅ 更新；但目前都不寫具體計數 |
| AUDIT_LOG.md | append-only 事實 | ✅ 永遠是當下真相 |

**規則簡記**：snapshot 文件不改、事實文件即時更新、規範文件不寫計數。

---

## 4. 為什麼會出錯（root cause）

A01 執行時：
- Plan 不可讀 → 我用 `grep -rn "30+" --include="*.md" --include="*.yaml"` 找來源
- 第一個有「30+」字樣的檔案出現在 `outputs/drafts/`（因為 audit log 草稿曾複製貼上）
- 我**腦補**「README 是規範文件 → 規範文件可能寫」就寫進 §1.1
- 沒在當下做反向驗證（直接 `grep "30+" README.md`）

**對應失敗模式**：SPEC-04「不知道何時停止」+ VAL-03「看到格式正確就當內容正確」。
具體是：歸因推論未交叉驗證；應該寫入草稿前 grep 一次。

**緩解**（給未來自己）：草稿引用「某某文件寫某某話」時，必須附 grep 結果或檔名:行號。

---

## 5. DoD 驗收

| # | DoD | 狀態 | 證據 |
|---|-----|:-:|------|
| 1 | A01 §1.1 修正錯誤歸因 | ✅ | 改為 plan §Context + task card context 欄位 |
| 2 | A01 §1.1 更新實際計數 | ✅ | 18 / 17 / 2 / 6 列出 |
| 3 | W01 §9 待驗證表修正 | ✅ | 改為 plan §Context；標已解 |
| 4 | N1 §7.2 對 N2 描述更新 | ✅ | 整段重寫，移除「修 README」誤導 |
| 5 | 確認 README 確實無此字樣 | ✅ | §1.1 grep 證明 |
| 6 | 計數規則寫下 | ✅ | §3 表 + 簡記 |

6/6 通過。

## 6. 副產品：失敗模式紀錄

把這次 root cause（草稿引用未交叉驗證）寫成 retro 候補項。**不開新 task**，留待下一次 retro 時統合處理 — 對應 plan §3.7 的「結構性天花板」議題（Claude 自我審查的可靠性問題）。
