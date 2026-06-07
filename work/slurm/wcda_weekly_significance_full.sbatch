#!/bin/bash
#SBATCH --job-name=qpo_sig_full
#SBATCH --partition=main
#SBATCH --cpus-per-task=88
#SBATCH --mem=160G
#SBATCH --time=3-00:00:00
#SBATCH --output=work/slurm/logs/wcda_weekly_significance_full_%j.out
#SBATCH --error=work/slurm/logs/wcda_weekly_significance_full_%j.err

set -euo pipefail

cd /mnt/mydisk/server/projects/QPO
mkdir -p work/slurm/logs

echo "[INFO] host=$(hostname)"
echo "[INFO] start=$(date -Is)"
echo "[INFO] cwd=$(pwd)"
echo "[INFO] cpus=${SLURM_CPUS_PER_TASK:-88}"

find data/processed/periodicity/agn_wcda_weekly_survey \
  \( -name 'wcda_weekly_local_significance.csv' \
     -o -name 'wcda_weekly_cwt_global_significance.png' \
     -o -name 'wcda_weekly_wwz_global_significance.png' \
     -o -name 'agn_wcda_weekly_significance_summary.csv' \) \
  -delete

/opt/anaconda3/bin/python3 src/pipeline/weekly_qpo_local_significance.py \
  --wcda-week-survey \
  --n-surrogates 1000 \
  --workers "${SLURM_CPUS_PER_TASK:-88}"

/opt/anaconda3/bin/python3 src/pipeline/build_agn_wcda_weekly_survey_report.py

echo "[INFO] end=$(date -Is)"
