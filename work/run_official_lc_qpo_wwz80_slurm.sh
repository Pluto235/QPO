#!/usr/bin/env bash
# Run one source/cadence official-WCDA QPO task on the original 80-division WWZ grid.
set -euo pipefail

cadence=${1:?usage: run_official_lc_qpo_wwz80_slurm.sh <2day|8day>}
sources=(1ES1727p502 1ES1959p650 1ES2344p514 4C_p42d22 BLLacertae Crab IC310 M87 Mkn421 Mkn501 NGC1275)
source_token=${sources[${SLURM_ARRAY_TASK_ID:?SLURM_ARRAY_TASK_ID is required}]}

exec /opt/anaconda3/bin/python3 src/pipeline/official_lc_qpo_analysis.py \
  --cadences "$cadence" \
  --sources "$source_token" \
  --n-surrogates 200 \
  --workers "${SLURM_CPUS_PER_TASK:-8}" \
  --wwz-time-divisions 80 \
  --wwz-freq-step-factor 0.5 \
  --skip-summary
