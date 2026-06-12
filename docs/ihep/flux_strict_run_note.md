# Strict WCDA Flux Run Note

Updated: 2026-05-23 14:04 CST

## Current status

The strict WCDA forward-folding workflow is implemented in `MakeLC/standard_flux_lc.py`.

Smoke tests passed:
- `DI_Merge` creates strict daily/weekly map ROOT files.
- `Src_Main` v0.99 reads the generated map through xrootd and writes `ParRes.yaml`.
- Fixed source position, point-source morphology, PL spectrum, fixed `alpha=2.6`, free `F0` at 3 TeV.
- `fit_status` now preserves `STATUS : OK/NotOK` from the standard-program log.

Strict requested coverage:
- daily: 2021-03-08 to 2025-07-31, 1607 rows
- weekly: 2021-03-08_2021-03-14 to 2025-07-21_2025-07-27, 229 rows

Known no-input daily bins from source sky-map manifests:
- 2021-07-29
- 2024-07-31
- 2024-08-01
- 2024-12-09
- 2024-12-10

## Production attempt

Map cluster attempts on `scheduler@schedd11.ihep.ac.cn`:
- `2659290`: removed; missing `accounting_group`, no matching slots.
- `2659332`: failed before running ROOT; CVMFS env source with `set -u` hit `ANYSW_LANG_K: unbound variable`.
- `2659377`: removed/replaced; 8 GB request matched too few slots.
- `2659406`: failed before running ROOT; wrapper sourced CVMFS before `myrootenv` Python, causing `libharfbuzz.so.0: undefined symbol: FT_Get_Transform`.
- `2659449`: ROOT jobs ran successfully until EOS quota became the blocker; later jobs failed with `Disk quota exceeded` while creating map ROOT files.

The current wrapper no longer sources CVMFS before Python; Python starts cleanly, and `DI_Merge/Src_Main` source CVMFS only inside their child shell.

## Current generated products

EOS map directory:
- `/eos/user/l/liushijie/QPO/flux_strict`

Current map counts:
- daily maps present: 932
- weekly maps present: 1

Current generated map coverage:
- daily maps: 2021-03-08_2021-03-08 through 2024-04-21_2024-04-21, with the known no-input gap at 2021-07-29
- weekly maps: only 2021-03-08_2021-03-14 from smoke test

Approximate storage use observed:
- `/eos/user/l/liushijie/QPO/flux_strict`: 2.1T
- `/eos/user/l/liushijie/QPO/flux_strict/maps/day`: 1.1T
- `/eos/user/l/liushijie/QPO/flux_strict/maps/week`: 1.4G

## Hard blocker

EOS quota/space for `/eos/user/l/liushijie/QPO/flux_strict` is exhausted. ROOT/xrootd reports:

`Unable to get quota space - quota not defined or exhausted ... Disk quota exceeded`

Until more EOS space is available or the map storage strategy is changed, the full strict daily+weekly flux curves cannot be completed.

## Commands after storage is fixed

Regenerate configs if the output root changes:

```bash
python MakeLC/standard_flux_lc.py prepare --eos-root /path/to/new/eos/root
```

Submit map jobs:

```bash
python MakeLC/standard_flux_lc.py submit map
```

After map jobs complete, validate logs and outputs, then submit fits:

```bash
find JOBs_flux_strict/logs -name 'map_<cluster>_*.err' -size +0 -print
python MakeLC/standard_flux_lc.py submit fit
```

After fits complete:

```bash
python MakeLC/standard_flux_lc.py merge
python MakeLC/standard_flux_lc.py plot
```

Final CSV/figures are written under `results/flux/`.
