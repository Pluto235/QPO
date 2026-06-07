# Mrk 421 ATLAS and ASAS-SN Data Setup

Checked on 2026-06-01.

This note explains how to fetch ATLAS forced photometry and ASAS-SN Sky Patrol
data for Mrk 421 without committing credentials. The target is the local
LHAASO/WCDA window:

- WCDA weekly bin labels: 2021-03-08 to 2026-03-29.
- Query MJD range used here: `59281.0--61129.0`.
- Coordinates: RA `166.11383 deg`, Dec `38.20883 deg`.

## Local Python Environment

Use the project `py310` environment:

```bash
/Users/luoji/miniconda3/envs/py310/bin/python
```

ASAS-SN dependencies now work locally if `pyarrow` is installed from a wheel:

```bash
/Users/luoji/miniconda3/envs/py310/bin/python -m pip install pyarrow==16.1.0 skypatrol==0.6.21
```

This was tested successfully on 2026-06-01.

## ASAS-SN Sky Patrol

For the current `pyasassn` route, no username/token was needed in the successful
local test. The client connects to the Sky Patrol service and downloads the light
curve after resolving the `asas_sn_id`.

Run:

```bash
/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/fetch_mkn421_asassn.py
```

Expected outputs:

```text
data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/asassn_skypatrol_index.csv
data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/asassn_skypatrol_mkn421.csv
```

Verified local result for the LHAASO MJD query window:

- Resolved ID: `asas_sn_id = 128849645138`.
- Returned rows in `MJD 59281.0--61129.0`: 239.
- Returned MJD range: `59295.2574--60641.5806`.
- Filter counts in the LHAASO window: `g` 239.
- Quality counts: `G` 195, `B` 41, missing 3.

The full Sky Patrol light curve has 785 rows from `MJD 56595.6238--60641.5806`,
with `g` 505 and `V` 280 rows. In other words, the current public/client data
provide useful LHAASO-window coverage but do not reach the 2025--2026 end of the
WCDA window.

Useful options:

```bash
# Only resolve the ASAS-SN ID near the Mrk 421 coordinates.
/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/fetch_mkn421_asassn.py --resolve-only

# Save a wider historical ASAS-SN light curve.
/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/fetch_mkn421_asassn.py --mjd-min 0 --mjd-max 999999
```

Data columns include:

- `mjd`, `jd`
- `phot_filter`
- `mag`, `mag_err`
- `flux`, `flux_err`
- `limit`, `fwhm`, `image_id`, `camera`, `quality`

Recommended first quality cut:

```text
quality == "G" and mag_err < 99
```

## ATLAS Forced Photometry

ATLAS does require an account/token.

Official API guide:

```text
https://fallingstar-data.com/forcedphot/apiguide/
```

### 1. Register / Login

Open:

```text
https://fallingstar-data.com/forcedphot/
```

Create or use an account. Keep the username/password outside the repository.

### 2. Get A Token

Option A: use username/password environment variables for one command.

```bash
export ATLAS_USERNAME='your_username'
export ATLAS_PASSWORD='your_password'
/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/fetch_mkn421_atlas_forced.py --token-only
```

The script prints the token. Then unset the password:

```bash
unset ATLAS_PASSWORD
```

Option B: if you already have a token, skip username/password and set:

```bash
export ATLAS_TOKEN='paste_token_here'
```

Do not put any of these values in a tracked file.

### 3. Queue And Download Mrk 421

With `ATLAS_TOKEN` set:

```bash
/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/fetch_mkn421_atlas_forced.py
```

Default request:

```text
ra=166.11383
dec=38.20883
mjd_min=59281.0
mjd_max=61129.0
```

The official API example documents `mjd_min`. The script sends `mjd_max` as well
to keep the downloaded product bounded to the LHAASO window. If the queue rejects
that optional field, rerun with:

```bash
/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/fetch_mkn421_atlas_forced.py --omit-mjd-max
```

Expected outputs:

```text
data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/atlas_forced_photometry_raw.txt
data/processed/multiwavelength/mkn421/optical_lhaaso_2021_2026/atlas_forced_photometry.csv
```

The ATLAS queue can be throttled or delayed. The script follows the official API
pattern: queue the request, poll the task URL, then download the result URL.

Useful options:

```bash
# Poll longer if the server queue is slow.
/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/fetch_mkn421_atlas_forced.py --max-poll-minutes 180

# Request only the daily-WCDA overlap window.
/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/fetch_mkn421_atlas_forced.py --mjd-min 60120 --mjd-max 61129
```

## After Download

For plotting against LHAASO:

1. Keep ASAS-SN `g` separate from ATLAS `c/o`.
2. Use only good-quality ASAS-SN points first: `quality == "G"` and `mag_err < 99`.
3. For ATLAS, inspect the returned columns before applying cuts; typical forced
   photometry products need S/N and quality filtering.
4. Convert magnitudes or forced-flux units to a common optical flux-density unit,
   preferably `mJy`, before putting optical bands on one y-axis.
5. Keep WCDA in a separate panel unless using a calibrated physical gamma-ray
   flux product.

## Sources

- ATLAS forced photometry API guide: <https://fallingstar-data.com/forcedphot/apiguide/>
- ASAS-SN Sky Patrol getting started: <https://asas-sn.github.io/skypatrol/getting_started.html>
- ASAS-SN Sky Patrol query docs: <https://asas-sn.github.io/skypatrol/queries.html>
- ASAS-SN Sky Patrol light-curve docs: <https://asas-sn.github.io/skypatrol/lightcurves.html>
