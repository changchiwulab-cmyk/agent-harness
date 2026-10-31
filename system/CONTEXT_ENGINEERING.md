# Context Engineering — 上下文工程紀律（G-C）

> 本檔只寫 Claude Code 原生**沒**做、需要本 harness 自己守的紀律。
> 組裝順序與執行期載入集以 `CLAUDE.md` 為唯一事實來源；路徑引用／先查 repo 再 web search 見 `system/GLOBAL_RULES.md`。
> （20261031-P02：原「原生分工表」「組裝順序」「JIT 檢索」三段與 CLAUDE.md／GLOBAL_RULES 重複且載入集互相矛盾，已移除。）

## 一、結構化工作筆記（scratchpad）— 讓 memory/ 真正運作

過去 `memory/` 幾乎沒運作，因為唯一寫入管道是「長期記憶（需人工確認）」，門檻過高，
導致**任務內的中間思考無處可放**，每次都靠對話歷史硬扛。補上**任務範圍**的工作筆記層：

| 層 | 位置 | 生命週期 | 權限 |
|----|------|---------|------|
| 工作筆記 scratchpad | `outputs/drafts/<task_id>-scratchpad.md` | 任務內；完成後可丟棄或併入產出 | **allow**（write_drafts） |
| 跨 session 接續點 | `state/last_checkpoint.yaml`（G-D） | 跨 session；任務 done 後失效 | allow（write_logs 同級） |
| 長期記憶 | `memory/active_projects/<project>/` | 永久；**需人工確認** | ask |

**scratchpad 慣例**：
- 用途：把長對話中「值得保留但還不是產出」的中間結論寫進 scratchpad，從 context 卸載，
  之後 JIT 讀回（業界稱 structured note-taking / agentic memory）。
- 內容：待辦、已確認的中間結論、暫存路徑引用、下一步。**不存**敏感資料（同 memory 禁則）。
- 不違反 `deny: auto_write_memory`：scratchpad 是任務範圍暫存草稿，**不是**長期知識；
  要變長期記憶仍須經 `memory/` 的人工確認流程。

## 二、子任務 context 隔離

- 當一個子任務的 context 與主線**明顯不同**（如大量原始資料整理），用獨立 scratchpad 隔離，
  整理完只把**結論**帶回主線，原始材料留在 scratchpad/路徑引用。
- 需要真正的 context 隔離時，用 `.claude/agents/` 的原生子代理（一卡一 skill）；**不**做開放式 multi-agent 編排。

## 自我檢查（長任務中途與收尾）

- [ ] context 是否塞了用不到的全文？（應改路徑引用）
- [ ] 中間結論是否已卸載到 scratchpad，而非全靠對話歷史？
- [ ] 跨 session 前是否已更新 `state/last_checkpoint.yaml`（G-D）？
- [ ] `check_context_budget.rb` 仍綠？
