# Work Log

This file is the cumulative lab-style project log.
After each completed work session, append a new entry using `devlog`; do not replace prior entries unless correcting factual mistakes.

## 2026-09-02

- Regenerated the Mrk 421 WCDA 2-day xgm-window periodicity composite with yellow horizontal guides for the CWT candidates at 49.5 and 124.8 d and WWZ candidates at 49.8 and 110.9 d; updated slide 9 to identify them as display-only global-spectrum annotations.

## 2026-08-18

- Standardized every source-specific headline in `reports/official_wcda_2day_8day_qpo_presentation_20260817.html` to lead with the source name followed by the scientific takeaway, then rendered and visually checked all 20 slides for clipping and overlap.

## 2026-08-17

- Added a rigorous-significance workflow slide to `reports/mkn421_mkn501_qpo_presentation.html`, distinguishing the AR(1) red-noise null, pointwise thresholds, WWZ search-wide FAP, and claim-level look-elsewhere/independent-recovery requirements; renumbered the deck to 18 slides.
- Converted the Mrk 421/Mrk 501 QPO status report into a 17-slide English academic-paper HTML presentation at `reports/mkn421_mkn501_qpo_presentation.html`, reorganized it source-first, added reliable page numbers and interactive cadence/method figure switches, and included one-page LC/periodicity/significance appendices for all eight control sources.
- Conservatively synchronized the local QPO checkout with ETO by merging ETO commit `a759ef2` (daily QPO significance workflows) with the local v0.99 data-path update, pulling the uncommitted official-QPO source, documentation, tests, and processed products without overwrite, and preserving conflicting local QPO products in the named Git stash `pre-eto-sync-2026-08-17-preserve-local-qpo-results`.
- Recomputed all 22 official WCDA 2-day/8-day WWZ products on ETO with the original 80-time-division, 0.5 frequency-step grid and 200 AR(1) surrogates; regenerated presentation assets, reran the two Mrk 421 windows on the same grid, and refreshed the 19-slide official HTML deck without changing its user-authored layout.

## 2026-07-23

- Downloaded arXiv `2511.03140`, converted the 15-page PDF to Markdown with MinerU 3.2.3 while retaining extraction assets locally, and synced `2511.03140.{pdf,md}` to PDC under `/home/luoji/qposim/documents/` with matching SHA-256 checks.

## 2026-07-14

- Generated 81-frame fixed-color `R <= 2`, `z <= 60` density, pressure, axial-velocity, Mach-number, and summary GIFs for corrected HD jet run `116655`, verified that every animation changes across the full time range, and synced the products locally.

## 2026-07-13

- Copied the official gPLUTO `Test_Problems/HD/Jet` cylindrical HD template from PDC into `qposim/2D HD over-pressured jet/` as the starting point for a 2D HD over-pressured recollimation-jet exercise.
- Refactored `qposim/2D HD over-pressured jet/` into a paper-oriented HD baseline with ambient initialization, a light over-pressured inlet jet, and the reduced `RHO_J/RHO_A/PRS_A/VJET` parameter set.
- Synced the HD over-pressured jet setup to PDC under `/home/luoji/qposim/hd2d_overpressured_jet`, generated a `linux.nvc++.acc.defs` gPLUTO makefile, compiled it with NVHPC OpenACC, and verified a 10-step GPU smoke run on `NVIDIA devicenum=0`.
- Added Slurm smoke/full GPU batch scripts for `/home/luoji/qposim/hd2d_overpressured_jet` and verified smoke job `116647` using the Slurm 26.05.1 client under `/opt/slurm/26.05.1/bin`.
- Removed smoke-test scripts/logs/data from the HD over-pressured jet setup, submitted formal Slurm GPU job `116648`, and completed the run to `t=100` with outputs under `/home/luoji/qposim/hd2d_overpressured_jet/runs/116648/`.
- Added a dependency-light VTK post-processing script for the HD over-pressured jet run and generated density, pressure, axial-velocity, Mach-number, and summary GIF movies under `/home/luoji/qposim/hd2d_overpressured_jet/runs/116648/movies/`.
- Reoriented the HD jet post-processing movies so the jet axis `z/R_j` is vertical and radius `R/R_j` is horizontal, preserving the first horizontal render under `runs/116648/movies_horizontal_old/`.
- Deleted the `t=100` HD jet run `116648`, reran the case to `t=300` as Slurm job `116652` with reduced `dbl` cadence, and generated updated density, pressure, axial-velocity, Mach-number, and summary movies under `runs/116652/movies/`.
- Extended the HD jet post-processing script with zoom and fixed robust color-scale options, then generated `R <= 2` zoom movies with all-frame fixed percentile colorbars under `runs/116652/movies_Rlt2_Zlt80_fixed/`.
- Continued HD jet run `116652` from restart output `#30` at `t=300` to `t=1200` with Slurm GPU job `116654`, then generated fixed-color `R <= 2` movies under `runs/116652/movies_Rlt2_Zlt80_fixed_t1200/` and synced them locally.
- Rebuilt the classical HD case as a preexisting Mach-5 over-pressured jet with a passive tracer and HLLC solver, completed fresh GPU Slurm job `116655` to `t=400`, and verified forward flow plus recollimation pressure/radius nodes in the final state.

