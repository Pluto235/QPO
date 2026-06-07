#!/bin/bash
#SBATCH --job-name=qpo_sig_smoke
#SBATCH --partition=main
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=work/slurm/logs/wcda_weekly_significance_smoke_%j.out
#SBATCH --error=work/slurm/logs/wcda_weekly_significance_smoke_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

echo "[INFO] host=$(hostname)"
echo "[INFO] start=$(date -Is)"
echo "[INFO] cwd=$(pwd)"
echo "[INFO] cpus=${SLURM_CPUS_PER_TASK:-8}"

/opt/anaconda3/bin/python3 src/pipeline/weekly_qpo_local_significance.py \
  --wcda-week-survey \
  --sources mkn421 mkn501 \
  --n-surrogates 20 \
  --workers "${SLURM_CPUS_PER_TASK:-8}"

echo "[INFO] end=$(date -Is)"
