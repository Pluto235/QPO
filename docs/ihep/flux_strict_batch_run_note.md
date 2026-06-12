# Strict WCDA Flux Batch Run Note

Current production workflow:

- Script: `MakeLC/standard_flux_lc.py`
- Work dir: `JOBs_flux_strict_batch/`
- Temporary EOS maps: `/eos/user/l/liushijie/QPO/flux_strict_batch/`
- Final CSV/figures: `results/flux_strict_batch/`
- Schedd: `scheduler@schedd11.ihep.ac.cn`

Policy:

- Do not run bulk ROOT processing on the login node.
- Run map and fit production through HTCondor only.
- Treat daily merged ROOT map files as temporary cache.
- Delete a daily batch's map ROOT files only after both Mrk421 and Mrk501 fits have non-empty `ParRes.yaml`.
- Keep weekly map ROOT files after weekly fit validation/merge so future source weekly flux curves can reuse the maps and run fit only.
- Fits with `STATUS : NotOK` but non-empty `ParRes.yaml` are accepted as completed bins and retained in final CSV with `fit_status=NotOK`.
- If map validation fails or any expected fit lacks `ParRes.yaml`, keep the batch maps and diagnose before cleanup.

Prepared batches:

| batch | cadence | range | estimated map bytes |
|---|---|---|---:|
| day_2021 | day | 2021-03-08 to 2021-12-31 | 187467057628 |
| day_2022 | day | 2022-01-01 to 2022-12-31 | 229615691390 |
| day_2023 | day | 2023-01-01 to 2023-12-31 | 229615691390 |
| day_2024 | day | 2024-01-01 to 2024-12-31 | 227728439132 |
| day_2025 | day | 2025-01-01 to 2025-07-31 | 133365826232 |
| week_2021 | week | 2021-03-08 to 2022-01-02 | 31213443806 |
| week_2022 | week | 2022-01-03 to 2023-01-01 | 37746490184 |
| week_2023 | week | 2023-01-02 to 2023-12-31 | 37746490184 |
| week_2024 | week | 2024-01-01 to 2025-01-05 | 38472384226 |
| week_2025 | week | 2025-01-06 to 2025-07-27 | 21050927218 |

Useful commands:

```bash
python MakeLC/standard_flux_lc.py batch-status
python MakeLC/standard_flux_lc.py run-batches --steps 1
python MakeLC/standard_flux_lc.py advance-batch --batch day_2021
python MakeLC/standard_flux_lc.py cleanup-batch-maps day_2021 --dry-run
condor_q -name scheduler@schedd11.ihep.ac.cn $USER
condor_q -global $USER
```

Expected final outputs:

- `results/flux_strict_batch/LHAASO-WCDA_Mkn421_2021-03-08_2025-07-31_day_flux.csv`
- `results/flux_strict_batch/LHAASO-WCDA_Mkn501_2021-03-08_2025-07-31_day_flux.csv`
- `results/flux_strict_batch/LHAASO-WCDA_Mkn421_2021-03-08_2025-07-27_week_flux.csv`
- `results/flux_strict_batch/LHAASO-WCDA_Mkn501_2021-03-08_2025-07-27_week_flux.csv`



## 2026-05-28 00:08 CST update

- Changed validation policy: fits with non-empty `ParRes.yaml` and `STATUS : NotOK` are accepted as completed bins and kept in final CSV with `fit_status=NotOK`.
- `day_2021` completed, merged, and cleaned. It contributed 596 fitted source-day rows: 584 `OK`, 12 `NotOK`, plus 2 no-input source rows.
- Final CSVs under `results/flux_strict_batch/` have been written; remaining unprocessed bins are still `missing_parres`.
- EOS temporary maps were cleaned after `day_2021`; current temporary map storage is effectively empty except any new `day_2022` outputs.
- `day_2022` map batch submitted to HTCondor on `scheduler@schedd11.ihep.ac.cn` as cluster `2691960` with 37 chunk jobs. At the last check it was idle, not held.
- Submit memory policy now uses map `5000 MB`, fit `8000 MB`.
