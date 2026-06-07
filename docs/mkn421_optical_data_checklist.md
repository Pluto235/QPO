# Mrk 421 Optical Data Checklist for the LHAASO Window

Checked on 2026-06-01.

This checklist is for adding non-uniform optical and optical/UV monitoring points to the
current Mrk 421 LHAASO/WCDA periodicity context. The immediate plotting target is a
single multi-instrument time-series figure after converting magnitudes to a common flux
density unit, preferably `mJy`.

## Target Window

The local WCDA weekly product spans 264 weekly bins:

- Weekly bin labels: 2021-03-08 to 2026-03-29.
- Weekly MJD centers: `59284.33328206009` to `61125.16668842604`.
- Approximate center-date span: 2021-03-11 to 2026-03-26.
- Source coordinates used for probes: RA `166.11383 deg`, Dec `38.20883 deg`.

The local WCDA daily product currently spans:

- Daily bin labels: 2023-06-25 to 2026-03-29.
- Daily MJD centers: `60120.16688923612` to `61128.16676400474`.

For data requests, ask for the full weekly bin-label range
`2021-03-08--2026-03-29`; for API queries using MJD centers, use
`59284.333--61125.167`.

## Acquisition Status Summary

| Priority | Dataset | Bands / quantity | Window coverage expected | Access status | What we can do now | What needs user action |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ZTF public light curves via IRSA | `g`, `r`, sparse `i`; magnitudes | Partial LHAASO coverage; verified rows end before 2026 in the current public release | Direct public API | Download immediately and convert mag to `mJy` | None, unless we need proprietary/newer ZTF data |
| 1 | AAVSO VSX / International Database export | Visual, `V`, `B`, `R`, `CV`, `CR`, `TG`; magnitudes | Full LHAASO range has returned data | Direct API-style VSX export | Download immediately, then quality-filter by band/type/validation flag | None |
| 1 | CDS/VizieR 2022 MAGIC/IXPE MWL campaign | `R-band`, Swift-UVOT `W1/M2/W2`, plus non-optical | Short campaign only, MJD `59695.0034--59756.5` | Direct public download | Download immediately; useful for the 2022 IXPE/MWL window | None |
| 2 | ATLAS forced photometry | `c`, `o` forced-flux/magnitude light curves | Should cover most/all of the LHAASO range if queued successfully | Requires account/token | Prepare request script once credentials exist | Register/login for ATLAS forced photometry and provide token/credentials outside git |
| 2 | ASAS-SN Sky Patrol | Usually `V` and/or `g`; magnitudes/fluxes through client | Likely broad coverage; exact rows not yet verified locally | Requires Sky Patrol username/token password and a compatible Python env | Set up on conda/Linux/ETO and query once credentials/env are ready | Obtain Sky Patrol username/token password if not already available |
| 2 | Tuorla blazar monitoring | Mostly optical `R`/flux density quick-look; numeric data by request | Current quick-look page includes Mrk 421 and was updated 2026-03-06 | Quick-look public; numeric table requires contact | Use only as a target for request, not image digitization | Request numeric Mrk 421 light curve for 2021-03-08--2026-03-29 |
| 3 | WEBT/GASP archive | Optical/NIR magnitudes or fluxes, errors, observatory labels | Campaign-dependent, potentially dense if Mrk 421 is available | Request to WEBT archive after publication | Prepare request text | Ask WEBT for Mrk 421 final light curves; respect their tabular republication policy |
| 3 | Swift-UVOT from HEASARC/MAST | `V/B/U/UVW1/UVM2/UVW2` count rates or fluxes after extraction | Many Swift observations exist near Mrk 421; exact UVOT light curve requires extraction | Public archive, no API token normally | Build an extraction/query workflow later | None unless using proprietary tools/storage |
| 4 | TESS FFI | Broad red optical high-cadence flux | Very short sectors only; MAST probe found sector 48 in 2022 inside the LHAASO window | Public archive, but requires image light-curve extraction | Optional high-cadence short-window experiment | None |
| 4 | Steward Observatory archive | Optical photometry/polarimetry | Public Mrk 421 archive appears to stop at Fermi cycle 10, 2018 | Direct public archive | Useful only as archival baseline, not for the LHAASO window | None |

## Verified Access Probes

### ZTF public IRSA light curves

Status: verified direct API.

Probe query pattern:

```text
https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE+166.1138+38.2088+0.0028&BANDNAME=r&NOBS_MIN=3&TIME=59284.333+61125.167&BAD_CATFLAGS_MASK=32768&FORMAT=CSV
```

