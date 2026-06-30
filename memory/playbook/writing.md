# Writing Playbook

程序記憶：writing skill 的可重用啟發與踩過的坑。格式見 `PLAYBOOK_ENTRY_TEMPLATE.md`。

<!-- ENTRY id=PB-writing-001 skill=writing tags=draft-first,output -->
## 對外內容一律先到 drafts/
Email、提案、發文、正式報告先寫 outputs/drafts/，等人工確認才晉升 reports/。
晉升前過 scripts/output_scan.py 掃機密/個資。
來源：CLAUDE.md 硬規則 2 / system/SAFETY_POLICY.md

<!-- ENTRY id=PB-writing-002 skill=writing tags=cost,token-budget -->
## writing 實測 token 超估最兇，預留 buffer
writing 實測平均約為原預估 2 倍（校準係數 2.00）；建 Task Card 時把
max_tool_calls/max_retries 上調一檔。輸出長度浮動大時尤其留意。
來源：system/COST_POLICY.md 校準係數
