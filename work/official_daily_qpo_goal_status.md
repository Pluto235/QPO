# Official WCDA QPO Goal Status

## 2026-08-04 17:59 CST - Phase 0 started

- Current phase: Phase 0 - Start Goal And Establish State (`IN PROGRESS`).
- Goal: active persistent Goal created without a token budget.
- ETO canonical path: `/home/server/projects/QPO` resolves to `/mnt/mydisk/server/projects/QPO`.
- Git branch and initial worktree: `main...origin/main`; preserved untracked files are `docs/official_daily_qpo_execution_plan.md`, `docs/official_daily_qpo_rebuild_status.md`, and `docs/terra_official_qpo_goal_prompt.md`.
- Completed checks: fully read root `AGENTS.md`, root `CLAUDE.md`, and `docs/official_daily_qpo_execution_plan.md`; confirmed no production work has been submitted.
- Active jobs: none.
- Output counts: none; production has not begun.
- Failures or holds: none observed. IHEP connectivity and remote rebuild-status read remain unverified.
- Decision needed: none.
- Next action: perform read-only ETO-to-IHEP DNS, SSH configuration, remote hostname, repository-path, HTCondor, and lightweight status-report checks.
- Last verification command: `sed -n '231,500p' docs/official_daily_qpo_execution_plan.md`.

## 2026-08-04 18:00 CST - Phase 0 gate passed; Phase 1 started

- Current phase: Phase 1 - Synchronize Lightweight IHEP Context To ETO (`IN PROGRESS`).
- Goal: active persistent Goal; no production task has been submitted.
- Completed checks: `ihep` resolved and connected non-interactively to `lxlogin007.ihep.ac.cn`; the remote status report at `/home/lhaaso/liushijie/QPO/docs/official_daily_qpo_rebuild_status.md` was fully read. It verifies only the three official v1.0 2-day Mrk 421 interface smokes, not production profile likelihoods. IHEP exposes five schedds (`schedd06`, `schedd07`, `schedd10`, `schedd11`, `schedd12`); the current user has no jobs. ETO Slurm is queryable and has an available `main` partition. A remote-to-ETO `rsync --dry-run` of the status report succeeded.
- Exact paths: ETO `/home/server/projects/QPO` -> `/mnt/mydisk/server/projects/QPO`; IHEP `/home/lhaaso/liushijie/QPO`; official LC config `/home/lhaaso/hushicong/public/v1.0/config/Data/WCDA/Cod/LCData_20210305_20250731.yaml`; public DGE `/home/lhaaso/hushicong/public/DGE_Template`.
- Active jobs: none on either scheduler for this user.
- Output counts: no production output; one dry-run transfer item.
- Failures or holds: no user jobs. Global schedd held counts are informational only and are not attributable to this goal.
- Decision needed: none.
- Next action: locate and read every applicable IHEP `AGENTS.md`, then inspect the remote light-curve wrapper and its direct local imports before selecting a minimal, hash-recorded synchronization set.
- Last verification command: `rsync --dry-run --archive --itemize-changes -e 'ssh -o BatchMode=yes -o ConnectTimeout=12' ihep:/home/lhaaso/liushijie/QPO/docs/official_daily_qpo_rebuild_status.md work/ihep_phase0_remote_probe/`.

## 2026-08-04 18:04 CST - Phase 1 incremental synchronization

- Current phase: Phase 1 - Synchronize Lightweight IHEP Context To ETO (`IN PROGRESS`).
- Completed checks: no additional IHEP `AGENTS.md` files were found below `/home/lhaaso/liushijie/QPO`. The remote `MakeLC/standard_flux_lc.py` was audited for imports and official-LC/profile-relevant interfaces. It has no local Python helper imports. Its reusable portions are official LC DataConfig parsing, source-declination response selection, row manifests, and Condor chunk generation. Its hard-coded Gamma=2.6, disabled DGE, point-estimate merge, and fixed `schedd11` default are explicitly excluded from production reuse.
- Lightweight transfer: 8 selected source/status/smoke files were pulled, checksum-verified, and recorded in `work/ihep_official_lc_handoff.json`. No ROOT map, job directory, production log, or simulation array was transferred.
- Active jobs: none.
- Output counts: 8/8 handoff artifacts hash-verified; no production outputs.
- Failures or holds: none.
- Decision needed: none.
- Next action: acquire a compact, read-only 2/8/32-day official DataConfig fixture/index, then implement and test cadence-agnostic ETO parsing against it before assessing the Phase 1 gate.
- Last verification command: `python -m json.tool work/ihep_official_lc_handoff.json >/dev/null`.

