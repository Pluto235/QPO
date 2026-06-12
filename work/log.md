# Work Log

This file is the cumulative lab-style project log.
After each completed work session, append a new entry using `devlog`; do not replace prior entries unless correcting factual mistakes.

## 2026-06-12

- Completed a cross-environment QPO sync audit across the local Mac checkout, ETO, and IHEP; added local MinerU paper extraction products, archived missing IHEP flux/forward-folding run notes under `docs/ihep/`, and recorded `work/cross_environment_sync_2026-06-12.md` as the final lightweight GitHub handoff manifest while excluding raw FITS/ROOT, simulation arrays, and paper PDFs.

## 2026-06-08

- Synchronized the local QPO working tree toward GitHub handoff, including current AGN WCDA survey/v2 strict-flux pipelines, processed CSV products, reports, presentation artifacts, Slurm handoff scripts, and `.DS_Store` ignore hygiene while keeping heavy raw/binary analysis data excluded.

## 2026-06-04

- Added per-source Fermi-LAT QPO prior context to the AGN WCDA weekly survey report, separating the reported Mrk 421/Mrk 501 GeV priors, the mixed NGC 1275 prior, and no-prior context for the remaining WCDA survey sources.
- Added strict-flux weekly TS detection-quality tiers to the AGN WCDA weekly survey report, marking Mrk 421/Mrk 501 as timing-grade and the low-TS survey sources as diagnostic-only despite any CWT/WWZ peaks.

## 2026-06-03

- Updated the AGN WCDA weekly survey report top strict-flux summary table to expand all CWT/WWZ candidate peaks per source, while preserving the source-first card layout and counts/excess-rate foldouts.
- Added a collapsed counts/proxy comparison foldout immediately after the v2 xgm MJD 60200-60700 flux WWZ quick-look figure, including the v1 poster-style WWZ and AR(1) local-significance figures in both local and any-reports copies.
- Added an explicit xgm poster comparison note to the v2 WCDA strict-flux report, contrasting the poster counts-based 51.05 d >99% visual claim with the local v1 counts/proxy AR(1) reproduction and v2 strict-flux WWZ/CWT local/global FAP results.
- Completed the ETO Slurm strict-flux significance run for the 10-source AGN WCDA weekly survey, pulled back the per-source AR(1) CWT/WWZ significance CSV/PNG products, and refreshed `reports/agn_wcda_weekly_survey_report.{md,html}` with strict-flux significance quick-look sections.
- Added CWT quick-look and 1000-surrogate AR(1) CWT significance for the v2 Mrk 421 daily flux xgm window MJD 60200-60700, and updated the v2 report/public copy with CWT local/global FAP tables and figures.
- Added targeted AR(1) WWZ surrogate significance for the v2 Mrk 421 daily flux xgm window MJD 60200-60700, ran 1000 surrogates on ETO Slurm job `41930`, pulled the CSV/NPZ/PNG products, and updated the v2 report/public copy with local/global FAP results.
- Added Mrk 421 and Mrk 501 strict weekly flux products to the AGN WCDA weekly survey report, making the source-first strict-flux section a 10-source view with Mrk 421 and Mrk 501 ordered first and counts/excess-rate diagnostics folded under each source.
- Added a v2 WCDA strict-flux uncertainty-outlier QC pass that excludes `N0_err > 5 x median(N0_err)` rows from derived aligned products, regenerates the v2 daily flux figures/reports, and saves rejected-row audit CSVs beside each aligned light curve.
- Added the eight-source strict WCDA weekly flux periodicity workflow, generated N0-based CWT/WWZ quick-look products under `data/processed/periodicity/agn_wcda_weekly_flux_survey/`, and updated `reports/agn_wcda_weekly_survey_report.{md,html}` with a no-significance strict-flux section.
- Pulled the eight IHEP strict AGN weekly flux CSVs and companion PNG/PDF figures from `/home/lhaaso/liushijie/QPO/results/flux_strict_agn_week/` into local `results/flux_strict_agn_week/`, verifying each CSV has 229 weekly rows spanning `date1=2021-03-08` through `date2=2025-07-27` and all 16 figures are non-empty.

## 2026-06-02

- Shortened the Nature-style QPO cover letter and generated a plain Pages document under `prestation/` for the writing-course peer-review vote.

## 2026-06-01

