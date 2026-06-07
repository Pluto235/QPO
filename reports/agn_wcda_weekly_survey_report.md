# AGN WCDA Weekly Periodicity Survey

Generated on 2026-06-04 from `data/processed/periodicity/agn_wcda_weekly_survey/`.

This report applies the same WCDA weekly quick-look pipeline to 10 LHAASO AGN targets: Mrk 421, Mrk 501, and the eight newly pulled IHEP AGN products. It uses strict weekly flux products as the primary source-by-source view, with photon-count/excess-rate products folded below for validation.

Important scope note: this is not a QPO detection claim. The optional significance section is an AR(1) quick-look only, with no source-level, method-level, or survey-level trial correction. Detection-quality tiers below are based on weekly strict-flux TS, not on CWT/WWZ peak strength. The Fermi-LAT notes are prior context from the earlier survey page and are not recomputed in this report.

## Data And Method

- Input products are weekly WCDA count CSVs under `data/processed/wcda_week/`.
- Photon-count diagnostics use `excess_counts = sum(n_on - n_bkg)` plus total `n_on` and `n_bkg` curves.
- Periodicity inputs use the existing v1 excess-rate proxy `wcda_flux_excess = sum(n_on - n_bkg) / tobs` with propagated on/off errors.
- CWT uses a Morlet wavelet through `pycwt`; WWZ uses `libwwz` with `time_divisions=80` and `freq_step_factor=0.5`.
- The weekly period search range is 50-600 days.
- Strict-flux detection tiering: Tier A if median TS >= 9 or TS>=9 fraction >= 50%; Tier B if TS>=9 fraction >= 10% or TS>=4 fraction >= 25%; Tier C otherwise. Tier C peaks are diagnostic/control results only.
- Per-source Fermi-LAT prior context is summarized from `https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html` for interpretation only; it is not part of the WCDA CWT/WWZ significance calculation.

## Strict Flux Weekly Source Results

This source-first section uses 10 strict weekly flux products: Mrk 421 and Mrk 501 from `data/processed/wcda_week/`, plus the eight IHEP AGN flux products under `results/flux_strict_agn_week/`. Each source starts with strict flux (`N0`, `N0_err`) as the primary result; the older counts/excess-rate products are folded below for validation.

Detection-quality tiers are based on strict-flux weekly TS. Tier A means timing-grade quick-look input; Tier B is exploratory; Tier C is diagnostic/control only even if CWT/WWZ returns peaks.

| Source | Detection tier | Median TS | TS>=9 weeks | Method | Peak period [d] | Observed | Local FAP | Global FAP | Above 95% | Above 99% | Interpretation |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| Mrk 421 | Tier A: timing-grade | 137.90 | 218 / 229 | CWT | 129.87 | 2.796 | - | - | no | no | weekly WCDA detection quality is high enough for flux-timing interpretation |
|  |  |  |  | CWT | 367.33 | 3.700 | - | - | no | no |  |
|  |  |  |  | WWZ | 131.25 | 4.398 | 0.4815 | 0.9970 | no | no |  |
|  |  |  |  | WWZ | 383.65 | 3.188 | 0.7363 | 1.0000 | no | no |  |
| Mrk 501 | Tier A: timing-grade | 22.27 | 165 / 229 | CWT | 154.44 | 2.685 | - | - | no | no | weekly WCDA detection quality is high enough for flux-timing interpretation |
|  |  |  |  | CWT | 462.80 | 6.449 | - | - | no | no |  |
|  |  |  |  | WWZ | 149.72 | 4.508 | 0.5335 | 0.9970 | no | no |  |
|  |  |  |  | WWZ | 281.98 | 4.757 | 0.7293 | 0.9960 | no | no |  |
|  |  |  |  | WWZ | 436.07 | 8.065 | 0.3397 | 0.8861 | no | no |  |
| 1ES 1959+650 | Tier C: diagnostic only | 0.49 | 20 / 229 | CWT | 103.08 | 1.821 | - | - | no | no | low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence |
|  |  |  |  | CWT | 308.88 | 5.586 | - | - | no | no |  |
|  |  |  |  | WWZ | 108.87 | 1.761 | 0.8671 | 1.0000 | no | no |  |
|  |  |  |  | WWZ | 309.30 | 5.032 | 0.1718 | 0.6454 | no | no |  |
| 1ES 1727+502 | Tier C: diagnostic only | 1.35 | 18 / 229 | CWT | 77.22 | 1.819 | - | - | no | no | low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence |
|  |  |  |  | CWT | 129.87 | 2.037 | - | - | no | no |  |
|  |  |  |  | WWZ | 77.25 | 1.745 | 0.2607 | 0.9481 | no | no |  |
|  |  |  |  | WWZ | 136.88 | 2.224 | 0.1678 | 0.7672 | no | no |  |
|  |  |  |  | WWZ | 505.06 | 3.362 | 0.0699 | 0.2887 | no | no |  |
| 1ES 2344+514 | Tier C: diagnostic only | 0.39 | 11 / 229 | CWT | 173.36 | 3.533 | - | - | no | no | low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence |
|  |  |  |  | CWT | 367.33 | 6.118 | - | - | yes | no |  |
|  |  |  |  | WWZ | 184.30 | 3.323 | 0.2747 | 0.8931 | no | no |  |
|  |  |  |  | WWZ | 342.49 | 6.745 | 0.0370 | 0.1898 | yes | no |  |
| BL Lacertae | Tier C: diagnostic only | 0.06 | 6 / 229 | CWT | 137.59 | 1.382 | - | - | no | no | low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence |
|  |  |  |  | CWT | 308.88 | 2.944 | - | - | yes | no |  |
|  |  |  |  | WWZ | 116.84 | 1.544 | 0.3706 | 0.9510 | no | no |  |
|  |  |  |  | WWZ | 309.30 | 3.676 | 0.0180 | 0.1319 | yes | no |  |
| NGC 1275 | Tier C: diagnostic only | 0.06 | 9 / 229 | CWT | 231.40 | 5.017 | - | - | yes | no | low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence |
|  |  |  |  | CWT | 436.83 | 7.593 | - | - | yes | yes |  |
|  |  |  |  | WWZ | 239.64 | 4.606 | 0.0649 | 0.3107 | yes | no |  |
|  |  |  |  | WWZ | 505.06 | 8.233 | 0.0090 | 0.0310 | yes | yes |  |
| M 87 | Tier C: diagnostic only | 0.24 | 3 / 229 | CWT | 81.81 | 1.236 | - | - | no | no | low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence |
|  |  |  |  | CWT | 137.59 | 1.378 | - | - | no | no |  |
|  |  |  |  | CWT | 367.33 | 1.389 | - | - | no | no |  |
|  |  |  |  | WWZ | 79.17 | 1.367 | 0.1898 | 0.8951 | no | no |  |
|  |  |  |  | WWZ | 136.88 | 1.327 | 0.3067 | 0.9171 | no | no |  |
|  |  |  |  | WWZ | 383.65 | 1.434 | 0.2098 | 0.8501 | no | no |  |
| 4C +42.22 | Tier C: diagnostic only | 0.00 | 2 / 229 | CWT | 145.77 | 2.900 | - | - | no | no | low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence |
|  |  |  |  | WWZ | 149.72 | 1.835 | 0.5904 | 0.9970 | no | no |  |
| IC 310 | Tier C: diagnostic only | 0.21 | 14 / 229 | none | - | - | - | - | - | - | low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence |

