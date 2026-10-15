# WCDA Cod Official LC 10-Source QPO Survey Execution Plan

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: plan
- Origin Date: 2026-08-04
- Verification Status: `UNVERIFIED` for the full experiment; official input and three-bin interface smoke are `VERIFIED`
- Version Label: `official_qpo_plan_v1`
- Execution Host: ETO (`/home/server/projects/QPO`)
- WCDA Compute Host: IHEP, remotely orchestrated from ETO
- Frozen Decisions: user-confirmed during the 2026-08-04 design interview

## Objective

Rebuild the historical 10-source WCDA AGN periodicity survey with the official
Cod daily-map-derived 2/8/32-day light-curve configurations and their released
period-dependent responses. Produce auditable profile-likelihood light curves,
run the frozen exploratory periodicity protocol, validate detector-time
systematics with controls, and write a new self-contained Chinese HTML report.

This plan supersedes the old weekly quick-look workflow. The old report is a
historical baseline only; its peaks and AR(1) significance values are not inputs
to the new statistical conclusions.

## Scientific Scope And Claim Boundary

### Fixed source sample

1. Mrk 421 (`Mkn421`)
2. Mrk 501 (`Mkn501`)
3. 1ES 1959+650 (`1ES1959p650`)
4. 1ES 1727+502 (`1ES1727p502`)
5. 1ES 2344+514 (`1ES2344p514`)
6. BL Lacertae (`BLLacertae`)
7. NGC 1275 (`NGC1275`)
8. M 87 (`M87`)
9. 4C +42.22 (`4C_p42d22`)
10. IC 310 (`IC310`)

### Frozen analysis decisions

- Data interval: official Cod coverage only, 2021-03-08 through 2025-07-31.
- Primary cadence: official 8-day LC configurations, 200 bins per source.
- Auxiliary cadences: full independent 2-day survey (803 bins per source) and
  full 32-day survey (50 bins per source). The later decision to scan every
  source supersedes the earlier candidate-only 2-day idea.
- Period ranges: 50-600 days for 2-day and 8-day; 128-600 days for 32-day.
- Use all official LC bins. Do not delete bins based on flux, TS, exposure, or
  periodogram appearance.
- Fit all seven WCDA nhit bins jointly. Do not add energy-resolved searches.
- Each source uses a fixed source-specific spectrum. Priority is published
  LHAASO spectrum, then full-interval fit, then fixed Gamma=2.6 if unconstrained.
- Use the official public DGE template for every target and control ROI supported
  by public `Src_Main`. Per the user-approved 2026-08-05 amendment, explicitly
  set `DGE.Active: 0` where the ROI centre has `|b| > 15` degrees and public
  `Src_Main` rejects active DGE; record the per-ROI policy in the registry,
  immutable manifests, and final report.
- Keep the historical single-target ROI model. NGC 1275 and IC 310 remain
  source-confusion-sensitive; report their results as ROI variability.
- Preserve a per-bin flux profile likelihood. Upper limits are display products,
  not ordinary measurements and not replacements for low-TS bins.
- Discovery methods: likelihood-ratio periodogram, CWT, and WWZ. They are
  method-specific analyses, not a combined statistic.
- Red-noise null families: single power-law PSD, bending power-law PSD, and
  CARMA(1,0), with parameter uncertainty and the real sampling/measurement model.
- Simulations: exactly 10,000 per source, cadence, and null family. The same
  simulated light curves may be evaluated by all three methods.
- Each method reports its own frequency-global p-value. Do not correct across
  methods or across the 10 sources, and do not select the minimum p-value as a
  combined significance.
- Do not assign detection, candidate, or hint labels. Rank and describe results.
- Cycle interpretation: at least 4 cycles is evidence-eligible morphology;
  3-4 cycles is a finite-cycle peak; fewer than 3 cycles is long-term variation.
  This is descriptive and does not override the exploratory claim boundary.
- Cross-cadence agreement: absolute frequency difference no larger than 1/T,
  where T is the common time baseline.
- Raw light curves are primary. Trend/detrended variants are sensitivity checks.
- Fermi-LAT is literature context only; do not recompute or combine it with WCDA
  p-values.
- Controls: Crab, one catalog-vetoed same-declination blank field per target,
  and response-period-boundary diagnostics. Show controls but do not use them to
  empirically correct target light curves.
- Final product: Chinese self-contained HTML, English abstract, machine-readable
  CSV/JSON outputs.

Because method-level and source-level trials are intentionally not corrected,
the final report is an exploratory survey and must not claim a WCDA QPO
detection. This limitation is a frozen design choice, not an implementation bug.

