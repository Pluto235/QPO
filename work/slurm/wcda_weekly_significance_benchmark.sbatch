#!/bin/bash
#SBATCH --job-name=qpo_sig_bench
#SBATCH --partition=main
#SBATCH --cpus-per-task=88
#SBATCH --mem=160G
#SBATCH --time=06:00:00
#SBATCH --output=work/slurm/logs/wcda_weekly_significance_benchmark_%j.out
#SBATCH --error=work/slurm/logs/wcda_weekly_significance_benchmark_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

START_EPOCH=$(date +%s)
echo "[INFO] host=$(hostname)"
echo "[INFO] start=$(date -Is)"
echo "[INFO] cwd=$(pwd)"
echo "[INFO] cpus=${SLURM_CPUS_PER_TASK:-88}"

/opt/anaconda3/bin/python3 src/pipeline/weekly_qpo_local_significance.py \
  --wcda-week-survey \
  --sources mkn421 \
  --n-surrogates 88 \
  --workers "${SLURM_CPUS_PER_TASK:-88}"

END_EPOCH=$(date +%s)
ELAPSED=$((END_EPOCH - START_EPOCH))
EST_SECONDS=$(python3 - <<PY
import math
elapsed = float(${ELAPSED})
print(int(math.ceil(elapsed * math.ceil(1000 / 88) * 10 * 1.2)))
PY
)
echo "[INFO] end=$(date -Is)"
echo "[INFO] benchmark_elapsed_seconds=${ELAPSED}"
echo "[INFO] estimated_full_seconds=${EST_SECONDS}"