## 2026-08-04 18:09 CST - Phase 1 gate passed; Phase 2 started

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`).
- Completed checks: synchronized 1,053 public YAML DataConfigs only (803 2-day, 200 8-day, 50 32-day; 1,046,670 bytes) from the official v1.0 source. `src/utils/official_lc.py` parses and validates contiguous IDs, all seven nhit bins, response periods and the declination-selected response slot. The parser test passed for all collections, and `src/pipeline/build_official_lc_config_manifest.py` created a 1,053-row ETO provenance manifest. The master config SHA-256 is `3d0d261c5e014dbc43d737fb805c2b7052e20bfb004fb4fb63e980272b8b2a7b`.
- Active jobs: none.
- Output counts: 1,053/1,053 official config rows parsed; 8/8 earlier smoke handoff artifacts remain hash-verified.
- Failures or holds: none.
- Decision needed: none.
- Next action: audit authoritative source-spectrum material already available in the repository and inspect the public DGE interface on IHEP before writing a frozen, provenance-bearing 10-source plus control registry.
- Last verification command: `PYTHONPATH=src pytest -q tests/test_official_lc.py`.

## 2026-08-04 18:23 CST - Phase 2 spectral-fit manifest prepared

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`).
- Completed checks: public 2LHAASO position association supplied seven source-specific published spectra within the predeclared 0.2-degree match radius; `bllac`, `ngc1275`, and `4c_p42d22` remain `UNVERIFIED` and require full-interval fits. The public DGE interface and tutorial parameterization were audited. The deterministic 1LHAASO-catalog-veto blank selection and pending-model registry passed local tests.
- Prepared IHEP work: `/home/lhaaso/liushijie/QPO/JOBs_official_qpo_spectral_fits/` contains an immutable three-row CSV manifest (`500c5eb8fc88f33309ca274c39f4065e619539e48fcc45898289715e281a1424`) and a separate headerless Condor args file (`3ea2abd6c4474e9d5e9e2883d53e96c45201db7f36f420f8541b0fc10fbfea45`). It prepares only BL Lac, NGC 1275, and 4C +42.22 with DGE active, fixed position, seven nhit bins, and free F0/index; submission has not occurred.
- Pre-submit validation: `condor_submit -dry-run` produced exactly 3 jobs with no warning. IHEP home has 77 GB available. `schedd06` is the selected current schedd based on the live queue audit (2 held, 2,172 running, 2,228 idle), rather than the obsolete hard-coded `schedd11`.
- Active jobs: none.
- Output counts: 3/3 full-interval spectral-fit rows prepared; 0/3 submitted or completed.
- Failures or holds: the initial dry-run exposed a CSV-header-as-job defect; it was fixed by separating the headerless Condor args file, then revalidated with exactly three dry-run jobs. No actual scheduler hold exists for this goal.
- Decision needed: none.
- Next action: submit only these three validated full-interval spectral-fit jobs to `scheduler@schedd06.ihep.ac.cn`, then monitor their terminal state and validate `ParRes.yaml` before updating any frozen spectrum.
- Last verification command: `condor_submit -dry-run /home/lhaaso/liushijie/QPO/JOBs_official_qpo_spectral_fits/spectral_fits.classads /home/lhaaso/liushijie/QPO/JOBs_official_qpo_spectral_fits/spectral_fits.sub`.

## 2026-08-04 18:23 CST - Phase 2 spectral-fit submission

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`).
- Submission: IHEP HTCondor `scheduler@schedd06.ihep.ac.cn`, cluster `80164595`, submitted from the validated three-row manifest without modification.
- Active jobs: `80164595.0`, `80164595.1`, and `80164595.2`; initial state is `Idle` for all 3/3, with no hold reason.
- Output counts: 3/3 submitted; 0/3 completed; no `ParRes.yaml` has been accepted yet.
- Failures or holds: none for this goal.
- Decision needed: none.
- Next action: boundedly monitor `80164595`, then inspect terminal logs and parse only finite, non-boundary full-interval spectral fits before updating source models.
- Last verification command: `condor_q -name scheduler@schedd06.ihep.ac.cn 80164595 -af ClusterId ProcId JobStatus HoldReason EnteredCurrentStatus RemoteHost`.

## 2026-08-04 18:27 CST - Phase 2 monitoring and profile-interface audit

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`).
- Active jobs: IHEP cluster `80164595`, `3/3 Idle`, `0 held`, `0 completed`. `condor_q -better-analyze` found 45,094 matching machines and 78 currently able to run the job; no constraint mismatch was found. The queue is serving 44,650 matching slots to other users, so the current state is normal priority wait rather than a diagnosed failure.
- Completed checks: no executable public per-bin profile scan was found. The public LC analysis YAML references `lc_cpprofile.py`, but no matching file exists under public v1.0. `Src_Main` logs AIC/BIC/TS; fixed-F0 scans with unchanged free parameters can therefore use `(AIC - min(AIC))/2` as Delta log L. Local parser/bracketing tests for that contract pass.
- Output counts: 3/3 spectral-fit jobs submitted; 0/3 terminal outputs accepted. Local configuration fixture/registry/profile tests pass 9/9.
- Failures or holds: none. The earlier Condor CSV header defect remains recorded as resolved; the final dry-run parsed 3 exact jobs without warning.
- Decision needed: none.
- Next action: monitor the existing three jobs without duplicate submission. On completion, validate status/log/ParRes and update the three target spectra; only then may Phase 2 be assessed for its remaining DGE profile-smoke requirement.
- Last verification command: `condor_q -name scheduler@schedd06.ihep.ac.cn -better-analyze 80164595.0`.