Observed rows in the full LHAASO MJD-center query:

| Band | Rows | MJD range returned | Comment |
| --- | ---: | --- | --- |
| `g` | 277 | `59290.2290--60814.2876` | Useful seasonal optical coverage, but not to 2026 |
| `r` | 262 | `59290.2614--60942.5267` | Best ZTF band for this source |
| `i` | 18 | `59308.3061--60067.3904` | Sparse; optional |

IRSA notes that `TIME` endpoints are MJD, `FORMAT=CSV` is supported, and public
light curves are available through the ZTF light-curve API. Proprietary ZTF data,
if needed, require IRSA login.

Planned local target:

```text
data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/ztf_public_lc.csv
```

### AAVSO

Status: verified direct export through the VSX object endpoint.

VSX identity probe:

```text
https://www.aavso.org/vsx/index.php?view=api.object&ident=MRK%20421&format=json
```

Returned source identity:

- Name: `MRK 421`
- AUID: `000-BBR-960`
- OID: `185253`
- RA/Dec: `166.11383`, `38.20883`
- Type: `BLLAC`

Full-window data probe:

```text
https://www.aavso.org/vsx/index.php?view=api.object&ident=000-BBR-960&data=100000&fromjd=2459284.833&tojd=2461125.667&csv
```

Observed rows for the full LHAASO range: `1316`.

Band/type counts from the quick probe:

| Field | Counts |
| --- | --- |
| Bands | `Vis.` 1104, `V` 115, `CV` 46, `TG` 25, `B` 22, `CR` 3, `R` 1 |
| Observation types | Visual 1102, CCD 208, DSLR 6 |
| JD range returned | `2459285.444--2461125.432` |

This is a high-cadence supplement, but the data are heterogeneous. For the first
plot, separate at least `Visual`, `CCD`, and transformed standard filters; do not
mix them into a single fitted light curve without quality cuts.

Planned local target:

```text
data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/aavso_vsx_full_window.csv
```

### CDS/VizieR 2022 IXPE/MWL campaign

Status: verified direct public download.

Main data table:

```text
https://cdsarc.cds.unistra.fr/ftp/J/A+A/684/A127/fig1.dat
```

ReadMe:

```text
https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/A+A/684/A127?format=html&tex=true
```

The `fig1.dat` table contains 470 multiwavelength rows. The optical/UV-relevant
subset includes:

- `R-band`: 76 rows.
- `Swift-UVOT`: 126 rows across `W1`, `M2`, and `W2`.
- Campaign MJD range: `59695.0034--59756.5`.

This is not a full-window monitoring source, but it is the cleanest directly
downloadable numerical table for the 2022 Mrk 421 IXPE/MWL campaign.

Planned local target:

```text
data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/cds_aa684_a127_fig1.csv
```

### Nature Astronomy Mrk 421 IXPE paper

Status: not a direct bulk optical light-curve download in the quick public check.

The Nature Astronomy paper's data availability statement says that supporting
data are either public at HEASARC or available from the corresponding author upon
request. For our immediate plotting goal, the A&A/CDS `J/A+A/684/A127` table is
more directly usable because it publishes numeric figure data for the 2022
radio-to-TeV/IXPE campaign.

Recommendation:

- Use the CDS A&A table immediately.
- If we need the exact Nature Astronomy figure/source data beyond what is in CDS
  or HEASARC, request it from the corresponding author.

### ATLAS forced photometry

Status: account/token required.

API guide confirms:

- Base URL: `https://fallingstar-data.com/forcedphot`
- Token route: `/api-token-auth/`
- Queue route: `/queue/`
- Required request fields include `ra`, `dec`, and `mjd_min`; we should also pass
  `mjd_max` if accepted by the service.

Suggested request:

```text
ra=166.11383
dec=38.20883
mjd_min=59281.0
mjd_max=61129.0
```

User action needed:

- Register/login for ATLAS forced photometry.
- Provide token or run the token step locally; do not commit credentials.

### ASAS-SN Sky Patrol

Status: likely useful, but not yet downloaded.

The official route is the `pyasassn` / Sky Patrol client. The documentation says
that after receiving a username and token password, the user can create a
`SkyPatrolClient` and query catalog/light-curve data.

Local blocker:

- A quick local install attempt in an isolated environment failed because the
  dependency chain tried to build older binary-heavy packages on this Mac/Python
  combination.

Recommendation:

- Treat this as an environment problem, not a data unavailability problem.
- Try a conda-forge environment, Linux, or ETO before spending time patching the
  local Mac install.

