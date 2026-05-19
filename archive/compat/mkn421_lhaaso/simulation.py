#!/usr/bin/env python3
"""Archived compatibility entry point for WCDA simulation generation.

This file is kept under ``archive/compat/`` for historical reference.
Active usage should run ``src/pipeline/wcda_weekly.py`` directly.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline.wcda_weekly import main


if __name__ == "__main__":
    main()
