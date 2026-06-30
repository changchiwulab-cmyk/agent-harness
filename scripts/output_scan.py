#!/usr/bin/env python3
"""Output safety scanner: catch secrets / PII before a draft goes outbound.

The harness ingests untrusted web/file content and emits outbound drafts. This
scanner is the executable half of system/SAFETY_POLICY.md's output rule — run it
before a draft is promoted to outputs/reports/ or sent anywhere (GATE_POLICY
risk_check). It mirrors scripts/permissions_guard.py's deny-pattern style: a
conservative, auditable pattern list, not a sandbox.

Findings are reported as file:line:rule with a *redacted* preview (the secret is
never echoed in full). Exit code is non-zero if anything is found.

Usage:
    output_scan.py outputs/drafts/some-draft.md
    output_scan.py                       # default: scan outputs/drafts + outputs/reports
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = ("outputs/drafts", "outputs/reports")

# Lines containing one of these markers are skipped (intentional examples/fixtures).
ALLOWLIST_MARKERS = ("scan-ignore", "pragma: allowlist secret")

# Matches whose *value* looks like an obvious placeholder are not real secrets.
# Kept deliberately specific: broad words like "test" are excluded because they
# would suppress real secrets sitting on a line that merely mentions them (e.g.
# a run note "tested token: ghp_..."). For intentional examples, use a
# [scan-ignore] marker on the line instead.
PLACEHOLDER_HINTS = (
    "example", "redacted", "placeholder", "dummy", "fake", "changeme",
    "your_", "your-", "xxxx", "<", ">", "...", "abc123",
)


@dataclass(frozen=True)
class SecretRule:
    rule_id: str
    pattern: re.Pattern
    description: str
    luhn: bool = False  # validate the digit run with the Luhn algorithm first


SECRET_RULES: tuple[SecretRule, ...] = (
    SecretRule("private_key", re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
        "private key block"),
    SecretRule("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
               "AWS access key id"),
    SecretRule("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b"),
               "GitHub token"),
    SecretRule("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b"),
               "GitHub fine-grained PAT"),
    SecretRule("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
               "Slack token"),
    SecretRule("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b"),
               "Anthropic API key"),
    SecretRule("openai_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{19,}\b"),
               "OpenAI-style secret key (incl. hyphenated project keys)"),
    SecretRule("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b"),
               "bearer token"),
    # No leading \b: catches keywords embedded after a word char too, e.g.
    # OPENAI_API_KEY=... (the trailing \b still guards against 'secretary=').
    SecretRule("generic_secret", re.compile(
        r"(?i)(?:api[_-]?key|secret|token|passwd|password|access[_-]?key)\b"
        r"\s*[:=]\s*['\"]?(?P<val>[A-Za-z0-9/+_\-]{16,})"),
        "assigned secret/credential"),
    SecretRule("tw_national_id", re.compile(r"\b[A-Z][12]\d{8}\b"),
               "Taiwan national id"),
    SecretRule("credit_card", re.compile(r"\b(?:\d[ -]?){13,19}\b"),
               "credit card number", luhn=True),
)


@dataclass
class Finding:
    path: str
    line: int
    rule_id: str
    description: str
    preview: str


@dataclass
class ScanReport:
    findings: list[Finding] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.findings


def luhn_valid(digits: str) -> bool:
    nums = [int(c) for c in digits if c.isdigit()]
    if not (13 <= len(nums) <= 19):
        return False
    total = 0
    for i, n in enumerate(reversed(nums)):
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _looks_placeholder(value: str) -> bool:
    # Only the matched value is inspected — never the surrounding line — so an
    # unrelated word elsewhere on the line cannot suppress a real secret.
    low = value.lower()
    return any(h in low for h in PLACEHOLDER_HINTS)


def _redact(text: str) -> str:
    text = text.strip()
    if len(text) <= 8:
        return text[0] + "***" if text else "***"
    return f"{text[:4]}…{text[-2:]} ({len(text)} chars)"


def scan_text(text: str, path: str = "<text>") -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if any(marker in line for marker in ALLOWLIST_MARKERS):
            continue
        for rule in SECRET_RULES:
            for m in rule.pattern.finditer(line):
                hit = m.group("val") if ("val" in (m.groupdict() or {})) else m.group(0)
                if rule.luhn and not luhn_valid(hit):
                    continue
                if _looks_placeholder(hit):
                    continue
                findings.append(Finding(
                    path=path, line=lineno, rule_id=rule.rule_id,
                    description=rule.description, preview=_redact(hit),
                ))
    return findings


def _iter_files(targets: list[Path]) -> list[Path]:
    files: list[Path] = []
    for t in targets:
        if t.is_dir():
            files.extend(sorted(p for p in t.rglob("*") if p.is_file()))
        elif t.is_file():
            files.append(t)
    return files


def scan_paths(paths: list[str], root: Path = ROOT) -> ScanReport:
    targets = [(root / p if not Path(p).is_absolute() else Path(p)) for p in paths]
    report = ScanReport()
    for f in _iter_files(targets):
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = f.relative_to(root).as_posix() if str(f).startswith(str(root)) else str(f)
        report.findings.extend(scan_text(text, rel))
    return report


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    paths = [a for a in args if not a.startswith("-")] or list(DEFAULT_PATHS)
    report = scan_paths(paths)
    if report.clean:
        print(f"OK: no secrets/PII found in {', '.join(paths)}")
        return 0
    print("FAILED: potential secrets/PII found (redacted):", file=sys.stderr)
    for f in report.findings:
        print(f"- {f.path}:{f.line} [{f.rule_id}] {f.description}: {f.preview}", file=sys.stderr)
    print(
        "\nIf a finding is an intentional example, add '[scan-ignore]' on that line.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
