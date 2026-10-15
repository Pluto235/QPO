# Crab poster Figure 2 refinement — 2026-10-14

- ETO Slurm job `66077`: COMPLETED, exit `0:0`, elapsed `00:22:40`.
- WWZ grid: 80 × 317 → 240 × 1263, frequency-step factor 0.5 → 0.125; period search remains 10–600 d.
- Preserve the 799/803 strict-selection observations, CWT products, AR(1) alpha and all 1000 surrogate seeds.
- Recalculate observed WWZ and all 1000 surrogates on the refined grid. Observed/null full-grid parity errors are 6.02e-11 / 7.47e-12.
- Refined WWZ peak: 373.1678945 d; CWT peak: 374.0017503 d. Yellow guides use each method's own peak.
- WWZ full-search FAP: 1/1001 = 0.0009990; four-control-source correction: 4/1001 = 0.0039960. The fixed control family remains four sources.
- Old release products remain under `data/processed/periodicity/detector_controls_20261011/`; new products use `detector_controls_crab_highres_20261014/`.

Run from the ETO QPO repository root:

```sh
sbatch work/poster_crab_highres_20261014/run.sbatch
```

The job reuses the pure Python dependencies from the earlier Mrk 421 poster run. Copy `libwwz`/`pycwt` distribution metadata into that dependency directory when needed; package source remains unchanged.

For the final 300 dpi PNG and PDF with vector text/guide lines, run this lightweight export from the local repository root:

```sh
PYTHONPATH=src /Users/luoji/miniconda3/envs/py310/bin/python - <<'PY'
import json, pandas as pd
import matplotlib.pyplot as plt
from unittest.mock import patch
from pipeline.periodicity_v1 import _plot_periodicity_summary
from pipeline.detector_controls_2day_qpo import _load_npz
from utils.project_paths import PERIODICITY_DIR, ALIGNED_DIR
key = 'detector_controls_crab_highres_20261014'
out = PERIODICITY_DIR / key / 'crab'
meta = json.loads((out / 'run_metadata.json').read_text())
obs = pd.read_csv(ALIGNED_DIR / key / 'crab' / 'wwz_observed.csv')
cwt, wwz, refs = (_load_npz(out / f) for f in ('cwt.npz', 'wwz.npz', 'significance_refs.npz'))
with patch('pipeline.periodicity_v1.plt.close'):
    _plot_periodicity_summary(out / 'Crab_strict_2day_cwt_wwz.pdf',
        f"Crab WCDA 2-day flux · strict selection {len(obs)}/{meta['raw_rows']} · E0={meta['pivot_energy_TeV']:g} TeV",
        obs.mjd.to_numpy(), obs.flux.to_numpy(), obs.flux_err.to_numpy(), cwt, wwz,
        include_global_row=True,
        cwt_significance={k[4:]: v for k, v in refs.items() if k.startswith('cwt_')},
        wwz_significance={k[4:]: v for k, v in refs.items() if k.startswith('wwz_')},
        light_curve_ylim=tuple(meta['display_ylim']), mark_lc_clipping=True,
        global_legends_above=True, mark_global_peaks_on_maps=True)
    fig = plt.gcf()
    maps = [ax for ax in fig.axes if ax.get_title() in ('CWT Power', 'WWZ Power')]
    assert len(maps) == 2
    for ax in maps:
        assert any(line.get_color() == '#F0E442' for line in ax.lines)
        ax.set_rasterization_zorder(2)
    fig.savefig(out / 'Crab_strict_2day_cwt_wwz.pdf', dpi=300)
    fig.savefig(out / 'Crab_strict_2day_cwt_wwz.png', dpi=300)
plt.close(fig)
PY
```

Power-map rasterization prevents PDF mesh seams while keeping labels and guides as vectors. The control feature is an observational-response diagnostic; this refinement does not establish a physical Crab QPO.