### Mrk 421

`Strict flux primary result`

- Detection quality: Tier A: timing-grade; median TS 137.90; TS>=9 weeks 218 / 229 (95.2%).
- Interpretation: weekly WCDA detection quality is high enough for flux-timing interpretation.
- Usable strict-flux points: 229 / 229; excluded fit rows: 0.
- Date range: 2021-03-08 to 2025-07-27; median cadence 7.000 d.
- Flux CWT global peak: 367.33 d, GWS 3.700.
- Flux WWZ global peak: 131.25 d, mean WWZ 4.398.

![Mrk 421 strict weekly flux light curve](../data/processed/periodicity/agn_wcda_weekly_flux_survey/mkn421/wcda_strict_flux_weekly_lightcurve.png)

![Mrk 421 strict weekly flux CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_flux_survey/mkn421/wcda_strict_flux_weekly_periodicity.png)

#### Fermi-LAT prior context

- Status: Reported Fermi-LAT QPO prior.
- Prior result: The prior Fermi-LAT survey highlights Mrk 421 as a key LHAASO follow-up target: Ren+22 reports a CWT candidate at 300 +/- 64 d in 30 d bins (>5 sigma, 3 fitted cycles) and 300 +/- 65 d in 7 d bins (>5 sigma). The same survey lists Mrk 421 as one of only two direct Fermi-QPO / 1LHAASO catalog matches.
- Interpretation for this WCDA report: This is the strongest external GeV prior in the current sample and supports treating Mrk 421 as the primary timing-grade WCDA target.
- Source of context: https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html

#### Strict flux significance quick look

CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.

| Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| CWT | 129.87 | 12.29 | 2.796 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| CWT | 367.33 | 4.34 | 3.700 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 131.25 | 12.16 | 4.398 | 0.4815 | 0.9970 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 383.65 | 4.16 | 3.188 | 0.7363 | 1.0000 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |

![Mrk 421 strict flux CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_flux_survey/mkn421/wcda_strict_flux_weekly_cwt_global_significance.png)

![Mrk 421 strict flux WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_flux_survey/mkn421/wcda_strict_flux_weekly_wwz_global_significance.png)

<details>
<summary>Counts / excess-rate validation for Mrk 421</summary>

- Counts/excess-rate points: 264; MJD 59284.333-61125.167.
- Counts CWT global peak: 367.33 d, GWS 4.486.
- Counts WWZ global peak: 363.22 d, mean WWZ 5.177.

![Mrk 421 WCDA weekly photon-count diagnostic](../data/processed/periodicity/agn_wcda_weekly_survey/mkn421/wcda_weekly_counts.png)

![Mrk 421 WCDA weekly CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_survey/mkn421/wcda_weekly_periodicity.png)

![Mrk 421 counts CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_survey/mkn421/wcda_weekly_cwt_global_significance.png)

![Mrk 421 counts WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_survey/mkn421/wcda_weekly_wwz_global_significance.png)

</details>

### Mrk 501

`Strict flux primary result`

- Detection quality: Tier A: timing-grade; median TS 22.27; TS>=9 weeks 165 / 229 (72.1%).
- Interpretation: weekly WCDA detection quality is high enough for flux-timing interpretation.
- Usable strict-flux points: 229 / 229; excluded fit rows: 0.
- Date range: 2021-03-08 to 2025-07-27; median cadence 7.000 d.
- Flux CWT global peak: 462.80 d, GWS 6.449.
- Flux WWZ global peak: 436.07 d, mean WWZ 8.065.

![Mrk 501 strict weekly flux light curve](../data/processed/periodicity/agn_wcda_weekly_flux_survey/mkn501/wcda_strict_flux_weekly_lightcurve.png)

