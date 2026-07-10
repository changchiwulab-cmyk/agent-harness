#!/usr/bin/env python3
"""Stop hook：收尾漂移檢查（**fail-open，永遠 exit 0，不修改任何檔案**）。

在主 agent 結束回應時，提醒衍生檔案是否漂移（AUDIT_LOG / frontend data.json）
與 spec 一致性。只警告、不阻斷、不寫檔；clean 時保持安靜。

呈現方式：依 Claude Code hooks 規範，Stop hook 的純 stdout 只進 debug log、不會
顯示給使用者；故以 JSON 的 `systemMessage` 欄位輸出，才能把非阻斷提醒呈現出來。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

CHECKS = [
    (["ruby", "scripts/check_spec_consistency.rb"], "spec consistency"),
    (["python3", "scripts/generate_audit_log.py", "--check"], "audit log"),
    (["python3", "scripts/generate_frontend_manifest.py", "--check"], "frontend data.json"),
]


def run_checks(root: Path) -> list[str]:
    warnings = []
    for cmd, label in CHECKS:
        try:
            r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                out = (r.stdout + r.stderr).strip().splitlines()
                warnings.append(f"[{label}] 漂移/未通過：{out[-1] if out else ''}")
        except Exception:
            continue  # fail-open：缺 ruby / 逾時等一律跳過
    return warnings


def format_message(warnings: list[str]) -> str:
    """把漂移警告組成 Stop hook 的 JSON 輸出（systemMessage）；clean 時回傳空字串。"""
    if not warnings:
        return ""
    body = "\n".join(f"  - {w}" for w in warnings)
    msg = (
        "⚠️ Stop hook 漂移提醒（fail-open，不阻斷）：\n"
        f"{body}\n"
        "  → 重新產生：python3 scripts/generate_audit_log.py && "
        "python3 scripts/generate_frontend_manifest.py"
    )
    return json.dumps({"systemMessage": msg}, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args, _ = parser.parse_known_args(argv)
    try:
        out = format_message(run_checks(args.root))
        if out:
            print(out)
    except Exception:
        pass
    return 0  # 永遠 exit 0


if __name__ == "__main__":
    sys.exit(main())
