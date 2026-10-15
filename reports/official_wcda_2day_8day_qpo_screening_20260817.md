# Official WCDA 2-day / 8-day QPO screening (2026-08-17)

## Scope

This screening uses the collaboration release `WCDA_official_LC_2day_8day_20260817`, derived from the latest official WCDA daily sky-map products. It covers ten AGN targets and the Crab control source at 2-day and 8-day cadence.

Only rows with `fit_status == OK`, finite `N0` and `N0_err`, and `N0_err > 0` enter the periodicity calculation. Rejected or missing bins are neither filled with zero nor interpolated. The 2-day curves retain 797–802 of 803 bins depending on source; the 8-day curves retain all 200 bins except BL Lacertae (199/200).

## Method

- CWT: Morlet wavelet, global wavelet spectrum, search range 10–600 days (2-day) or 32–600 days (8-day). The 95% and 99% references use the PyCWT time-averaged AR(1) red-noise calculation.
- WWZ: the same period ranges, 80 time divisions, frequency-step factor 0.5. Significance uses 200 Gaussian AR(1) surrogates on the identical sampling, a ±10% local-period window, and the maximum across the complete period search for the single-curve global FAP.
- The minimum resolvable Monte Carlo FAP is `1 / 201 = 0.004975`.
- The reported global WWZ FAP corrects the period search within one light curve only. It does not correct the search across sources, cadences, or methods.
- Response-period offsets and other WCDA systematics are not modeled in this screening.

## Main findings

Mrk 421 has no CWT or WWZ candidate above the adopted AR(1) 95% references in either cadence.

Mrk 501 has a 2-day WWZ peak near 436.7 days with local FAP 0.00498, but its single-curve global FAP is 0.0995 and only 3.67 cycles are covered. The corresponding 8-day peak is not significant (global FAP 0.891). This is not a significant QPO candidate under the current search.

The AGN peaks with single-curve WWZ global FAP below 0.05 are:

| Source | Cadence | Period (day) | Cycles | Local FAP | Single-curve global FAP |
|---|---:|---:|---:|---:|---:|
| 1ES 1959+650 | 2-day | 310.1 | 5.17 | 0.00498 | 0.00995 |
| NGC 1275 | 2-day | 505.5 | 3.17 | 0.00498 | 0.02488 |

Neither survives a simple 22-light-curve Bonferroni correction: the adjusted FAP values are approximately 0.219 and 0.547. NGC 1275 also covers fewer than four cycles. These are follow-up candidates, not QPO detections.

The Crab control shows a strong peak near 383–384 days in both cadences, with single-curve global FAP 0.00498 in each. CWT also finds a broad long-period Crab peak. Because the release documentation independently reports response-period discontinuities and excess Crab scatter, this repeatable control-source feature is evidence that response-period/instrumental systematics must be modeled before interpreting long-period AGN features physically.

## Interpretation

No source meets a survey-level QPO detection criterion in this initial CWT/WWZ screening. The most useful next step is a systematics-aware follow-up of 1ES 1959+650 and NGC 1275, alongside Crab and response-period boundary diagnostics. Candidate confirmation should use a frozen targeted period/window, at least 1,000–10,000 surrogates, response-period offset correction or nuisance modeling, and an explicit source/cadence/method trials budget.

## Products

- Combined candidate/significance table: `data/processed/periodicity/official_lc_20260817/official_lc_qpo_significance_summary.csv`
- Per-source CWT/WWZ arrays and figures: `data/processed/periodicity/official_lc_20260817/{2day,8day}/<source_id>/`
- Cleaned aligned inputs: `data/processed/aligned/official_lc_20260817/{2day,8day}/<source_id>/`
- Released light curves: `data/processed/wcda_{2day,8day}/official_20260817/`
- Original verified handoff: `data/raw/wcda/official_lc/WCDA_official_LC_2day_8day_20260817_handoff/`
- Reproducible entry point: `src/pipeline/official_lc_qpo_analysis.py`
