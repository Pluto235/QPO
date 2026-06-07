#!/bin/bash
#SBATCH --job-name=qpo_xgm_sig
#SBATCH --partition=main
#SBATCH --cpus-per-task=88
#SBATCH --mem=160G
#SBATCH --time=2-00:00:00
#SBATCH --output=work/slurm/logs/xgm_poster_wwz_significance_full_%j.out
#SBATCH --error=work/slurm/logs/xgm_poster_wwz_significance_full_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

echo "[INFO] host=$(hostname)"
echo "[INFO] start=$(date -Is)"
echo "[INFO] cwd=$(pwd)"
echo "[INFO] cpus=${SLURM_CPUS_PER_TASK:-88}"

/opt/anaconda3/bin/python3 src/pipeline/xgm_poster_wwz_significance.py \
  --n-surrogates 1000 \
  --workers "${SLURM_CPUS_PER_TASK:-88}"

/opt/anaconda3/bin/python3 src/pipeline/reproduce_xgm_poster.py

echo "[INFO] end=$(date -Is)"