![Mrk 501 strict weekly flux CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_flux_survey/mkn501/wcda_strict_flux_weekly_periodicity.png)

#### Fermi-LAT prior context

- Status: Reported Fermi-LAT QPO prior.
- Prior result: The prior Fermi-LAT survey lists Mrk 501 as the second direct Fermi-QPO / 1LHAASO catalog match. Ren+22 reports 326 +/- 76 d in 7 d bins (>5 sigma, 7 fitted cycles) and 315 +/- 98 d in 30 d bins (2.9 sigma).
- Interpretation for this WCDA report: This is a useful GeV prior, but the 30 d versus 7 d difference flags binning sensitivity; WCDA results should be interpreted with that caveat.
- Source of context: https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html

#### Strict flux significance quick look

CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.

| Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| CWT | 154.44 | 10.33 | 2.685 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| CWT | 462.80 | 3.45 | 6.449 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. Fewer than four observed cycles. |
| WWZ | 149.72 | 10.66 | 4.508 | 0.5335 | 0.9970 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 281.98 | 5.66 | 4.757 | 0.7293 | 0.9960 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 436.07 | 3.66 | 8.065 | 0.3397 | 0.8861 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. Fewer than four observed cycles. |

![Mrk 501 strict flux CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_flux_survey/mkn501/wcda_strict_flux_weekly_cwt_global_significance.png)

![Mrk 501 strict flux WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_flux_survey/mkn501/wcda_strict_flux_weekly_wwz_global_significance.png)

<details>
<summary>Counts / excess-rate validation for Mrk 501</summary>

- Counts/excess-rate points: 264; MJD 59284.333-61125.167.
- Counts CWT global peak: 389.17 d, GWS 4.407.
- Counts WWZ global peak: 402.98 d, mean WWZ 6.385.

![Mrk 501 WCDA weekly photon-count diagnostic](../data/processed/periodicity/agn_wcda_weekly_survey/mkn501/wcda_weekly_counts.png)

![Mrk 501 WCDA weekly CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_survey/mkn501/wcda_weekly_periodicity.png)

![Mrk 501 counts CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_survey/mkn501/wcda_weekly_cwt_global_significance.png)

![Mrk 501 counts WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_survey/mkn501/wcda_weekly_wwz_global_significance.png)

</details>

### 1ES 1959+650

`Strict flux primary result`

- Detection quality: Tier C: diagnostic only; median TS 0.49; TS>=9 weeks 20 / 229 (8.7%).
- Interpretation: low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence.
- Usable strict-flux points: 228 / 229; excluded fit rows: 1.
- Date range: 2021-03-08 to 2025-07-27; median cadence 7.000 d.
- Flux CWT global peak: 308.88 d, GWS 5.586.
- Flux WWZ global peak: 309.30 d, mean WWZ 5.032.

**Low-TS caveat:** this source is not significantly detected in most weekly strict-flux bins. Treat the periodicity maps and AR(1) quick-look rows as diagnostics only, not as LHAASO QPO evidence.

![1ES 1959+650 strict weekly flux light curve](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es1959p650/wcda_strict_flux_weekly_lightcurve.png)

![1ES 1959+650 strict weekly flux CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es1959p650/wcda_strict_flux_weekly_periodicity.png)

#### Fermi-LAT prior context

- Status: No exact-source Fermi-LAT QPO prior in the survey.
- Prior result: The prior Fermi-LAT QPO survey does not list 1ES 1959+650 as an exact-source QPO candidate in its compiled 2020-2025 sample.
- Interpretation for this WCDA report: Use the WCDA strict-flux detection tier and internal CWT/WWZ checks as the main screening evidence; there is no supporting GeV-QPO prior from that survey.
- Source of context: https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html

#### Strict flux significance quick look

CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.

| Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| CWT | 103.08 | 15.48 | 1.821 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| CWT | 308.88 | 5.17 | 5.586 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 108.87 | 14.66 | 1.761 | 0.8671 | 1.0000 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 309.30 | 5.16 | 5.032 | 0.1718 | 0.6454 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |

![1ES 1959+650 strict flux CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es1959p650/wcda_strict_flux_weekly_cwt_global_significance.png)

![1ES 1959+650 strict flux WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es1959p650/wcda_strict_flux_weekly_wwz_global_significance.png)

<details>
<summary>Counts / excess-rate validation for 1ES 1959+650</summary>

- Counts/excess-rate points: 264; MJD 59284.333-61125.167.
- Counts CWT global peak: 327.25 d, GWS 4.874.
- Counts WWZ global peak: 330.61 d, mean WWZ 5.274.

![1ES 1959+650 WCDA weekly photon-count diagnostic](../data/processed/periodicity/agn_wcda_weekly_survey/1es1959p650/wcda_weekly_counts.png)

![1ES 1959+650 WCDA weekly CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_survey/1es1959p650/wcda_weekly_periodicity.png)

![1ES 1959+650 counts CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_survey/1es1959p650/wcda_weekly_cwt_global_significance.png)

![1ES 1959+650 counts WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_survey/1es1959p650/wcda_weekly_wwz_global_significance.png)

</details>

### 1ES 1727+502

`Strict flux primary result`

- Detection quality: Tier C: diagnostic only; median TS 1.35; TS>=9 weeks 18 / 229 (7.9%).
- Interpretation: low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence.
- Usable strict-flux points: 229 / 229; excluded fit rows: 0.
- Date range: 2021-03-08 to 2025-07-27; median cadence 7.000 d.
- Flux CWT global peak: 583.10 d, GWS 2.926.
- Flux WWZ global peak: 505.06 d, mean WWZ 3.362.

