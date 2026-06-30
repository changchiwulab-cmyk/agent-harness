# Analysis Playbook

程序記憶：analysis skill 的可重用啟發與踩過的坑。格式見 `PLAYBOOK_ENTRY_TEMPLATE.md`。

<!-- ENTRY id=PB-analysis-001 skill=analysis tags=recommendation,decision -->
## 給建議，不要給選項型錄
決策支援的產出是「推薦哪個 + 為什麼」，不是把所有選項平鋪。
列考量過的替代方案與其取捨，但要明確收斂到一個建議。
來源：skills/analysis/SKILL.md

<!-- ENTRY id=PB-analysis-002 skill=analysis tags=assumptions,risk -->
## 把關鍵假設與風險顯性化
分析結論若依賴假設，要把假設列出並標風險等級；高風險假設不可當事實。
呼應 GLOBAL_RULES：區分已知事實 / 合理推論 / 待驗證 / 高風險假設。
來源：system/GLOBAL_RULES.md 輸出規則