## 2026-07-12

- Downloaded arXiv `2411.17389`, converted the PDF to Markdown with `mineru-pdf-to-md`, and synced `2411.17389.{pdf,md}` to PDC under `/home/luoji/qposim/documents/` with matching SHA-256 checks.
- Synced WeChat-received `plot2.py` to PDC under `/home/luoji/qposim/initial_setup_gpluto/plot2.py` and verified the remote SHA-256 hash matches the local file.

## 2026-07-11

- Synced WeChat-received `plot2.py` to PDC under `/home/luoji/qposim/initial_setup/plot2.py` and verified the remote SHA-256 hash matches the local file.
- Synced `qposim/initial_setup.zip` from the local checkout to PDC under `/home/luoji/qposim/initial_setup.zip` and verified the remote SHA-256 hash matches the local file.

## 2026-07-09

- Converted `/Users/luoji/Downloads/userguide.pdf` into Markdown with `mineru-pdf-to-md`, split the gPLUTO user guide into chapter Markdown files with extracted image assets, and synced the PDF/Markdown tutorial bundle to PDC under `/home/luoji/qposim/tutorial/` with matching SHA-256 checks for `userguide.pdf` and `userguide.md`.

## 2026-07-03

- Installed official gPLUTO 0.91 commit `870aa807` on PDC under `/home/luoji/opt/gPLUTO-870aa807`, verified the transferred archive SHA-256, and compiled/ran a serial GPU OpenACC `HD/Shock_Tubes` smoke test with NVHPC 24.5 on Tesla V100.

## 2026-06-16

- Added generated CWT/WWZ PNG result figures under `data/processed/periodicity/` to the lightweight Git handoff set for report writing, while keeping NPZ/HDF5/FITS/ROOT/PDF analysis artifacts excluded.

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

## 2026-07-21

- Searched NASA ADS, arXiv, and journal sources for recollimation-kink QPO studies relevant to Mrk 421; identified direct generic radiative demonstrations, a Mrk 421 kink-reconnection PSD comparison, an observational kink-event search including Mrk 421, and the remaining source-specific GeV/TeV modeling gap.
- Audited the PDC `hxf_toroidal_fig` reproduction: all six Hu et al. Table-2 cases reached `t=400` with complete final outputs and empty final stderr; confirmed the exact 2D setup and qualitative 3D morphology while identifying mixed 3D grids, reduced resolution, and `20 R_j/c` output cadence as limits on controlled kink and QPO analysis.
- Added an execution-oriented recollimation-kink gamma-ray QPO roadmap covering controlled RMHD simulations, high-cadence mode diagnostics, nonthermal synchrotron/SSC radiation, synthetic-observation significance tests, parallel learning, and manuscript gates.

## 2026-07-28

- Audited completed PDC MHD3 job `116705` (`320x320x450`, `48/7.5 cells per R_j` transverse/axial, 131 double-precision snapshots with cadence 1 over `t=300-400`) and updated the recollimation-kink gamma-ray QPO roadmap to mark data generation complete while retaining convergence, mode-analysis, controls, and radiation gates as pending.
- Recorded the MHD3 reproduction of Hu et al.'s first-paper kink as a confirmed dynamical result, while keeping kink periodicity, dissipation coupling, numerical robustness, and gamma-ray QPO production as separate pending evidence levels.

## 2026-08-17