**Low-TS caveat:** this source is not significantly detected in most weekly strict-flux bins. Treat the periodicity maps and AR(1) quick-look rows as diagnostics only, not as LHAASO QPO evidence.

![1ES 1727+502 strict weekly flux light curve](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es1727p502/wcda_strict_flux_weekly_lightcurve.png)

![1ES 1727+502 strict weekly flux CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es1727p502/wcda_strict_flux_weekly_periodicity.png)

#### Fermi-LAT prior context

- Status: No exact-source Fermi-LAT QPO prior in the survey.
- Prior result: The prior Fermi-LAT report mentions 1ES 1727+502 in the reverse LHAASO catalog cross-match context, but explicitly not as a member of the compiled Fermi-QPO sample.
- Interpretation for this WCDA report: Treat this as a WCDA-driven exploratory target rather than a GeV-prior target.
- Source of context: https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html

#### Strict flux significance quick look

CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.

| Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| CWT | 77.22 | 20.67 | 1.819 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| CWT | 129.87 | 12.29 | 2.037 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 77.25 | 20.66 | 1.745 | 0.2607 | 0.9481 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 136.88 | 11.66 | 2.224 | 0.1678 | 0.7672 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 505.06 | 3.16 | 3.362 | 0.0699 | 0.2887 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. Fewer than four observed cycles. |

![1ES 1727+502 strict flux CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es1727p502/wcda_strict_flux_weekly_cwt_global_significance.png)

![1ES 1727+502 strict flux WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es1727p502/wcda_strict_flux_weekly_wwz_global_significance.png)

<details>
<summary>Counts / excess-rate validation for 1ES 1727+502</summary>

- Counts/excess-rate points: 264; MJD 59284.333-61125.167.
- Counts CWT global peak: 308.88 d, GWS 2.690.
- Counts WWZ global peak: 303.36 d, mean WWZ 3.224.

![1ES 1727+502 WCDA weekly photon-count diagnostic](../data/processed/periodicity/agn_wcda_weekly_survey/1es1727p502/wcda_weekly_counts.png)

![1ES 1727+502 WCDA weekly CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_survey/1es1727p502/wcda_weekly_periodicity.png)

![1ES 1727+502 counts CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_survey/1es1727p502/wcda_weekly_cwt_global_significance.png)

![1ES 1727+502 counts WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_survey/1es1727p502/wcda_weekly_wwz_global_significance.png)

</details>

### 1ES 2344+514

`Strict flux primary result`

- Detection quality: Tier C: diagnostic only; median TS 0.39; TS>=9 weeks 11 / 229 (4.8%).
- Interpretation: low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence.
- Usable strict-flux points: 229 / 229; excluded fit rows: 0.
- Date range: 2021-03-08 to 2025-07-27; median cadence 7.000 d.
- Flux CWT global peak: 583.10 d, GWS 8.041.
- Flux WWZ global peak: 600.00 d, mean WWZ 7.838.

**Low-TS caveat:** this source is not significantly detected in most weekly strict-flux bins. Treat the periodicity maps and AR(1) quick-look rows as diagnostics only, not as LHAASO QPO evidence.

![1ES 2344+514 strict weekly flux light curve](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es2344p514/wcda_strict_flux_weekly_lightcurve.png)

![1ES 2344+514 strict weekly flux CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es2344p514/wcda_strict_flux_weekly_periodicity.png)

#### Fermi-LAT prior context

- Status: No exact-source Fermi-LAT QPO prior in the survey.
- Prior result: The prior Fermi-LAT report only brings 1ES 2344+514 into positional cross-match context; it is not listed as an exact-source Fermi-QPO candidate.
- Interpretation for this WCDA report: Any WCDA periodicity feature should stand on the WCDA detection quality and significance checks, not on a prior Fermi-LAT QPO claim.
- Source of context: https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html

#### Strict flux significance quick look

CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.

| Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| CWT | 173.36 | 9.21 | 3.533 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| CWT | 367.33 | 4.34 | 6.118 | - | - | yes | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 184.30 | 8.66 | 3.323 | 0.2747 | 0.8931 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 342.49 | 4.66 | 6.745 | 0.0370 | 0.1898 | yes | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |

![1ES 2344+514 strict flux CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es2344p514/wcda_strict_flux_weekly_cwt_global_significance.png)

![1ES 2344+514 strict flux WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_flux_survey/1es2344p514/wcda_strict_flux_weekly_wwz_global_significance.png)

<details>
<summary>Counts / excess-rate validation for 1ES 2344+514</summary>

- Counts/excess-rate points: 264; MJD 59284.333-61125.167.
- Counts CWT global peak: 218.41 d, GWS 1.987.
- Counts WWZ global peak: 89.50 d, mean WWZ 2.043.

![1ES 2344+514 WCDA weekly photon-count diagnostic](../data/processed/periodicity/agn_wcda_weekly_survey/1es2344p514/wcda_weekly_counts.png)

![1ES 2344+514 WCDA weekly CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_survey/1es2344p514/wcda_weekly_periodicity.png)

![1ES 2344+514 counts CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_survey/1es2344p514/wcda_weekly_cwt_global_significance.png)

![1ES 2344+514 counts WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_survey/1es2344p514/wcda_weekly_wwz_global_significance.png)

</details>

### BL Lacertae

`Strict flux primary result`

