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
WCDA_RAW_DIR = RAW_DATA_DIR / "wcda"
FERMI_MONTH_DIR = PROCESSED_DATA_DIR / "fermi_month" / "mkn421"
FERMI_WEEK_DIR = PROCESSED_DATA_DIR / "fermi_week"
ALIGNED_DIR = PROCESSED_DATA_DIR / "aligned"
PERIODICITY_DIR = PROCESSED_DATA_DIR / "periodicity"
MULTIWAVELENGTH_DIR = PROCESSED_DATA_DIR / "multiwavelength"
WCDA_DAY_DIR = PROCESSED_DATA_DIR / "wcda_day"
WCDA_WEEK_DIR = PROCESSED_DATA_DIR / "wcda_week"
WCDA_SIM_DIR = SIMULATION_DATA_DIR / "wcda"
EMMANOULOPOULOS_DIR = PROJECT_ROOT / "src" / "methods" / "emmanoulopoulos"


def ensure_dir(path: Path) -> Path:
    """Create a directory if it does not exist and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path