- Recomputed 1000-surrogate AR(1) WWZ pointwise significance curves on ETO for the eight appendix control sources, saved reusable significance arrays, generated single-page flux/CWT/WWZ composites with 95%/99% references on both global spectra, and simplified slides 10–17 of `reports/mkn421_mkn501_qpo_presentation.html` to one composite figure per source.
- Extracted and checksum-verified the official WCDA 2-day/8-day release, completed the 22-source-cadence CWT/WWZ AR(1) screening on ETO, and summarized the systematics-limited candidates in `reports/official_wcda_2day_8day_qpo_screening_20260817.md`.
- Built the independent 17-slide English `academic-paper` presentation for the official daily-map-derived WCDA 2-day/8-day QPO screen, added presentation-scale Mrk 421/501 light curves, and fixed the IC 310 no-peak path so WWZ AR(1) reference curves are computed even when no candidate FAP row is defined.
- Standardized every source's 2-day and 8-day presentation flux axes to the source-specific 8-day range without deleting measurements, generated 22 matched-axis periodicity composites with explicit clipping annotations, and refreshed the HTML deck and rendered previews.
- Reorganized the official WCDA presentation into a 19-slide Crab-validation, Mrk 421/Mrk 501 primary-target, and eight-source appendix structure; added official 2-day xgm-window analyses for both primary targets, applied display-only robust flux limits to the xgm composites, verified the deck and targeted tests, and synchronized the report, scripts, assets, and results to ETO.
- Reduced the official WCDA presentation to 18 slides by removing the Mrk 501 xgm-window page, restricting the xgm reproduction narrative to Mrk 421, updating the primary-target conclusion and all page numbers, rerendering the deck, and synchronizing the revision to ETO.
- Added a reproducible official Mrk 421 2-day bright-window test for MJD 59800–60500 with 200 AR(1) WWZ surrogates, added its result as slide 6 of the 19-slide report, and found only non-significant ≈50–140 day red-noise-like structures.
- Added an official Mrk 501 2-day MJD 59600–60400 subwindow test with 200 AR(1) WWZ surrogates, added its result as slide 10 of the 20-slide report, and found a ≈160 day pointwise 95% excess with global FAP 0.159 rather than a significant QPO.

## 2026-08-20

- Completed the exact-grid Fermi-LAT 2-day/8-day light curves for Mrk 421 and Mrk 501 on ETO with resumable chunks and per-bin failure isolation, verified all 803/200-row CSV/FITS/PNG products and classifications, and checksum-synced the final products and provenance to the Mac; Mrk 421 retained 18 failed 2-day bins and one failed 8-day bin, while Mrk 501 retained one failed 2-day bin and no failed 8-day bins.

## 2026-08-25

- Added and validated the exact-WCDA-workflow Fermi CWT/WWZ pipeline, completed four 1,000-surrogate `all-successful` AR(1) analyses on ETO as Slurm jobs `65868`/`65869`, checksum-synced all products to the Mac, and identified a Mrk 501 2-day approximately 260-day follow-up candidate with single-curve global FAP 0.004995 and four-curve Bonferroni FAP 0.01998 that is not significant in the 8-day WWZ analysis.
- Added four source- and cadence-specific Fermi result slides to `reports/official_wcda_2day_8day_qpo_presentation_20260817.html`, with matched LHAASO-WCDA/Fermi CWT and WWZ map panels, reproducible comparison figures, updated conclusions, and 24-slide numbering.
- Added one switchable Fermi-LAT 2-day/8-day light-curve slide for each primary target before its WCDA/Fermi periodicity comparisons, and renumbered the official QPO presentation to 26 slides.
- Merged the Mrk 421 2-day and 8-day WCDA/Fermi CWT/WWZ comparison pages into one cadence-switchable slide, clarified the LHAASO-WCDA and Fermi-LAT null result, and renumbered the official QPO presentation to 25 slides.
- Added concise, source-verified prior-periodicity annotations to the Mrk 421 and Mrk 501 WCDA/Fermi comparison slides, distinguishing Mrk 421's prior null result from the historical 72 d, 23 d harmonic, and ≈322 d Mrk 501 candidates.
- Added display-only, centered 32-day rolling-median overlays to the Mrk 501 Fermi-LAT 2-day and 8-day light-curve panels on slide 12; regenerated only those two display figures, leaving all timing inputs and QPO results unchanged.
- Tightened the Mrk 421 Fermi-LAT 2-day presentation y-axis to the detected-flux range, retaining eight extreme low-TS upper limits as labeled boundary markers while preserving the unchanged all-successful timing input.

## 2026-09-02