- Added the isolated WCDA strict-flux periodicity v2 workflow, generated Mrk 421/501 N0-based CWT/WWZ quick-look products and bilingual v2 reports, and published a local `any-reports/qpo-periodicity-v2/` copy with surrogate significance explicitly deferred.
- Added `src/pipeline/mkn421_optical_lhaaso_2021_2026_sync.py`, cached ZTF/AAVSO/CDS public optical data, generated the Mrk 421 optical/near-UV/WCDA weekly alignment products, and updated `reports/periodicity_v1_report.{md,html}` with the same-window optical supplement.
- Pulled the completed IHEP strict-batch WCDA flux CSV products for Mrk 421 and Mrk 501 into `data/processed/wcda_day/` and `data/processed/wcda_week/`, preserving day/week cadence naming and verifying row counts and flux-fit columns.
- Added `src/pipeline/fetch_mkn421_asassn.py` and `src/pipeline/fetch_mkn421_atlas_forced.py`, documented setup in `docs/mkn421_atlas_asassn_setup.md`, installed the local ASAS-SN client dependency path, and downloaded the current Mrk 421 ASAS-SN Sky Patrol LHAASO-window CSV.
- Reworked the Mrk 421 MJD 59500-60500 fixed-window analysis to add a pre-specified 140 d target-band CWT/WWZ local check, reran 1000 AR(1) WWZ surrogates, saved the surrogate global spectra, and updated `reports/periodicity_v1_report.{md,html}` with the targeted-band non-detection.
- Added `src/pipeline/windowed_weekly_local_significance.py`, ran the fixed-window Mrk 421 WCDA weekly MJD 59500-60500 CWT/WWZ local-significance check with 1000 AR(1) WWZ surrogates, and updated `reports/periodicity_v1_report.{md,html}` with the local-only non-detection result.
- Removed the short 2022 radio-LHAASO alignment section from the main periodicity v1 report because its WCDA overlap is too sparse for the report narrative; retained the longer TELAMON weekly supplement as the radio timing context.
- Updated the fixed-window Mrk 421 global-spectrum figures and report tables to also mark the 145-149 d secondary feature, while keeping the AR(1) non-detection interpretation explicit.
- Audited Mrk 421 optical/UV monitoring options for the LHAASO/WCDA 2021-2026 window, verified direct ZTF, AAVSO, and CDS/VizieR access probes, and documented API/request blockers in `docs/mkn421_optical_data_checklist.md`.
- Added the TELAMON 2022-2026 Mrk 421 radio-LHAASO weekly alignment supplement to `reports/periodicity_v1_report.{md,html}` and the `any-reports/qpo-periodicity-v1/` publishing checkout, including the new public PNG asset and homepage date/description refresh.
- Added `src/pipeline/mkn421_telamon_lhaaso_2022_2026_sync.py` to parse/cache TELAMON Mrk 421 averaged 14 mm and 7 mm light curves, generate the 2022-2026 WCDA weekly synchronization figure, and write `reports/mkn421_telamon_lhaaso_2022_2026_sync.md`.

## 2026-05-30

- Added the 2022 Mrk 421 radio-LHAASO short-window alignment supplement to the periodicity v1 report source and GitHub Pages publishing checkout, including bilingual public-page text, the weekly radio/WCDA PNG asset, updated report date, and homepage card metadata.

## 2026-05-22
- Migrated the ETO QPO working tree from `/mnt/mydisk/server/projects/QPO` to `/Users/luoji/Documents/projects/QPO` on the Mac.
- Preserved the remote `.git` history and current working-tree state; the local `main` branch remains one commit ahead of `origin/main`.
- Kept the local `prestation/` directory in place and excluded remote `archive/`.
- Slimmed data migration to `data/processed/**/*.csv` only: 15 CSV files, 819,512 bytes total. Raw FITS, paper PDFs, simulation HDF5 files, and processed binary products were intentionally excluded.
- Enabled local sparse checkout to exclude `archive/` from the working tree while keeping repository history available.

## 2026-05-27

