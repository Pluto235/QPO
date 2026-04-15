# Repository Guidelines

## Project Structure & Module Organization
This repository is organized around two analysis workspaces. `mkn421_fermi/` contains the Fermi-LAT pipeline (`run.py`, `config.yaml`), raw event data in `data/`, generated `fermipy` products in `mkn421/`, and the bundled `emmanoulopoulos/` simulation package. `mkn421_lhaaso/` contains the joint Fermi-WCDA notebooks, CSV/LC inputs, and simulation scripts under `simulations/`. Historical or exploratory material lives in `archive/`; keep new work out of that tree unless you are intentionally archiving it. Use `work/` for scratch outputs only.

## Build, Test, and Development Commands
There is no single top-level build system; run the relevant entrypoint directly.

- `python mkn421_fermi/run.py`: runs the Fermi-LAT setup, ROI fit, and monthly light-curve generation.
- `python mkn421_lhaaso/simulations/generate_wcda_weekly_sims.py --output mkn421_lhaaso/simulations/wcda_weekly_sims_full.h5 --nsim 10000 --ncores 48 --chunk 256 --overwrite`: generates WCDA weekly Emmanoulopoulos simulations.
- `pytest mkn421_fermi/emmanoulopoulos/emmanoulopoulos/test`: runs the packaged simulation tests.
- `jupyter notebook`: opens the notebook workflow used by `mkn421_fermi/mkn421.ipynb` and `mkn421_lhaaso/mkn421_lhaaso.ipynb`.

## Coding Style & Naming Conventions
Python code follows existing PEP 8-style conventions: 4-space indentation, `snake_case` for functions and variables, `UPPER_CASE` for module constants such as `BASE_DIR`, and short module docstrings for CLI scripts. Keep new scripts notebook-adjacent and name them for the dataset or task, for example `generate_wcda_weekly_sims.py`. Preserve generated `fermipy` output directories and avoid broad renames of reproducibility artifacts.

## Testing Guidelines
Automated tests currently exist only for the vendored `emmanoulopoulos` package and use `pytest`. Add new tests under `mkn421_fermi/emmanoulopoulos/emmanoulopoulos/test/` with names like `test_LC.py` or `test_feature.py`. For notebook or pipeline changes, include a short manual validation note in the PR describing the command run, input files used, and whether plots or HDF5/FITS outputs were regenerated.

## Commit & Pull Request Guidelines
Current history uses short, imperative commit subjects, for example `add method.ipynb`. Follow that pattern and keep subjects focused on one change. PRs should state which workspace is affected (`mkn421_fermi` or `mkn421_lhaaso`), list reproduced commands, mention any large generated artifacts, and attach screenshots when notebook plots materially change.
