# Mrk 421 Optical/UV-LHAASO 2021-2026 Alignment

Generated on 2026-06-01.

This quick-look aligns public optical and near-UV monitoring points with the local LHAASO/WCDA weekly excess-rate proxy. It is exploratory only and reports no DCF, FAP, correlation coefficient, lag, or optical QPO significance.

## Data Sources

- ATLAS forced photometry cache: `data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/atlas_forced_photometry.csv`.
- ASAS-SN Sky Patrol cache: `data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/asassn_skypatrol_mkn421.csv`.
- ZTF public light-curve cache: `data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/ztf_public_lc.csv`.
- AAVSO VSX export cache: `data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/aavso_vsx_full_window.csv`.
- CDS/VizieR A&A 684 A127 fig1 cache: `data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/cds_aa684_a127_fig1.csv`; ReadMe: [https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/A+A/684/A127?format=html&tex=true](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/A+A/684/A127?format=html&tex=true).
- WCDA weekly input: `data/processed/wcda_week/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv`.

## Coverage

- Plotted MJD window: 59284.333-61125.167.
- Finite WCDA weekly points in plotted window: 264 (MJD 59284.333-61125.167).
- Plotted optical points: 3487.
- Plotted near-UV points: 126.
- Unified quick-look flux table: `data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/optical_uv_flux_points.csv`.
- Quality and coverage summary: `data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/optical_uv_quality_summary.csv`.

## Quality Summary

| survey | panel | band | input_rows | plotted_rows | mjd_min | mjd_max | flux_min_mjy | flux_max_mjy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAVSO | optical | B | 22 | 22 | 60327.9285 | 61116.9292 | 6.996 | 25.730 |
| AAVSO | optical | CR | 3 | 3 | 60751.8001 | 60756.8127 | 17.502 | 17.615 |
| AAVSO | optical | CV | 46 | 46 | 59296.8104 | 61093.8330 | 12.607 | 41.747 |
| AAVSO | optical | R | 1 | 1 | 59987.0832 | 59987.0832 | 27.459 | 27.459 |
| AAVSO | optical | TG | 25 | 25 | 59313.8733 | 61065.9743 | 10.986 | 32.933 |
| AAVSO | optical | V | 115 | 115 | 59311.1527 | 61116.9261 | 10.800 | 33.902 |
| AAVSO | optical | Vis. | 1104 | 1103 | 59284.9440 | 61124.9320 | 9.133 | 47.932 |
| ASAS-SN Sky Patrol | optical | g | 239 | 195 | 59295.2574 | 60451.2869 | 17.289 | 36.248 |
| ATLAS | optical | c | 613 | 463 | 59284.3833 | 61091.5638 | 0.092 | 19.444 |
| ATLAS | optical | o | 2246 | 923 | 59297.4440 | 61026.5672 | 0.120 | 26.336 |
| CDS/VizieR A&A 684 A127 | near-UV | M2 | 42 | 42 | 59696.9242 | 59755.1684 | 7.160 | 18.200 |
| CDS/VizieR A&A 684 A127 | near-UV | W1 | 41 | 41 | 59696.9242 | 59755.1684 | 7.970 | 18.100 |
| CDS/VizieR A&A 684 A127 | near-UV | W2 | 43 | 43 | 59696.9242 | 59755.1684 | 6.230 | 16.400 |
| CDS/VizieR A&A 684 A127 | optical | R-band | 76 | 34 | 59703.0000 | 59747.7901 | 14.100 | 21.700 |
| ZTF public | optical | zg | 277 | 277 | 59290.2290 | 60814.2876 | 0.034 | 29.091 |
| ZTF public | optical | zi | 18 | 18 | 59308.3061 | 60067.3904 | 19.458 | 34.495 |
| ZTF public | optical | zr | 262 | 262 | 59290.2614 | 60942.5267 | 0.159 | 33.316 |

## Figure

![Mrk 421 optical/UV-LHAASO alignment](../data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/mkn421_optical_uv_lhaaso_2021_2026_weekly.png)

## Notes

- Optical magnitudes are converted to approximate flux density in mJy for quick-look plotting. The plot does not apply host-galaxy subtraction, color correction, cross-filter normalization, or SED modeling.
- AAVSO Visual points are retained with low alpha to preserve cadence context without giving them the same visual weight as CCD/DSLR/filter photometry.
- CDS R-band is plotted with the optical points; Swift-UVOT W1/M2/W2 are plotted in a separate near-UV panel.
- WCDA values use the project proxy `flux_excess = sum(n_on - n_bkg) / tobs`; they are not calibrated physical gamma-ray fluxes and are not plotted on the optical mJy axis.
