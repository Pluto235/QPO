# Project Guidelines

## Goal

This repository supports blazar QPO analysis for **Mrk 421**. The current focus is keeping the Fermi and WCDA workflows reproducible while gradually moving reusable logic out of notebooks.

## File Architecture

```text
QPO/
├─ AGENTS.md
├─ README.md
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

## Analysis Pipelines

Two analysis chains are implemented:

1. **Fermi monthly** — `src/pipeline/fermi_month.py` drives `fermipy` using `src/pipeline/fermi_month_config.yaml`. Fits the ROI, saves it to `data/processed/fermi_month/mkn421/mkn421_fulltime.fits`, then generates a 30-day binned light curve for source `4FGL J1104.4+3812`. Requires `$FERMI_DIFFUSE_DIR` to be set.

2. **WCDA weekly simulation** — `src/pipeline/wcda_weekly.py` delegates to `src/simulation/generate_wcda_weekly_sims.py`. Reads raw LHAASO CSV from `data/raw/wcda/`, fits PSD and PDF via the Emmanoulopoulos sampler, then runs parallel simulations with `joblib` and writes results to an HDF5 file (`flux_sims`, `seed_sims`, `done_mask` datasets).

## Data Layout

- `data/processed/fermi_month/`: Fermi monthly products.
- `data/processed/fermi_week/`: Fermi weekly products.
- `data/processed/wcda_week/`: processed WCDA weekly products.
- `data/simulations/wcda/`: WCDA weekly simulations.

Raw inputs live under `data/raw/fermi/` and `data/raw/wcda/`.

## IHEP Connectivity

Checked from this machine on 2026-05-13.

- SSH account: `liushijie@lxlogin.ihep.ac.cn`.
- The login host resolved to `lxlogin008.ihep.ac.cn`; login home is `/afs/ihep.ac.cn/users/l/liushijie`.
- The actual IHEP working directory is `/home/lhaaso/liushijie`.
- `ssh -o BatchMode=yes -o ConnectTimeout=8 liushijie@lxlogin.ihep.ac.cn true` succeeds outside the Codex sandbox, so the current local account can authenticate non-interactively. Inside restricted sandboxes, DNS may fail even when the machine-level connection works.
- There is no `~/.ssh/config` entry for IHEP. Host keys for `lxlogin.ihep.ac.cn` are present in `~/.ssh/known_hosts`.
- Confirmed EOS WCDA raw data paths:
  - `/eos/lhaaso/ai/wcda/raw/`
  - `/eos/lhaaso/ai/wcda/raw/2022/`
  - `/eos/lhaaso/ai/wcda/raw/2022/0101/`
- Historical local shell history shows WCDA raw data was pulled with:

```bash
rsync -av --progress --partial --append-verify --info=progress2 \
  -e "ssh -o StrictHostKeyChecking=accept-new -o PubkeyAuthentication=no -o PreferredAuthentications=password" \
  liushijie@lxlogin.ihep.ac.cn:/eos/lhaaso/ai/wcda/raw/2022/0101/ \
  /mnt/mydisk/0101/
```

- For new transfers, prefer writing project products under `data/raw/` or `data/processed/` according to `src/utils/project_paths.py`; avoid hard-coding new absolute local paths unless documenting a one-off sync.
- Do not commit private keys, passwords, tokens, or full credential dumps. Connection notes should stay limited to hostnames, usernames, verified remote paths, and reproducible commands.

## Working Rules

- Notebooks are for display, validation, and exploratory analysis only.
- Reusable logic belongs in `src/`.
- `src/pipeline/` holds runnable entry points.
- `src/simulation/` holds simulation scripts.
- `src/methods/` holds reusable analysis methods or vendored method code.
- `src/utils/` holds shared helpers; `src/utils/project_paths.py` is the single source of truth for all directory paths — import from there rather than constructing paths ad-hoc.
- The Emmanoulopoulos method is vendored under `src/methods/emmanoulopoulos/` and must be added to `sys.path` manually (not installed as a package).
- If a file may still matter but is no longer part of the main workflow, move it to `archive/` instead of deleting it.

## Project Notes

- `work/overview.md` is the main project overview.
- `work/log.md` is the running lab-style project log.
- Historical compatibility layers live under `archive/compat/`.
- Keep names and paths simple; keep active entry points under `src/`.