## Runtime Topology

The agent and canonical working tree remain on ETO:

```text
/home/server/projects/QPO
```

ETO owns:

- source integration and tests;
- result manifests and lightweight light-curve/profile products;
- CWT, WWZ, likelihood-periodogram and red-noise simulation jobs;
- Slurm execution for large periodicity/simulation workloads;
- report generation, integrity checks and Git history.

IHEP owns:

- access to official EOS daily maps and official v1.0 LC DataConfigs;
- `Src_Main`, public DGE templates and period response files;
- all WCDA ROOT/forward-folding/profile-likelihood work;
- HTCondor job submission, logs and primary fit outputs.

The ETO agent may orchestrate IHEP over the established SSH path, but it must not
run bulk ROOT work on an IHEP login node and must not copy the official sky-map
collection to ETO. Transfer only code, YAML/CSV/JSON manifests, compressed logs,
figures and final profile-likelihood products needed by the ETO analysis.

## Verified Baseline

- Official daily maps: 1592 maps, 2021-03-08 to 2025-07-31, 83 periods, 15
  missing natural days.
- Official v1.0 LC configurations: 803 two-day, 200 eight-day, and 50 32-day
  bins.
- Official LC master config:
  `/home/lhaaso/hushicong/public/v1.0/config/Data/WCDA/Cod/LCData_20210305_20250731.yaml`.
- T001, T048 and T083 formal 2-day smoke tests passed for Mrk 421.
- Current IHEP implementation:
  `/home/lhaaso/liushijie/QPO/MakeLC/standard_flux_lc.py`.
- Current limitation: it hard-codes Gamma=2.6, has DGE disabled, and only
  harvests point estimate/error/TS rather than a full profile likelihood.
- Current ETO periodicity code implements quick-look CWT/WWZ and AR(1)
  significance. It does not implement this plan's likelihood periodogram,
  composite nulls, low-TS likelihood treatment, or 2/8/32-day schema.

## ETO Code Reuse Audit

The following existing ETO files are reference inputs. Audit their dependencies
and tests before editing them in place:

- `src/methods/periodicity.py`
- `src/pipeline/agn_strict_flux_weekly_periodicity.py`
- `src/pipeline/strict_flux_weekly_significance.py`
- `src/pipeline/weekly_qpo_local_significance.py`
- `src/pipeline/periodicity_v1.py`
- `src/pipeline/build_agn_wcda_weekly_survey_report.py`
- `src/simulation/generate_wcda_weekly_sims.py`
- `src/utils/source_registry.py`
- `src/utils/project_paths.py`
- `src/methods/emmanoulopoulos/` including its license and tests
- `reports/agn_wcda_weekly_survey_report.{md,html}` as historical presentation
  reference only

Do not preserve obsolete fixed row counts, weekly-only filenames, AR(1)-only
logic, TS-based row filtering, or the assumption that symmetric `N0_err` is the
complete measurement likelihood.

## Durable Artifacts

Use these target locations on ETO unless an existing path authority requires a
more specific child path:

| Artifact | Path | Success criterion |
|---|---|---|
| Frozen protocol | `docs/official_daily_qpo_execution_plan.md` | This file remains the authority |
| Goal status ledger | `work/official_daily_qpo_goal_status.md` | Timestamped phase, jobs, blockers and next action |
| IHEP handoff manifest | `work/ihep_official_lc_handoff.json` | Host paths, hashes, schemas and transfer state |
| Source spectral registry | `data/config/official_qpo_source_models.yaml` | 10 targets + Crab + 10 blank fields, provenance included |
| Fit manifest | `data/processed/official_qpo/manifests/fit_manifest.csv` | One row per expected fit, response provenance present |
| Light curves | `data/processed/official_qpo/lightcurves/` | 2/8/32-day CSV or Parquet for every target |
| Profiles | `data/processed/official_qpo/profiles/` | Per-bin flux grid and Delta log L, schema validated |
| Controls | `data/processed/official_qpo/controls/` | Crab, 10 blank fields, boundary diagnostics |
| Periodicity products | `data/processed/official_qpo/periodicity/` | Method/null/cadence/source outputs complete |
| Simulation manifests | `data/simulations/official_qpo/` | Seeds, null parameters, batch completion and maxima |
| Summary tables | `reports/data/official_qpo/` | CSV/JSON values used by the report |
| Final report | `reports/agn_wcda_official_lc_qpo_survey.html` | Self-contained, links/checks verified |
| Report source | `reports/agn_wcda_official_lc_qpo_survey.md` | Chinese body and English abstract |

