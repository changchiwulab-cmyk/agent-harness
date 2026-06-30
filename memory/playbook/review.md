# Review Playbook

程序記憶：review skill 的可重用啟發與踩過的坑。格式見 `PLAYBOOK_ENTRY_TEMPLATE.md`。

<!-- ENTRY id=PB-review-001 skill=review tags=definition-of-done,completion -->
## 逐條比對 definition_of_done，不要整體打分
完成驗證是逐條 pass/fail，fail 要說明缺什麼，不是給一個籠統「大致 OK」。
可用 scripts/run_evals.py 的量表輔助結構性檢查。
來源：system/GATE_POLICY.yaml completion_check

<!-- ENTRY id=PB-review-002 skill=review tags=stop-condition,failure-drill -->
## 停止條件是正常控制流，不是例外
連續失敗 3 次就停下並寫 error log，不要自行硬修。定期做失敗演練確保路徑沒壞。
來源：memory/episodes/20260529-E002_failure-drill-stop-after-3.yaml / CLAUDE.md 硬規則 3
