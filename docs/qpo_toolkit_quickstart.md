# QPO toolkit quickstart

The reusable workflow accepts a CSV with exactly three required columns:

```text
time,flux,flux_err
```

`time` is interpreted as MJD by default. `flux` and `flux_err` must use the
same unit. Run from the repository root with the project Python environment:

```bash
PYTHONPATH=src python -m qpo.cli analyze examples/mkn421_example.csv \
  --outdir results/mkn421_example --label "Mrk 421" --n-surrogates 1000
```

The command writes `integrated.png`, `candidates.csv`, `significance.csv`,
`qc.json`, `manifest.json`, `cwt.npz`, and `wwz.npz`. CWT uses a regular grid
with only short gaps (up to two median cadences) interpolated. WWZ uses the
actual observation times. The default significance workflow is PyCWT AR(1)
reference for CWT and AR(1) Gaussian Monte Carlo surrogates for WWZ.

Use `--period-min`, `--period-max`, `--n-periods`, `--seed`,
`--wwz-time-divisions`, and `--wwz-freq-step-factor` to override defaults.
The fixed default seed is recorded in `manifest.json` so repeated runs are
reproducible. Candidate FAP values are local-window and global search results;
they are not automatically combined across sources or methods.
