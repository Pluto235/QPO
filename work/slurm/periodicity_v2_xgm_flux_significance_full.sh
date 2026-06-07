#!/bin/bash
#SBATCH --job-name=qpo_v2_xgm_sig
#SBATCH --partition=main
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=1-00:00:00
#SBATCH --output=work/slurm/logs/periodicity_v2_xgm_flux_significance_%j.out
#SBATCH --error=work/slurm/logs/periodicity_v2_xgm_flux_significance_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

echo "[INFO] host=$(hostname)"
echo "[INFO] start=$(date -Is)"
echo "[INFO] cwd=$(pwd)"
echo "[INFO] cpus=${SLURM_CPUS_PER_TASK:-32}"

/opt/anaconda3/bin/python3 src/pipeline/periodicity_v2_xgm_flux_significance.py \
  --n-surrogates 1000 \
  --workers "${SLURM_CPUS_PER_TASK:-32}"

echo "[INFO] end=$(date -Is)"
