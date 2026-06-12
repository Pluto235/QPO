# Cross-Environment QPO Sync - 2026-06-12

This note records the final sync pass across the local Mac checkout, ETO, and
IHEP before continuing QPO work from another machine.

## Local Mac

- Path: `/Users/luoji/Documents/projects/QPO`
- Git remote: `git@github.com:Pluto235/QPO.git`
- Branch: `main`
- Baseline before this pass: `63eeb1a`
- Added local MinerU extraction products for the Chen 2024 Fermi-LAT blazar QPO
  survey under `docs/papers/mineru-md/`.
- Kept extracted Markdown, JSON, and small image assets in Git.
- Kept MinerU PDF render/intermediate files ignored by the existing `*.pdf`
  policy.

## ETO

- Checked path: `/mnt/mydisk/server/projects/QPO`
- Equivalent path also visible through `/home/server/projects/QPO`.
- The ETO working tree is about 24 GB and contains large FITS/PDF/Fermi monthly
  products that remain intentionally excluded from Git.
- After fetching `origin`, ETO was behind the GitHub `main` state already pushed
  from the Mac. No newer lightweight ETO-only reports, code, or CSV products
  were identified for this pass.
- Action taken: no files copied from ETO in this pass.

## IHEP

- Checked path: `/home/lhaaso/liushijie/QPO`
- This path is not a Git checkout. It is an operational compute/output area with
  many per-source and per-job directories.
- Existing lightweight IHEP data products were already represented in Git from
  the earlier sync:
  - `data/processed/wcda_week/*.csv`
  - `data/processed/wcda_day/*_flux.csv`
  - `results/flux_strict_agn_week/*.csv`
  - `results/flux_strict_agn_week/figures/*.png`
- Added missing IHEP operational notes under `docs/ihep/`:
  - `flux_handoff.md`
  - `flux_forward_folding_action_plan.md`
  - `flux_strict_run_note.md`
  - `flux_strict_batch_run_note.md`
  - `flux_strict_agn_week_run_note.md`

## Excluded On Purpose

- Raw Fermi FITS products.
- LHAASO/WCDA ROOT maps and large job directories.
- Simulation arrays and periodicity grids such as `.npz`, `.npy`, `.h5`, and
  `.hdf5`.
- Paper PDFs and generated PDF variants.
- Local `.DS_Store` and Codex-local metadata.

The final GitHub commit after this pass is the authoritative lightweight
handoff state for continuing the QPO project on another machine.
