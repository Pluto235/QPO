#!/bin/bash
#SBATCH --job-name=qpo_flux_sig
#SBATCH --partition=main
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=work/slurm/logs/strict_flux_significance_%x_%j.out
#SBATCH --error=work/slurm/logs/strict_flux_significance_%x_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

if [[ -z "${SOURCE_ID:-}" ]]; then
  echo "[ERROR] SOURCE_ID is required" >&2
  exit 2
fi
N_SURROGATES="${N_SURROGATES:-1000}"
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
