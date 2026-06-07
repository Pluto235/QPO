# Mrk 421 / Mrk 501 WCDA Periodicity Analysis v1

Generated from local pipeline outputs in `data/processed/periodicity/{mkn421,mkn501}/`. Current report date: 2026-06-01.

This version keeps the existing Mrk 421 WCDA/Fermi quick-look analysis and the Mrk 501 LHAASO-WCDA weekly light curve. It runs CWT and WWZ checks, adds a first local-significance assessment for the current Mrk 421 and Mrk 501 WCDA weekly candidate peaks, and adds a fixed-window Mrk 421 MJD 59500-60500 local-only check. It also keeps a TELAMON 14 mm / 7 mm weekly comparison as the main radio-LHAASO timing supplement and adds a same-window Mrk 421 optical/near-UV alignment supplement.

The updated figures use a clearer layout: the light curve is shown across the first row, while CWT and WWZ maps are separated on the second row. In the regular periodicity section after the xgm poster comparison, WWZ main displays now use linear heatmap color normalization; previous log-color versions are retained as visual references. The period axis remains log-scaled.

## Peak Summary

| Source | Series | N | MJD min | MJD max | Median dt [d] | CWT peak [d] | CWT GWS | WWZ peak [d] | WWZ power |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mrk 421 | WCDA daily | 360 | 60763.167 | 61128.167 | 1.000 | 104.95 | 19.650 | 109.77 | 29.772 |
| Mrk 421 | WCDA weekly | 264 | 59284.333 | 61125.167 | 7.000 | 367.33 | 4.486 | 363.22 | 5.177 |
| Mrk 421 | Fermi weekly on WCDA axis | 250 | 59284.333 | 61062.167 | 7.000 | 583.10 | 2.828 | 513.37 | 3.260 |
| Mrk 501 | WCDA weekly | 264 | 59284.333 | 61125.167 | 7.000 | 389.17 | 4.407 | 402.98 | 6.385 |

## Figure Notes

- Mrk 421 WCDA daily covers 2025-03-29 04:00 UTC to 2026-03-29 04:00 UTC.
- Mrk 421 WCDA daily: CWT peak 104.95 d (GWS 19.650); WWZ peak 109.77 d (power 29.772).
- Mrk 421 WCDA weekly covers 2021-03-11 07:59 UTC to 2026-03-26 04:00 UTC.
- Mrk 421 WCDA weekly: CWT peak 367.33 d (GWS 4.486); WWZ peak 363.22 d (power 5.177).
- Mrk 421 Fermi weekly on WCDA axis covers 2021-03-11 07:59 UTC to 2026-01-22 04:00 UTC.
- Mrk 421 Fermi weekly on WCDA axis: CWT peak 583.10 d (GWS 2.828); WWZ peak 513.37 d (power 3.260).
- Mrk 501 WCDA weekly covers 2021-03-11 07:59 UTC to 2026-03-26 04:00 UTC.
- Mrk 501 WCDA weekly: CWT peak 389.17 d (GWS 4.407); WWZ peak 402.98 d (power 6.385).

The quick-look CWT/WWZ maps are not post-trial significance products. The local-significance section below gives a first local-only assessment of the current weekly candidate peaks; no look-elsewhere, source-level, or method-level trial correction is applied.

## 2022-2026 TELAMON-LHAASO Weekly Alignment Supplement

