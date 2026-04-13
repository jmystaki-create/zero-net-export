#!/usr/bin/env python3
"""Validate that a Home Assistant Zero Net Export install matches the current repo build."""
from __future__ import annotations

from pathlib import Path
import sys

from compare_install_fingerprint import main as compare_main


if __name__ == "__main__":
    raise SystemExit(compare_main())
