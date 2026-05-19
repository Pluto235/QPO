# QPO

Mrk 421 blazar QPO analysis workspace with lightweight project structure.

## Scope

- `data/raw/fermi/`: Fermi event files, spacecraft file, and weekly `.lc` input.
- `data/raw/wcda/`: WCDA weekly CSV input.
- `data/processed/fermi_month/`: fermipy monthly products and ROI outputs.
- `data/processed/fermi_week/`: processed weekly Fermi CSV products.
- `data/simulations/wcda/`: WCDA simulation HDF5 outputs.
- `src/pipeline/`: runnable pipeline entry points.
- `src/simulation/`: simulation scripts.
- `src/methods/`: reusable analysis methods and vendored method code.
- `notebooks/`: analysis and validation notebooks.
- `work/`: project overview and running log.
- `archive/`: historical notebooks, legacy outputs, and deprecated material kept for reference.

## Main entry points

- `python src/pipeline/fermi_month.py`
- `python src/pipeline/wcda_weekly.py --output data/simulations/wcda/wcda_weekly_sims_full.h5 --nsim 10000 --ncores 48 --chunk 256 --overwrite`
- `pytest -q src/methods/emmanoulopoulos/emmanoulopoulos/test`

Legacy compatibility directories have been archived under `archive/compat/`.
