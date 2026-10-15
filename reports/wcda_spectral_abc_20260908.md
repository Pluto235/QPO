# WCDA spectral-index A/B/C comparison

Analysis date: 2026-09-08. Scope: Mrk 421 and Mrk 501, **8-day cadence only**.

## Frozen comparison

| Source | A: release index | B: full-interval index | C: lower index | C: upper index |
|---|---:|---:|---:|---:|
| Mrk 421 | 2.60000 | 2.93636 | 2.93107 | 2.94165 |
| Mrk 501 | 2.60000 | 2.84471 | 2.83170 | 2.85772 |

A reuses the checksum-verified 2026-08-17 release. B reuses validated public
`Src_Main` full-interval PL fits from `JOBs_official_qpo_spectral_fits_dge_policy_r5`.
Their local statistical index errors are 0.00529 and 0.01301, respectively;
C uses the corresponding minus/plus one-sigma indices.

These reference fits use the official full-interval aggregate map/response
`Data_20210305_20250731.yaml`. They are **not** simultaneous fits with a shared
index and independent normalizations for the exact 200 eight-day bins. The
full-interval reference also covers the final days beyond the 8-day release's
last bin. This is an explicitly conditional sensitivity experiment, not a new
measurement of time-dependent spectra or an exhaustive systematic-error band.

All 1,200 new bin fits returned final `STATUS: OK`. Each source retains the
same 200/200 bins in all four configurations. The bin configurations preserve
the release maps, period-dependent Group1 responses, single-source ROI,
fixed position, seven WCDA nhit bins, DGE off and KM2A off. Only the fixed PL
index changes; the normalization is fitted independently in every bin.

## Flux sensitivity

All flux quantities below refer to the differential normalization at **3 TeV**,
not an integral photon flux. Differences from A are model sensitivity, not a
measurement of A's error against a known true flux.

| Source | B/A mean normalization | Mean change | Pearson r, A versus B | Shape residual RMS / B mean |
|---|---:|---:|---:|---:|
| Mrk 421 | 0.78506 | -21.49% | 0.99905 | 8.06% |
| Mrk 501 | 0.91980 | -8.02% | 0.99887 | 5.64% |

The shape residual is `B(t) - k A(t)`, with the single least-squares scale
`k = sum(A B) / sum(A^2)`; its RMS is divided by the mean B normalization.
It is descriptive and does not treat the two fits to the same photons as
independent measurements.

C changes the mean normalization relative to B by about +0.58%/-0.58% for
Mrk 421 and +0.83%/-0.86% for Mrk 501. Across response periods, the 5th–95th
percentile range of the mean B/A normalization is 0.746–0.998 for Mrk 421 and
0.869–1.074 for Mrk 501. These varying ratios establish that the transformation
is not a single constant scale; they do not isolate an instrumental cause from
source-state dependence and statistical fluctuations.

## Periodicity comparison

All four versions are recalculated on the common valid-bin mask using the
existing WCDA screen: CWT/Morlet with analytical AR(1) global-spectrum
references, WWZ with 80 time divisions and frequency-step factor 0.5, and a
32–600 day search. Each WWZ run uses 200 Gaussian AR(1) surrogates, seed
20260817, and the same random seeds across A/B/C; AR(1) parameters are estimated
separately for each curve. Local FAP uses a +/-10% period window. Global FAP
accounts for the period search within a curve only. The Monte Carlo resolution
is 1/201 = 0.00498. The spectral alternatives are additional exploratory
analyses, not independent replications.

| Source | Configuration | WWZ candidate periods (days) | Corresponding global FAP | CWT candidates above 95% reference |
|---|---|---|---|---:|
| Mrk 421 | A, B, C-minus, C-plus | 50.3, 131.0, 383.3 | 1.000, 1.000, 1.000 | 0 in each |
| Mrk 501 | A, B, C-minus, C-plus | 149.4, 435.8 | 1.000, 0.89552 | 0 in each |

The Mrk 501 435.8-day peak has local FAP 0.36816 in every configuration.
Identical empirical FAP values reflect equal exceedance counts at the current
simulation resolution, not proof of identical underlying probabilities.

**Conclusion:** the spectral choice materially changes the absolute 3 TeV
normalization and introduces smaller time-dependent shape differences, while
the non-significant 8-day QPO classification is stable across these A/B/C
choices. C probes only the small statistical uncertainty of the average PL
index. This does not establish robustness to time-dependent spectra, spectral
curvature, DGE/background alternatives, all response uncertainties, or the
2-day analysis. Those are separate experiments.

- [Mrk 421 figure](../data/processed/spectral_abc_20260908/Mkn421_comparison.png), [metrics](../data/processed/spectral_abc_20260908/Mkn421_metrics.csv), [significance](../data/processed/spectral_abc_20260908/Mkn421_significance.csv)
- [Mrk 501 figure](../data/processed/spectral_abc_20260908/Mkn501_comparison.png), [metrics](../data/processed/spectral_abc_20260908/Mkn501_metrics.csv), [significance](../data/processed/spectral_abc_20260908/Mkn501_significance.csv)

## Reproducibility and provenance

- [Index reference fits and hashes](../data/processed/spectral_abc_20260908/provenance.json)
- [Collected bin fits](../data/processed/spectral_abc_20260908/lightcurves.csv)
- [Preparation and collection script](../src/pipeline/wcda_spectral_abc.py)
- [Comparison and plotting script](../src/pipeline/analyze_wcda_spectral_abc.py)
- [Slurm script](../work/slurm/wcda_spectral_abc.sbatch)

IHEP work root: `JOBs_spectral_abc_8day_20260908_r2`, relative to its QPO checkout.
Pilot cluster: 3467720. Production cluster: 3467723. ETO analysis array: 65908.
The first preparation attempt (3467708) failed because YAML sorting changed the
SRC key order required by public Src_Main; it was stopped and retained for
audit. The corrected run preserves the release key order and passed both pilots.

Run on IHEP, from its production checkout:

```bash
/usr/bin/python MakeLC/wcda_spectral_abc.py prepare --work JOBs_spectral_abc_8day_20260908_r2
condor_submit -name scheduler@schedd11.ihep.ac.cn JOBs_spectral_abc_8day_20260908_r2/pilot.sub
# After both pilots are terminal and validated:
condor_submit -name scheduler@schedd11.ihep.ac.cn JOBs_spectral_abc_8day_20260908_r2/fit.sub
# After the production jobs are terminal:
/usr/bin/python MakeLC/wcda_spectral_abc.py collect --work JOBs_spectral_abc_8day_20260908_r2
```

The prepare command refuses an existing work root. Use a new run directory for
a deliberate rerun. Transfer `lightcurves.csv` and `provenance.json` to ETO's
`data/processed/spectral_abc_20260908/`, then submit the recorded Slurm script.
The main release and its original periodicity products are preserved.
