# Project Guidelines

## Goal

This repository supports blazar QPO analysis for **Mrk 421** and related comparison targets such as **Mrk 501**.

The current priorities are:

- keep the Fermi and WCDA workflows reproducible;
- move reusable logic from notebooks into `src/`;
- preserve a clean separation between raw data access, derived light curves, periodicity products, and reports;
- make it practical to work across the local machine, the ETO compute environment, and the IHEP cluster.

## Repository Role

- This local checkout is the main working branch for the project.
- The Git remote is `git@github.com:Pluto235/QPO.git`.
- Large compute jobs may be launched from the **ETO** server, where this repository also has a clone and Slurm is available.
- LHAASO / WCDA observational data are accessed from the **IHEP** cluster environment.

## File Architecture

```text
QPO/
├─ AGENTS.md
├─ README.md
├─ docs/
├─ data/
│  ├─ raw/
│  │  ├─ fermi/
│  │  └─ wcda/
│  ├─ processed/
│  │  ├─ aligned/
│  │  ├─ fermi_month/
│  │  ├─ fermi_week/
│  │  ├─ periodicity/
│  │  ├─ wcda_day/
│  │  └─ wcda_week/
│  └─ simulations/
│     └─ wcda/
├─ notebooks/
├─ prestation/
├─ reports/
├─ src/
│  ├─ methods/
│  ├─ pipeline/
│  ├─ simulation/
│  └─ utils/
├─ work/
│  ├─ overview.md
│  └─ log.md
└─ archive/
```

## Current Active Pipelines

Current runnable entry points live under `src/pipeline/`.

1. `src/pipeline/fermi_month.py`
   Runs the Fermi monthly workflow via `fermipy` and `src/pipeline/fermi_month_config.yaml`.
   Produces monthly light-curve products under `data/processed/fermi_month/`.
   Requires `$FERMI_DIFFUSE_DIR`.

2. `src/pipeline/wcda_weekly.py`
   Thin entry point for `src/simulation/generate_wcda_weekly_sims.py`.
   Runs WCDA weekly surrogate simulations and writes HDF5 outputs under `data/simulations/wcda/`.

3. `src/pipeline/periodicity_v1.py`
   Builds aligned light curves and runs the current CWT/WWZ periodicity checks.
   Uses WCDA daily, WCDA weekly, and optionally Fermi weekly inputs.
   Writes aligned series under `data/processed/aligned/<source_id>/` and periodicity outputs under `data/processed/periodicity/<source_id>/`.

4. `src/pipeline/weekly_qpo_local_significance.py`
   Evaluates local significance for current WCDA weekly candidate peaks, currently for `mkn421` and `mkn501`.
   Consumes saved periodicity products and writes CSV and figure outputs under `data/processed/periodicity/<source_id>/`.

5. `src/pipeline/reproduce_xgm_poster.py`
   Reproduces the xgm poster WWZ quick-look products for selected Mrk 421 WCDA daily windows.
   Writes outputs under `data/processed/periodicity/xgm_poster_repro/mkn421/`.

6. `src/pipeline/xgm_poster_wwz_significance.py`
   Computes WWZ local significance for the xgm poster reproduction windows.
   Writes summary CSV and figures beside the reproduction outputs.

## Data Layout

- `data/raw/fermi/`: raw Fermi inputs.
- `data/raw/wcda/`: raw WCDA inputs copied or synced from IHEP storage.
- `data/processed/fermi_month/`: processed Fermi monthly products.
- `data/processed/fermi_week/`: processed Fermi weekly products.
- `data/processed/wcda_day/`: processed WCDA daily light curves.
- `data/processed/wcda_week/`: processed WCDA weekly light curves.
- `data/processed/aligned/`: aligned multi-instrument light curves used by periodicity workflows.
- `data/processed/periodicity/`: CWT, WWZ, significance summaries, and related figures.
- `data/simulations/wcda/`: WCDA simulation products.

Use `src/utils/project_paths.py` as the single source of truth for project directories.
Do not hard-code new absolute paths in scripts when a project-relative path helper should be used instead.

## Documentation Layout

- `docs/` stores reference documentation, analysis guides, environment notes, and background material.
- `reports/` stores formal reports, result summaries, and reader-facing exported outputs.
- `work/` stores project-operational notes, handoff material, and running coordination documents.
- `work/log.md` is the lab-style running work log and should be appended after each completed work session using `devlog`.
- `README.md` remains the top-level repository entry point; general explanatory documents should go in `docs/`, not the repository root.
- `prestation/` stores presentation materials such as slides, posters, and talk assets.

## Compute Environments

### Local machine

