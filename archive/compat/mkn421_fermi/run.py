#!/usr/bin/env python3
"""Archived compatibility wrapper for the monthly Fermi pipeline.

This file is kept for historical reference under ``archive/compat/``.
Active usage should call ``src/pipeline/fermi_month.py`` directly.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline.fermi_month import main


if __name__ == "__main__":
    main()
