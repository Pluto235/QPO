# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run Fermi monthly pipeline
python src/pipeline/fermi_month.py

# Run WCDA weekly simulation (adjust --ncores to available CPUs)
python src/pipeline/wcda_weekly.py --output data/simulations/wcda/wcda_weekly_sims_full.h5 \
    --nsim 10000 --ncores 48 --chunk 256 --overwrite

# Slurm variant
srun python src/pipeline/wcda_weekly.py --output /path/to/wcda_weekly_sims_full.h5 \
    --nsim 10000 --ncores ${SLURM_CPUS_PER_TASK:-8} --chunk 256 --overwrite

# Run tests for the Emmanoulopoulos method
pytest -q src/methods/emmanoulopoulos/emmanoulopoulos/test

# Test IHEP SSH connectivity from this machine
ssh -o BatchMode=yes -o ConnectTimeout=8 liushijie@lxlogin.ihep.ac.cn true
```

## Repository Layout

```text
QPO/
├─ data/
│  ├─ raw/
│  │  ├─ fermi/
│  │  └─ wcda/
│  ├─ processed/
│  │  ├─ fermi_month/
│  │  ├─ fermi_week/
│  │  └─ wcda_week/
│  └─ simulations/
│     └─ wcda/
├─ src/
│  ├─ methods/
│  ├─ simulation/
│  ├─ pipeline/
│  └─ utils/
├─ notebooks/
├─ work/
│  ├─ overview.md
│  └─ log.md
└─ archive/
```

## Architecture

This workspace searches for quasi-periodic oscillations (QPO) in Mrk 421 light curves from Fermi-LAT and LHAASO-WCDA.

**Two analysis chains:**

1. **Fermi monthly** — `src/pipeline/fermi_month.py` drives `fermipy` using `src/pipeline/fermi_month_config.yaml`. It changes directory to `PROJECT_ROOT`, fits the ROI, saves it to `data/processed/fermi_month/mkn421/mkn421_fulltime.fits`, then reloads and generates a 30-day binned light curve for source `4FGL J1104.4+3812`.

2. **WCDA weekly simulation** — `src/pipeline/wcda_weekly.py` delegates to `src/simulation/generate_wcda_weekly_sims.py`, which reads the raw LHAASO CSV from `data/raw/wcda/`, computes excess count rates, fits PSD and PDF via the vendored Emmanoulopoulos sampler, then runs parallel simulations with `joblib` and writes results to an HDF5 file (`flux_sims`, `seed_sims`, `done_mask` datasets, chunked and gzip-compressed).

**Path constants** — `src/utils/project_paths.py` is the single source of truth for all directory paths. Import from here rather than constructing paths ad-hoc.

**Emmanoulopoulos method** — vendored under `src/methods/emmanoulopoulos/`. Must be added to `sys.path` manually (see `import_emmanoulopoulos()` in `generate_wcda_weekly_sims.py`) because it is not installed as a package.

**Notebooks** — display and validation only; no reusable computation logic lives there.

**Archive policy** — files that may still matter but are no longer in the active workflow go to `archive/` rather than being deleted.

## IHEP Connectivity

Checked from this machine on 2026-05-13.

- SSH account: `liushijie@lxlogin.ihep.ac.cn`.
- The login host resolved to `lxlogin008.ihep.ac.cn`; login home is `/afs/ihep.ac.cn/users/l/liushijie`.
- The actual IHEP working directory is `/home/lhaaso/liushijie`.
- Non-interactive SSH currently works outside the Codex sandbox:
  `ssh -o BatchMode=yes -o ConnectTimeout=8 liushijie@lxlogin.ihep.ac.cn true`.
- Restricted sandboxes may report DNS failure for `lxlogin.ihep.ac.cn` even when the machine-level connection is healthy.
- There is no local `~/.ssh/config` entry for IHEP; host keys are already in `~/.ssh/known_hosts`.
- Confirmed EOS WCDA raw data paths include:
  `/eos/lhaaso/ai/wcda/raw/`,
  `/eos/lhaaso/ai/wcda/raw/2022/`, and
  `/eos/lhaaso/ai/wcda/raw/2022/0101/`.
- Historical pull command found in shell history:

```bash
rsync -av --progress --partial --append-verify --info=progress2 \
  -e "ssh -o StrictHostKeyChecking=accept-new -o PubkeyAuthentication=no -o PreferredAuthentications=password" \
  liushijie@lxlogin.ihep.ac.cn:/eos/lhaaso/ai/wcda/raw/2022/0101/ \
  /mnt/mydisk/0101/
```

- Keep future synced project data under `data/raw/` or `data/processed/` where possible. Do not commit private keys, passwords, tokens, or credential dumps.

## Working notes

- `work/overview.md` — current project overview (Chinese)
- `work/log.md` — running lab-style log
- Fermi config uses `$FERMI_DIFFUSE_DIR` for diffuse model paths; that env variable must be set before running `fermi_month.py`.
