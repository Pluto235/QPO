# Work Log

## 2026-05-13

- Synced the IHEP WCDA merged light curves to local processed data:
  `LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv` and
  `LHAASO-WCDA_Mkn421_2025-03-29_2026-03-29_day.csv`.
- Added a v1 periodicity pipeline for WCDA daily, WCDA weekly, and Fermi weekly only; Fermi daily is intentionally deferred because no ready daily Fermi product is currently present.
- Generated LHAASO-axis aligned CSVs under `data/processed/aligned/`, keeping missing Fermi weekly bins as `NaN`.
- Ran CWT and WWZ without simulation-based significance analysis and saved `.npz` arrays, PNG quick-look plots, and `periodicity_v1_summary.csv` under `data/processed/periodicity/`.

## 2026-04-15

- Reorganized the repository into `data/`, `src/`, `notebooks/`, `work/`, and `archive/`.
- Moved Fermi raw files to `data/raw/fermi/`, WCDA raw CSV to `data/raw/wcda/`, and WCDA simulation HDF5 files to `data/simulations/wcda/`.
- Moved the main monthly fermipy product directory to `data/processed/fermi_month/` and the weekly Fermi CSV product to `data/processed/fermi_week/`.
- Moved active notebooks into `notebooks/` and archived older workspace READMEs and legacy method material.
- Archived `DELightcurveSimulation/`, standalone `DELCgen.py`, old Fermi root-level outputs, the old workspace READMEs, `remind.md`, and the empty `work/prompt.txt`.
- Relocated the WCDA simulation script to `src/simulation/` and the Fermi monthly runner to `src/pipeline/`.
- Added compatibility wrappers under `mkn421_fermi/` and `mkn421_lhaaso/` so old commands still resolve to the new locations.
- Archived the root-level compatibility directories under `archive/compat/` and made `src/` the only documented entry-point location.
- Updated script defaults and notebook path targets to use the new `data/` and `src/` layout.