- Pulled the completed IHEP WCDA weekly counts products for eight AGN survey targets into `data/processed/wcda_week/`, copied the IHEP status report into `docs/ihep-wcda-pull-tasklist-status.md`, and locally verified each CSV has 264 rows with the required `name,mjd,n_on,n_bkg,n_off,tobs` structure.
- Rewrote `docs/ihep-wcda-pull-tasklist.md` into an executable IHEP Codex handoff for eight AGN weekly WCDA counts targets, fixing the `MakeLC` reference pipeline, HTCondor / `hep_sub` submission requirement, and the “login node no large-scale compute” constraint, then synced it to `/home/lhaaso/liushijie/QPO/docs/` on IHEP.
- Reviewed `prestation/LHAASO-AGN-2026.pptx` and documented a practical LHAASO AGN QPO survey shortlist in `docs/lhaaso-agn-qpo-survey-candidates.md`, prioritizing post-`Mrk 421/501` targets and control samples.
- Added a multi-source survey metadata registry under `src/utils/source_registry.py` and generated `docs/lhaaso-agn-qpo-data-checklist.md` to track per-source data availability and next-step IHEP pulls.
- Added `docs/ihep-wcda-pull-tasklist.md` for the first six survey sources and refactored `src/pipeline/periodicity_v1.py` to resolve default inputs from the registry and support batch shortlist runs.
- Added and ran the 10-source AGN WCDA weekly survey pipeline, generating weekly photon-count diagnostics, CWT/WWZ quick-look products, a combined survey summary, and new Markdown/HTML reports under `reports/agn_wcda_weekly_survey_report.*`.

## 2026-05-28

- Synced the current 10-source WCDA weekly survey code, reports, and required processed products to ETO at `/mnt/mydisk/server/projects/QPO`, added Slurm smoke/benchmark/full-run scripts under `work/slurm/`, fixed the survey report significance figure label bug, and submitted full AR(1) significance job `26894` after smoke job `26892` and benchmark job `26893` passed.
- Validated completed ETO significance job `26894`, pulled the 10-source AR(1) significance CSV/PNG products and regenerated `reports/agn_wcda_weekly_survey_report.{md,html}` back to the local Mac checkout, and verified local report image paths and summary coverage.
- Pulled the published `qpo-periodicity-v1` report HTML and Markdown from ETO `/home/server/any-reports/qpo-periodicity-v1/` back into local `reports/periodicity_v1_report.{html,md}` and verified matching SHA-256 hashes.
- Pulled the full ETO `/home/server/any-reports/` publishing checkout into sibling project directory `/Users/luoji/Documents/projects/any-reports/`, preserving the standalone Git repository and verifying its `origin` remote and current `e1835a9` HEAD.
- Fixed local image paths in `reports/periodicity_v1_report.html` so the file-based report resolves figures from `data/processed/periodicity/` instead of the GitHub Pages `assets/` layout.
- Added fast AR(1) 95%/99% visual-reference curves to the xgm poster-style WWZ reproduction panels and refreshed the periodicity v1 report captions to distinguish those curves from the existing local-FAP significance products.
- Ran the xgm poster WWZ significance check on ETO with 1000 AR(1) surrogates, refreshed the poster-style and local-significance figures, and updated `reports/periodicity_v1_report.{md,html}` to highlight why the 51 d feature differs from the xgm poster significance claim.
- Documented the Mac-local `py310` conda interpreter requirement in `AGENTS.md` after confirming base/default Python lacks the scientific plotting and periodicity dependencies.
- Searched public Mrk 421 radio light-curve options for LHAASO comparison, identifying CDS/VizieR 2012-2018 OVRO 15 GHz data and a 2022 CDS multiwavelength campaign with Metsahovi 37 GHz, IRAM 86/230 GHz, and SMA 225 GHz points that overlap the WCDA weekly timeline.
- Added `src/pipeline/mkn421_radio_lhaaso_2022_sync.py` to parse/cache the CDS 2022 Mrk 421 radio flux-density table, generate the exploratory WCDA weekly radio-alignment figure, and write `reports/mkn421_radio_lhaaso_2022_sync.md` with the 2022 daily WCDA product marked pending.

## 2026-05-20

- Updated the periodicity v1 WWZ figures so their heatmap colors use log normalization and their period axes use log scaling.
- Reran the Mrk 421 and Mrk 501 v1 periodicity plotting workflow without changing the CWT/WWZ analysis grids or adding simulation-based significance tests.
- Refreshed the HTML and Markdown reports for `qpo-periodicity-v1` with the updated visualization note and report date.

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
