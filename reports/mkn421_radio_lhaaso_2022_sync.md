# Mrk 421 2022 Radio-LHAASO Exploratory Alignment

Generated on 2026-05-28.

This quick-look aligns public 2022 radio flux-density points with the local LHAASO/WCDA Mrk 421 excess-rate proxy. It is an exploratory visualization only: no DCF, FAP, correlation coefficient, lag, or QPO significance is reported here.

## Data Sources

- Radio: CDS/VizieR `J/A+A/684/A127`, table [`fig1.dat`](https://cdsarc.cds.unistra.fr/ftp/J/A+A/684/A127/fig1.dat); catalogue ReadMe: [https://cdsarc.cds.unistra.fr/ftp/J/A+A/684/A127/ReadMe](https://cdsarc.cds.unistra.fr/ftp/J/A+A/684/A127/ReadMe).
- Parsed radio cache: `data/processed/multiwavelength/mkn421/radio_lhaaso_2022/radio_2022_campaign.csv`.
- WCDA weekly input: `data/processed/wcda_week/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv`.
- WCDA daily input target: `data/processed/wcda_day/LHAASO-WCDA_Mkn421_2022-04-15_2022-07-07_day.csv`.

## Coverage

- Radio flux-density rows: 15; MJD 59698.7206-59753.7418.
- Plot window: MJD 59684.7206-59767.7418 (radio range padded by 14 days).
- 37GHz: 6 points.
- 86GHz: 4 points.
- 225GHz: 3 points.
- 230GHz: 2 points.
- WCDA weekly status: generated; points in window: 12.
- WCDA daily status: pending: input CSV missing; points in window: 0.

## Figures

- Weekly alignment: `../data/processed/multiwavelength/mkn421/radio_lhaaso_2022/mkn421_radio_lhaaso_2022_weekly.png`.
![Mrk 421 2022 radio-LHAASO weekly alignment](../data/processed/multiwavelength/mkn421/radio_lhaaso_2022/mkn421_radio_lhaaso_2022_weekly.png)

- Daily alignment: pending. Generate the 2022 WCDA daily CSV on IHEP with the MakeLC workflow, then place it at the daily input target above and rerun this pipeline.

## Notes

- WCDA values use the existing project proxy `flux_excess = sum(n_on - n_bkg) / tobs` with propagated on/off errors. This is not calibrated physical flux.
- Radio values are physical flux densities in Jy from the CDS table and are plotted in separate panels by frequency.
- The figure is intentionally not a correlation or lag measurement because the radio sampling in this short campaign is sparse.