- Detection quality: Tier C: diagnostic only; median TS 0.06; TS>=9 weeks 6 / 229 (2.6%).
- Interpretation: low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence.
- Usable strict-flux points: 229 / 229; excluded fit rows: 0.
- Date range: 2021-03-08 to 2025-07-27; median cadence 7.000 d.
- Flux CWT global peak: 583.10 d, GWS 7.418.
- Flux WWZ global peak: 600.00 d, mean WWZ 5.145.

**Low-TS caveat:** this source is not significantly detected in most weekly strict-flux bins. Treat the periodicity maps and AR(1) quick-look rows as diagnostics only, not as LHAASO QPO evidence.

![BL Lacertae strict weekly flux light curve](../data/processed/periodicity/agn_wcda_weekly_flux_survey/bllac/wcda_strict_flux_weekly_lightcurve.png)

![BL Lacertae strict weekly flux CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_flux_survey/bllac/wcda_strict_flux_weekly_periodicity.png)

#### Fermi-LAT prior context

- Status: No exact-source Fermi-LAT QPO prior in the survey.
- Prior result: The prior Fermi-LAT report contains many BL Lac class objects, but it does not list BL Lacertae itself as an exact-source QPO candidate in the compiled sample.
- Interpretation for this WCDA report: Do not infer a Fermi-QPO prior from class-level BL Lac mentions; interpret this source from its own WCDA strict-flux statistics.
- Source of context: https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html

#### Strict flux significance quick look

CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.

| Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| CWT | 137.59 | 11.60 | 1.382 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| CWT | 308.88 | 5.17 | 2.944 | - | - | yes | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 116.84 | 13.66 | 1.544 | 0.3706 | 0.9510 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 309.30 | 5.16 | 3.676 | 0.0180 | 0.1319 | yes | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |

![BL Lacertae strict flux CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_flux_survey/bllac/wcda_strict_flux_weekly_cwt_global_significance.png)

![BL Lacertae strict flux WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_flux_survey/bllac/wcda_strict_flux_weekly_wwz_global_significance.png)

<details>
<summary>Counts / excess-rate validation for BL Lacertae</summary>

- Counts/excess-rate points: 264; MJD 59284.333-61125.167.
- Counts CWT global peak: 583.10 d, GWS 2.784.
- Counts WWZ global peak: 600.00 d, mean WWZ 3.175.

![BL Lacertae WCDA weekly photon-count diagnostic](../data/processed/periodicity/agn_wcda_weekly_survey/bllac/wcda_weekly_counts.png)

![BL Lacertae WCDA weekly CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_survey/bllac/wcda_weekly_periodicity.png)

![BL Lacertae counts CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_survey/bllac/wcda_weekly_cwt_global_significance.png)

![BL Lacertae counts WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_survey/bllac/wcda_weekly_wwz_global_significance.png)

</details>

### NGC 1275

`Strict flux primary result`

- Detection quality: Tier C: diagnostic only; median TS 0.06; TS>=9 weeks 9 / 229 (3.9%).
- Interpretation: low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence.
- Usable strict-flux points: 229 / 229; excluded fit rows: 0.
- Date range: 2021-03-08 to 2025-07-27; median cadence 7.000 d.
- Flux CWT global peak: 436.83 d, GWS 7.593.
- Flux WWZ global peak: 505.06 d, mean WWZ 8.233.

**Low-TS caveat:** this source is not significantly detected in most weekly strict-flux bins. Treat the periodicity maps and AR(1) quick-look rows as diagnostics only, not as LHAASO QPO evidence.

![NGC 1275 strict weekly flux light curve](../data/processed/periodicity/agn_wcda_weekly_flux_survey/ngc1275/wcda_strict_flux_weekly_lightcurve.png)

![NGC 1275 strict weekly flux CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_flux_survey/ngc1275/wcda_strict_flux_weekly_periodicity.png)

#### Fermi-LAT prior context

- Status: Mixed / weak external prior.
- Prior result: The prior Fermi-LAT survey lists NGC 1275 as a Ren+22 CWT candidate in the LHAASO field of view, with a 92 +/- 33 d 7 d-bin feature (>5 sigma, 4 cycles). The same report places it outside the direct 1LHAASO catalog-match tier and notes weak TeV status compared with Mrk 421/501.
- Interpretation for this WCDA report: This is not a strong WCDA timing prior. Combined with low weekly strict-flux TS here, NGC 1275 should remain a diagnostic/control case unless stronger VHE detection quality is established.
- Source of context: https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html

#### Strict flux significance quick look

CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.

| Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| CWT | 231.40 | 6.90 | 5.017 | - | - | yes | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| CWT | 436.83 | 3.65 | 7.593 | - | - | yes | yes | 0 | Quick-look candidate peak; no source/method/survey trial correction. Fewer than four observed cycles. |
| WWZ | 239.64 | 6.66 | 4.606 | 0.0649 | 0.3107 | yes | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 505.06 | 3.16 | 8.233 | 0.0090 | 0.0310 | yes | yes | 1000 | Quick-look candidate peak; no source/method/survey trial correction. Fewer than four observed cycles. |

![NGC 1275 strict flux CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_flux_survey/ngc1275/wcda_strict_flux_weekly_cwt_global_significance.png)

![NGC 1275 strict flux WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_flux_survey/ngc1275/wcda_strict_flux_weekly_wwz_global_significance.png)

<details>
<summary>Counts / excess-rate validation for NGC 1275</summary>

- Counts/excess-rate points: 264; MJD 59284.333-61125.167.
- Counts CWT global peak: 173.36 d, GWS 3.096.
- Counts WWZ global peak: 174.19 d, mean WWZ 2.833.

