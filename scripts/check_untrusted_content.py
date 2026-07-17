#!/usr/bin/env python3
"""Input-guardrail detector (G-A enforcement point).

system/INPUT_GUARDRAILS.md states the rule "retrieved/external content is data,
not instructions". This module makes that rule *checkable* rather than prose:

1. ``detect_injection(text)`` — flags injection-style directive phrases that may
   appear inside untrusted (web/external/tool) content, e.g. "ignore previous
   instructions", "忽略前述指令", "reveal the system prompt".
2. ``is_quarantined(text)`` — true if the text marks untrusted content with the
   ``[未受信任來源]`` label mandated by INPUT_GUARDRAILS.md.
3. ``audit_output(text)`` — combines the two: untrusted content that carries
   injection directives MUST be quarantined; returns the unquarantined hits.

CLI:
    check_untrusted_content.py <file>...   # lint：有未隔離命中 exit 1，乾淨 0，無參數 2
    check_untrusted_content.py --stop-hook # Stop hook advisory：掃 session 新增/修改的
                                           # outputs/ 檔，命中→stderr 警告＋ledger 記錄
                                           # ＋systemMessage，永遠 exit 0、不 block
                                           #（20260716-P13；升級 blocking 前先觀察誤報率）
    check_untrusted_content.py --stats     # 彙整 ledger 命中數／verdict 標注進度

Stop hook 呈現方式比照 session_stop_checks.py：純 stdout 只進 debug log，
使用者可見警告走 JSON `systemMessage`；DoD 鎖定的機器可測面是 stderr。
Ledger（logs/untrusted_content_hits.jsonl，tracked——ephemeral session 下
gitignored 檔活不過 container，兩週誤報統計會斷）以 (file, rule, sha) 去重，
verdict 欄位留待人工標注 tp/fp。整條 --stop-hook 路徑 fail-open：advisory
不是安全邊界，出口硬防線仍在 permissions_guard.py 的 deny-by-default egress。

Deliberately a small phrase list, not an ML classifier — for a single-person
harness the deny-by-default egress (permissions_guard.py) is the hard stop;
this layer is a discipline lint, consistent with INPUT_GUARDRAILS "不做什麼".
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
LEDGER_RELPATH = "logs/untrusted_content_hits.jsonl"

# Directive phrases that should never be obeyed when they arrive via untrusted
# content. Kept lowercase; matching is case-insensitive. Bilingual (zh-Hant/en).
INJECTION_PATTERNS = [
    r"ignore (all )?(the )?(previous|prior|above|preceding) instructions",
    r"disregard (the )?(previous|prior|above|system) (instructions|prompt)",
    r"忽略(前述|上述|先前|以上)(所有)?指令",
    r"忽視(前述|上述|先前)(所有)?指令",
    r"(reveal|print|show|output|leak)( me)? (the |your )?system prompt",
    r"(洩漏|顯示|輸出|印出)(你的)?系統(提示|prompt)",
    r"(change|switch|update|forget) your (role|persona|identity|instructions)",
    r"(改變|切換|忘記)(你的)?(角色|身分|設定)",
    r"you are now (a |an )?",
    r"從現在起你(是|要扮演)",
    r"(send|email|post|publish|delete|transfer|pay)\b.*\b(immediately|now|to)",
]

QUARANTINE_MARKER = "[未受信任來源]"

_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_injection(text: str) -> list[str]:
    """Return the injection-directive substrings found in ``text`` (deduped)."""
    hits: list[str] = []
    for pat in _COMPILED:
        for m in pat.finditer(text or ""):
            frag = m.group(0).strip()
            if frag and frag not in hits:
                hits.append(frag)
    return hits


def is_quarantined(text: str) -> bool:
    """True if the text marks untrusted content with the mandated label."""
    return QUARANTINE_MARKER in (text or "")


def split_blocks(text: str) -> list[str]:
    """Split into blank-line-separated blocks (paragraphs/excerpts)."""
    return [b for b in re.split(r"\n\s*\n", text or "") if b.strip()]


def audit_output(text: str) -> list[str]:
    """Injection hits that appear in a block lacking a quarantine marker.

    The marker is tied to the *block* (blank-line-separated excerpt), not the
    whole document: echoing injection text for analysis is fine only when that
    same excerpt is marked ``[未受信任來源]``. This prevents one marker anywhere
    from whitelisting a separate unmarked injection elsewhere in a multi-excerpt
    report.
    """
    unquarantined: list[str] = []
    for block in split_blocks(text):
        hits = detect_injection(block)
        if hits and not is_quarantined(block):
            for h in hits:
                if h not in unquarantined:
                    unquarantined.append(h)
    return unquarantined


def audit_output_detailed(text: str) -> list[dict]:
    """audit_output 的規則層版本：回傳 [{"rule": pattern 原文, "fragment": 命中片段}]。

    ledger 需要「命中哪條規則」才能統計誤報率（DoD 3）；detect_injection 只回
    片段，故另開此函式，區塊級隔離語意與 audit_output 一致。
    """
    findings: list[dict] = []
    for block in split_blocks(text):
        if is_quarantined(block):
            continue
        for pat in _COMPILED:
            for m in pat.finditer(block):
                frag = m.group(0).strip()
                rec = {"rule": pat.pattern, "fragment": frag}
                if frag and rec not in findings:
                    findings.append(rec)
    return findings


def changed_output_files(root: Path) -> list[str]:
    """session 新增/修改的 outputs/ 檔（repo 相對路徑）。

    Stop payload 沒有改動檔清單，以 git 推導：工作樹 dirty（含 untracked）
    ∪ 相對 origin/main merge-base 的已 commit 差異（checkpoint commit 後檔案
    不再 dirty，缺這條會漏掃）。任何 git 步驟失敗（無 git、非 repo、逾時、
    無 origin/main）→ 靜默跳過該來源，fail-open。
    """
    found: list[str] = []

    def _add(rel: str) -> None:
        rel = rel.strip()
        if rel and rel not in found and (root / rel).is_file():
            found.append(rel)

    def _git(args: list[str]) -> list[str]:
        """NUL 分隔記錄（-z：路徑原樣輸出，非 ASCII 檔名不做 C-quoting）。"""
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=10)
        if r.returncode != 0:
            return []
        return [p for p in r.stdout.decode("utf-8", "replace").split("\0") if p]

    try:
        skip_next = False
        for rec in _git(["status", "--porcelain", "-z", "--untracked-files=all", "--", "outputs/"]):
            if skip_next:  # rename/copy 的原路徑（獨立 NUL 記錄），不掃
                skip_next = False
                continue
            status, path = rec[:2], rec[3:]
            if status and status[0] in "RC":  # -z 格式新路徑在前、原路徑為下一筆
                skip_next = True
            _add(path)
    except Exception:
        pass
    try:
        base = "".join(_git(["merge-base", "HEAD", "origin/main"])).strip()
        if base:
            for rec in _git(
                ["diff", "--name-only", "-z", "--diff-filter=ACMR", f"{base}..HEAD", "--", "outputs/"]
            ):
                _add(rec)
    except Exception:
        pass
    return found


def _load_seen(ledger: Path) -> set[tuple[str, str, str]]:
    """ledger 既有紀錄的去重鍵 (file, rule, sha)；壞行跳過，缺檔回空集合。"""
    seen: set[tuple[str, str, str]] = set()
    try:
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict):
                seen.add((rec.get("file", ""), rec.get("rule", ""), rec.get("sha", "")))
    except OSError:
        pass
    return seen


def _read_hook_payload() -> dict:
    """Stop hook 的 stdin JSON payload；tty/壞 JSON/非 mapping 一律 fail-open {}。"""
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _active_task_id(root: Path) -> str:
    """active task_id（state/active_task.yaml）；idle/缺檔/缺 PyYAML → 空字串。"""
    try:
        import active_task  # 同 scripts/ 目錄

        return active_task.active_task_id(root)
    except Exception:
        return ""


def run_stop_hook(
    root: Path | None = None,
    ledger: Path | None = None,
    files: list[str] | None = None,
) -> int:
    """Stop hook advisory 掃描（**fail-open，永遠 return 0，不阻斷**）。

    命中未隔離注入樣式：stderr 每筆一行（檔案路徑＋命中規則）、append ledger、
    stdout 輸出 systemMessage；乾淨時完全安靜。``files`` 供測試注入檔案清單
    （repo 相對路徑），省略時以 git 推導。
    """
    try:
        root = (root or DEFAULT_ROOT).resolve()
        ledger = ledger if ledger is not None else root / LEDGER_RELPATH
        session_id = str(_read_hook_payload().get("session_id", "") or "")
        rel_files = changed_output_files(root) if files is None else files
        if not rel_files:
            return 0
        seen = _load_seen(ledger)
        task_id = _active_task_id(root)
        records: list[dict] = []
        for rel in rel_files:
            try:
                text = (root / rel).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            findings = audit_output_detailed(text)
            if not findings:
                continue
            sha = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:12]
            for finding in findings:
                key = (rel, finding["rule"], sha)
                if key in seen:
                    continue
                seen.add(key)
                records.append(
                    {
                        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "file": rel,
                        "rule": finding["rule"],
                        "fragment": finding["fragment"],
                        "sha": sha,
                        "task_id": task_id,
                        "session_id": session_id,
                        "verdict": "",
                    }
                )
        if records:
            ledger.parent.mkdir(parents=True, exist_ok=True)
            with ledger.open("a", encoding="utf-8") as fh:
                for rec in records:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            lines = [f"{r['file']} 命中規則 {r['rule']!r}" for r in records]
            for line in lines:
                print(
                    f"[untrusted-content] {line}（advisory，不阻斷；已記錄 {LEDGER_RELPATH}）",
                    file=sys.stderr,
                )
            body = "\n".join(f"  - {line}" for line in lines)
            msg = (
                "⚠️ 注入樣式 advisory（不阻斷）：outputs/ 產出含未隔離的注入指令樣式\n"
                f"{body}\n"
                f"  → 正當引用請為該區塊加 {QUARANTINE_MARKER} 標記；"
                f"誤報請在 {LEDGER_RELPATH} 標注 verdict: fp"
            )
            print(json.dumps({"systemMessage": msg}, ensure_ascii=False))
    except Exception:
        pass  # fail-open：advisory 掃描不得干擾 Stop
    return 0


def run_stats(ledger: Path | None = None) -> int:
    """彙整 ledger：總命中、按 rule／file 分組、verdict 標注進度（DoD 3）。"""
    ledger = ledger if ledger is not None else DEFAULT_ROOT / LEDGER_RELPATH
    records: list[dict] = []
    try:
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict):
                records.append(rec)
    except OSError:
        pass
    print(f"total hits: {len(records)}")
    if not records:
        return 0
    for label, key in (("by rule:", "rule"), ("by file:", "file")):
        print(label)
        for value, n in Counter(r.get(key, "") for r in records).most_common():
            print(f"  {n:3d}  {value}")
    print("verdicts:")
    for verdict, n in sorted(
        Counter(r.get("verdict") or "unlabeled" for r in records).items()
    ):
        print(f"  {verdict}: {n}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="check_untrusted_content.py",
        description="G-A input-guardrail detector（lint / Stop hook advisory / stats）",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--stop-hook", action="store_true", dest="stop_hook")
    mode.add_argument("--stats", action="store_true")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv[1:])

    if args.stop_hook:
        return run_stop_hook()
    if args.stats:
        return run_stats()

    files = args.files
    if not files:
        print("usage: check_untrusted_content.py <file>...", file=sys.stderr)
        return 2
    failures = []
    for f in files:
        text = Path(f).read_text(encoding="utf-8")
        unquarantined = audit_output(text)
        if unquarantined:
            failures.append((f, unquarantined))
    if failures:
        print("FAILED: unquarantined injection directives found:")
        for f, hits in failures:
            print(f"- {f}: {hits} (mark untrusted content with {QUARANTINE_MARKER!r})")
        return 1
    print("OK: no unquarantined injection directives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
