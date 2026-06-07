# IHEP WCDA Weekly Counts Status

Run date: 2026-05-27 21:40 CST

Workspace: `/home/lhaaso/liushijie/QPO`

Shared merge log: `/home/lhaaso/liushijie/QPO/results/2021-03-08_2026-03-29_week.csv`

Merge policy: reused the existing 264-row weekly merge log. No new merge jobs were submitted.

Counting policy: all source counting was submitted through HTCondor/hep_sub. No login-node batch counting was used.

Resource note: the default 5 GB jobs stayed idle. Idle setup jobs were removed, and final counting was run on `schedd11` with `-mem 2000` after the two-source pilot passed validation.

All structural checks passed: yes

| source | label | status | cluster | output | checks |
|---|---|---|---:|---|---|
| `1ES1959p650` | 1ES 1959+650 | success | `2690993` | `/home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_1ES1959p650_2021-03-08_2026-03-29_week.csv` | rows=264; columns=ok; mjd=ok; arrays=ok; none_rows=0 |
| `1ES1727p502` | 1ES 1727+502 | success | `2691036` | `/home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_1ES1727p502_2021-03-08_2026-03-29_week.csv` | rows=264; columns=ok; mjd=ok; arrays=ok; none_rows=0 |
| `1ES2344p514` | 1ES 2344+514 | success | `2691037` | `/home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_1ES2344p514_2021-03-08_2026-03-29_week.csv` | rows=264; columns=ok; mjd=ok; arrays=ok; none_rows=0 |
| `BLLacertae` | BL Lacertae | success | `2691038` | `/home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_BLLacertae_2021-03-08_2026-03-29_week.csv` | rows=264; columns=ok; mjd=ok; arrays=ok; none_rows=0 |
| `NGC1275` | NGC 1275 | success | `2691039` | `/home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_NGC1275_2021-03-08_2026-03-29_week.csv` | rows=264; columns=ok; mjd=ok; arrays=ok; none_rows=0 |
| `M87` | M 87 | success | `2690992` | `/home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_M87_2021-03-08_2026-03-29_week.csv` | rows=264; columns=ok; mjd=ok; arrays=ok; none_rows=0 |
| `4C_p42d22` | 4C +42.22 | success | `2691040` | `/home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_4C_p42d22_2021-03-08_2026-03-29_week.csv` | rows=264; columns=ok; mjd=ok; arrays=ok; none_rows=0 |
| `IC310` | IC 310 | success | `2691041` | `/home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_IC310_2021-03-08_2026-03-29_week.csv` | rows=264; columns=ok; mjd=ok; arrays=ok; none_rows=0 |

Submitted and removed idle setup jobs:

- Initial pilot clusters on `schedd07`: `81198220`, `81198225`, removed while idle.
- Pilot clusters on `schedd11` with 5 GB: `2690933`, `2690934`, removed while idle.
- Initial six-source clusters on `schedd07`: `81200108`, `81200113`, `81200117`, `81200120`, `81200126`, `81200131`, removed while idle.

Final successful clusters:

- `1ES1959p650`: `2690993`
- `M87`: `2690992`
- `1ES1727p502`: `2691036`
- `1ES2344p514`: `2691037`
- `BLLacertae`: `2691038`
- `NGC1275`: `2691039`
- `4C_p42d22`: `2691040`
- `IC310`: `2691041`
