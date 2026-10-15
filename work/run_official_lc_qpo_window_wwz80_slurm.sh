#!/usr/bin/env bash
# Run one official WCDA 2-day MJD-window QPO analysis on the 80-division WWZ grid.
set -euo pipefail

window_key=${1:?usage: run_official_lc_qpo_window_wwz80_slurm.sh <bright|xgm>}
case "$window_key" in
  bright)
    window_min=59800
    window_max=60500
    output_key=bright_window_59800_60500
    target_period=140
    map_peak_args=(--mark-global-peaks-on-maps)
    ;;
  xgm)
    window_min=60200
    window_max=60700
    output_key=xgm_window_60200_60700
    target_period=51.05
    map_peak_args=()
    ;;
  *)
    echo "unknown window key: $window_key" >&2
    exit 2
    ;;
esac

exec /opt/anaconda3/bin/python3 src/pipeline/official_lc_xgm_window_qpo_analysis.py \
  --sources Mkn421 \
  --window-min "$window_min" \
  --window-max "$window_max" \
  --period-min 10 \
  --period-max 200 \
  --output-key "$output_key" \
  --target-period "$target_period" \
  "${map_peak_args[@]}" \
  --n-surrogates 200 \
  --workers "${SLURM_CPUS_PER_TASK:-8}" \
  --wwz-time-divisions 80 \
  --wwz-freq-step-factor 0.5
