#!/usr/bin/env python3
"""PreToolUse hook for MCP tools (matcher: ``mcp__.*``) — 20261031-P01.

permissions_guard.py 只看 Bash 指令；MCP 工具（GitHub merge／push、Drive share／trash、
外部訊息等）完全不經過 shell，原本繞過整條 deny 防線。本 guard 依工具名動詞分三級：

- deny  ：刪除／外發／發布／合併／分享／直推遠端檔案／金流 → exit 2 阻擋
- ask   ：其他寫入型動作（建 PR、留言、更新 issue、寫文件…）→ 交人工確認
- allow ：唯讀動詞（get/list/search/read/…）

設計取捨：
- 未知或無法解析的 MCP 工具 → ask（fail-closed 到人工，不放行也不 brick）。
- 壞 stdin／壞 JSON／內部例外 → ask，不 crash-open（exit 1 在 hook 語意是 non-blocking）。
- stdlib only：hook 不得因缺 PyYAML 而失效。
- 分類以工具名 token 判讀（``mcp__<server>__<tool>`` 的 <tool> 以 ``_``/``-`` 切分），
  唯讀動詞開頭 → allow，其次 deny token，其餘 ask；EXACT_OVERRIDES 處理動詞誤判（如 disable_pr_auto_merge）。

Output：
- allow → exit 0，無輸出
- ask   → exit 0，stdout ``hookSpecificOutput.permissionDecision = "ask"``
- deny  → exit 2，stdout ``{"decision": "block", ...}``＋stderr 原因（與其他 guard 一致）
"""

from __future__ import annotations

import json
import re
import sys

DENY_TOKENS = frozenset({
    # 刪除
    "delete", "trash", "remove", "destroy", "purge", "erase",
    # 對外發送／發布
    "send", "publish", "post", "tweet", "invite", "share",
    # 正式資料／遠端歷史變更
    "merge", "push", "fork", "transfer",
    # 金流
    "pay", "payment", "charge", "refund", "checkout",
})

# 不經分支直接改遠端 repo 檔案 = 繞過本地 checkpoint 與 review
DENY_EXACT_TOOLS = frozenset({"create_or_update_file"})

READ_TOKENS = frozenset({
    "get", "list", "search", "read", "query", "fetch", "download", "view",
    "describe", "check", "guide", "export", "find", "lookup", "status",
})

# (server, tool) 精確覆寫：動詞誤判或內部協作工具
EXACT_OVERRIDES: dict[tuple[str, str], str] = {
    # 降低自動合併風險的動作不該被當成 merge 擋下
    ("github", "disable_pr_auto_merge"): "ask",
    # 對使用者自己的 Claude session 傳訊／排程，非外部發送
    ("claude-code-remote", "send_message"): "ask",
    ("claude-code-remote", "send_later"): "ask",
}

_NAME_RE = re.compile(r"^mcp__(?P<server>.+?)__(?P<tool>.+)$")


def classify(tool_name: str) -> tuple[str, str]:
    """Return (decision, reason); decision ∈ {allow, ask, deny}."""
    m = _NAME_RE.match(tool_name or "")
    if not m:
        return "ask", f"無法解析的 MCP 工具名「{tool_name}」— 交人工確認"
    server, tool = m.group("server"), m.group("tool")
    override = EXACT_OVERRIDES.get((server, tool))
    if override:
        return override, f"{tool_name}：精確覆寫為 {override}"
    tokens = [t for t in re.split(r"[_\-]+", tool.lower()) if t]
    if tool.lower() in DENY_EXACT_TOOLS:
        return "deny", f"{tool_name}：直接改寫遠端正式資料（PERMISSIONS deny: modify_production_data）"
    # 唯讀動詞開頭優先（read_email／get_share_link 不該因受詞誤擋）
    if tokens and tokens[0] in READ_TOKENS:
        return "allow", f"{tool_name}：唯讀"
    hit = next((t for t in tokens if t in DENY_TOKENS), None)
    if hit:
        return "deny", (
            f"{tool_name}：動詞「{hit}」屬刪除／外發／發布／合併／金流"
            "（PERMISSIONS deny；硬規則 2：對外動作只產出草稿）"
        )
    return "ask", f"{tool_name}：寫入型或未分類的 MCP 動作 — 交人工確認"


def _emit_ask(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"mcp_guard: {reason}",
        }
    }, ensure_ascii=False))
    return 0


def _emit_block(reason: str) -> int:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    print(f"BLOCKED by mcp_guard: {reason}", file=sys.stderr)
    return 2


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return _emit_ask("hook 收到空輸入，無法判讀工具 — 交人工確認")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        return _emit_ask(f"hook 輸入不是合法 JSON（{e}）— 交人工確認")
    if not isinstance(payload, dict):
        return _emit_ask("hook 輸入不是 JSON 物件 — 交人工確認")
    tool_name = payload.get("tool_name") or payload.get("name") or ""
    decision, reason = classify(tool_name)
    if decision == "deny":
        return _emit_block(reason)
    if decision == "ask":
        return _emit_ask(reason)
    return 0


def run_guarded() -> int:
    try:
        return main()
    except Exception as e:  # noqa: BLE001 — crash 不得 open
        return _emit_ask(f"mcp_guard 內部錯誤（{type(e).__name__}: {e}）— 交人工確認")


if __name__ == "__main__":
    raise SystemExit(run_guarded())