- Added method-specific yellow candidate-period guides to the Mrk 421 MJD 59800–60500 CWT and WWZ maps, derived from the same global-spectrum peak finder and explicitly distinguished from significance contours.
- Merged the Mrk 501 2-day and 8-day WCDA/Fermi comparison pages into one cadence-switchable slide, retained both statistical interpretations and literature notes, and renumbered the official presentation to 24 slides.
- Added both the short (approximately 150–157 d) and long (approximately 420–437 d) LHAASO-WCDA candidate-period guides to the Mrk 501 2-day and 8-day CWT/WWZ comparison maps, regenerated the presentation figures, and kept the guides explicitly separate from significance claims.
- Recomputed the Mrk 421 MJD 59800–60500 bright-window WWZ analysis on ETO Slurm job `65904` with a 240 × 267 grid and 200 matching AR(1) surrogates, updated slide 8 to use the high-resolution map, and confirmed that the refined 147.26 d candidate remains non-significant (local FAP 0.154; global FAP 0.388).
- Capped the shared Mrk 421 2-day WCDA/Fermi CWT display scale at standardized power 20 on slide 7, added an explicit upper-saturation indicator and caption note, and regenerated the PNG/PDF without changing the underlying CWT products or significance results.

- **QPO** · 2026-09-07 16:00 · [uncommitted] Audit the 20260817 WCDA release against the ETO handoff: package checksums pass and all 22 local CSV hashes match; ten AGN use fixed PL gamma=2.6 at 3 TeV, Crab uses the public Example1 three-component model, and all DGE states are off; row-level response paths agree with source branches, with 83 periods in 2-day and 82 in 8-day (no T012 label); distinguish this release from the separate source-specific/DGE-policy rebuild registry, with per-bin production YAML/logs and ROOT contents outside this audit.
- **QPO** · 2026-09-07 16:07 · [uncommitted] Back up the current presentation and 37 referenced images in Git commit 6f7acc7; refine the academic-paper layout with shorter headings, larger figure areas, compact cadence switches, one-line conclusions, retained literature, and expandable analysis details; check all 24 slides at 1440×900 and 763×773 and verify cadence switching and detail expansion.
- **QPO** · 2026-09-08 15:29 · [uncommitted] Complete the Mrk 421/Mrk 501 8-day spectral-index A/B/C experiment: reuse validated full-interval PL references, collect 1200/1200 successful IHEP fits (pilot 3467720, production 3467723), run eight common-mask CWT/WWZ screens with 200 AR(1) surrogates each on ETO array 65908 (both tasks COMPLETED), and add English result slides 10/16 plus the experiment record; mean B/A normalization is 0.7851/0.9198 while minimum WWZ global FAP stays 1.000/0.8955 in all four alternatives; verify figures, all image links and 26-page numbering, with browser layout preview blocked by file-URL policy; retain the failed YAML-order attempt 3467708 for audit and explicitly limit conclusions to 8-day fixed-PL statistical-index sensitivity.

- **QPO** · 2026-10-12 20:52 · [uncommitted] Download and SHA256/CRC-verify the IHEP detector-controls four-source 2day bundle (Crab, IC443, Blank175, J1952); retain the full release under data/raw/wcda and byte-identical standardized LC copies plus inventory under data/processed/wcda_2day/detector_controls_20261011; document CWT/WWZ reuse, input-format and sampling adaptations, boundary flags, and the unresolved J1952 model gate in work/detector_controls_2day_20261011_preparation.md; verify py310 imports without running periodicity or significance analysis.

- **QPO** · 2026-10-12 21:45 · [uncommitted] Complete strict four-source detector-control 2day CWT/WWZ diagnostics locally in py310 (Crab/IC443/Blank175/J1952 retained 799/676/309/540 bins, 10–600 d, 1000 full-grid masked AR(1) surrogates per source, at most two single-thread workers); preserve installed-libwwz results with parity-tested cached operators, save reproducible arrays/seeds/FAPs and four five-panel PNGs, and deliver the offline embedded-image HTML/Markdown report reports/detector_controls_2day_qpo_20261011.html; Crab 384.35 d has four-source FAP 0.003996 while other source minima are >=0.0999, subject to control-source, strict-selection and J1952 model limitations; verify 21 targeted tests, raw checksums, independently recomputed FAPs, images, TOC, zoom and responsive layout; no Git commit or external publication.

- **QPO** · 2026-10-13 11:46 · [uncommitted] Restore the canonical local QPO working tree to ETO /mnt/newdisk/shijie/QPO (2.25 GB including Git history, uncommitted/untracked code, local data, reports and presentations; omit only caches and macOS temporary files); verify transferred file checksums and git fsck, retain qpo-toolkit at 68ffffd, and update AGENTS.md with the new disk path; old /mnt/mydisk is unmounted and empty, so ETO-only lost-disk files are not recovered; legacy fermi_mkn501_run absolute paths and scientific runtime remain unvalidated.

- **QPO** · 2026-10-13 11:46 · [uncommitted] Clarify AGENTS.md ETO storage policy: /mnt/newdisk replaces failed /mnt/mydisk, personal files live under /mnt/newdisk/shijie, and all new QPO work and backups use /mnt/newdisk/shijie/QPO; synchronize the instructions and log to ETO.

