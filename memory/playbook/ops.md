# Ops Playbook

程序記憶：ops skill 的可重用啟發與踩過的坑。格式見 `PLAYBOOK_ENTRY_TEMPLATE.md`。

<!-- ENTRY id=PB-ops-001 skill=ops tags=archive,git-mv,history -->
## 封存/搬移一律用 git mv 並走 Task Card
封存專案、搬檔不要直接刪+建，用 git mv 保留歷史，並透過 Task Card 執行以進 audit log。
確定終止的專案也不刪除，標註原因保留。
來源：memory/README.md / Task 20260417-O02

<!-- ENTRY id=PB-ops-002 skill=ops tags=checkpoint,determinism -->
## 產生型檔案要可重生且確定性
data.json、INDEX.yaml、AUDIT_LOG.md 等衍生檔由 script 產生，輸出須排序、確定性，
讓 CI 的 --check 能偵測漂移。改完資料記得重生並提交。
來源：scripts/generate_frontend_manifest.py / build_memory_index.py