## 2026-08-04 18:29 CST - Phase 2 queue observation

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`).
- Active jobs: IHEP cluster `80164595`; all three processes remain `Idle`, with no hold reason and no history record.
- Output counts: 3/3 submitted; 0/3 completed; 0 accepted spectral models.
- Failures or holds: none. No retry, migration, or duplicate submission was performed because resource analysis still shows valid matches and the jobs have not failed.
- Decision needed: none.
- Next action: continue bounded monitoring of `80164595`; upon a terminal state, validate the exact corresponding log and `ParRes.yaml` before making any spectrum or phase-gate claim.
- Last verification command: `condor_q -name scheduler@schedd06.ihep.ac.cn 80164595 -af ClusterId ProcId JobStatus HoldReason RemoteHost`.

## 2026-08-04 18:33 CST - Phase 2 PLC compatibility correction and second manifest

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`).
- Scientific/configuration correction: public 2LHAASO catalog models were re-audited against `/home/lhaaso/hushicong/public/v1.0/src/Src_SEDModel.yaml`. Six close catalog associations use `PLC`, which is not a public v1.0 `Src_Main` model tag and has no public conversion implementation. These six references remain documented but are now `UNVERIFIED`; only 1ES 2344+514 has directly runnable catalog `PL`. This corrects the initial overly permissive seven-model association without changing the frozen source sample.
- Prepared IHEP work: `/home/lhaaso/liushijie/QPO/JOBs_official_qpo_spectral_fits_plc/` contains a disjoint six-row manifest (`1f17c823c720342b024705865320c13d3c6d3734a74d12a3bc15105c5d6c7d7d`) for `mkn421`, `mkn501`, `1es1959p650`, `1es1727p502`, `m87`, and `ic310`. Its headerless queue args SHA-256 is `ffa9ed72070ba1549f0b6907065399931d5e1ad73bde66f8854f6fe48db439b7`.
- Pre-submit validation: the second `condor_submit -dry-run` parsed exactly 6 jobs with no warning. Live schedd audit retains `schedd06` as the selected schedder (1,786 running, 2,110 idle, 2 held). Existing `80164595` remains 3/3 Idle without a hold.
- Active jobs: `80164595` (3 Idle); second manifest prepared, not submitted.
- Output counts: 9 unresolved targets are now represented by 3 submitted plus 6 prepared full-interval fits; 0 terminal outputs accepted.
- Failures or holds: no goal jobs held or failed.
- Decision needed: none.
- Next action: submit the validated disjoint six-row manifest to `scheduler@schedd06.ihep.ac.cn`, then monitor both clusters without duplicate rows.
- Last verification command: `condor_status -schedd -af Name Machine TotalRunningJobs TotalIdleJobs TotalHeldJobs`.

## 2026-08-04 18:34 CST - Phase 2 second spectral-fit submission

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`).
- Submission: IHEP HTCondor `scheduler@schedd06.ihep.ac.cn`, cluster `80164665`, submitted from the validated six-row manifest without modification.
- Active jobs: `80164595` (3/3 Idle) plus `80164665` (6/6 Idle); 9/9 jobs have no hold reason and no completion record.
- Output counts: 9/9 full-interval spectral fits submitted; 0/9 completed; no source spectrum has been updated from a job result.
- Failures or holds: none. An initial comma-separated cluster query was invalid for this `condor_q` invocation and returned no rows; the corrected ClassAd constraint showed all nine expected rows.
- Decision needed: none.
- Next action: boundedly monitor both clusters by ClassAd constraint and validate each terminal source result against its own manifest row before accepting a fixed spectrum.
- Last verification command: `condor_q -name scheduler@schedd06.ihep.ac.cn -constraint 'ClusterId == 80164595 || ClusterId == 80164665' -af ClusterId ProcId JobStatus HoldReason RemoteHost`.

## 2026-08-04 18:37 CST - Phase 0 revalidation and Phase 2 queue observation

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`).
- Completed checks: re-read root `AGENTS.md`, root `CLAUDE.md`, the complete frozen execution plan, the local goal ledger, and the accessible IHEP rebuild status report. From ETO, `ihep` again connected in batch mode to `lxlogin007.ihep.ac.cn`; the remote QPO root is `/home/lhaaso/liushijie/QPO`. ETO resolves `/home/server/projects/QPO` to `/mnt/mydisk/server/projects/QPO`, and `squeue` reports no current user job.
- Active jobs: IHEP `scheduler@schedd06.ihep.ac.cn` clusters `80164595` (3/3 Idle) and `80164665` (6/6 Idle), for 9/9 submitted full-interval spectral fits; no process has a hold reason, remote host, or terminal output yet.
- Output counts: 0/9 terminal spectral-fit products accepted. A remote-to-ETO `rsync --dry-run` of the IHEP rebuild status remains viable; no production data transfer was performed.
- Failures or holds: none for this goal. No duplicate row, retry, or production submission was performed.
- Decision needed: none.
- Next action: monitor the two existing Condor clusters boundedly; after a terminal result, validate its matching manifest row, log, and `ParRes.yaml` before updating any source-specific spectrum or assessing the remaining Phase 2 DGE/profile-smoke prerequisite.
- Last verification command: `ssh -o BatchMode=yes -o ConnectTimeout=15 ihep "cd /home/lhaaso/liushijie/QPO && hostname && pwd -P && condor_status -schedd -af Name Machine TotalRunningJobs TotalIdleJobs TotalHeldJobs && condor_q -name scheduler@schedd06.ihep.ac.cn -constraint 'ClusterId == 80164595 || ClusterId == 80164665' -af ClusterId ProcId JobStatus HoldReason EnteredCurrentStatus RemoteHost"`.