Large ROOT files, temporary grids, `.out/.err/.log`, partial files and simulation
arrays are production intermediates and must stay in dedicated job/output areas,
not be committed as source.

## Execution Phases And Gates

### Phase 0 - Start Goal And Establish State

- [ ] Read ETO `AGENTS.md`, `CLAUDE.md`, this plan, and the IHEP status report.
- [ ] Record existing dirty files and do not overwrite/revert them.
- [ ] Create `work/official_daily_qpo_goal_status.md` with a phase checklist.
- [ ] Verify ETO-to-IHEP non-interactive connectivity from the actual tmux/Codex
  environment. A probe failure in a nested sandbox is not proof that the host
  connection is unavailable; inspect DNS, SSH config and the established tunnel.
- [ ] Verify IHEP schedds and ETO Slurm without submitting production work.

Gate 0 passes when both environments and the transfer direction are demonstrated
with read-only commands and exact host paths are recorded.

### Phase 1 - Synchronize Lightweight IHEP Context To ETO

- [ ] On IHEP, inspect all applicable `AGENTS.md` files before copying code.
- [ ] Pull only the current `MakeLC/standard_flux_lc.py`, the official rebuild
  status, small smoke manifests/results, and any direct helper it imports.
- [ ] Record source path, modification time and SHA-256 in the handoff manifest.
- [ ] Do not copy job directories wholesale or copy ROOT maps to ETO.
- [ ] Diff IHEP code against ETO architecture and port reusable logic into the
  ETO `src/` layout; do not make absolute IHEP paths the ETO path authority.

Gate 1 passes when the ETO tree can parse all official 2/8/32-day manifests from
a lightweight fixture and the provenance record is complete.

### Phase 2 - Freeze Source, DGE And Control Configurations

- [ ] Create the 10-source spectral registry.
- [ ] Verify each published LHAASO model against an authoritative source. Mark
  unresolved values `UNVERIFIED`; never invent a citation or parameter.
- [ ] Run full-interval spectral fits only for sources lacking a usable published
  model. If an index is unconstrained, apply the frozen Gamma=2.6 fallback.
- [ ] Select one same-declination blank field per source using a deterministic
  algorithm and catalog veto fixed before inspecting control periodograms.
- [ ] Build a public-DGE configuration from
  `/home/lhaaso/hushicong/public/DGE_Template`; do not retain obsolete private
  paths from the tutorial example.
- [ ] Keep the target-only spatial model, including the accepted NGC 1275/IC 310
  source-confusion limitation.

Gate 2 passes when every source/control has coordinates, spectral model,
provenance, response branch, DGE path and validation status in one registry.

### Phase 3 - Implement And Validate Profile Likelihood

- [ ] Inspect public `Src_Main` source/config behavior for `FluxPoint`, `FluxUL`,
  fixed-parameter fits and the reported objective value.
- [ ] Prefer an official profile/scan interface if it exposes the needed
  likelihood. Otherwise implement a deterministic fixed-F0 grid wrapper without
  modifying the public executable in place.
- [ ] Define a profile schema containing source, cadence, LC id, MJD, F0 grid,
  log likelihood or Delta log likelihood, MLE, bounds, Tobs, response period,
  response slot/file, DataConfig and software/config hashes.
- [ ] Make the grid adaptive only by a predeclared algorithm: bracket the MLE,
  cover both sides sufficiently, refine near the minimum, and flag profiles that
  touch the outer grid boundary.
- [ ] Preserve physical non-negative source flux. Explicitly test the boundary
  behavior for low-TS bins.
- [ ] Add unit tests for profile parsing, normalization and schema validation.
- [ ] Run at most three local IHEP smoke bins spanning T001, T048 and T083.
- [ ] Confirm the profile MLE matches the ordinary fit within tolerance and the
  grid covers the required Delta log L range.

Hard Gate 3: do not submit full light-curve production until 3/3 profiles are
finite, correctly bracketed, reproducible and consistent with `ParRes.yaml`.
Do not silently fall back to symmetric Gaussian errors.

### Phase 4 - Prepare HTCondor Production

- [ ] Generalize the IHEP job generator to source-specific spectra, the recorded
  public-DGE policy, controls, and 2/8/32-day official LC configurations.
- [ ] Generate immutable fit and profile manifests before submission.
- [ ] Validate non-empty inputs, exact expected counts, writable output/log
  directories and enough disk quota.
- [ ] Discover a usable schedd at submission time. Do not assume schedd11 is
  available merely because it was used previously.
