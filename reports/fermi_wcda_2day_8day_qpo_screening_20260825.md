# Fermi-LAT 2-day / 8-day QPO screening on the WCDA time grid (2026-08-25)

## Scope

This analysis applies the official WCDA CWT/WWZ screening workflow to the Fermi-LAT 0.1-300 GeV light curves of Mrk 421 and Mrk 501. The Fermi bins use the same MJD grid and observing interval as the official WCDA 2-day and 8-day products.

The selected `all-successful` policy retains the maximum-likelihood flux from every successful Fermipy fit, including bins with `TS < 9`. Those low-TS bins remain identified as 95% upper limits in the light-curve products. Failed fits remain missing and are neither interpolated nor replaced with zero.

| Source | Cadence | Grid rows | Analysis rows | Successful low-TS rows |
|---|---:|---:|---:|---:|
| Mrk 421 | 2 day | 803 | 785 | 66 |
| Mrk 421 | 8 day | 200 | 199 | 4 |
| Mrk 501 | 2 day | 803 | 802 | 313 |
| Mrk 501 | 8 day | 200 | 200 | 5 |

## Method

- CWT: Morlet(6), `dj = 1/12`, with a 10-600 day search for 2-day curves and 32-600 day search for 8-day curves. The 95% and 99% references are the PyCWT time-averaged analytic AR(1) levels.
- WWZ: the same period ranges, 80 time divisions, frequency-step factor 0.5, and decay constant 0.0125.
- WWZ significance: 1,000 Gaussian AR(1) surrogates on the identical successful-fit sampling, a +/-10% local-period window, and the maximum over the full period range for the single-curve global FAP.
- Monte Carlo FAP values use the finite-sample correction `(exceedances + 1) / (N + 1)`, so the minimum measurable FAP is `1/1001 = 0.000999`.
- A four-curve Bonferroni value is reported as `min(1, 4 * single-curve global FAP)`. This correction covers the two sources and two cadences, but not additional method or analysis-policy trials.

## Results

Mrk 421 has no significant periodicity in either cadence. Its strongest long-period 2-day WWZ candidate is approximately 384.35 days, with local FAP 0.05495 and single-curve global FAP 0.31069.

Mrk 501 has a consistent approximately 250-260 day feature in CWT and WWZ:

| Cadence | CWT peak | CWT pointwise reference | WWZ peak | Cycles | Local FAP | Single-curve global FAP | Four-curve adjusted FAP |
|---|---:|---|---:|---:|---:|---:|---:|
| 2 day | 249.62 d | Above 99% | 259.83 d | 6.17 | 0.000999 | 0.004995 | 0.01998 |
| 8 day | 264.46 d | Above 95%, below 99% | 258.72 d | 6.15 | 0.02997 | 0.13586 | 0.54346 |

The Mrk 501 2-day WWZ candidate passes the four-curve Bonferroni threshold, and the CWT peak independently identifies the same period range. However, the 8-day WWZ result does not pass its single-curve global test. The current result is therefore a follow-up candidate rather than a robust cadence-independent QPO detection.

## Interpretation and next checks

The main sensitivity concern is the `all-successful` treatment of low-significance likelihood fits. In particular, 313 of the 802 Mrk 501 2-day analysis bins have `TS < 9`. The next robustness analysis should repeat the frozen test with a detections-only series and, preferably, a likelihood- or censoring-aware treatment of low-TS bins. Candidate stability should also be checked under flux-error resampling and a null model more flexible than Gaussian AR(1).

No HTML presentation was modified in this analysis.

## Products

- Combined significance table: `data/processed/periodicity/fermi_wcda_20260818/all-successful/fermi_wcda_qpo_significance_summary.csv`
- Per-source arrays and figures: `data/processed/periodicity/fermi_wcda_20260818/all-successful/{2day,8day}/<source_id>/`
- Full analysis grids with retained gaps and policy flags: `data/processed/aligned/fermi_wcda_20260818/all-successful/{2day,8day}/<source_id>/`
- Reproducible pipeline: `src/pipeline/fermi_wcda_qpo_analysis.py`
- ETO Slurm scripts: `work/slurm/fermi_wcda_qpo_full.sbatch` and `work/slurm/fermi_wcda_qpo_collect.sbatch`
- Formal jobs: array `65868`, collector `65869`; all completed with exit code 0.