## 2026-08-04 18:46 CST - Phase 3 smoke wrapper environment diagnosis

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); the Phase 3 profile hard gate is being prepared and has not passed.
- Completed checks: prepared an immutable three-bin local smoke manifest at `/home/lhaaso/liushijie/QPO/JOBs_official_qpo_profile_smoke/` for verified-PL source `1es2344p514`, LC IDs `0001`, `0402`, and `0803`, with active public DGE, all seven nhit bins, and the official T001/T048/T083 Group1 response branch. Manifest SHA-256: `a84266cebc74923502ca027a137d76af4fc087fbe3fa3188d738fb14b82effca`.
- Active jobs: IHEP clusters `80164595` (3/3 Idle) and `80164665` (6/6 Idle); no spectral-fit terminal outputs, holds, or duplicate rows.
- Output counts: 0/3 profile smoke bins executed; 0/9 spectral fits accepted.
- Failures or holds: the first smoke-wrapper invocation stopped before `Src_Main` because the public environment script references `ANYSW_LANG_K` while Bash nounset was enabled. No fit or scan output was produced, and no public software was modified.
- Decision needed: none.
- Next action: regenerate the same prepared smoke wrapper with nounset enabled only after the public environment script is sourced, then execute the same three permitted local smoke bins and inspect each profile before any production work.
- Last verification command: `ssh -o BatchMode=yes -o ConnectTimeout=15 ihep 'cd /home/lhaaso/liushijie/QPO/JOBs_official_qpo_profile_smoke && ./run_profile_smoke.sh'`.

## 2026-08-04 19:03 CST - Phase 3 profile smoke resource diagnosis

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); Phase 3 hard gate remains `NOT PASSED`.
- Completed checks: the deterministic fixed-F0 wrapper was compiled and its focused local suite passed 14/14. It was packaged with its registry/profile helper for IHEP Python 3.9, uses a per-bin ordinary free-F0 fit followed by same-parameter-set DGE scans, preserves all seven nhit bins, records DataConfig/response metadata and hash provenance, and converts equal-degree-of-freedom scan AIC values to Delta log likelihood. The r1/r2 path diagnostics and r3 partial outputs were preserved in separate IHEP job roots.
- Active jobs: no local smoke process remains. IHEP spectral-fit clusters `80164595` (3/3 Idle) and `80164665` (6/6 Idle) remain the only active goal jobs.
- Output counts: r3 validated the ordinary `LC0001` fit plus two completed fixed-F0 scan points, each with non-empty `ParRes.yaml`; the third scan was intentionally interrupted before output completion. No complete profile JSON was accepted, so profile coverage is 0/3 and no source/DGE status was promoted.
- Failures or holds: r1 exposed a public environment/nounset incompatibility; r2 exposed the public relative-`Outdir` contract; both wrapper defects were corrected. r3 then measured about two minutes of CPU-bound DGE joint optimization per fixed-F0 point. Completing 3 bins x 5 points serially would be an inappropriate login-node batch loop, so the smoke was stopped without deleting its logs/results. Exact F0=0 remains schema-valid but is excluded from this public-v1.0 DGE smoke grid because it exhibited a boundary-minimizer stall.
- Decision needed: none.
- Next action: prepare a manifest-driven HTCondor profile pilot that preserves the same fixed-F0/DGE likelihood contract and validates all three profiles without using the IHEP login node for the grid; do not submit full light-curve production before that pilot passes.
- Last verification command: `ps -u liushijie -o pid,stat,cmd | grep -E 'Src_Main.*official_qpo_profile_smoke|prepare_official_qpo_profile_smoke' | grep -v grep || true`.

## 2026-08-04 19:06 CST - Phase 3 HTCondor normal-profile pilot submission

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); Phase 3 profile hard gate is pending the staged pilot outputs.
- Completed checks: `prepare_official_qpo_profile_pilot.py` creates a two-stage immutable pilot without a login-node grid loop. Its normal stage retains the verified public PL source, active public DGE, seven nhit bins, official LC0001/0402/0803 T001/T048/T083 DataConfigs, and the source-declination response branch. The local compile/test suite passed 15/15. IHEP `condor_submit -dry-run` parsed exactly 3 normal jobs with no warning. Normal args SHA-256 is `228dbd78f9ff49bd68beabeeaef32c397a8b99790245b17b8153cdde37098f5f`; the linked smoke manifest SHA-256 is `0717740ac29501d80bb8bb93423099913e65b3d6c98cb76b892547bdeefc8c6b`.
- Submission: IHEP `scheduler@schedd06.ihep.ac.cn`, cluster `80164823`, submitted from `/home/lhaaso/liushijie/QPO/JOBs_official_qpo_profile_pilot/normal_profile_pilot.sub` without modification.
- Active jobs: `80164823` (3/3 Idle) plus spectral clusters `80164595` (3/3 Idle) and `80164665` (6/6 Idle); 12/12 have no hold reason or terminal output.
- Output counts: 0/3 pilot normal outputs accepted; fixed-F0 scan manifest remains intentionally ungenerated until all three matching normal logs are `STATUS: OK` and `ParRes.yaml` is finite.
- Failures or holds: none for the new pilot. The previously diagnosed r1/r2/r3 local-smoke artifacts remain preserved and are not inputs to acceptance.
- Decision needed: none.
- Next action: monitor `80164823`; validate all three normal rows individually, then generate and dry-run the exactly 15 fixed-F0 profile scan jobs. Do not submit full light-curve production.
- Last verification command: `condor_q -name scheduler@schedd06.ihep.ac.cn -constraint 'ClusterId == 80164595 || ClusterId == 80164665 || ClusterId == 80164823' -af ClusterId ProcId JobStatus HoldReason RemoteHost`.

