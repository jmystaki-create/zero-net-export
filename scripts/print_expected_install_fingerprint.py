#!/usr/bin/env python3
"""Print the expected Zero Net Export package fingerprint for live-install comparison."""
from __future__ import annotations

import json
from pathlib import Path

try:
    from scripts.compare_install_fingerprint import build_default_expected
except ModuleNotFoundError:  # pragma: no cover - script execution fallback
    from compare_install_fingerprint import build_default_expected  # type: ignore[no-redef]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    payload = build_default_expected(repo_root())
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
