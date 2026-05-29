#!/usr/bin/env python3
"""Stop hook：收尾漂移檢查（**fail-open，永遠 exit 0，不修改任何檔案**）。

在主 agent 結束回應時，提醒衍生檔案是否漂移（AUDIT_LOG / frontend data.json）
與 spec 一致性。只警告、不阻斷、不寫檔；clean 時保持安靜。

把原本散落在 README「提交前檢查」的 prose 提醒，變成 session 收尾的自動提示。
"""
from __future__ import annotations

import argparse
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args, _ = parser.parse_known_args(argv)
    try:
        warnings = run_checks(args.root)
        if warnings:
            print("⚠️ Stop hook 提醒（fail-open，不阻斷）：")
            for w in warnings:
                print(f"  - {w}")
            print(
                "  → 重新產生：python3 scripts/generate_audit_log.py && "
                "python3 scripts/generate_frontend_manifest.py"
            )
    except Exception:
        pass
    return 0  # 永遠 exit 0


if __name__ == "__main__":
    sys.exit(main())