## 2026-08-04 19:09 CST - Phase 3 pilot macro-collision correction and resubmission

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); Phase 3 hard gate remains pending.
- Diagnosis: `80164823` never started (`NumJobStarts=0`), but its Condor queue column named `log` expanded the submit-file event-log macro and wrote 172-byte Condor event logs at the intended normal-fit log paths. This was a job-wrapper manifest defect, not a `Src_Main`, DGE, response, or source-spectrum result.
- Correction: the pilot generator now uses the distinct queue field `fit_log`, preserving Condor event logs under `logs/` and passing the ordinary fit log only as the executable fourth argument. Compile plus focused tests passed 6/6 after the fix; r2 `condor_submit -dry-run` again parsed exactly 3 jobs with no warnings.
- Submission: `80164823` was marked for removal before any process started; its diagnostics remain preserved. The corrected r2 manifest was submitted to IHEP `scheduler@schedd06.ihep.ac.cn` as cluster `80164837`.
- Active jobs: `80164837` (3/3 Idle), `80164595` (3/3 Idle), and `80164665` (6/6 Idle); 12/12 have no hold reason, remote host, normal log, or terminal output.
- Output counts: r2 normal args SHA-256 `8fe2c013b60bba9c4fa9893c1741756b7adc81ccdacf41f56c84fd2202e52af6`; r2 linked smoke manifest SHA-256 `368774282629a3be2c9c9916083a375c17c6f3b4dcf373b6f32ecc747aeadc92`; 0/3 normal pilot rows accepted.
- Failures or holds: no hold. No fixed-F0 scan job or full light-curve production has been submitted.
- Decision needed: none.
- Next action: monitor `80164837`; once all three normal outputs independently satisfy log/ParRes checks, generate the 15-row fixed-F0 scan manifest and dry-run it.
- Last verification command: `condor_q -name scheduler@schedd06.ihep.ac.cn -constraint 'ClusterId == 80164595 || ClusterId == 80164665 || ClusterId == 80164837' -af ClusterId ProcId JobStatus HoldReason RemoteHost`.

## 2026-08-04 19:12 CST - Phase 3 profile-pilot collector prepared

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); Phase 3 is awaiting the running-state transition of normal pilot `80164837`.
- Completed checks: added the manifest-driven fixed-F0 collector to `prepare_official_qpo_profile_pilot.py`. It accepts only exactly 15 scan rows (five per frozen LC ID), verifies normal and scan `STATUS: OK`, validates immutable args hashes and the grid derived from each ordinary MLE, applies the Delta-log-likelihood bracket validator, and writes the three profile JSON artifacts only after all checks pass. A complete fixture exercises the 3-normal/15-scan collection path. Local relevant tests pass 16/16; the synchronized IHEP Python 3.9 copy compiles.
- Active jobs: `80164837` remains 3/3 Idle; spectral clusters `80164595` and `80164665` remain 9/9 Idle; no holds or outputs.
- Output counts: 0/3 normal outputs, 0/15 scan outputs, and 0/3 accepted profiles. No new queue submission occurred.
- Failures or holds: none since the r2 pilot correction.
- Decision needed: none.
- Next action: bounded monitoring; on normal-pilot completion, validate all three rows before producing the fixed-F0 manifest and invoking its dry-run.
- Last verification command: `PYTHONPATH=src pytest -q tests/test_prepare_official_qpo_profile_pilot.py tests/test_prepare_official_qpo_profile_smoke.py tests/test_official_profile.py tests/test_official_qpo_registry.py tests/test_prepare_official_qpo_spectral_fits.py tests/test_official_lc.py`.

## 2026-08-04 19:15 CST - Phase 2 spectral-fit acceptance helper prepared

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); all nine source-spectrum jobs remain pending scheduler placement.
- Completed checks: added `official_spectral.py`, which accepts a full-interval fit only when its final log is `STATUS: OK`, its `ParRes.yaml` has a finite interior PL F0 and alpha with positive alpha uncertainty, and AIC/BIC/TS are parseable. Accepted fits become normalized fixed-spectrum registry records with log/config provenance; boundary or unconstrained index values are rejected rather than silently promoted. The helper is synchronized to IHEP and compiles under Python 3.9.
- Active jobs: `80164595` (3/3 Idle), `80164665` (6/6 Idle), and normal-profile pilot `80164837` (3/3 Idle); no holds, starts, or outputs.
- Output counts: 0/9 accepted spectra; 0/3 normal profiles; 0/15 fixed-F0 scans.
- Failures or holds: none. Resource analysis for `80164837.0` found 32,461 matching machines and 56 currently able slots, so the continued Idle state is normal priority wait rather than a constraint failure.
- Decision needed: none.
- Next action: monitor only on material queue change; validate any terminal spectral or normal-pilot outputs using the prepared acceptance helpers.
- Last verification command: `condor_q -name scheduler@schedd06.ihep.ac.cn -better-analyze 80164837.0`.