This longer supplement uses the public TELAMON Mrk 421 source page, [`1104+3812`](https://telamon.astro.uni-wuerzburg.de/sources/1104-3812), and parses the embedded Plotly averaged light-curve arrays for `aver_lc14` and `aver_lc7`. These are TELAMON averaged 14 mm and 7 mm flux-density light curves in Jy, not single-frequency measurements. The local parsed cache has 110 total TELAMON rows: 14 mm = 65 and 7 mm = 45.

The plotted overlap with the local WCDA weekly file covers MJD 59580.0000-61125.1667. Within that synchronized window there are 221 finite WCDA weekly points, 33 TELAMON 14 mm points, and 25 TELAMON 7 mm points. The top panel again uses `WCDA excess-rate proxy = sum(n_on - n_bkg) / tobs`, not calibrated physical flux. TELAMON extends slightly later than the current WCDA weekly file, so the figure is clipped at the WCDA weekly endpoint.

![Mrk 421 TELAMON-LHAASO weekly alignment](../data/processed/multiwavelength/mkn421/telamon_lhaaso_2022_2026/mkn421_telamon_lhaaso_2022_2026_weekly.png)

This figure is for visual timing context only and reports no DCF, FAP, correlation coefficient, lag, or QPO significance.

## 2021-2026 Optical/UV-LHAASO Alignment Supplement

This supplement adds public optical and near-UV monitoring points for Mrk 421 in the local WCDA weekly window. The input sources are local ATLAS forced photometry, local ASAS-SN Sky Patrol, freshly cached public ZTF light curves, AAVSO VSX export data, and the CDS/VizieR A&A 684 A127 `fig1.dat` table used as the directly downloadable numerical counterpart to the 2022 IXPE/MWL campaign context. The Nature Astronomy IXPE supporting data are not treated as a hard dependency in this pass.

The plotted window is MJD 59284.333-61125.167. The main optical panel contains 3487 quick-look flux-density points after quality cuts, and the separate Swift-UVOT near-UV panel contains 126 points. The lower panel again uses the local WCDA weekly `flux_excess = sum(n_on - n_bkg) / tobs` proxy, not calibrated physical gamma-ray flux. Optical magnitudes are converted to approximate `F_nu` in mJy for visualization only; no host-galaxy subtraction, color correction, cross-filter normalization, or SED modeling is applied.

| Survey | Panel | Band | Input rows | Plotted rows | MJD min | MJD max |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| ATLAS | optical | c | 613 | 463 | 59284.3833 | 61091.5638 |
| ATLAS | optical | o | 2246 | 923 | 59297.4440 | 61026.5672 |
| ASAS-SN Sky Patrol | optical | g | 239 | 195 | 59295.2574 | 60451.2869 |
| ZTF public | optical | zg | 277 | 277 | 59290.2290 | 60814.2876 |
| ZTF public | optical | zr | 262 | 262 | 59290.2614 | 60942.5267 |
| ZTF public | optical | zi | 18 | 18 | 59308.3061 | 60067.3904 |
| AAVSO | optical | Vis. | 1104 | 1103 | 59284.9440 | 61124.9320 |
| AAVSO | optical | B/V/R/CV/CR/TG | 212 | 212 | 59296.8104 | 61116.9292 |
| CDS/VizieR A&A 684 A127 | optical | R-band | 76 | 34 | 59703.0000 | 59747.7901 |
| CDS/VizieR A&A 684 A127 | near-UV | W1/M2/W2 | 126 | 126 | 59696.9242 | 59755.1684 |

![Mrk 421 optical/UV-LHAASO weekly alignment](../data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/mkn421_optical_uv_lhaaso_2021_2026_weekly.png)

This figure is for visual timing context only and reports no DCF, FAP, correlation coefficient, lag, optical QPO significance, or physical cross-band flux normalization. The full quick-look flux table and quality summary are saved as `data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/optical_uv_flux_points.csv` and `data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/optical_uv_quality_summary.csv`.

## Local-significance assessment of current candidate peaks

This section freezes the candidate peaks already visible in the Mrk 421 and Mrk 501 WCDA weekly global spectra and asks only whether those fixed peaks look locally unusual under simple red-noise null models. The WCDA series is still `wcda_flux_excess`, a photon-count/excess-rate proxy rather than a final calibrated flux product; this is a workflow pass that should be rerun when calibrated flux is available.

CWT uses `pycwt` Morlet global-wavelet-spectrum references for an AR(1) red-noise null. WWZ uses 1000 AR(1) Gaussian surrogate light curves on the same weekly sampling and reports a local-window FAP within ±10% of each candidate period. CWT and WWZ are two views of the same light curve structure, not independent discoveries. Peaks with only about 3-5 observed cycles should be treated as candidates or hints, not robust QPO detections.

| Source | Method | Period [d] | Cycles | Observed | Local FAP | 95% ref. | 99% ref. | Reading |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Mrk 421 | CWT | 129.87 | 14.17 | GWS 2.965 | — | 11.371 | 14.095 | Below AR(1) 95% local reference. |
| Mrk 421 | CWT | 367.33 | 5.01 | GWS 4.486 | — | 14.675 | 20.042 | Below AR(1) 95% local reference; only about five cycles. |
| Mrk 421 | WWZ | 135.67 | 13.57 | WWZ 4.634 | 0.4665 | 7.442 | 9.232 | Not locally unusual in the AR(1) surrogate test. |
| Mrk 421 | WWZ | 363.22 | 5.07 | WWZ 5.177 | 0.6244 | 15.565 | 21.794 | Not locally unusual in the AR(1) surrogate test. |
| Mrk 501 | CWT | 137.59 | 13.38 | GWS 1.270 | — | 3.687 | 4.593 | Below AR(1) 95% local reference. |
| Mrk 501 | CWT | 389.17 | 4.73 | GWS 4.407 | — | 4.766 | 6.545 | Close to but below the AR(1) 95% local reference; only about five cycles. |
| Mrk 501 | WWZ | 61.22 | 30.07 | WWZ 1.783 | 0.5165 | 2.500 | 2.984 | Not locally unusual in the AR(1) surrogate test. |
| Mrk 501 | WWZ | 140.87 | 13.07 | WWZ 1.761 | 0.7113 | 3.665 | 4.692 | Not locally unusual in the AR(1) surrogate test. |
| Mrk 501 | WWZ | 402.98 | 4.57 | WWZ 6.385 | 0.0310 | 5.233 | 7.726 | Passes this local 95% surrogate check but not 99%; still not a global/post-trial detection. |

Reading: in this first local-only pass, most current weekly peaks are consistent with the simple AR(1) red-noise null. The strongest exception is Mrk 501 WWZ near 403 d, with local-window FAP ≈ 0.031, but it has only about 4.6 cycles and has not been corrected for the period search, two-source comparison, or using both CWT and WWZ.

## Mrk 421 fixed-window local check, MJD 59500-60500

This section tests the user-specified Mrk 421 WCDA weekly window `MJD 59500-60500` as a fixed window, not as a sliding-window search. The actual finite weekly samples cover MJD 59501.167-60495.167 with 143 points and a median cadence of 7.000 d. The window's own strongest peak is reported, and a pre-specified 140 d target band is tested separately. No Fermi weekly or WCDA daily counterpart is included here because the requested result is WCDA weekly only and the current WCDA daily product does not cover this MJD range.

The CWT strongest GWS peak is 308.88 d, and the WWZ strongest mean-power peak is 314.89 d. Because the shorter candidate is scientifically interesting, the 140 d hypothesis is now treated as a targeted test: the band is fixed in advance to 140 d ±10%, i.e. 126-154 d, and the local maximum inside that band is evaluated. The targeted-band maxima are 145.77 d in CWT and 149.32 d in WWZ. The WWZ result uses 1000 AR(1) Gaussian surrogate weekly light curves on the same sampling; the 314.89 d strongest-peak FAP and the 140 d targeted-band FAP are computed from the same surrogate ensemble. This is fixed-window local-only: no window-search, source-level, method-level, or broad period-search trial correction is applied.

| Window | Method | Period [d] | Cycles | Observed | Local FAP | 95% ref. | 99% ref. | Reading |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 59500-60500 | CWT | 308.88 | 3.22 | GWS 4.026 | — | 13.448 | 19.128 | Below AR(1) 95% local reference; fewer than four cycles. |
| 59500-60500 | WWZ | 314.89 | 3.16 | WWZ 5.499 | 0.3676 | 14.391 | 20.180 | Not locally unusual in the AR(1) surrogate test; fewer than four cycles. |
| 59500-60500 | CWT targeted 140 d band | 145.77 | 6.82 | GWS 3.857 | — | 11.187 | 14.824 | Target-band maximum inside 126-154 d; below AR(1) 95% local reference. |
| 59500-60500 | WWZ targeted 140 d band | 149.32 | 6.66 | WWZ 5.130 | 0.3526 | 8.733 | 12.491 | Target-band maximum inside 126-154 d; not locally unusual in the AR(1) surrogate test. |

Reading: in this fixed-window check, neither the ~310 d structure nor the pre-specified 140 d target band passes the current AR(1) local 95% reference in CWT or WWZ. The ~310 d peak is additionally weak because the window covers only about 3.2 cycles. The 140 d band remains worth tracking because it gives about 6.7 cycles and was tested as a targeted hypothesis, but with WWZ local FAP = 0.3526 it is still a candidate/hint rather than a robust QPO detection.

![Mrk 421 WCDA weekly fixed-window periodicity, MJD 59500-60500](../data/processed/periodicity/mkn421/windows/59500_60500/wcda_weekly_window_periodicity.png?v=mkn421-window-target140-20260601)

![Mrk 421 WCDA weekly fixed-window CWT local reference](../data/processed/periodicity/mkn421/windows/59500_60500/wcda_weekly_window_cwt_global_significance.png?v=mkn421-window-target140-20260601)

![Mrk 421 WCDA weekly fixed-window WWZ local significance](../data/processed/periodicity/mkn421/windows/59500_60500/wcda_weekly_window_wwz_local_significance.png?v=mkn421-window-target140-20260601)


## Regular WWZ Color-Scale Comparison

Main regular figures now use linear WWZ heatmap color normalization. The Mrk 421 and Mrk 501 WCDA weekly summary figures additionally show CWT and WWZ global spectra below the 2D maps. Red dashed lines mark algorithmic candidate peaks in those global spectra; they are not significance-vetted detections.

![Mrk 421 WCDA daily linear-color WWZ](../data/processed/periodicity/mkn421/wcda_daily_periodicity.png)

Log-color reference kept for comparison:

![Mrk 421 WCDA daily log-color WWZ](../data/processed/periodicity/mkn421/wcda_daily_periodicity_logcolor.png)

![Mrk 421 WCDA weekly linear-color WWZ with global spectra](../data/processed/periodicity/mkn421/wcda_weekly_periodicity.png)

![Mrk 421 WCDA weekly CWT global spectrum local significance](../data/processed/periodicity/mkn421/wcda_weekly_cwt_global_significance.png)

![Mrk 421 WCDA weekly WWZ global spectrum local significance](../data/processed/periodicity/mkn421/wcda_weekly_wwz_global_significance.png)

Log-color reference kept for comparison:

![Mrk 421 WCDA weekly log-color WWZ with global spectra](../data/processed/periodicity/mkn421/wcda_weekly_periodicity_logcolor.png)

![Mrk 421 Fermi weekly on WCDA axis linear-color WWZ](../data/processed/periodicity/mkn421/fermi_weekly_on_wcda_axis_periodicity.png)

Log-color reference kept for comparison:

![Mrk 421 Fermi weekly on WCDA axis log-color WWZ](../data/processed/periodicity/mkn421/fermi_weekly_on_wcda_axis_periodicity_logcolor.png)

![Mrk 501 WCDA weekly linear-color WWZ with global spectra](../data/processed/periodicity/mkn501/wcda_weekly_periodicity.png)

![Mrk 501 WCDA weekly CWT global spectrum local significance](../data/processed/periodicity/mkn501/wcda_weekly_cwt_global_significance.png)

![Mrk 501 WCDA weekly WWZ global spectrum local significance](../data/processed/periodicity/mkn501/wcda_weekly_wwz_global_significance.png)

Log-color reference kept for comparison:

![Mrk 501 WCDA weekly log-color WWZ with global spectra](../data/processed/periodicity/mkn501/wcda_weekly_periodicity_logcolor.png)

## xgm poster 复现检查

Input file: `data/processed/wcda_day/LHAASO-WCDA_Mkn421_2023-06-25_2026-03-29_day.csv`.

This comparison uses `excess_counts = sum(n_on - n_bkg)` as a photon-count flux proxy. It is not a calibrated physical flux, and it is not guaranteed to be the exact same flux definition used in the xgm poster. The xgm poster periods are reference labels from the poster.

Important difference from the xgm poster: the significance curves in this report are my AR(1) Gaussian surrogate WWZ references, computed with `N=1000` surrogates on the same daily sampling and the same saved WWZ period grid. They are not a reproduction of the poster author's significance calculation. Under this null model, the MJD 60200-60700 feature near 51 d is above the pointwise 95% reference but below the pointwise 99% reference, and its ±10% local-window FAP is 0.0619. This explains why it can look stronger in the xgm poster while not passing 99% here. No global look-elsewhere correction is applied.

| Window | xgm poster reported | My reproduction | Reading |
| --- | --- | --- | --- |
| 60200-60700 | 51.05 d | Global WWZ peak 111.01 d; nearest 51.05 d grid point is 49.93 d, power 12.330, rank 3 | 50 d is a strong local feature, but not the dominant peak in this run |
| 61020-61098 | 2.54, 5.2, 16.6 d | Global peak at 50.00 d upper boundary; 16.96 d ranks 3, 5.12 d ranks 10, 2.52 d is not prominent | 16.6 d has a visible counterpart; the shorter candidates are weaker here |

| Window | Target source | Target [d] | Nearest grid [d] | Local-window peak [d] | WWZ power | 95% ref. | 99% ref. | Rank | Cycles | My local FAP | Reading |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 60200-60700 | xgm poster reference | 51.05 | 49.92 | 49.92 | 12.330 | 11.017 | 14.897 | 3 | 9.77 | 0.0619 | Above pointwise 95% but below 99% in my AR(1) surrogate reference; does not pass the ±10% local-window 5% FAP threshold. |
| 60200-60700 | my reproduction peak | 111.01 | 111.01 | 111.01 | 13.612 | 15.895 | 21.717 | 1 | 4.49 | 0.0779 | My global peak is stronger than the xgm 51.05 d grid point, but remains below the local AR(1) references. |
| 61020-61098 | xgm poster reference | 2.54 | 2.52 | 2.30 | 0.671 | 0.550 | 0.650 | 24 | 30.31 | 0.0340 | Passes my local 95% and pointwise 99% surrogate check, but the absolute WWZ power is low and this is not trial corrected. |
| 61020-61098 | xgm poster reference | 5.20 | 5.12 | 5.12 | 0.909 | 1.452 | 1.899 | 10 | 14.81 | 0.5095 | Not locally unusual in my AR(1) surrogate test. |
| 61020-61098 | xgm poster reference | 16.60 | 16.96 | 15.28 | 2.767 | 8.582 | 11.784 | 2 | 4.64 | 0.6024 | Visible in my reproduction but not locally significant in this surrogate test. |
| 61020-61098 | my reproduction boundary peak | 50.00 | 50.00 | 50.00 | 18.573 | 15.768 | 29.757 | 1 | 1.54 | 0.0360 | Above pointwise 95% but below 99%; at the search upper boundary with only 1.54 cycles, so do not treat as a robust QPO. |

![xgm poster comparison, MJD 60200-60700](../data/processed/periodicity/xgm_poster_repro/mkn421/mkn421_daily_60200_60700_wwz_poster_style.png?v=wwz-ar1-n1000-20260528)

![My WWZ local significance check, MJD 60200-60700](../data/processed/periodicity/xgm_poster_repro/mkn421/mkn421_daily_60200_60700_wwz_local_significance.png?v=wwz-ar1-n1000-20260528)

![xgm poster comparison, MJD 61020-61098](../data/processed/periodicity/xgm_poster_repro/mkn421/mkn421_daily_61020_61098_wwz_poster_style.png?v=wwz-ar1-n1000-20260528)

![My WWZ local significance check, MJD 61020-61098](../data/processed/periodicity/xgm_poster_repro/mkn421/mkn421_daily_61020_61098_wwz_local_significance.png?v=wwz-ar1-n1000-20260528)

Interpretation: this is a comparison between the xgm poster labels and my current reproduction using the available daily `excess_counts` series. The 50 d feature appears locally in the 60200-60700 window, but my global WWZ peak is at longer periods, and the 51 d feature is not above my `N=1000` AR(1) 99% reference. The short-window page shows the clearest counterpart near 16.6 d visually, while only the very-short 2.54 d local-window check crosses the current pointwise 99% reference.