![NGC 1275 WCDA weekly photon-count diagnostic](../data/processed/periodicity/agn_wcda_weekly_survey/ngc1275/wcda_weekly_counts.png)

![NGC 1275 WCDA weekly CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_survey/ngc1275/wcda_weekly_periodicity.png)

![NGC 1275 counts CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_survey/ngc1275/wcda_weekly_cwt_global_significance.png)

![NGC 1275 counts WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_survey/ngc1275/wcda_weekly_wwz_global_significance.png)

</details>

### M 87

`Strict flux primary result`

- Detection quality: Tier C: diagnostic only; median TS 0.24; TS>=9 weeks 3 / 229 (1.3%).
- Interpretation: low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence.
- Usable strict-flux points: 229 / 229; excluded fit rows: 0.
- Date range: 2021-03-08 to 2025-07-27; median cadence 7.000 d.
- Flux CWT global peak: 367.33 d, GWS 1.389.
- Flux WWZ global peak: 383.65 d, mean WWZ 1.434.

**Low-TS caveat:** this source is not significantly detected in most weekly strict-flux bins. Treat the periodicity maps and AR(1) quick-look rows as diagnostics only, not as LHAASO QPO evidence.

![M 87 strict weekly flux light curve](../data/processed/periodicity/agn_wcda_weekly_flux_survey/m87/wcda_strict_flux_weekly_lightcurve.png)

![M 87 strict weekly flux CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_flux_survey/m87/wcda_strict_flux_weekly_periodicity.png)

#### Fermi-LAT prior context

- Status: No exact-source Fermi-LAT QPO prior in the survey.
- Prior result: The prior Fermi-LAT QPO survey does not list M 87 as an exact-source QPO candidate in the compiled 2020-2025 sample.
- Interpretation for this WCDA report: Use this source mainly as a radio-galaxy comparison/control target in the WCDA survey.
- Source of context: https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html

#### Strict flux significance quick look

CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.

| Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| CWT | 81.81 | 19.51 | 1.236 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| CWT | 137.59 | 11.60 | 1.378 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| CWT | 367.33 | 4.34 | 1.389 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 79.17 | 20.16 | 1.367 | 0.1898 | 0.8951 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 136.88 | 11.66 | 1.327 | 0.3067 | 0.9171 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 383.65 | 4.16 | 1.434 | 0.2098 | 0.8501 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |

![M 87 strict flux CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_flux_survey/m87/wcda_strict_flux_weekly_cwt_global_significance.png)

![M 87 strict flux WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_flux_survey/m87/wcda_strict_flux_weekly_wwz_global_significance.png)

<details>
<summary>Counts / excess-rate validation for M 87</summary>

- Counts/excess-rate points: 264; MJD 59284.333-61125.167.
- Counts CWT global peak: 389.17 d, GWS 2.292.
- Counts WWZ global peak: 402.98 d, mean WWZ 2.804.

![M 87 WCDA weekly photon-count diagnostic](../data/processed/periodicity/agn_wcda_weekly_survey/m87/wcda_weekly_counts.png)

![M 87 WCDA weekly CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_survey/m87/wcda_weekly_periodicity.png)

![M 87 counts CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_survey/m87/wcda_weekly_cwt_global_significance.png)

![M 87 counts WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_survey/m87/wcda_weekly_wwz_global_significance.png)

</details>

### 4C +42.22

`Strict flux primary result`

- Detection quality: Tier C: diagnostic only; median TS 0.00; TS>=9 weeks 2 / 229 (0.9%).
- Interpretation: low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence.
- Usable strict-flux points: 229 / 229; excluded fit rows: 0.
- Date range: 2021-03-08 to 2025-07-27; median cadence 7.000 d.
- Flux CWT global peak: 145.77 d, GWS 2.900.
- Flux WWZ global peak: 149.72 d, mean WWZ 1.835.

**Low-TS caveat:** this source is not significantly detected in most weekly strict-flux bins. Treat the periodicity maps and AR(1) quick-look rows as diagnostics only, not as LHAASO QPO evidence.

![4C +42.22 strict weekly flux light curve](../data/processed/periodicity/agn_wcda_weekly_flux_survey/4c_p42d22/wcda_strict_flux_weekly_lightcurve.png)

![4C +42.22 strict weekly flux CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_flux_survey/4c_p42d22/wcda_strict_flux_weekly_periodicity.png)

#### Fermi-LAT prior context

- Status: No exact-source Fermi-LAT QPO prior in the survey.
- Prior result: The prior Fermi-LAT QPO survey does not list 4C +42.22 as an exact-source QPO candidate in its compiled sample.
- Interpretation for this WCDA report: Treat any WCDA periodicity feature as exploratory and require WCDA-side robustness before assigning physical weight.
- Source of context: https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html

#### Strict flux significance quick look

CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.

| Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| CWT | 145.77 | 10.95 | 2.900 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| WWZ | 149.72 | 10.66 | 1.835 | 0.5904 | 0.9970 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |

![4C +42.22 strict flux CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_flux_survey/4c_p42d22/wcda_strict_flux_weekly_cwt_global_significance.png)

![4C +42.22 strict flux WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_flux_survey/4c_p42d22/wcda_strict_flux_weekly_wwz_global_significance.png)

<details>
<summary>Counts / excess-rate validation for 4C +42.22</summary>

- Counts/excess-rate points: 262; MJD 59284.333-61125.167.
- Counts CWT global peak: 145.77 d, GWS 2.027.
- Counts WWZ global peak: 140.87 d, mean WWZ 2.282.

![4C +42.22 WCDA weekly photon-count diagnostic](../data/processed/periodicity/agn_wcda_weekly_survey/4c_p42d22/wcda_weekly_counts.png)