## 2026-08-04 19:18 CST - Phase 2 immutable spectral-registry collector prepared

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); no queued job has entered a terminal state.
- Completed checks: added `collect_official_qpo_spectral_fits.py`. It consumes one or more immutable `spectral_fit_manifest.csv` files only when their registry SHA-256 agrees with the supplied registry, rejects duplicate/unknown sources and all invalid fits, then writes a new registry path without overwriting the pending original. Each accepted record stores log/ParRes hashes, DataConfig and response-slot provenance. The collector and its standalone helpers are synchronized to IHEP and compile under Python 3.9.
- Active jobs: `80164595` (3/3 Idle), `80164665` (6/6 Idle), and `80164837` (3/3 Idle); no hold, start, log, or output.
- Output counts: 0/9 accepted spectra, 0/3 normal profile fits, 0/15 scans, 0/3 profiles.
- Failures or holds: none. The normal pilot has no output files, consistent with its `NumJobStarts=0` queue state.
- Decision needed: none.
- Next action: monitor existing clusters without resubmission; on spectral completion, run the collector against the exact originating manifests and inspect its new registry hash before promoting any model.
- Last verification command: `PYTHONPATH=src pytest -q tests/test_collect_official_qpo_spectral_fits.py tests/test_official_spectral.py tests/test_prepare_official_qpo_profile_pilot.py tests/test_prepare_official_qpo_profile_smoke.py tests/test_official_profile.py tests/test_official_qpo_registry.py tests/test_prepare_official_qpo_spectral_fits.py tests/test_official_lc.py`.

## 2026-08-04 19:20 CST - Goal blocked on external HTCondor scheduling

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`BLOCKED_BY_EXTERNAL_SCHEDULER`).
- Blocking condition: IHEP HTCondor clusters `80164595` (3 full-interval spectra), `80164665` (6 full-interval spectra), and `80164837` (3 normal-profile pilot fits) remain 12/12 Idle after repeated bounded checks. No job has a hold reason, remote host, start, output, or failed resource constraint. `better-analyze` for the pilot found 32,461 matching machines and 56 currently able slots; the queue is serving matching capacity to other users.
- Work preserved: all immutable manifests, source/DGE/profile acceptance helpers, r1/r2/r3 smoke diagnostics, collector tests, and status records remain in place. No duplicate submission, queue migration, retry, cleanup, or production LC submission was performed.
- Resume condition: any goal job enters Running or terminal state, or IHEP scheduling state changes so a previously accepted manifest can be submitted/run. On resume, validate terminal rows against their exact manifests before generating the fixed-F0 scan stage or promoting source spectra.
- Last verification command: `condor_q -name scheduler@schedd06.ihep.ac.cn -constraint 'ClusterId == 80164595 || ClusterId == 80164665 || ClusterId == 80164837' -af ClusterId ProcId JobStatus HoldReason RemoteHost`.

## 2026-08-05 12:02 CST - Phase 2 public-DGE compatibility block

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`BLOCKED_BY_FROZEN_PROTOCOL_CONFLICT`); Phase 3 profile hard gate remains unpassed.
- Completed work: original spectral clusters `80164595`/`80164665` and normal-profile cluster `80164837` left the queue overnight. The normal-profile pilot completed `3/3` with Condor exit 0; LC0001 and LC0803 were `STATUS: OK`, while LC0402 was `STATUS: NotOK` at the physical source-F0/DGE-F0 lower boundary. Its immutable 15-row scan cluster `80175952` completed: LC0001 and LC0803 are `10/10 STATUS: OK`; LC0402 is `5/5 STATUS: NotOK` from the same DGE boundary. A two-row, non-production fixed-DGE LC0402 numerical diagnostic was dry-run without warnings and submitted as `80176086` (2 Idle at this snapshot).
- Spectral wrapper corrections: the public environment/nounset failure was corrected; then the spectral Condor `log` macro collision was found and corrected to `fit_log`, with regression tests. The accidental `80175863` retry was removed before any start. Retry-r3 `80175889` produced one independently accepted BL Lac spectrum in a new registry copy (`872e92ffdb9ee1174a3b8e383470a3666df87d4a5ddba23dd9945b6175f38183`); its remaining rows are not promoted. Retry-r4 `80175991` correctly used the repaired runner but all six selected high-latitude sources stopped before fitting, with no `ParRes.yaml`.
- Hard conflict: the public v1.0 executable itself reports `Error: Activate DGEs but center of ROI is at large galactic latitude (abs(gb)>15 degree)! Returned.` for Mkn421, Mkn501, 1ES1959p650, 1ES1727p502, M87, and 4C_p42d22. Thus the frozen protocol requirement that every target/control run with DGE active conflicts with the equally frozen prohibition on modifying public IHEP software. These are public-program rejections, not scheduler, resource, source-spectrum, or wrapper failures.
- Active jobs: fixed-DGE diagnostic `80176086` (2 Idle). All production-like light-curve work remains unsubmitted; the hourly read-only Condor monitor covers the spectral, profile-pilot, and diagnostic project names.
- Decision needed: authorize one protocol change before proceeding: either accept the public executable's automatic DGE deactivation for `|b| > 15` degrees and record it per source/control, or permit a user-space replacement/wrapper that can retain DGE for those ROIs. Neither choice has been assumed.
- Last verification command: `ssh ihep 'for f in /home/lhaaso/liushijie/QPO/JOBs_official_qpo_spectral_fits_retry_r4/fits/*/fit.log; do tail -80 "$f"; done'`.

