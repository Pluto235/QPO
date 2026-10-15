# Project Guidelines

## Goal

This repository supports blazar QPO analysis for **Mrk 421** and related comparison targets such as **Mrk 501**.

The current priorities and scope (updated 2026-10-15) are:

- keep the Fermi and WCDA workflows reproducible;
- move reusable logic from notebooks into `src/`;
- preserve a clean separation between raw data access, derived light curves, periodicity products, and reports;
- maintain the main QPO project on the local Mac and perform light-curve generation on IHEP;
- use ETO only for synchronization;
- leave QPO detection and `qposim` work paused for now; resume only when explicitly requested. `qposim` work is carried out on PDC.

## Repository Role

- The main QPO project lives on the local Mac at `/Users/luoji/Documents/projects/QPO`; this checkout is the canonical working tree.
- The Git remote is `git@github.com:Pluto235/QPO.git`.
- **IHEP** is the execution environment for light-curve generation and access to LHAASO / WCDA observational data. For WCDA generation, first read `/home/lhaaso/liushijie/tutorial/wcda_v1_official_lc_pipeline.md` on IHEP.
- **ETO** holds a synchronized copy only; do not launch QPO analysis, light-curve generation, periodicity, or simulation jobs there.
- **PDC** is where `qposim` work is carried out. Do not treat the local `qposim/` directory as an active QPO task or resume its work by default.

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

## Pipeline Reference and Current Scope

Runnable entry points live under `src/pipeline/`. Light-curve generation tasks run on IHEP; follow the official WCDA tutorial above for WCDA products. The periodicity and surrogate-simulation entries below (2–6) are retained as references and are paused along with QPO detection; do not run or extend them unless explicitly requested.

1. `src/pipeline/fermi_month.py`
   Runs the Fermi monthly workflow via `fermipy` and `src/pipeline/fermi_month_config.yaml`.
   Produces monthly light-curve products under `data/processed/fermi_month/`.
   Run on IHEP with the required Fermi environment and `$FERMI_DIFFUSE_DIR` available.

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

### Local Mac — main project

- Primary place for project maintenance, code editing, notebook work, quick validation, result inspection, and report generation.
- Keep this checkout as the canonical working tree. Run light-curve generation on IHEP and bring the required products back into the local project layout.
- On this Mac, run scientific Python / plotting scripts with the conda `py310` environment:
  `/Users/luoji/miniconda3/envs/py310/bin/python`.
- Do not rely on the default `python3`, `/Users/luoji/miniconda3/bin/python`, or conda `base` for these workflows; they have been observed to miss core dependencies such as `numpy`, `pandas`, `matplotlib`, `pycwt`, and `libwwz`.
- If a script fails with `ModuleNotFoundError` for scientific packages on the Mac, first retry with the explicit `py310` interpreter before changing code or installing packages.

### ETO server — synchronization only

- SSH host alias is `ETO` in `~/.ssh/config`.
- Login lands in `/home/server`.
- Store synchronized QPO copies and backups under `/mnt/newdisk/shijie`; the synchronized repository is `/mnt/newdisk/shijie/QPO`.
- Use ETO only for synchronization with the canonical local Mac project. Its available compute or Slurm facilities do not make it an execution target for current QPO work.
- Do not launch light-curve generation, analysis, periodicity, or simulation jobs on ETO.

### IHEP cluster — light-curve generation

- SSH host alias is `ihep` in `~/.ssh/config`.
- Account: `liushijie@lxlogin.ihep.ac.cn`.
- The login environment is the entry point to the IHEP / LHAASO cluster.
- Run light-curve generation tasks on IHEP and use its LHAASO observational data access for WCDA light curves or photon-count series.
- The actual working directory on IHEP is `/home/lhaaso/liushijie`.
- Before generating WCDA light curves, read and follow `/home/lhaaso/liushijie/tutorial/wcda_v1_official_lc_pipeline.md` on IHEP.
- Sync required generated products and provenance back to the canonical local Mac checkout using the project data layout.
- The login-node home under AFS is separate from the main LHAASO working area; avoid treating the login landing directory as the main project storage location.

### PDC server — qposim

- `qposim` work is carried out on PDC, separately from the current local QPO light-curve work.
- `qposim` is paused in the current task scope. Do not start, modify, or resume its simulations or post-processing unless explicitly requested.

## Remote Repository Paths

### ETO

Historical path verification from this machine on 2026-10-13; the current ETO role is synchronization only.

- The SSH alias `ETO` connects successfully in batch mode.
- The login directory is `/home/server`.
- The current storage disk is mounted at `/mnt/newdisk`, replacing the failed disk previously mounted at `/mnt/mydisk`; the personal directory is `/mnt/newdisk/shijie`.
- Use `/mnt/newdisk/shijie/QPO` for the ETO synchronized QPO copy and backups; do not use the old `/mnt/mydisk` paths.
- The QPO checkout is restored from the canonical local working tree at `/mnt/newdisk/shijie/QPO`, including Git history and uncommitted files.
- `/mnt/mydisk` is currently an unmounted, empty directory; old ETO-only files are not recovered by this restore.
- Legacy files under `src/pipeline/fermi_mkn501_run/` still contain `/mnt/mydisk/server/projects/QPO` paths and require adaptation before use.

### IHEP

Working-path notes are based on existing local project records.

- The main writable analysis area is `/home/lhaaso/liushijie`.
- The login-node home is under `/afs/ihep.ac.cn/users/l/liushijie`.
- A sibling local reference project at [AGENTS.md](/Users/luoji/Documents/projects/ihep/QPO/AGENTS.md) documents `/home/lhaaso/liushijie` as the intended working root for IHEP-side QPO work.
- A historical non-interactive login probe failed on 2026-05-27; the exact remote clone path is not established by that record. The current working root and official tutorial path above are user-provided; read the tutorial on IHEP before generation.

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

- Maintain QPO primarily on the local Mac; route light-curve generation to IHEP and use ETO only for synchronization.
- Leave QPO detection (including CWT/WWZ searches and significance reruns) and `qposim` work paused unless explicitly requested; `qposim` execution belongs on PDC.
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
