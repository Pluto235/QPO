#!/bin/bash
#SBATCH --job-name=qpo_flux_sig_bench
#SBATCH --partition=main
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=work/slurm/logs/strict_flux_significance_benchmark_%j.out
#SBATCH --error=work/slurm/logs/strict_flux_significance_benchmark_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

SOURCE_ID="${SOURCE_ID:-mkn421}"
N_SURROGATES="${N_SURROGATES:-64}"
WORKERS="${SLURM_CPUS_PER_TASK:-32}"

echo "[INFO] host=$(hostname)"
echo "[INFO] start=$(date -Is)"
echo "[INFO] source=${SOURCE_ID} n_surrogates=${N_SURROGATES} workers=${WORKERS}"
echo "[INFO] cpus=${SLURM_CPUS_PER_TASK:-unset} mem=${SLURM_MEM_PER_NODE:-unset}"
/usr/bin/time -v /opt/anaconda3/bin/python3 src/pipeline/strict_flux_weekly_significance.py \
  --sources "${SOURCE_ID}" \
  --n-surrogates "${N_SURROGATES}" \
  --workers "${WORKERS}"
echo "[INFO] end=$(date -Is)"