## 2026-08-05 14:31 CST - Phase 2 public-DGE policy amendment accepted

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); the prior frozen-protocol conflict is resolved by the user's explicit decision. Phase 3 profile hard gate remains unpassed.
- Decision: the user accepted the public-v1.0 compatibility policy: retain the public DGE template where public `Src_Main` supports the ROI centre, and explicitly set `DGE.Active: 0` for every target/control ROI with `|b| > 15` degrees. No public IHEP software will be modified.
- Completed checks: amended the authoritative execution plan; rebuilt `data/config/official_qpo_source_models.yaml` as `official_qpo_source_registry_v2_public_dge_guard` with SHA-256 `f6c3843ea3f21de91933be6cbf4fa1b25b4582159d9d9ed2623133586883996a`. All 10 targets, 10 deterministic blanks, and Crab now contain Galactic latitude, 15-degree threshold, explicit active state, and decision text. The existing independently collected BL Lac registry copy (`872e92ffdb9ee1174a3b8e383470a3666df87d4a5ddba23dd9945b6175f38183`) remains separate and is not overwritten.
- Validation: compiled the affected registry, builder, spectrum, profile-smoke, and fixed-DGE diagnostic modules. The focused registry/spectrum/profile/collector suite passed `23/23`; DGE configuration checks confirm the six originally rejected high-latitude targets are inactive, while supported ROIs retain the public template. Fixed-source-F0 YAML now uses physical bounds `[0.0, 500.0]`, eliminating the equal-Minuit-limit encoding.
- Active jobs: `80176086` is no longer listed by `condor_q`; `condor_history` returned no classad during this check, so no terminal diagnostic result is accepted yet. The hourly monitor remains active but its recent remote runs log the IHEP AFS `.bashrc` permission warning; scheduler commands themselves are present on `lxlogin007`.
- Next action: synchronize the lightweight registry and generators to IHEP, prepare a new immutable DGE-policy spectral retry manifest for only the six public-rejected high-latitude targets, dry-run it, and validate its per-row DGE state before any submission. Separately inspect the terminal fixed-DGE diagnostic artifacts before deciding whether a supported low-latitude DGE-nuisance treatment needs an additional diagnostic.
- Last verification command: `PYTHONPATH=src pytest -q tests/test_official_qpo_registry.py tests/test_prepare_official_qpo_profile_smoke.py tests/test_prepare_official_qpo_spectral_fits.py tests/test_prepare_official_qpo_fixed_dge_diagnostic.py tests/test_prepare_official_qpo_profile_pilot.py tests/test_collect_official_qpo_spectral_fits.py tests/test_official_profile.py tests/test_official_spectral.py tests/test_official_lc.py`.

## 2026-08-05 14:31 CST - Phase 2 high-latitude spectral retry prepared

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); Phase 3 profile hard gate remains unpassed and no full light-curve production job has been submitted.
- Completed work: synchronized the policy registry and only its required lightweight generators/helpers to IHEP. Prepared `/home/lhaaso/liushijie/QPO/JOBs_official_qpo_spectral_fits_dge_policy_r5/` for the six public-rejected targets: `mkn421`, `mkn501`, `1es1959p650`, `1es1727p502`, `m87`, and `4c_p42d22`. The first IHEP preparation attempt used the ETO-only Python path and made no files; the succeeding IHEP `/usr/bin/python3` (3.9.25) preparation succeeded after synchronizing the missing shared path helper.
- Immutable artifacts: manifest SHA-256 `f726726795bbc1831e59ee9b7f93c783aabd4d62dc8868df478765ebaca0d43c`; queue args SHA-256 `5d0e9ee47a6a6856929d2cd3848d4e9dabee3fc57c3d8c798b7e1f7a38f766cc`; summary SHA-256 `c75660fc5565081177300b4abf905c68bb5d76b2ff010c131daf4f0573f5327d`; submit-file SHA-256 `9144bb96134e2746749c861aa9b0cbecf99646281dba1d1b402d0af09fcddd45`. A checksum-identical local copy is retained in `data/processed/official_qpo/manifests/spectral_dge_policy_r5/`.
- Validation: each manifest row now records Galactic latitude, the 15-degree public threshold, DGE state, and decision. The six rows have latitudes `65.031568`, `38.858811`, `17.688943`, `33.550440`, `74.560192`, and `18.806322` degrees respectively; all specify `dge_active=0`, and their generated `ParInit.yaml` files independently contain `DGE.Active: 0`. `condor_submit -dry-run` parsed exactly `6` jobs to dry-run cluster `1` with no warning.
- Active jobs: none were added. The retry is prepared only, not submitted. Existing diagnostic cluster `80176086` still requires artifact-level terminal validation because it is absent from the live queue and no classad was returned by this scheduler's history query.
- Next action: inspect fixed-DGE diagnostic logs/outputs through the recovered IHEP access path, then submit only this already validated six-row retry when the Phase 2 scheduler step is authorized by the workflow; do not create or submit full light-curve production work before the 3/3 profile gate passes.
- Last verification command: `condor_submit -dry-run spectral_fits.dryrun spectral_fits.sub` in the retry-r5 root.

## 2026-08-05 14:31 CST - Phase 2 high-latitude spectral retry submitted

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); Phase 3 profile hard gate remains unpassed. No full light-curve production task has been submitted.
- Submission: the validated retry-r5 six-row manifest was submitted to IHEP HTCondor cluster `80177636` via `scheduler@schedd06.ihep.ac.cn`. Its initial verified state is `6/6 Idle`, `NumJobStarts=0`, no `RemoteHost`, and no hold reason.
- Submission diagnosis: an initial default `condor_submit spectral_fits.sub` returned `ERROR: Can't find address of local schedd` before creating a cluster. Repeating the immutable manifest's dry-run with the explicit scheduler parsed `6` jobs, then `condor_submit -name scheduler@schedd06.ihep.ac.cn spectral_fits.sub` successfully created `80177636`. This is an IHEP login-environment schedd-discovery issue, not a fit or manifest change.
- Monitoring: the established hourly monitor already queries the explicit working schedd and remains submission-free. It will cover the new cluster by its `qpo_official_spectral_fit` project name.
- Next action: monitor `80177636` for starts, holds, and terminal per-row artifacts; accept only rows with `STATUS: OK` and finite `ParRes.yaml` through the immutable collector. Inspect the older fixed-DGE diagnostic independently; do not submit any full light-curve production work before the 3/3 profile gate passes.
- Last verification command: `condor_q -name scheduler@schedd06.ihep.ac.cn -constraint "ClusterId == 80177636" -af ClusterId ProcId JobStatus NumJobStarts RemoteHost HoldReasonCode HoldReason`.