- **QPO** · 2026-10-13 12:04 · [uncommitted] Audit ETO post-disk-loss data recovery against the Mac and IHEP: SHA256-match all 2091 data/results files, verify saved LC row counts and IHEP release/ABC matches, identify missing Fermi PH/SC inputs, two background models, source registries, fitting provenance, MakeLC, ROI caches and simulation library; verify 1053 per-bin official configs and 1385 upstream references (LC0687 map absent), distinguish the changed master config and node-local J1952 link from disk-loss damage, and save the Chinese HTML/Markdown report plus JSON evidence under reports/eto_data_recovery_20261013; inspect the rendered report and synchronize only report/log artifacts to ETO; no science reruns, production data restore, dependency install or job submission.

- **QPO** · 2026-10-13 19:01 · [uncommitted] Audit PDC qposim Git and Mac synchronization scope: verify two live GitHub branches from Mac, confirm current PDC branch is 14 commits ahead with 54,579 untracked files and PDC GitHub SSH authentication failure; inventory approximately 2.3 TB of simulation products, 75 GB of Git metadata including 67.51 GiB temporary objects, and 1.50 GB of candidate code/report/table files excluding tools and caches; save Markdown/HTML findings under reports/qposim_sync_audit_20261013, document report dependencies, symlinks, nested worktrees and local conflict handling; no synchronization, push, history rewrite, remote cleanup or simulation jobs.

- **QPO** · 2026-10-13 19:29 · [uncommitted] Synchronize the PDC qposim working-file snapshot to Mac qposim without local Git: SHA256-verify all 28,766 selected code/report/config/small-input files (2,210,553,358 bytes), preserve and checksum-back up all 167 original Mac files under archive/qposim_mac_before_sync_20261013, normalize 2,387 internal absolute links and record 619 remote-only dependencies; save manifests, nested Git provenance and transfer/verification logs under reports/qposim_sync_20261013, remove the verified temporary transfer copy; no PDC changes, push, large simulation data transfer or science reruns.

- **QPO** · 2026-10-13 20:10 · [uncommitted] Review only the supplied poster template and create three English LHAASO/TDLI layout concepts under prestation/poster/redesign_concepts, with navy/white recommended, white and burgundy alternatives, unchanged institutional logos, a comparison board, design notes and a self-contained HTML explainer; verify single-page PDFs, the recommended poster's exact 60 × 120 cm dimensions, English editable text, placeholder labeling and rendered layouts; preserve the original poster and scientific content; no LaTeX implementation, compilation or print release.

- **QPO** · 2026-10-13 20:58 · [uncommitted] Implement the user-selected minimal white poster as prestation/poster/minimal_template.tex: retain the reference-style SJTU seal, serif title/authors/TDLI affiliation and right-side LHAASO mark; use equal columns with Introduction, Methods, Conclusion and Summary only, and move the QR placeholder to the bottom right; compile with temporary local Tectonic after the standalone app compiler cannot resolve image assets, render and visually inspect the actual PDF, verify one English 60 × 120 cm page and no overflow/missing-glyph errors, SHA256-check the unchanged original main.tex, package the source/logo/PDF ZIP and record the superseded design preference; all scientific text, figures, contact details and QR remain placeholders.

- **QPO** · 2026-10-13 21:09 · [uncommitted] Restore the B-concept navy bands in minimal_template.tex: surround the reference-style white title panel with navy and place white contact text plus the bottom-right QR placeholder in the navy footer; paint at page level to avoid tikzposter margin clipping, preserve the four sections and original main.tex, rebuild and visually inspect the actual PDF/PNG, verify navy at both sides of the top/bottom bands and white in the body, clean compilation and 60 × 120 cm single-page geometry, and refresh the matching source/PDF ZIP and design notes.

- **QPO** · 2026-10-13 21:54 · [uncommitted] Tighten the approved minimal poster navy regions: reduce header/footer heights from 16/8.8 cm to 14.6/7.2 cm, reduce title padding and the bottom-right QR placeholder from 5.5 to 4.8 cm, and preserve the reference-style title and four-section body; recompile and visually inspect the actual PDF/PNG, verify clean compilation, single-page 60 × 120 cm geometry and blue/white regions, refresh the byte-matched source/PDF ZIP, and update design notes.