- [ ] Start with a small HTCondor pilot covering bright, faint, DGE, blank-field,
  early/middle/late response and all three cadences.
- [ ] Derive runtime/memory/disk requests from pilot logs. The historical fit
  default is 2500 MB memory and 2000 MB disk, not a guaranteed profile-grid value.

Gate 4 passes when the pilot has no held jobs, outputs validate, profile coverage
is adequate, and resource requests are evidence-based.

### Phase 5 - Run Official Light-Curve Production

Expected target fits before profile-grid multiplication:

| Cadence | Bins/source | Sources | Fits |
|---|---:|---:|---:|
| 8-day | 200 | 10 | 2,000 |
| 32-day | 50 | 10 | 500 |
| 2-day | 803 | 10 | 8,030 |
| Target total | | | 10,530 |

The 8-day Crab plus 10 blank-field controls add about 2,200 base fits. The
minimum base workload is therefore about 12,730 fits, before any explicit F0
grid multiplication or DGE-off diagnostic subset.

- [ ] Run 8-day targets and controls first.
- [ ] Validate and merge 8-day outputs before 32-day submission.
- [ ] Validate and merge 32-day outputs before 2-day submission.
- [ ] Monitor `condor_q -global`, held reasons, output counts and missing profiles.
- [ ] Never run bulk ROOT loops or bulk retries on an IHEP login node.
- [ ] Retry only diagnosed failed rows; preserve the original failure manifest.
- [ ] Copy only validated lightweight merged products to ETO.

Hard Gate 5 requires exact row coverage for every official LC configuration,
explicit status for every failed/missing row, no unbounded profile, complete
response provenance, and no silent row removal.

### Phase 6 - Build The ETO Analysis Package

- [ ] Refactor cadence-agnostic input/schema handling under `src/`.
- [ ] Keep CWT/WWZ reusable kernels but remove weekly-only constants and fixed
  row-count assumptions.
- [ ] Implement a likelihood-ratio periodogram that consumes per-bin profiles.
- [ ] For observed CWT/WWZ, use the per-bin MLE series and documented uncertainty
  representation. State explicitly that these transforms do not consume the full
  profile in the same way as the likelihood periodogram.
- [ ] Compute and save the sampling-window spectrum for each source/cadence.
- [ ] Enforce 50-600 d for 2/8-day and 128-600 d for 32-day in one config.
- [ ] Apply cone-of-influence/edge diagnostics to CWT outputs.
- [ ] Add raw-primary and frozen trend-sensitivity variants without selecting
  whichever gives the smallest p-value.
- [ ] Add deterministic tests on synthetic white noise, red noise, injected
  periodicity, missing bins and boundary-dominated profiles.

Gate 6 passes when deterministic synthetic tests recover expected periods within
the stated frequency resolution and null-only tests show calibrated behavior.

### Phase 7 - Fit Null Models And Run Simulations On ETO Slurm

- [ ] Fit single power-law PSD, bending power-law PSD and CARMA(1,0) separately
  for every source/cadence, propagating continuum parameter uncertainty.
- [ ] Preserve the source flux distribution where the model requires it and
  forward-model the actual sampling and measurement/profile-likelihood process.
- [ ] Generate exactly 10,000 simulations per source/cadence/null family.
- [ ] Use deterministic seed derivation from an immutable master seed plus
  source/cadence/null/simulation index; record the formula and all batch ranges.
- [ ] Evaluate likelihood periodogram, CWT and WWZ on the same simulation set.
- [ ] Compute each method's frequency-global p-value from the maximum statistic
  over its frozen search range, using `(exceedances + 1) / (N + 1)`.
- [ ] Report the binomial/Monte Carlo interval and minimum resolvable p-value.
- [ ] Do not calculate or imply method-combined or 10-source survey p-values.
- [ ] Submit large simulation batches through Slurm, with checkpointed outputs,
  per-batch manifests and reproducible collection.

Estimated scale for 10 targets across three cadences is 900,000 simulated light
curves and 2.7 million method evaluations. Running the 11 eight-day controls with
the same three nulls adds 330,000 light curves and 990,000 method evaluations.

Hard Gate 7 requires all expected batches or an explicit failure ledger, unique
seed coverage, finite maxima, reproducible collection, and no missing source /
cadence / method / null combination.

### Phase 8 - Controls And Robustness

- [ ] Produce Crab, 10 blank-field and response-boundary light curves and plots.
- [ ] Run the same 8-day periodicity and null workflow for the controls.
- [ ] Show coincident target/control/window frequencies without correcting the
  target light curves.
