# Mrk 421 TELAMON-LHAASO 2022-2026 Weekly Alignment

Generated on 2026-06-01.

This quick-look aligns the TELAMON public Mrk 421 averaged 14 mm and 7 mm radio bands with the local LHAASO/WCDA weekly excess-rate proxy. It is exploratory only: no DCF, FAP, correlation coefficient, lag, or QPO significance is reported here.

## Data Sources

- TELAMON source page: [https://telamon.astro.uni-wuerzburg.de/sources/1104-3812](https://telamon.astro.uni-wuerzburg.de/sources/1104-3812).
- Radio extraction: embedded Plotly averaged light-curve arrays `aver_lc14` and `aver_lc7` from the source page.
- Parsed TELAMON cache: `data/processed/multiwavelength/mkn421/telamon_lhaaso_2022_2026/telamon_averaged_bands.csv`.
- WCDA weekly input: `data/processed/wcda_week/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv`.

## Coverage

- Requested date range: 2022-01-01 to 2026-12-31.
- Plotted overlap window: MJD 59580.0000-61125.1667.
- Full TELAMON parsed range: MJD 59086.7281-61155.0056; total parsed rows: 110.
- Full WCDA weekly finite range: MJD 59284.3333-61125.1667.
- WCDA weekly points in plotted window: 221.
- TELAMON 14mm points in plotted window: 33.
- TELAMON 7mm points in plotted window: 25.

## Figure

- Weekly TELAMON-LHAASO alignment: `../data/processed/multiwavelength/mkn421/telamon_lhaaso_2022_2026/mkn421_telamon_lhaaso_2022_2026_weekly.png`.
![Mrk 421 TELAMON-LHAASO weekly alignment](../data/processed/multiwavelength/mkn421/telamon_lhaaso_2022_2026/mkn421_telamon_lhaaso_2022_2026_weekly.png)

## Notes

- TELAMON radio values are flux densities in Jy. The 14 mm and 7 mm products are averaged band light curves, not single-frequency points.
- WCDA values use the project proxy `flux_excess = sum(n_on - n_bkg) / tobs` with propagated on/off errors. This is not calibrated physical flux.
- This figure is intended for visual timing context only; the radio and gamma-ray panels are not normalized or cross-correlated.