- **QPO** · 2026-10-13 22:04 · [uncommitted] Save the approved compact navy-band poster to the independent git@github.com:Pluto235/poster.git repository, cloned at /Users/luoji/Documents/projects/poster; copy and SHA256-verify only the final LaTeX/PDF/PNG/ZIP and two required logos, add a concise README and LaTeX build-artifact ignore rules, independently compile from the new checkout and verify 60 × 120 cm geometry and package links/integrity, then commit 87ca952 and push main; verify the live remote HEAD matches the local commit and the poster checkout is clean; reference poster and research data remain outside this publication.

- **QPO** · 2026-10-14 12:52 · [uncommitted] Review the independent poster template, official WCDA survey and detector-control reports, matched Fermi screening, and local qposim dynamics/radiation reports for three LHAASO poster content recommendations: foreground the survey-level non-detection and control-source systematics, distinguish jet dynamics and exploratory single-snapshot SSC from confirmed gamma-ray QPOs, and prioritize sensitivity-qualified synthetic-observation/injection-recovery comparisons as proposed follow-up; no poster edits, science reruns, remote-state verification or publication.

- **QPO** · 2026-10-14 13:08 · [uncommitted] Fill the existing LHAASO/TDLI template into an English content-review draft at sibling poster/drafts/lhaaso_qpo_v1: include the WCDA candidate table and four unchanged result figures (Mrk 501, Crab, jet-displacement WWZ, Mrk 421-like Syn+SSC), label missing author inputs A1-A6 and unfinished analyses B1-B3 in red, and retain the original template; compile with local Tectonic after the app compiler cannot resolve companion images, inspect the final PNG, verify one 60 x 120 cm PDF with embedded fonts, no TeX layout warnings or off-page text, 72 pt footer clearance, and source-asset hashes; save editable LaTeX, PDF/PNG, provenance and validation JSON; no science reruns, commit, push or print release, and original composite labels remain to be enlarged for printing.

- **QPO** · 2026-10-14 13:14 · [uncommitted] Restore the original transparent white TDLI building drawing at 11.2 cm width beside the bottom-right QR code and center contact information in the 7.2 cm footer; inspect official TDLI blue/general PPT downloads, preserve the supplied white artwork unchanged, rebuild and visually check the single-page 60 × 120 cm PDF with no TeX layout errors, refresh both local template copies and the self-contained ZIP, and push poster/main b396627 with matching remote HEAD; keep the reference poster and existing content draft untouched.

- **QPO** · 2026-10-14 13:22 · [uncommitted] Move the poster building drawing to the left footer, retain centered Contact and right QR, and add the unmodified official TDLI white logo above Contact; use page-level footer placement to prevent margin clipping, verify one 60 × 120 cm page with unchanged text and pixel-identical rendering above the footer, refresh both template copies and the complete ZIP, and push poster/main 4dd886e with matching remote HEAD; preserve existing content drafts and the original reference poster.

- **QPO** · 2026-10-14 13:27 · [uncommitted] Crop the repeated SJTU seal and transparent edges from the footer TDLI logo using LaTeX trim/clip, center the remaining bilingual institute name at 11 cm width above Contact with clear spacing, and preserve the full official PNG; inspect PDF/PNG, verify one 60 × 120 cm page with unchanged text and rendering above the footer, refresh both template copies and the self-contained ZIP, and push poster/main 710a1fb with matching remote HEAD; existing content drafts remain untouched.

- **QPO** · 2026-10-14 13:30 · [uncommitted] Reduce the cropped bilingual TDLI footer name from 11 to 9 cm while preserving its center and Contact placement; compile and inspect the PDF footer, verify 60 × 120 cm geometry, unchanged text and upper layout, refresh both template copies and ZIP, and push poster/main e4d362c with matching remote HEAD.

- **QPO** · 2026-10-14 13:37 · [uncommitted] Synchronize the QPO poster draft footer from the verified poster origin/main e4d362c template: copy the TDLI building and white institute-name assets, adopt the page-anchored left-building/center-logo-and-contact/right-QR layout, retain red A5/A6 placeholders and center the draft label; verify the draft body is byte-identical, compile and inspect the full PDF plus footer crop, confirm 60 x 120 cm single-page geometry, no TeX layout warnings or off-page text, 72 pt body/footer clearance and all nine asset hashes; update provenance and validation JSON, with no Git commit/push or science changes.

- **QPO** · 2026-10-14 13:47 · [uncommitted] Fill the QPO poster draft authors as Shijie Liu and Hao Zhou with the shared TDLI/SJTU affiliation, replace the contact placeholder with the supplied email, and display the supplied WeChat QR using an exact LaTeX viewport with a four-module white quiet zone; preserve original QR pixels and byte-identical scientific columns, remove completed A1/A5/A6 placeholders, recompile and visually inspect the full poster/footer, verify single-page 60 x 120 cm geometry, no TeX layout warnings, all ten asset hashes and exact QR payload-hash agreement between the original and 90 dpi PDF rendering via Apple Vision; update provenance/validation records, with no Git push or physical print/phone-scan test.