![4C +42.22 WCDA weekly CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_survey/4c_p42d22/wcda_weekly_periodicity.png)

![4C +42.22 counts CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_survey/4c_p42d22/wcda_weekly_cwt_global_significance.png)

![4C +42.22 counts WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_survey/4c_p42d22/wcda_weekly_wwz_global_significance.png)

</details>

### IC 310

`Strict flux primary result`

- Detection quality: Tier C: diagnostic only; median TS 0.21; TS>=9 weeks 14 / 229 (6.1%).
- Interpretation: low weekly TS; periodicity peaks are diagnostics, not LHAASO QPO evidence.
- Usable strict-flux points: 229 / 229; excluded fit rows: 0.
- Date range: 2021-03-08 to 2025-07-27; median cadence 7.000 d.
- Flux CWT global peak: 583.10 d, GWS 11.078.
- Flux WWZ global peak: 600.00 d, mean WWZ 10.923.

**Low-TS caveat:** this source is not significantly detected in most weekly strict-flux bins. Treat the periodicity maps and AR(1) quick-look rows as diagnostics only, not as LHAASO QPO evidence.

![IC 310 strict weekly flux light curve](../data/processed/periodicity/agn_wcda_weekly_flux_survey/ic310/wcda_strict_flux_weekly_lightcurve.png)

![IC 310 strict weekly flux CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_flux_survey/ic310/wcda_strict_flux_weekly_periodicity.png)

#### Fermi-LAT prior context

- Status: No exact-source Fermi-LAT QPO prior in the survey.
- Prior result: The prior Fermi-LAT QPO survey does not list IC 310 as an exact-source QPO candidate in the compiled 2020-2025 sample.
- Interpretation for this WCDA report: This remains a WCDA-driven exploratory/flaring target rather than a Fermi-prior QPO target.
- Source of context: https://pluto235.github.io/any-reports/qpo-fermi-lat-detections.html

#### Strict flux significance quick look

CWT uses an AR(1) theory reference; WWZ uses AR(1) Gaussian surrogates on the same strict-flux weekly sampling. These are not source-level, method-level, or survey-level trial corrected.

_No strict-flux significance rows found for this source._

![IC 310 strict flux CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_flux_survey/ic310/wcda_strict_flux_weekly_cwt_global_significance.png)

![IC 310 strict flux WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_flux_survey/ic310/wcda_strict_flux_weekly_wwz_global_significance.png)

<details>
<summary>Counts / excess-rate validation for IC 310</summary>

- Counts/excess-rate points: 264; MJD 59284.333-61125.167.
- Counts CWT global peak: 389.17 d, GWS 4.057.
- Counts WWZ global peak: 402.98 d, mean WWZ 4.337.

![IC 310 WCDA weekly photon-count diagnostic](../data/processed/periodicity/agn_wcda_weekly_survey/ic310/wcda_weekly_counts.png)

![IC 310 WCDA weekly CWT and WWZ quick-look](../data/processed/periodicity/agn_wcda_weekly_survey/ic310/wcda_weekly_periodicity.png)

![IC 310 counts CWT AR(1) reference](../data/processed/periodicity/agn_wcda_weekly_survey/ic310/wcda_weekly_cwt_global_significance.png)

![IC 310 counts WWZ AR(1) surrogate significance](../data/processed/periodicity/agn_wcda_weekly_survey/ic310/wcda_weekly_wwz_global_significance.png)

</details>

## Counts / Excess-Rate Overview

The original 10-source counts/excess-rate quick-look is kept here as a secondary overview. The detailed counts figures are also available in each source's collapsed validation block above.

| Source | Series | N | MJD min | MJD max | Median dt [d] | CWT peak [d] | CWT GWS | WWZ peak [d] | WWZ power |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mrk 421 | wcda_weekly | 264 | 59284.333 | 61125.167 | 7.000 | 367.33 | 4.486 | 363.22 | 5.177 |
| Mrk 501 | wcda_weekly | 264 | 59284.333 | 61125.167 | 7.000 | 389.17 | 4.407 | 402.98 | 6.385 |
| 1ES 1959+650 | wcda_weekly | 264 | 59284.333 | 61125.167 | 7.000 | 327.25 | 4.874 | 330.61 | 5.274 |
| 1ES 1727+502 | wcda_weekly | 264 | 59284.333 | 61125.167 | 7.000 | 308.88 | 2.690 | 303.36 | 3.224 |
| 1ES 2344+514 | wcda_weekly | 264 | 59284.333 | 61125.167 | 7.000 | 218.41 | 1.987 | 89.50 | 2.043 |
| BL Lacertae | wcda_weekly | 264 | 59284.333 | 61125.167 | 7.000 | 583.10 | 2.784 | 600.00 | 3.175 |
| NGC 1275 | wcda_weekly | 264 | 59284.333 | 61125.167 | 7.000 | 173.36 | 3.096 | 174.19 | 2.833 |
| M 87 | wcda_weekly | 264 | 59284.333 | 61125.167 | 7.000 | 389.17 | 2.292 | 402.98 | 2.804 |
| 4C +42.22 | wcda_weekly | 262 | 59284.333 | 61125.167 | 7.000 | 145.77 | 2.027 | 140.87 | 2.282 |
| IC 310 | wcda_weekly | 264 | 59284.333 | 61125.167 | 7.000 | 389.17 | 4.057 | 402.98 | 4.337 |

## Significance Quick Look

