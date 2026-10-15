#!/bin/bash
#SBATCH --job-name=fermi_qpo
#SBATCH --partition=main
#SBATCH --array=0-3
#SBATCH --cpus-per-task=32
#SBATCH --mem=32G
#SBATCH --time=3-00:00:00
#SBATCH --output=work/slurm/logs/fermi_wcda_qpo_%A_%a.out
#SBATCH --error=work/slurm/logs/fermi_wcda_qpo_%A_%a.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

sources=(mkn421 mkn421 mkn501 mkn501)
cadences=(2day 8day 2day 8day)
task_id=${SLURM_ARRAY_TASK_ID:?SLURM_ARRAY_TASK_ID is required}

echo "[INFO] host=$(hostname) task=${task_id} source=${sources[$task_id]} cadence=${cadences[$task_id]} start=$(date -Is)"

/opt/anaconda3/bin/python3 src/pipeline/fermi_wcda_qpo_analysis.py \
  --sources "${sources[$task_id]}" \
  --cadences "${cadences[$task_id]}" \
  --flux-policy all-successful \
  --n-surrogates 1000 \
  --workers "${SLURM_CPUS_PER_TASK:-32}" \
  --wwz-time-divisions 80 \
  --wwz-freq-step-factor 0.5 \
  --skip-summary

echo "[INFO] end=$(date -Is)"