- Primary place for code editing, notebook work, quick validation, and report generation.
- Treat this checkout as the canonical working tree unless a task clearly belongs on ETO or IHEP.
- On this Mac, run scientific Python / plotting / periodicity scripts with the conda `py310` environment:
  `/Users/luoji/miniconda3/envs/py310/bin/python`.
- Do not rely on the default `python3`, `/Users/luoji/miniconda3/bin/python`, or conda `base` for these workflows; they have been observed to miss core dependencies such as `numpy`, `pandas`, `matplotlib`, `pycwt`, and `libwwz`.
- Example local command:
  `/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/reproduce_xgm_poster.py`.
- If a script fails with `ModuleNotFoundError` for scientific packages on the Mac, first retry with the explicit `py310` interpreter before changing code or installing packages.

### ETO server

- SSH host alias is `ETO` in `~/.ssh/config`.
- Login lands in `/home/server`.
- This server has a clone of the repository and can be used for larger jobs.
- Use ETO when the work needs longer runtime, heavier CPU usage, or Slurm submission.
- Prefer running batch or large periodicity / simulation workloads there instead of overloading the local machine.
- Slurm commands `sbatch` and `squeue` are available.
- Python is available as `/opt/anaconda3/bin/python3`.

### IHEP cluster

- SSH host alias is `ihep` in `~/.ssh/config`.
- Account: `liushijie@lxlogin.ihep.ac.cn`.
- The login environment is the entry point to the IHEP / LHAASO cluster.
- Use IHEP to access LHAASO observational data, including WCDA products used to derive light curves or photon-count series.
- The actual working directory on IHEP is `/home/lhaaso/liushijie`.
- The login-node home under AFS is separate from the main LHAASO working area; avoid treating the login landing directory as the main project storage location.

## Remote Repository Paths

### ETO

Checked from this machine on 2026-05-27.

- The SSH alias `ETO` connects successfully in batch mode.
- The login directory is `/home/server`.
- Slurm is installed and usable from this environment.
- The home directory contains a `projects` symlink to `/mnt/mydisk/server/projects`.
- A `QPO` directory was not located by the non-interactive probe under `/home/server` during this check, so the exact ETO clone path is still unverified.

### IHEP

Working-path notes are based on existing local project records.

- The main writable analysis area is `/home/lhaaso/liushijie`.
- The login-node home is under `/afs/ihep.ac.cn/users/l/liushijie`.
- A sibling local reference project at [AGENTS.md](/Users/luoji/Documents/projects/ihep/QPO/AGENTS.md) documents `/home/lhaaso/liushijie` as the intended working root for IHEP-side QPO work.
- A direct non-interactive login probe from this session failed on 2026-05-27, so the exact remote clone path for this repository was not re-verified in this turn.

## IHEP Data Notes

Checked from this machine on 2026-05-13.

- Confirmed EOS WCDA raw data paths:
  - `/eos/lhaaso/ai/wcda/raw/`
  - `/eos/lhaaso/ai/wcda/raw/2022/`
  - `/eos/lhaaso/ai/wcda/raw/2022/0101/`
- A historical transfer command used `rsync` over SSH from `liushijie@lxlogin.ihep.ac.cn` into a local directory.
- For future transfers, prefer syncing into `data/raw/wcda/` or another project-managed path derived from `src/utils/project_paths.py`.

Keep connection notes minimal and reproducible:

- safe to record host aliases, usernames, verified remote paths, and sync patterns;
- do not commit passwords, private keys, tokens, or full credential dumps.

## Working Rules

- Notebooks are for display, validation, and exploratory analysis only.
- Reusable logic belongs in `src/`.
- Documentation and reference guides belong in `docs/`.
- Formal reports and exported writeups belong in `reports/`.
- Ongoing work notes and handoff context belong in `work/`.
- After each work session, append a new entry to `work/log.md` using `devlog`.
- `src/pipeline/` holds runnable entry points.
- `src/simulation/` holds simulation scripts.
- `src/methods/` holds reusable methods and vendored method code.
- `src/utils/` holds shared helpers.
- `src/utils/project_paths.py` is the path authority for the repository.
- The vendored Emmanoulopoulos implementation lives in `src/methods/emmanoulopoulos/` and is imported by manually adding the relevant source directory to `sys.path`; it is not installed as a package.
- If a file still has reference value but is no longer part of the active workflow, move it to `archive/` instead of deleting it.

## Project Notes

- `docs/` is the default home for background guides such as the LHAASO gamma-source analysis reference.
- `work/overview.md` is the main project overview.
- `work/log.md` is the running lab-style project log and is updated by appending new `devlog` entries.
- `reports/` holds formal analysis outputs and summaries.
- Historical compatibility layers live under `archive/compat/`.
- Keep active entry points under `src/` with simple, descriptive names.