CWT rows use an AR(1) theory reference from PyCWT. WWZ rows use AR(1) Gaussian surrogates on the same weekly sampling and report both local-window and global-search FAP. These are not source-level, method-level, or survey-level trial corrected.

| Source | Method | Period [d] | Cycles | Observed | Local FAP | Global FAP | Above 95% | Above 99% | N sim | Note |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| Mrk 421 | CWT | 129.87 | 14.17 | 2.965 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| Mrk 421 | CWT | 367.33 | 5.01 | 4.486 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| Mrk 421 | WWZ | 135.67 | 13.57 | 4.634 | 0.4665 | 0.9980 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| Mrk 421 | WWZ | 363.22 | 5.07 | 5.177 | 0.6244 | 0.9940 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| Mrk 501 | CWT | 137.59 | 13.38 | 1.270 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| Mrk 501 | CWT | 389.17 | 4.73 | 4.407 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| Mrk 501 | WWZ | 61.22 | 30.07 | 1.783 | 0.5165 | 1.0000 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| Mrk 501 | WWZ | 140.87 | 13.07 | 1.761 | 0.7113 | 1.0000 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| Mrk 501 | WWZ | 402.98 | 4.57 | 6.385 | 0.0310 | 0.1189 | yes | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 1959+650 | CWT | 327.25 | 5.63 | 4.874 | - | - | yes | yes | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 1959+650 | WWZ | 330.61 | 5.57 | 5.274 | 0.0070 | 0.0270 | yes | yes | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 1727+502 | CWT | 115.70 | 15.91 | 1.488 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 1727+502 | CWT | 308.88 | 5.96 | 2.690 | - | - | yes | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 1727+502 | WWZ | 79.80 | 23.07 | 1.416 | 0.4685 | 0.9860 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 1727+502 | WWZ | 135.67 | 13.57 | 1.859 | 0.2468 | 0.8482 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 1727+502 | WWZ | 303.36 | 6.07 | 3.224 | 0.0340 | 0.1858 | yes | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 2344+514 | CWT | 86.68 | 21.24 | 1.725 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 2344+514 | CWT | 218.41 | 8.43 | 1.987 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 2344+514 | WWZ | 89.50 | 20.57 | 2.043 | 0.0649 | 0.6434 | yes | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| 1ES 2344+514 | WWZ | 214.85 | 8.57 | 2.017 | 0.1508 | 0.6573 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| BL Lacertae | CWT | 109.21 | 16.86 | 2.016 | - | - | yes | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| BL Lacertae | CWT | 308.88 | 5.96 | 1.497 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| BL Lacertae | WWZ | 111.11 | 16.57 | 2.249 | 0.0300 | 0.4086 | yes | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| BL Lacertae | WWZ | 192.39 | 9.57 | 0.944 | 0.6543 | 1.0000 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| BL Lacertae | WWZ | 303.36 | 6.07 | 1.516 | 0.3087 | 0.8931 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| NGC 1275 | CWT | 86.68 | 21.24 | 1.630 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| NGC 1275 | CWT | 173.36 | 10.62 | 3.096 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| NGC 1275 | CWT | 367.33 | 5.01 | 2.665 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| NGC 1275 | WWZ | 89.50 | 20.57 | 2.101 | 0.2787 | 0.9510 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| NGC 1275 | WWZ | 174.19 | 10.57 | 2.833 | 0.1658 | 0.7073 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| NGC 1275 | WWZ | 363.22 | 5.07 | 2.712 | 0.2048 | 0.7662 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| M 87 | CWT | 103.08 | 17.86 | 1.707 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| M 87 | CWT | 218.41 | 8.43 | 0.976 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| M 87 | CWT | 389.17 | 4.73 | 2.292 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| M 87 | WWZ | 104.78 | 17.57 | 2.044 | 0.0989 | 0.7003 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| M 87 | WWZ | 228.16 | 8.07 | 1.024 | 0.6683 | 1.0000 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| M 87 | WWZ | 402.98 | 4.57 | 2.804 | 0.0849 | 0.3177 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| 4C +42.22 | CWT | 145.77 | 12.63 | 2.027 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| 4C +42.22 | WWZ | 140.87 | 13.07 | 2.282 | 0.0579 | 0.4715 | yes | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| IC 310 | CWT | 86.68 | 21.24 | 1.411 | - | - | no | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| IC 310 | CWT | 389.17 | 4.73 | 4.057 | - | - | yes | no | 0 | Quick-look candidate peak; no source/method/survey trial correction. |
| IC 310 | WWZ | 87.38 | 21.07 | 1.560 | 0.4865 | 0.9920 | no | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |
| IC 310 | WWZ | 402.98 | 4.57 | 4.337 | 0.0200 | 0.1079 | yes | no | 1000 | Quick-look candidate peak; no source/method/survey trial correction. |

## Outputs

- Survey aligned CSVs: `data/processed/aligned/agn_wcda_weekly_survey/<source_id>/wcda_weekly_aligned.csv`.
- Survey arrays and figures: `data/processed/periodicity/agn_wcda_weekly_survey/<source_id>/`.
- Survey summary CSV: `data/processed/periodicity/agn_wcda_weekly_survey/agn_wcda_weekly_survey_summary.csv`.
- Strict flux aligned CSVs: `data/processed/aligned/agn_wcda_weekly_flux_survey/<source_id>/wcda_strict_flux_weekly_aligned.csv`.
- Strict flux arrays and figures: `data/processed/periodicity/agn_wcda_weekly_flux_survey/<source_id>/`.
- Strict flux summary CSV: `data/processed/periodicity/agn_wcda_weekly_flux_survey/agn_wcda_weekly_flux_survey_summary.csv`.