- [ ] Compare raw and trend-sensitivity results.
- [ ] Compare cadence peaks using `|f1 - f2| <= 1/T`.
- [ ] Report cycle counts and mark <3-cycle results as long-term variation.
- [ ] Compare new official products to old weekly results only as a historical
  reproducibility/response-change diagnostic.

Gate 8 passes when every ranked target peak has window, cadence, trend, control,
response-boundary and cycle-count context.

### Phase 9 - Report, Integrity Audit And Finalization

- [ ] Generate machine-readable master tables first; render report values only
  from those tables.
- [ ] Write Chinese main text and an English abstract.
- [ ] Include data provenance, response mapping, source spectra, DGE setup,
  profile-likelihood method, all null models, exact simulation counts, controls,
  negative results, limitations and reproduction commands.
- [ ] Present each source/method/null/cadence global p-value separately.
- [ ] Do not use `detection`, `candidate`, `hint`, or sigma-equivalent language
  that bypasses the frozen exploratory claim boundary.
- [ ] State the lack of method/source trials correction prominently.
- [ ] State NGC 1275/IC 310 source confusion and the no-control-correction choice.
- [ ] Build a self-contained HTML and verify all embedded figures/tables render.
- [ ] Audit every report number against CSV/JSON, every citation against an
  authoritative source, and every claim against the frozen protocol.
- [ ] Perform an independent methodology review and revise before finalization.
- [ ] Append a factual session summary to `work/log.md` using the repository's
  devlog convention.

Hard Gate 9 passes only when the report integrity audit has zero unresolved
number/citation mismatches and all required artifacts are present.

## Monitoring And Progress Contract

`work/official_daily_qpo_goal_status.md` is the durable heartbeat. Update it:

- at the start and end of every phase;
- after every submission, completion, hold/failure diagnosis and merge;
- whenever a frozen decision, expected output count or resource estimate changes;
- before ending any agent turn while work remains.

Each update must include timestamp, current phase, completed checks, active job
IDs and host, output counts, failures/holds, decision needed, next action and the
exact verification command last run. Do not mark many stale checklist items done
in one retrospective update.

During active jobs, the agent should monitor boundedly and communicate useful
changes. Do not spam unchanged queue snapshots. Never leave a live command or
monitor session uncollected when ending a turn.

## Decision And Escalation Rules

The agent may decide ordinary implementation details when they preserve this
protocol and are supported by tests. It must stop and ask the user before:

- changing any frozen scientific decision;
- replacing profile likelihood with point estimates/symmetric errors;
- changing the source list, cadence, search range, null family or simulation count;
- adding method/source trial correction or applying a candidate threshold;
- applying a Crab/control correction to target fluxes;
- changing the single-target ROI choice;
- moving bulk official maps off IHEP;
- performing destructive cleanup, publishing, committing or pushing unless
  separately authorized.

When a technical blocker appears, attempt scoped diagnosis and at least two
independent safe alternatives. Do not infer scientific permission from a
software limitation. Record unresolved blockers in the status ledger.

## Required Verification Commands

At minimum, adapt and run these checks as implementation evolves:

```bash
# ETO
cd /home/server/projects/QPO
python -m compileall src
pytest -q
git status --short

# IHEP, invoked remotely from ETO after connectivity validation
cd /home/lhaaso/liushijie/QPO
python -m compileall MakeLC
condor_status -schedd -af Name Machine TotalRunningJobs TotalIdleJobs TotalHeldJobs
condor_q -global "$USER"
```

Commands that process the full survey must be Slurm jobs on ETO or HTCondor jobs
on IHEP. Only 1-3-bin/file smoke tests may run interactively on login nodes.

## Definition Of Done

The persistent goal is complete only when all of the following are true:

1. Frozen protocol, source registry and provenance manifests are present.
2. Profile likelihood is validated and retained for every official target bin.
3. All 10 targets have validated 2/8/32-day products or explicit, justified
   failure rows; all official bins remain represented.
4. Crab and 10 blank-field 8-day controls plus response-boundary diagnostics are
   complete.
5. Three methods and three null models have the expected 10,000-simulation
   coverage for every required target/cadence combination.
6. Window, trend, cadence, cycle and control diagnostics are complete.
7. Master CSV/JSON tables exactly reproduce every number in the final report.
8. Chinese self-contained HTML, English abstract, report source and reproduction
   commands exist and pass integrity review.
9. Goal status and work log record the final verification commands and residual
   limitations.
10. No production process or required monitoring session remains running.

Do not mark the Goal complete because code was written, jobs were merely
submitted, or the report shell exists. Completion means the validated experiment
and final report are finished end to end.