## 2026-08-05 14:31 CST - Phase 2 high-latitude spectral retry collected

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); Phase 3 profile hard gate remains unpassed. No full light-curve production task has been submitted.
- Terminal validation: all `6/6` retry-r5 source logs end `STATUS : OK`, and every corresponding `out/ParRes.yaml` is non-empty. Although this schedd did not return historical classads after quick completion, direct immutable-artifact validation is complete for each row.
- Accepted spectra: `mkn421` `(F0=0.70391, alpha=2.93636)`, `mkn501` `(0.24863, 2.84471)`, `1es1959p650` `(0.18975, 3.34173)`, `1es1727p502` `(0.06258, 2.93958)`, `m87` `(0.02356, 2.50216)`, and `4c_p42d22` `(0.00541, 2.84540)`, in the public `1.e-12 TeV^-1 cm^-2 s^-1` normalization convention. All six are finite, interior to the frozen F0/index bounds, and have positive index uncertainty.
- Collection: synchronized the amended collector and its profile parser dependency, then wrote the new non-overwriting registry `/home/lhaaso/liushijie/QPO/data/config/official_qpo_source_models_dge_policy_r5_collected.yaml` with SHA-256 `12059d6e0d06a83080597903dea6c61c6d76797e623394d192d460dc333a9ef0`; an identical local copy is retained in `data/config/`. Local schema validation passed and each accepted spectral record preserves `dge_configuration.active=false`, the high-latitude decision, and per-log/ParRes hashes. The prior BL Lac-only registry remains separate and unmodified.
- Validation: the updated DGE-aware collector/spec helper and focused related suite passed `11/11`; the broader affected suite had passed `23/23` before collection.
- Active jobs: no retry-r5 job remains in `condor_q`. The fixed-DGE LC0402 diagnostic still has no accepted terminal result pending direct artifact inspection.
- Next action: audit the fixed-DGE diagnostic's actual output paths and, if needed, use the corrected physical fixed-F0 bounds for one new non-production LC0402 diagnostic before deciding whether the supported low-latitude nuisance treatment can satisfy the 3/3 profile gate.
- Last verification command: local `validate_registry(..., require_production_ready=False)` plus printed accepted DGE/power-law records from `data/config/official_qpo_source_models_dge_policy_r5_collected.yaml`.

## 2026-08-05 14:39 CST - Phase 3 LC0402 fixed-DGE numerical diagnostic resubmitted

- Current phase: Phase 2 - Freeze Source, DGE And Control Configurations (`IN PROGRESS`); Phase 3 profile hard gate remains unpassed. This two-row work is a non-production numerical diagnostic, not a light-curve submission.
- Diagnosis completed: direct artifact inspection of historical `80176086` found both jobs terminated normally (exit 0). Its normal DGE-fixed LC0402 fit was `STATUS: OK`; the fixed-F0 row alone was `STATUS: NotOK` because Minuit received equal F0 limits `2e-05, 2e-05`. The failure was deterministic input encoding, not an unconstrained fixed-DGE numerical fit.
- Immutable r3 diagnostic: prepared `/home/lhaaso/liushijie/QPO/JOBs_official_qpo_fixed_dge_diagnostic_r3/` from the completed profile-pilot-r2 LC0402 ordinary fit. The fixed row has `DGE.Active=1`, both public DGE spectral parameters fixed, source `F0` fixed with physical bounds `[2e-05, 0.0, 500.0, 1, '1e-15']`, and no equal bounds. Args SHA-256 `507f294591b3c23522ef6864ff803ce4fabfcac857db97f65664461e7d6441ca`; submit SHA-256 `76f2732de5865867e780aa3304bfb94ea33256af2a19a4a2f8126a3fb976d1bf`; summary SHA-256 `e7ab2e34c18da623421911efd9120a964ca580d0d127de7f569fdc5baaa824a7`.
- Validation and submission: local diagnostic/profile tests passed `7/7`; explicit-schedd dry-run parsed exactly `2` jobs. Submitted as IHEP HTCondor cluster `80177642`; initial state is `2/2 Idle`, zero starts, no remote host or hold. The hourly read-only monitor was run manually and now records both jobs under their actual `qpo_official_fixed_dge_diagnostic` classad.
- Next action: validate normal and fixed-F0 r3 logs/ParRes when terminal. Only if both are `STATUS: OK` will this establish that the LC0402 issue is the free-DGE nuisance degeneracy rather than the fixed-F0 interface. It does not itself pass the 3/3 profile gate or authorize production light curves.
- Last verification command: `condor_q -name scheduler@schedd06.ihep.ac.cn -constraint "ClusterId == 80177642" -af ClusterId ProcId Owner ProjectName JobBatchName JobStatus`.