- **QPO** · 2026-10-14 14:05 · [uncommitted] Replace poster draft Figure 1 with the exact Mrk 421 bright-window figure from the WCDA presentation slide 8 (MJD 59800–60500); highlight low-significance structures near 50, 100 and 150 d as a harmonic-like period pattern, explicitly leave harmonics unconfirmed, and retain the 147.3 d peak full-search FAP 0.388. Update figure provenance and validation records; compile and visually inspect the PDF, verify one 60 × 120 cm page, 74 pt footer clearance, all 11 asset hashes and no TeX layout warnings. No periodicity analysis rerun or Git commit/push.

- **QPO** · 2026-10-14 14:20 · [uncommitted] Refine the poster Mrk 421 slide-8 WWZ significance from 200 to 1000 Gaussian AR(1) surrogates on ETO (Slurm 66075, completed 0:0), preserving the 349-bin light curve, 240 × 267 grid, seed and analytic CWT references; reuse CachedWWZ with observed/null parity below 4e-13, exactly reproduce the first-200 tail counts and thresholds, save all spectra/seeds and provenance, and independently verify FAPs 0.972028/0.478521/0.379620 at 50.8/96.4/147.3 d. Replace poster Figure 1 and its FAP caption, explicitly distinguish the unchanged 200-draw survey table, compile and visually verify one 60 × 120 cm page with 74 pt footer clearance and no layout warnings; cached-kernel tests pass (2), no commit/push or broader survey rerun.

- **QPO** · 2026-10-14 14:25 · [uncommitted] Rewrite the poster Scientific question from the supplied QPO proposal (pages 1 and 3): motivate complementary TeV/GeV monitoring and transient Mrk 421 searches, and pose current-driven kink instability as a hypothesis connecting WCDA, RMHD and synchrotron/SSC diagnostics. Preserve sections 2–4, the 1000-surrogate statistics, figures, authors and footer; retain a concise red A2 title/collaboration reminder. Record proposal provenance, compile and visually verify the 60 × 120 cm single-page PDF, all 11 asset hashes, no TeX warnings and 65 pt footer clearance; no analysis rerun or Git push.

- **QPO** · 2026-10-14 14:58 · [uncommitted] Analyze the four-source detector-control report, saved light curves and J1952 frozen model for three annual-structure hypotheses: seasonal response residuals, transit solar-time coupling, and background/model/selection effects; verify retained-bin flux/error medians and explain why Blank cannot exclude multiplicative efficiency modulation and IC443 non-detection needs sensitivity calibration; save a new sourced Markdown/HTML supplement, check all eight panels and local links with zero STE warnings, and retain ANALYZED status. Browser policy blocks file:// preview, so no visual browser verification, periodicity rerun, source refit, weather/calibration inspection, phase comparison or injection recovery.

- **QPO** · 2026-10-14 16:30 · [uncommitted] Apply the approved 3-column x 4-row sample list to sibling poster/drafts/lhaaso_qpo_v1/poster.tex: list the actual ten AGN and Crab control, emphasize Mrk 421/Mrk 501, and compact section-2 spacing without changing the declared body size or figure sizes. Recompile and inspect the full PDF, table and footer; verify all 11 source IDs against the saved survey, one 60 x 120 cm page, 13.43 pt footer clearance, no off-page text or TeX layout warnings, and all 11 unchanged asset hashes. Refresh PDF/PNG and provenance/validation records; no scientific rerun, Git commit/push or print release.

- **QPO** · 2026-10-14 16:57 · [uncommitted] Remove the complete References and result provenance section from sibling poster/drafts/lhaaso_qpo_v1 and remove the final-references instruction from printing TODO A4, retaining sources.json and all source assets. Recompile and visually inspect the PDF/PNG; verify the removed text is absent, one 60 x 120 cm page, 139.15 pt footer clearance, no off-page text or TeX layout warnings, and all 11 asset hashes unchanged. Refresh provenance/validation records; no scientific rerun or Git commit/push.

