#!/usr/bin/env python3
"""Run the Fermi-LAT monthly Mrk 421 pipeline."""

import os
import sys
from pathlib import Path

from fermipy.gtanalysis import GTAnalysis


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.project_paths import FERMI_MONTH_DIR, PROJECT_ROOT


CONFIG_PATH = Path(__file__).resolve().with_name("fermi_month_config.yaml")
ROI_PATH = FERMI_MONTH_DIR / "mkn421_fulltime.fits"
SRC_NAME = "4FGL J1104.4+3812"


def main():
    os.chdir(PROJECT_ROOT)
    FERMI_MONTH_DIR.mkdir(parents=True, exist_ok=True)

    gta = GTAnalysis(str(CONFIG_PATH), logging={"verbosity": 3})
    gta.setup()
    gta.optimize()
    gta.free_sources(distance=3.0)
    gta.fit()
    gta.write_roi(str(ROI_PATH))

    gta = GTAnalysis(str(CONFIG_PATH), logging={"verbosity": 3})
    gta.load_roi(str(ROI_PATH))
    return gta.lightcurve(
        SRC_NAME,
        binsz=30 * 86400,
        free_background=True,
        use_local_ltcube=False,
    )


if __name__ == "__main__":
    main()
