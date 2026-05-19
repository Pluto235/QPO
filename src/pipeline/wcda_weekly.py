#!/usr/bin/env python3
"""Pipeline entry point for WCDA weekly simulations."""

import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from simulation.generate_wcda_weekly_sims import main


if __name__ == "__main__":
    main()
