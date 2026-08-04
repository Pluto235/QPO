#!/bin/bash
#SBATCH --job-name=qpo_daily_sig_full
#SBATCH --partition=main
#SBATCH --cpus-per-task=32
#SBATCH --mem=96G
#SBATCH --time=3-00:00:00
#SBATCH --output=work/slurm/logs/daily_significance_full_%j.out
#SBATCH --error=work/slurm/logs/daily_significance_full_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

echo "[INFO] host=$(hostname)"
echo "[INFO] start=$(date -Is)"
echo "[INFO] cwd=$(pwd)"
echo "[INFO] cpus=${SLURM_CPUS_PER_TASK:-32}"

/opt/anaconda3/bin/python3 src/pipeline/daily_qpo_local_significance.py \
  --sources mkn421 mkn501 \
  --n-surrogates 1000 \
  --workers "${SLURM_CPUS_PER_TASK:-32}"

echo "[INFO] end=$(date -Is)"