User action needed:

- If no Sky Patrol credentials exist, request/obtain username and token password.

### Tuorla blazar monitoring

Status: quick-look page verified; numeric data require request.

The public page explicitly says the light curves are a quick-look service and
that publication use should not extract data from images; users should contact
the team to ask for the needed data. The Mrk 421 quick-look pages currently expose
image products, including:

```text
https://tuorlablazar.utu.fi/Mkn_421.html
https://tuorlablazar.utu.fi/Mkn_421_jy.html
```

User action needed:

- Request numeric Mrk 421 optical light curve for 2021-03-08--2026-03-29.
- Ask for columns: JD/MJD, filter, magnitude or flux density, uncertainty,
  telescope/observatory, host-galaxy subtraction or calibration notes.

### WEBT/GASP

Status: request needed.

The WEBT archive page says final light curves are stored after publication and
can be requested from the WEBT President. The archive files contain Julian Date,
magnitude or flux, error, observatory, and campaign label. It also says WEBT data
cannot be republished in tabular form.

User action needed:

- Ask whether Mrk 421 final optical/NIR light curves are available for
  2021-03-08--2026-03-29, or at least for the 2022 IXPE/MWL and 2023--2026 LHAASO
  windows.
- Confirm acceptable use for a plotted comparison figure and derived correlation
  analysis.

## Plotting / Unit Alignment Plan

Yes: the optical observations can be plotted together without enforcing uniform
sampling. The practical first version should be:

1. Convert each magnitude measurement to flux density `F_nu` in `mJy` using the
   correct photometric zero point for its filter system.
2. Keep each filter/instrument as a separate marker/color series on the same
   `F_nu (mJy)` y-axis.
3. Do not combine different filters into one optical light curve unless we later
   apply color corrections or restrict to a single band, e.g. `R/r`.
4. For AAVSO, plot `V/B/R/CV/CR/TG/Visual` separately at first. The visual data
   are valuable for cadence but should be visually distinguished from CCD
   photometry.
5. For ZTF, use PSF magnitudes directly for quick-look flux density, then later
   decide whether host-galaxy correction is needed.
6. Overlay the WCDA weekly or daily product in a separate lower panel; do not put
   WCDA counts/s on the same physical y-axis as optical `mJy`.

Recommended first figure layers:

- Top panel: all optical flux-density points in `mJy` (`ZTF g/r/i`, AAVSO
  filtered/visual, CDS `R-band`, later ATLAS/ASAS-SN/Tuorla/WEBT).
- Middle panel: optional UVOT `W1/M2/W2` in `mJy`, separated because UV filters
  are not directly comparable to optical `R/r`.
- Bottom panel: LHAASO/WCDA excess-rate proxy or calibrated WCDA flux when ready.

## Request Checklist for the User

Highest impact account/API actions:

1. ATLAS forced photometry account/token.
2. ASAS-SN Sky Patrol username/token password.
3. Tuorla numeric Mrk 421 optical light curve request.
4. WEBT/GASP archive request if we want the densest campaign-grade optical/NIR
   light curves and can comply with their usage policy.
5. Nature Astronomy corresponding-author request only if the CDS A&A table and
   HEASARC public products do not contain the exact IXPE/MWL points needed.

## Sources

- ZTF API: <https://irsa.ipac.caltech.edu/docs/program_interface/ztf_lightcurve_api.html>
- AAVSO VSX Mrk 421 identity endpoint: <https://www.aavso.org/vsx/index.php?view=api.object&ident=MRK%20421&format=json>
- CDS/VizieR A&A 684 A127 ReadMe: <https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/A+A/684/A127?format=html&tex=true>
- CDS/VizieR A&A 684 A127 `fig1.dat`: <https://cdsarc.cds.unistra.fr/ftp/J/A+A/684/A127/fig1.dat>
- Nature Astronomy Mrk 421 IXPE paper: <https://www.nature.com/articles/s41550-023-02032-7>
- ATLAS forced photometry API guide: <https://fallingstar-data.com/forcedphot/apiguide/>
- ASAS-SN Sky Patrol getting started: <https://asas-sn.github.io/skypatrol/getting_started.html>
- Tuorla blazar monitoring: <https://tuorlablazar.utu.fi/>
- WEBT archive: <https://www.oato.inaf.it/blazars/webt/the-webt-archive/>
- Steward Observatory Fermi blazar monitoring: <https://james.as.arizona.edu/~psmith/Fermi/>