- **QPO** · 2026-10-14 19:27 · [uncommitted] Remove only the WWZ parenthetical (200 per survey curve; 1000 for Fig. 1) from the poster main significance paragraph; verify the rest of poster.tex matches the preceding version by SHA256 reconstruction. Recompile and inspect the PDF/PNG, verify the selected text is absent, Figure 1 retains its simulation-count caption, one 60 x 120 cm page, 139.15 pt footer clearance and no off-page text or TeX layout warnings; refresh provenance/validation records. No science rerun or Git commit/push.

- **QPO** · 2026-10-14 19:42 · [uncommitted] Specify Figure 1 WWZ peak periods as 50.8, 96.4 and 147.3 d in the poster caption, verified against the saved 1000-surrogate candidate CSV; retain approximate 1:2:3 period spacing with unconfirmed harmonics. Verify all other poster.tex content is unchanged by SHA256 reconstruction, recompile and inspect the PDF/PNG plus caption crop, and confirm one 60 x 120 cm page with no off-page text or TeX layout warnings; refresh provenance/validation records. No scientific rerun or Git commit/push.

- **QPO** · 2026-10-14 22:00 · [uncommitted] Complete Crab poster Figure 2 refinement on ETO Slurm 66077 (COMPLETED 0:0, 22m40s): increase WWZ grid from 80 x 317 to 240 x 1263 and recompute 1000 masked AR(1) surrogates with unchanged 799/803 strict observations, CWT arrays, alpha and seeds. Add opt-in existing yellow map guides through detector_controls_2day_qpo.py, verify 15 targeted tests and observed/null full-grid parity 6.02e-11/7.47e-12, and independently recompute FAP/percentile references. WWZ peak shifts from 384.345 to 373.168 d (CWT 374.002 d); full-search/four-source FAPs remain 0.000999/0.003996. Export seam-free 300 dpi PNG and PDF with vector labels/guides, retain old products, replace poster Figure 2 and synchronize only Crab body/caption; compile and inspect 60 x 120 cm PDF with 139.15 pt footer clearance, no off-page text/layout warnings and all 11 asset hashes. Save run/export provenance and reproduction notes; no other control rerun, Git commit/push or physical-QPO claim.

- **QPO** · 2026-10-14 22:59 · [uncommitted] Replace poster B1 with an English discussion linking qualitative red-noise/faint-flux sensitivity limits, the unconfirmed Mrk 421 flare-time harmonic-like pattern, and a proposed current-driven kink origin for short-lived modulation. Scope TeV non-detection to this catalog search after checking the historical Mrk 501 TeV QPO candidate paper astro-ph/9907205; avoid a universal no-prior-discovery claim or a quantified/causal sensitivity result. Verify all other poster.tex content is unchanged by SHA256 reconstruction, compile and inspect PDF/PNG and the discussion crop, confirm one 60 x 120 cm page, 16.59 pt footer clearance, no off-page text/layout warnings and all 11 unchanged asset hashes; update provenance/validation records. No scientific rerun or Git commit/push.

- **QPO** · 2026-10-15 19:43 · [uncommitted] Clarify source identities in the annual-control supplement: Crab and J1952/DA495 are PWNe, while IC443 is an interacting SNR with pion-decay evidence. Explain why Crab as a bright TeV standard candle gives a strong systematics clue, why spatial extension does not average away a common annual efficiency modulation, and why weak-bin precision alone cannot explain IC443 non-detection given J1952’s lower median flux/error and unresolved ROI model. Verify primary references, saved precision ratios and all eight generated HTML panels/local links with zero STE warnings; no new source fits, annual-amplitude estimates, injection recovery or browser preview.

- **QPO** · 2026-10-15 19:53 · [uncommitted] Consolidate Mac and ETO QPO research work for GitHub main, retaining main history and the separate qpo-toolkit branch; recover ETO-only aligned CSV and job logs, preserve overwritten ETO files under /mnt/newdisk/shijie/QPO-sync-backup-20261015, and synchronize active research files with checksum checks. Exclude independent qposim, archives, caches and machine-specific Python dependencies from cross-machine sync; retain Git heavy-data exclusions. Validation: tests/ gives 48 passed and 12 failed due to absent source-model registry and related inputs; root pytest additionally cannot collect the uninstalled vendored emmanoulopoulos package. No scientific reruns or fixes.

- **QPO** · 2026-10-15 22:10 · [uncommitted] Update AGENTS.md to make the local Mac the canonical QPO project, route light-curve generation to IHEP using /home/lhaaso/liushijie/tutorial/wcda_v1_official_lc_pipeline.md, restrict ETO to synchronization, and leave QPO detection and qposim paused unless explicitly requested, with qposim execution on PDC. Retain pipeline references and historical path notes; check document consistency and whitespace only, with no remote connection, scientific rerun, synchronization, commit or push.
