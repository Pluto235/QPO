"""Shared path helpers for the QPO project."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SIMULATION_DATA_DIR = DATA_DIR / "simulations"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
WORK_DIR = PROJECT_ROOT / "work"
ARCHIVE_DIR = PROJECT_ROOT / "archive"

FERMI_RAW_DIR = RAW_DATA_DIR / "fermi"
FERMI_MKN501_RAW_DIR = RAW_DATA_DIR / "fermi_mkn501"
FERMI_WCDA_RAW_DIR = RAW_DATA_DIR / "fermi_wcda_20260818"
WCDA_RAW_DIR = RAW_DATA_DIR / "wcda"
FERMI_MONTH_DIR = PROCESSED_DATA_DIR / "fermi_month" / "mkn421"
FERMI_WEEK_DIR = PROCESSED_DATA_DIR / "fermi_week"
FERMI_WCDA_PROCESSED_DIR = PROCESSED_DATA_DIR / "fermi_wcda_20260818"
ALIGNED_DIR = PROCESSED_DATA_DIR / "aligned"
PERIODICITY_DIR = PROCESSED_DATA_DIR / "periodicity"
FERMI_WCDA_ALIGNED_DIR = ALIGNED_DIR / "fermi_wcda_20260818"
FERMI_WCDA_PERIODICITY_DIR = PERIODICITY_DIR / "fermi_wcda_20260818"
MULTIWAVELENGTH_DIR = PROCESSED_DATA_DIR / "multiwavelength"
WCDA_DAY_DIR = PROCESSED_DATA_DIR / "wcda_day"
WCDA_WEEK_DIR = PROCESSED_DATA_DIR / "wcda_week"
WCDA_2DAY_DIR = PROCESSED_DATA_DIR / "wcda_2day"
WCDA_8DAY_DIR = PROCESSED_DATA_DIR / "wcda_8day"
WCDA_SIM_DIR = SIMULATION_DATA_DIR / "wcda"
EMMANOULOPOULOS_DIR = PROJECT_ROOT / "src" / "methods" / "emmanoulopoulos"
OFFICIAL_QPO_DIR = PROCESSED_DATA_DIR / "official_qpo"
OFFICIAL_QPO_MANIFEST_DIR = OFFICIAL_QPO_DIR / "manifests"
OFFICIAL_QPO_FIXTURE_DIR = OFFICIAL_QPO_DIR / "fixtures"


def ensure_dir(path: Path) -> Path:
    """Create a directory if it does not exist and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path
